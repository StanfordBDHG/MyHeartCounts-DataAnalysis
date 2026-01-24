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


@pytest.fixture
def sample_fhir_hk_quantity_doc() -> dict[str, Any]:
    """Provide sample FHIR HK quantity observation document."""
    return {
        "identifier": [
            {"id": "037758F0-5944-43D1-B99A-398C4B10B05B"},
        ],
        "effectivePeriod": {
            "start": "2024-01-15T10:30:00.123456789-06:00",
            "end": "2024-01-15T10:30:05.987654321-06:00",
        },
        "valueQuantity": {
            "value": 72.5,
            "unit": "count/min",
        },
        "extension": [
            {
                "url": "https://bdh.stanford.edu/fhir/defs/sampleUploadTimeZone",
                "valueString": "America/Chicago",
            },
            {
                "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice",
                "extension": [
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice/name",
                        "valueString": "Apple Watch",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice/manufacturer",
                        "valueString": "Apple Inc.",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice/model",
                        "valueString": "Watch",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice/hardwareVersion",
                        "valueString": "Watch6,12",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceDevice/softwareVersion",
                        "valueString": "26.3",
                    },
                ],
            },
            {
                "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision",
                "extension": [
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/source",
                        "extension": [
                            {
                                "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/source/name",
                                "valueString": "My App",
                            },
                            {
                                "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/source/bundleIdentifier",
                                "valueString": "com.apple.health.123",
                            },
                        ],
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/version",
                        "valueString": "3068.0.7.0.1",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/productType",
                        "valueString": "Watch6,12",
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sourceRevision/OSVersion",
                        "valueString": "26.3.0",
                    },
                ],
            },
            {
                "url": "https://bh.stanford.edu/fhir/defs/metadata",
                "extension": [
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/metadata/HKMetadataKeyHeartRateMotionContext",
                        "valueDecimal": 1,
                    },
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/metadata/HKMetadataKeyDevicePlacementSide",
                        "valueString": "left",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_fhir_hk_quantity_doc_minimal() -> dict[str, Any]:
    """Provide minimal FHIR HK quantity doc with missing optional fields."""
    return {
        "effectivePeriod": {
            "start": "2024-01-15T10:30:00Z",
            "end": "2024-01-15T10:30:05Z",
        },
        "valueQuantity": {
            "value": 100,
            "unit": "count",
        },
        "extension": [],
    }


@pytest.fixture
def mock_storage_client() -> MagicMock:
    """Provide a mocked GCS storage client."""
    return MagicMock()


@pytest.fixture
def sample_historic_hk_records() -> list[dict[str, Any]]:
    """Provide sample historic HK records as would be found in GCS JSON files."""
    return [
        {
            "identifier": [{"id": "historic-sample-1"}],
            "effectivePeriod": {
                "start": "2024-01-10T08:00:00Z",
                "end": "2024-01-10T08:00:05Z",
            },
            "valueQuantity": {"value": 65.0, "unit": "count/min"},
            "extension": [
                {
                    "url": "https://bdh.stanford.edu/fhir/defs/sampleUploadTimeZone",
                    "valueString": "America/New_York",
                },
            ],
        },
        {
            "identifier": [{"id": "historic-sample-2"}],
            "effectivePeriod": {
                "start": "2024-01-10T09:00:00Z",
                "end": "2024-01-10T09:00:05Z",
            },
            "valueQuantity": {"value": 72.0, "unit": "count/min"},
            "extension": [],
        },
    ]
