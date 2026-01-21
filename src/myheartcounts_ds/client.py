"""Client for accessing MyHeartCounts Firebase data."""

from __future__ import annotations

import random
from typing import Any

from google.cloud import firestore_v1 as firestore

from myheartcounts_ds.config import MHCConfig
from myheartcounts_ds.constants import HEALTHKIT_COLLECTION_PREFIX, ObservationType
from myheartcounts_ds.models import User


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
        category: ObservationType = ObservationType.ALL,
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
            if collection.id.startswith(HEALTHKIT_COLLECTION_PREFIX):
                type_id = collection.id[len(HEALTHKIT_COLLECTION_PREFIX) :]
                # Filter by category if specified
                if category == ObservationType.ALL or type_id.startswith(category.value):
                    types.add(type_id)

        return types

    def _list_observation_types_by_category(
        self,
        category: ObservationType,
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
        return self._list_observation_types_by_category(ObservationType.ALL, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HEALTHKIT, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.MHC_CUSTOM, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.SENSORKIT, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_QUANTITY, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_CATEGORY, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_CORRELATION, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_WORKOUT, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_CLINICAL, user, user_limit)

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
        return self._list_observation_types_by_category(ObservationType.HK_DATA, user, user_limit)
