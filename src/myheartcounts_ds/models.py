"""Data models for MyHeartCounts data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    """Represents a MyHeartCounts user profile.

    Attributes:
        id: Firebase Auth UID (document ID).
        disabled: Whether the user account is disabled.
        date_of_birth: User's date of birth.
        date_of_enrollment: When the user enrolled in the study.
        last_active_date: Last activity timestamp.
        language: Preferred language code.
        time_zone: IANA timezone identifier.
        participant_group: Study group assignment.
        biological_sex_at_birth: Coded biological sex.
        blood_type: Coded blood type.
        height_in_cm: Height in centimeters.
        weight_in_kg: Weight in kilograms.
        us_region: US state/region code.
        education_us: Education level.
        household_income_us: Coded household income.
        race_ethnicity: Coded race/ethnicity.
        latino_status: Coded Latino/Hispanic status.
        mhc_gender_identity: Coded gender identity.
        comorbidities: Dictionary of comorbidity data.
        stage_of_change: Current stage of change.
        did_opt_in_to_trial: Whether user opted into trial.
        future_studies: Whether user consented to future studies.
        last_signed_consent_date: When user last signed consent.
        last_signed_consent_version: Version of consent signed.
        most_recent_onboarding_step: Last completed onboarding step.
        preferred_notification_time: Preferred time for notifications.
        preferred_workout_types: Preferred workout types.
    """

    id: str
    disabled: bool = False

    date_of_birth: datetime | None = None
    date_of_enrollment: datetime | None = None
    last_active_date: datetime | None = None

    language: str | None = None
    time_zone: str | None = None
    participant_group: int | None = None

    biological_sex_at_birth: int | None = None
    blood_type: int | None = None
    height_in_cm: float | None = None
    weight_in_kg: float | None = None

    us_region: str | None = None
    education_us: str | None = None
    household_income_us: int | None = None
    race_ethnicity: int | None = None
    latino_status: int | None = None
    mhc_gender_identity: int | None = None

    comorbidities: dict[str, Any] | None = None
    stage_of_change: str | None = None

    did_opt_in_to_trial: bool | None = None
    future_studies: bool | None = None
    last_signed_consent_date: datetime | None = None
    last_signed_consent_version: str | None = None
    most_recent_onboarding_step: str | None = None
    preferred_notification_time: str | None = None
    preferred_workout_types: str | None = None

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict[str, Any]) -> User:
        """Create a User from a Firestore document.

        Args:
            doc_id: The Firestore document ID (user's Firebase UID).
            data: The document data dictionary.

        Returns:
            A User instance populated with the document data.
        """
        return cls(
            id=doc_id,
            disabled=data.get("disabled", False),
            date_of_birth=_to_datetime(data.get("dateOfBirth")),
            date_of_enrollment=_to_datetime(data.get("dateOfEnrollment")),
            last_active_date=_to_datetime(data.get("lastActiveDate")),
            language=data.get("language"),
            time_zone=data.get("timeZone"),
            participant_group=data.get("participantGroup"),
            biological_sex_at_birth=data.get("biologicalSexAtBirth"),
            blood_type=data.get("bloodType"),
            height_in_cm=data.get("heightInCM"),
            weight_in_kg=data.get("weightInKG"),
            us_region=data.get("usRegion"),
            education_us=data.get("educationUS"),
            household_income_us=data.get("householdIncomeUS"),
            race_ethnicity=data.get("raceEthnicity"),
            latino_status=data.get("latinoStatus"),
            mhc_gender_identity=data.get("mhcGenderIdentity"),
            comorbidities=data.get("comorbidities"),
            stage_of_change=data.get("stageOfChange"),
            did_opt_in_to_trial=data.get("didOptInToTrial"),
            future_studies=data.get("futureStudies"),
            last_signed_consent_date=_to_datetime(data.get("lastSignedConsentDate")),
            last_signed_consent_version=data.get("lastSignedConsentVersion"),
            most_recent_onboarding_step=data.get("mostRecentOnboardingStep"),
            preferred_notification_time=data.get("preferredNotificationTime"),
            preferred_workout_types=data.get("preferredWorkoutTypes"),
        )


def _to_datetime(value: Any) -> datetime | None:
    """Convert a Firestore timestamp or datetime to a Python datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Handle Firestore DatetimeWithNanoseconds which is a datetime subclass
    # but might not be recognized by isinstance due to import differences
    if hasattr(value, "timestamp"):
        # Convert to standard datetime to ensure consistent type
        return datetime.fromtimestamp(value.timestamp(), tz=value.tzinfo)
    return None
