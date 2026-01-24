"""Tests for User model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from myheartcounts_ds.models import User


class TestUserFromFirestore:
    """Tests for User.from_firestore() method."""

    def test_parses_complete_document(self, sample_user_data: dict[str, Any]) -> None:
        """User.from_firestore() parses all fields from complete document."""
        user = User.from_firestore("user-123", sample_user_data)

        assert user.id == "user-123"
        assert user.disabled is False
        assert user.date_of_birth == datetime(1990, 5, 15, tzinfo=timezone.utc)
        assert user.date_of_enrollment == datetime(
            2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc
        )
        assert user.last_active_date == datetime(
            2024, 6, 1, 8, 30, 0, tzinfo=timezone.utc
        )
        assert user.language == "en"
        assert user.time_zone == "America/Los_Angeles"
        assert user.participant_group == 1
        assert user.biological_sex_at_birth == 1
        assert user.blood_type == 2
        assert user.height_in_cm == 175.5
        assert user.weight_in_kg == 70.0
        assert user.us_region == "CA"
        assert user.education_us == "bachelors"
        assert user.household_income_us == 3
        assert user.race_ethnicity == 1
        assert user.latino_status == 0
        assert user.mhc_gender_identity == 1
        assert user.comorbidities == {"diabetes": False, "hypertension": True}
        assert user.stage_of_change == "action"
        assert user.did_opt_in_to_trial is True
        assert user.future_studies is True
        assert user.last_signed_consent_date == datetime(
            2024, 1, 10, 11, 0, 0, tzinfo=timezone.utc
        )
        assert user.last_signed_consent_version == "1.2"
        assert user.most_recent_onboarding_step == "complete"
        assert user.preferred_notification_time == "09:00"
        assert user.preferred_workout_types == "running,cycling"

    def test_handles_empty_document(self, minimal_user_data: dict[str, Any]) -> None:
        """User.from_firestore() handles document with no optional fields."""
        user = User.from_firestore("user-456", minimal_user_data)

        assert user.id == "user-456"
        assert user.disabled is False
        assert user.date_of_birth is None
        assert user.date_of_enrollment is None
        assert user.last_active_date is None
        assert user.language is None
        assert user.time_zone is None
        assert user.participant_group is None
        assert user.biological_sex_at_birth is None
        assert user.blood_type is None
        assert user.height_in_cm is None
        assert user.weight_in_kg is None
        assert user.us_region is None
        assert user.education_us is None
        assert user.household_income_us is None
        assert user.race_ethnicity is None
        assert user.latino_status is None
        assert user.mhc_gender_identity is None
        assert user.comorbidities is None
        assert user.stage_of_change is None
        assert user.did_opt_in_to_trial is None
        assert user.future_studies is None
        assert user.last_signed_consent_date is None
        assert user.last_signed_consent_version is None
        assert user.most_recent_onboarding_step is None
        assert user.preferred_notification_time is None
        assert user.preferred_workout_types is None

    def test_handles_none_values_for_optional_fields(self) -> None:
        """User.from_firestore() handles explicit None values for optional fields."""
        data = {
            "dateOfBirth": None,
            "dateOfEnrollment": None,
            "lastActiveDate": None,
            "language": None,
            "timeZone": None,
            "participantGroup": None,
        }
        user = User.from_firestore("user-789", data)

        assert user.id == "user-789"
        # disabled defaults to False when not in data
        assert user.disabled is False
        assert user.date_of_birth is None
        assert user.language is None

    def test_converts_datetime_fields(self) -> None:
        """User.from_firestore() converts datetime fields properly."""
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        data = {
            "dateOfBirth": dt,
            "dateOfEnrollment": dt,
            "lastActiveDate": dt,
            "lastSignedConsentDate": dt,
        }
        user = User.from_firestore("user-dt", data)

        assert user.date_of_birth == dt
        assert user.date_of_enrollment == dt
        assert user.last_active_date == dt
        assert user.last_signed_consent_date == dt

    def test_maps_camelcase_to_snake_case(self) -> None:
        """User.from_firestore() maps camelCase Firestore keys to snake_case."""
        data = {
            "dateOfBirth": datetime(1990, 1, 1, tzinfo=timezone.utc),
            "dateOfEnrollment": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "lastActiveDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "timeZone": "UTC",
            "participantGroup": 2,
            "biologicalSexAtBirth": 1,
            "bloodType": 3,
            "heightInCM": 180.0,
            "weightInKG": 75.0,
            "usRegion": "NY",
            "educationUS": "masters",
            "householdIncomeUS": 4,
            "raceEthnicity": 2,
            "latinoStatus": 1,
            "mhcGenderIdentity": 2,
            "stageOfChange": "preparation",
            "didOptInToTrial": False,
            "futureStudies": False,
            "lastSignedConsentDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "lastSignedConsentVersion": "2.0",
            "mostRecentOnboardingStep": "consent",
            "preferredNotificationTime": "18:00",
            "preferredWorkoutTypes": "walking",
        }
        user = User.from_firestore("user-case", data)

        # Verify snake_case attributes are populated from camelCase keys
        assert user.date_of_birth is not None
        assert user.date_of_enrollment is not None
        assert user.last_active_date is not None
        assert user.time_zone == "UTC"
        assert user.participant_group == 2
        assert user.biological_sex_at_birth == 1
        assert user.blood_type == 3
        assert user.height_in_cm == 180.0
        assert user.weight_in_kg == 75.0
        assert user.us_region == "NY"
        assert user.education_us == "masters"
        assert user.household_income_us == 4
        assert user.race_ethnicity == 2
        assert user.latino_status == 1
        assert user.mhc_gender_identity == 2
        assert user.stage_of_change == "preparation"
        assert user.did_opt_in_to_trial is False
        assert user.future_studies is False
        assert user.last_signed_consent_date is not None
        assert user.last_signed_consent_version == "2.0"
        assert user.most_recent_onboarding_step == "consent"
        assert user.preferred_notification_time == "18:00"
        assert user.preferred_workout_types == "walking"

    def test_handles_firestore_timestamp_with_timestamp_method(self) -> None:
        """User.from_firestore() handles objects with timestamp() method."""

        class MockFirestoreTimestamp:
            """Mock Firestore DatetimeWithNanoseconds."""

            def __init__(self, ts: float, tz: timezone) -> None:
                self._ts = ts
                self.tzinfo = tz

            def timestamp(self) -> float:
                return self._ts

        ts = datetime(2024, 5, 20, 14, 30, 0, tzinfo=timezone.utc).timestamp()
        mock_ts = MockFirestoreTimestamp(ts, timezone.utc)

        data = {"dateOfBirth": mock_ts}
        user = User.from_firestore("user-ts", data)

        assert user.date_of_birth is not None
        assert user.date_of_birth.year == 2024
        assert user.date_of_birth.month == 5
        assert user.date_of_birth.day == 20
