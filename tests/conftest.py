"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Provide sample Firestore user document data."""
    return {
        "disabled": False,
        "dateOfBirth": datetime(1990, 5, 15, tzinfo=timezone.utc),
        "dateOfEnrollment": datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
        "lastActiveDate": datetime(2024, 6, 1, 8, 30, 0, tzinfo=timezone.utc),
        "language": "en",
        "timeZone": "America/Los_Angeles",
        "participantGroup": 1,
        "biologicalSexAtBirth": 1,
        "bloodType": 2,
        "heightInCM": 175.5,
        "weightInKG": 70.0,
        "usRegion": "CA",
        "educationUS": "bachelors",
        "householdIncomeUS": 3,
        "raceEthnicity": 1,
        "latinoStatus": 0,
        "mhcGenderIdentity": 1,
        "comorbidities": {"diabetes": False, "hypertension": True},
        "stageOfChange": "action",
        "didOptInToTrial": True,
        "futureStudies": True,
        "lastSignedConsentDate": datetime(2024, 1, 10, 11, 0, 0, tzinfo=timezone.utc),
        "lastSignedConsentVersion": "1.2",
        "mostRecentOnboardingStep": "complete",
        "preferredNotificationTime": "09:00",
        "preferredWorkoutTypes": "running,cycling",
    }


@pytest.fixture
def minimal_user_data() -> dict[str, Any]:
    """Provide minimal Firestore user document data with only required fields."""
    return {}


@pytest.fixture
def mock_firestore_client() -> MagicMock:
    """Provide a mocked Firestore client."""
    return MagicMock()
