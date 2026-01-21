"""Client for accessing MyHeartCounts Firebase data."""

from __future__ import annotations

import random
import re
from datetime import datetime
from typing import Any

import pandas as pd
from google.cloud import firestore_v1 as firestore

from myheartcounts_ds.config import MHCConfig
from myheartcounts_ds.constants import (
    HEALTH_OBSERVATION_COLLECTION_PREFIX,
    HealthObservationsType,
)
from myheartcounts_ds.models import User
from myheartcounts_ds.typegen.generated_types import DiscoveredObservationType


def _parse_timestamp_naive(timestamp_str: str) -> datetime | None:
    """Parse ISO 8601 timestamp, returning timezone-naive datetime.

    Handles nanosecond precision (truncates to microseconds).
    Strips timezone suffix (-06:00, Z, etc.) for naive comparison.

    Args:
        timestamp_str: ISO 8601 formatted timestamp string.

    Returns:
        Timezone-naive datetime, or None if parsing fails.
    """
    if not timestamp_str:
        return None

    # Strip timezone suffix: handles +HH:MM, -HH:MM, Z
    # Pattern matches: 2024-01-15T10:30:00.123456789-06:00
    timestamp_str = re.sub(r"([+-]\d{2}:\d{2}|Z)$", "", timestamp_str)

    # Truncate nanoseconds to microseconds (6 digits after decimal)
    # Match datetime portion with optional fractional seconds
    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?", timestamp_str)
    if not match:
        return None

    base_time = match.group(1)
    fraction = match.group(2)

    if fraction:
        # Pad or truncate to exactly 6 digits (microseconds)
        fraction = fraction[:6].ljust(6, "0")
        timestamp_str = f"{base_time}.{fraction}"
    else:
        timestamp_str = base_time

    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None


def _extract_extension_value(extensions: list[dict], url_suffix: str) -> dict | None:
    """Extract extension object by URL suffix.

    Args:
        extensions: List of FHIR extension objects.
        url_suffix: The URL suffix to match (e.g., "sampleUploadTimeZone").

    Returns:
        The matching extension object, or None if not found.
    """
    for ext in extensions:
        url = ext.get("url", "")
        if url.endswith(url_suffix):
            return ext
    return None


def _extract_nested_extension_value(
    extension: dict | None, nested_url_suffix: str
) -> str | None:
    """Extract valueString from nested extension.

    Args:
        extension: FHIR extension object containing nested extensions.
        nested_url_suffix: The URL suffix to match in nested extensions.

    Returns:
        The valueString of the matching nested extension, or None if not found.
    """
    if extension is None:
        return None

    nested_extensions = extension.get("extension", [])
    for nested in nested_extensions:
        url = nested.get("url", "")
        if url.endswith(nested_url_suffix):
            value = nested.get("valueString")
            return str(value) if value is not None else None
    return None


def _extract_metadata(extensions: list[dict]) -> dict[str, Any] | None:
    """Extract metadata fields from FHIR extensions.

    Metadata is nested inside a parent extension with URL ending in "/metadata".
    The actual metadata keys are in the nested extension array with URLs like:
    https://bdh.stanford.edu/fhir/defs/metadata/<key>

    Args:
        extensions: List of FHIR extension objects.

    Returns:
        Dictionary of metadata key-value pairs, or None if no metadata found.
        Keys are the metadata key names (e.g., "HKMetadataKeyHeartRateMotionContext").
    """
    metadata: dict[str, Any] = {}

    # Find the parent metadata extension (URL ends with "/metadata")
    # Note: URL may use "bh" or "bdh" prefix
    for ext in extensions:
        url = ext.get("url", "")
        if url.endswith("/metadata"):
            # Look inside nested extensions for actual metadata fields
            nested_extensions = ext.get("extension", [])
            for nested in nested_extensions:
                nested_url = nested.get("url", "")
                # Extract key from URL like ".../metadata/HKMetadataKeyHeartRateMotionContext"
                if "/metadata/" in nested_url:
                    key = nested_url.split("/metadata/")[-1]
                    # Extract the value - could be valueString, valueInteger, etc.
                    value = None
                    for value_key in (
                        "valueString",
                        "valueInteger",
                        "valueDecimal",
                        "valueBoolean",
                    ):
                        if value_key in nested:
                            value = nested[value_key]
                            break
                    if value is not None:
                        metadata[key] = value

    return metadata if metadata else None


def _parse_hk_quantity_record(doc_data: dict) -> dict:
    """Parse FHIR HK quantity observation into flat dict matching DataFrame columns.

    Args:
        doc_data: Raw Firestore document data containing FHIR observation.

    Returns:
        Dictionary with keys matching DataFrame column names.
    """
    extensions = doc_data.get("extension", [])

    # Extract timestamps from effectivePeriod or effectiveDateTime
    effective_period = doc_data.get("effectivePeriod", {})
    start_time = _parse_timestamp_naive(effective_period.get("start", ""))
    end_time = _parse_timestamp_naive(effective_period.get("end", ""))

    # Fallback to effectiveDateTime for point-in-time observations
    if start_time is None or end_time is None:
        effective_datetime = doc_data.get("effectiveDateTime", "")
        point_time = _parse_timestamp_naive(effective_datetime)
        if point_time is not None:
            if start_time is None:
                start_time = point_time
            if end_time is None:
                end_time = point_time

    # Extract timezone (top-level extension)
    tz_ext = _extract_extension_value(extensions, "sampleUploadTimeZone")
    source_timezone = tz_ext.get("valueString") if tz_ext else None

    # Extract sourceRevision fields
    source_revision_ext = _extract_extension_value(extensions, "sourceRevision")
    source_revision_extensions = (
        source_revision_ext.get("extension", []) if source_revision_ext else []
    )

    # Extract source info from sourceRevision/source
    source_ext = _extract_extension_value(source_revision_extensions, "/source")
    source_name = _extract_nested_extension_value(source_ext, "/name")
    source_bundle_id = _extract_nested_extension_value(source_ext, "/bundleIdentifier")

    # Extract other sourceRevision fields
    source_version = _extract_nested_extension_value(source_revision_ext, "/version")
    source_product_type = _extract_nested_extension_value(
        source_revision_ext, "/productType"
    )
    source_os_version = _extract_nested_extension_value(
        source_revision_ext, "/OSVersion"
    )

    # Extract sourceDevice fields (no fallbacks)
    source_device_ext = _extract_extension_value(extensions, "sourceDevice")
    device_name = _extract_nested_extension_value(source_device_ext, "/name")
    device_manufacturer = _extract_nested_extension_value(
        source_device_ext, "/manufacturer"
    )
    device_model = _extract_nested_extension_value(source_device_ext, "/model")
    device_hardware_version = _extract_nested_extension_value(
        source_device_ext, "/hardwareVersion"
    )
    device_software_version = _extract_nested_extension_value(
        source_device_ext, "/softwareVersion"
    )

    # Extract metadata fields
    metadata = _extract_metadata(extensions)

    # Extract sample ID from identifier array
    identifiers = doc_data.get("identifier", [])
    sample_id = identifiers[0].get("id") if identifiers else None

    # Extract value and unit
    value_quantity = doc_data.get("valueQuantity", {})
    value = value_quantity.get("value")
    unit = value_quantity.get("unit")

    return {
        "sample_id": sample_id,
        "start_time": start_time,
        "end_time": end_time,
        "value": value,
        "unit": unit,
        "source_timezone": source_timezone,
        "source_name": source_name,
        "source_bundle_id": source_bundle_id,
        "source_version": source_version,
        "source_product_type": source_product_type,
        "source_os_version": source_os_version,
        "device_name": device_name,
        "device_manufacturer": device_manufacturer,
        "device_model": device_model,
        "device_hardware_version": device_hardware_version,
        "device_software_version": device_software_version,
        "metadata": metadata,
    }


class MHC4Client:
    """Client for accessing MyHeartCounts Firebase/Firestore data.

    Uses Application Default Credentials (ADC) for authentication.
    Run `gcloud auth application-default login` to set up credentials.

    Example:
        >>> client = MHCClient()
        >>> users = client.list_users(limit=10)
        >>> for user in users:
        ...     print(user.id, user.date_of_enrollment)
    """

    def __init__(self, config: MHCConfig | None = None) -> None:
        """Initialize the client.

        Args:
            config: Configuration for the Firebase project. If None,
                uses MHCConfig.from_env() which defaults to production.
        """
        self._config = config or MHCConfig.from_env()
        self._db: firestore.Client | None = None

    @property
    def config(self) -> MHCConfig:
        """Return the current configuration."""
        return self._config

    @property
    def db(self) -> firestore.Client:
        """Return the Firestore client, creating it if necessary."""
        if self._db is None:
            self._db = firestore.Client(project=self._config.project_id)
        return self._db

    def list_users(self, limit: int | None = None) -> list[User]:
        """List all users in the database.

        Args:
            limit: Maximum number of users to return. If None, returns all users.

        Returns:
            List of User objects.
        """
        collection_ref: Any = self.db.collection("users")

        if limit is not None:
            collection_ref = collection_ref.limit(limit)

        users: list[User] = []
        for doc in collection_ref.stream():
            data: dict[str, Any] = doc.to_dict() or {}
            user = User.from_firestore(doc.id, data)
            users.append(user)

        return users

    def get_user(self, user_id: str) -> User | None:
        """Get a specific user by ID.

        Args:
            user_id: The Firebase Auth UID of the user.

        Returns:
            User object if found, None otherwise.
        """
        doc_ref: Any = self.db.collection("users").document(user_id)
        doc: Any = doc_ref.get()

        if not doc.exists:
            return None

        data: dict[str, Any] = doc.to_dict() or {}
        return User.from_firestore(doc.id, data)

    def _get_user_observation_types(
        self,
        user_id: str,
        category: HealthObservationsType = HealthObservationsType.ALL,
    ) -> set[str]:
        """Get observation types for a single user, optionally filtered by category.

        Args:
            user_id: The Firebase Auth UID of the user.
            category: The category to filter by. Use ObservationType.ALL for no filtering.

        Returns:
            Set of observation type identifiers found in the user's subcollections.
        """
        user_doc_ref: Any = self.db.collection("users").document(user_id)
        types: set[str] = set()

        for collection in user_doc_ref.collections():
            if collection.id.startswith(HEALTH_OBSERVATION_COLLECTION_PREFIX):
                type_id = collection.id[len(HEALTH_OBSERVATION_COLLECTION_PREFIX) :]
                # Filter by category if specified
                if category == HealthObservationsType.ALL or type_id.startswith(
                    category.value
                ):
                    types.add(type_id)

        return types

    def _list_observation_types_by_category(
        self,
        category: HealthObservationsType,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """Generic method to list observation types by category.

        Args:
            category: The category to filter by.
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of observation type identifiers.
        """
        if user is not None:
            return self._get_user_observation_types(user, category)

        all_users = self.list_users()

        if len(all_users) > user_limit:
            sampled_users = random.sample(all_users, user_limit)
        else:
            sampled_users = all_users

        all_types: set[str] = set()
        for u in sampled_users:
            all_types.update(self._get_user_observation_types(u.id, category))

        return all_types

    # Public API methods

    def list_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List all observation types (HealthKit, MHC Custom, and SensorKit).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of all observation type identifiers.
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.ALL, user, user_limit
        )

    def list_healthkit_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit observation types (HK* identifiers).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit type identifiers (e.g., 'HKQuantityTypeIdentifierStepCount').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HEALTHKIT, user, user_limit
        )

    def list_mhc_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List MHC custom observation types (MHC* identifiers).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of MHC custom type identifiers (e.g., 'MHCCustomSampleTypeDietMEPAScore').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.MHC_CUSTOM, user, user_limit
        )

    def list_sensorkit_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List SensorKit observation types (com.apple.SensorKit.* identifiers).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of SensorKit type identifiers (e.g., 'com.apple.SensorKit.heart.rate').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.SENSORKIT, user, user_limit
        )

    # HealthKit subcategory methods

    def list_hk_quantity_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit quantity observation types (HKQuantityTypeIdentifier*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit quantity type identifiers (e.g., 'HKQuantityTypeIdentifierHeartRate').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_QUANTITY, user, user_limit
        )

    def list_hk_category_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit category observation types (HKCategoryTypeIdentifier*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit category type identifiers (e.g., 'HKCategoryTypeIdentifierSleepAnalysis').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_CATEGORY, user, user_limit
        )

    def list_hk_correlation_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit correlation observation types (HKCorrelationTypeIdentifier*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit correlation type identifiers (e.g., 'HKCorrelationTypeIdentifierBloodPressure').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_CORRELATION, user, user_limit
        )

    def list_hk_workout_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit workout observation types (HKWorkoutTypeIdentifier*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit workout type identifiers (e.g., 'HKWorkoutTypeIdentifier').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_WORKOUT, user, user_limit
        )

    def list_hk_clinical_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit clinical observation types (HKClinicalTypeIdentifier*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit clinical type identifiers (e.g., 'HKClinicalTypeIdentifierLabResultRecord').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_CLINICAL, user, user_limit
        )

    def list_hk_data_observation_types(
        self,
        user: str | None = None,
        user_limit: int = 100,
    ) -> set[str]:
        """List HealthKit data observation types (HKDataType*).

        Args:
            user: If specified, return types for this user only.
                If None, sample from all users.
            user_limit: Maximum number of users to sample when user is None.

        Returns:
            Set of HealthKit data type identifiers (e.g., 'HKDataTypeIdentifierHeartbeatSeries').
        """
        return self._list_observation_types_by_category(
            HealthObservationsType.HK_DATA, user, user_limit
        )

    def get_hk_quantity(
        self,
        observation_type: DiscoveredObservationType,
        user_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> pd.DataFrame:
        """Get HealthKit quantity observations for a user.

        Retrieves HK quantity records from Firestore and returns them as a
        typed pandas DataFrame.

        Args:
            observation_type: The HK quantity type to retrieve. Must be a
                DiscoveredObservationType member with name starting with "HK_QUANTITY_".
            user_id: The Firebase Auth UID of the user.
            start_time: If provided, only return records where start_time >= this value.
                Must be timezone-naive for comparison with database timestamps.
            end_time: If provided, only return records where start_time < this value.
                Must be timezone-naive for comparison with database timestamps.

        Returns:
            DataFrame with columns:
                - sample_id: str - unique identifier for the sample (from identifier/id)
                - start_time: datetime64[ns] - observation start time (naive)
                - end_time: datetime64[ns] - observation end time (naive)
                - value: float64 - the measured quantity value
                - unit: str - unit of measurement
                - source_timezone: str - timezone of the recording device
                - source_name: str - name of the data source (e.g., app name)
                - source_bundle_id: str - bundle identifier of the source app
                - source_version: str - version of the source app
                - source_product_type: str - product type from sourceRevision
                - source_os_version: str - OS version from sourceRevision
                - device_name: str - device name from sourceDevice
                - device_manufacturer: str - device manufacturer
                - device_model: str - device model identifier
                - device_hardware_version: str - hardware version from sourceDevice
                - device_software_version: str - software version from sourceDevice
                - metadata: dict | None - HK metadata fields as key-value pairs

        Raises:
            ValueError: If observation_type is not an HK_QUANTITY_* type.

        Example:
            >>> from myheartcounts_ds import MHC4Client, DiscoveredObservationType
            >>> client = MHC4Client()
            >>> df = client.get_hk_quantity(
            ...     DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            ...     user_id="abc123",
            ...     start_time=datetime(2024, 1, 1),
            ...     end_time=datetime(2024, 2, 1),
            ... )
        """
        # Validate that observation_type is an HK quantity type
        if not observation_type.name.startswith("HK_QUANTITY_"):
            raise ValueError(
                f"observation_type must be an HK_QUANTITY_* type, got {observation_type.name}"
            )

        # Build collection path
        collection_name = f"{HEALTH_OBSERVATION_COLLECTION_PREFIX}{observation_type.value}"
        collection_ref: Any = self.db.collection("users").document(user_id).collection(
            collection_name
        )

        # Fetch all documents from the collection
        records: list[dict] = []
        for doc in collection_ref.stream():
            doc_data: dict[str, Any] = doc.to_dict() or {}
            parsed = _parse_hk_quantity_record(doc_data)

            # Apply time filtering
            record_start = parsed.get("start_time")
            if start_time is not None and record_start is not None:
                if record_start < start_time:
                    continue
            if end_time is not None and record_start is not None:
                if record_start >= end_time:
                    continue

            records.append(parsed)

        # Create DataFrame with proper column types
        df = pd.DataFrame(
            records,
            columns=[
                "sample_id",
                "start_time",
                "end_time",
                "value",
                "unit",
                "source_timezone",
                "source_name",
                "source_bundle_id",
                "source_version",
                "source_product_type",
                "source_os_version",
                "device_name",
                "device_manufacturer",
                "device_model",
                "device_hardware_version",
                "device_software_version",
                "metadata",
            ],
        )

        # Convert types
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df
