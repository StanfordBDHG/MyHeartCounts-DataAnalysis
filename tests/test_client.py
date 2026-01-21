"""Tests for MHC4Client."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from myheartcounts_ds.client import MHC4Client
from myheartcounts_ds.config import MHCConfig
from myheartcounts_ds.models import User
from myheartcounts_ds.typegen.generated_types import DiscoveredObservationType


class TestMHC4ClientInit:
    """Tests for MHC4Client initialization."""

    def test_uses_provided_config(self) -> None:
        """Client uses the provided config."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        assert client.config.project_id == "test-project"

    def test_defaults_to_from_env_config(self) -> None:
        """Client defaults to MHCConfig.from_env() when no config provided."""
        with patch.dict(os.environ, {"MHC_PROJECT_ID": "env-project"}):
            client = MHC4Client()
            assert client.config.project_id == "env-project"


class TestMHC4ClientListUsers:
    """Tests for MHC4Client.list_users() method."""

    def test_returns_list_of_users(
        self, mock_firestore_client: MagicMock, sample_user_data: dict[str, Any]
    ) -> None:
        """list_users() returns a list of User objects."""
        # Setup mock documents
        mock_doc1 = MagicMock()
        mock_doc1.id = "user-1"
        mock_doc1.to_dict.return_value = sample_user_data

        mock_doc2 = MagicMock()
        mock_doc2.id = "user-2"
        mock_doc2.to_dict.return_value = {"language": "es"}

        # Setup mock collection
        mock_collection = MagicMock()
        mock_collection.stream.return_value = [mock_doc1, mock_doc2]
        mock_firestore_client.collection.return_value = mock_collection

        # Create client and inject mock
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        users = client.list_users()

        assert len(users) == 2
        assert all(isinstance(u, User) for u in users)
        assert users[0].id == "user-1"
        assert users[1].id == "user-2"
        assert users[1].language == "es"
        mock_firestore_client.collection.assert_called_once_with("users")

    def test_applies_limit(
        self, mock_firestore_client: MagicMock, sample_user_data: dict[str, Any]
    ) -> None:
        """list_users(limit=N) applies limit to query."""
        mock_doc = MagicMock()
        mock_doc.id = "user-1"
        mock_doc.to_dict.return_value = sample_user_data

        mock_limited = MagicMock()
        mock_limited.stream.return_value = [mock_doc]

        mock_collection = MagicMock()
        mock_collection.limit.return_value = mock_limited
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        users = client.list_users(limit=5)

        assert len(users) == 1
        mock_collection.limit.assert_called_once_with(5)

    def test_returns_empty_list_when_no_users(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_users() returns empty list when no users exist."""
        mock_collection = MagicMock()
        mock_collection.stream.return_value = []
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        users = client.list_users()

        assert users == []

    def test_handles_document_with_none_dict(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_users() handles documents where to_dict() returns None."""
        mock_doc = MagicMock()
        mock_doc.id = "user-empty"
        mock_doc.to_dict.return_value = None

        mock_collection = MagicMock()
        mock_collection.stream.return_value = [mock_doc]
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        users = client.list_users()

        assert len(users) == 1
        assert users[0].id == "user-empty"


class TestMHC4ClientGetUser:
    """Tests for MHC4Client.get_user() method."""

    def test_returns_user_when_found(
        self, mock_firestore_client: MagicMock, sample_user_data: dict[str, Any]
    ) -> None:
        """get_user() returns User object when document exists."""
        mock_doc = MagicMock()
        mock_doc.id = "user-123"
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_user_data

        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        user = client.get_user("user-123")

        assert user is not None
        assert isinstance(user, User)
        assert user.id == "user-123"
        mock_collection.document.assert_called_once_with("user-123")

    def test_returns_none_when_not_found(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """get_user() returns None when document doesn't exist."""
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        user = client.get_user("nonexistent-user")

        assert user is None

    def test_handles_document_with_none_dict(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """get_user() handles documents where to_dict() returns None."""
        mock_doc = MagicMock()
        mock_doc.id = "user-empty"
        mock_doc.exists = True
        mock_doc.to_dict.return_value = None

        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        user = client.get_user("user-empty")

        assert user is not None
        assert user.id == "user-empty"


class TestMHC4ClientListHealthkitObservationTypes:
    """Tests for MHC4Client.list_healthkit_observation_types() method."""

    def test_returns_healthkit_types_for_single_user(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_healthkit_observation_types(user=...) returns types for that user."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierHeartRate"),
            MagicMock(id="questionnaireResponses"),  # Should be filtered out
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_healthkit_observation_types(user="user123")

        assert result == {
            "HKQuantityTypeIdentifierStepCount",
            "HKQuantityTypeIdentifierHeartRate",
        }
        mock_collection.document.assert_called_once_with("user123")

    def test_returns_empty_set_when_no_healthkit_collections(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_healthkit_observation_types returns empty set when no HealthKit collections."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = [
            MagicMock(id="questionnaireResponses"),
        ]

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_healthkit_observation_types(user="user123")

        assert result == set()

    def test_samples_users_when_no_user_specified(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_healthkit_observation_types samples users when user is None."""
        # Setup mock documents for list_users
        mock_user_docs = []
        for i in range(5):
            mock_doc = MagicMock()
            mock_doc.id = f"user{i}"
            mock_doc.to_dict.return_value = {}
            mock_user_docs.append(mock_doc)

        # Setup collections for each user (different types per user)
        def make_doc_ref(user_id: str) -> MagicMock:
            mock_doc_ref = MagicMock()
            if user_id == "user0":
                mock_doc_ref.collections.return_value = [
                    MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
                ]
            elif user_id == "user1":
                mock_doc_ref.collections.return_value = [
                    MagicMock(id="HealthObservations_HKQuantityTypeIdentifierHeartRate"),
                ]
            else:
                mock_doc_ref.collections.return_value = []
            return mock_doc_ref

        mock_collection = MagicMock()
        mock_collection.stream.return_value = mock_user_docs
        mock_collection.document.side_effect = make_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_healthkit_observation_types()

        # Should contain types from both user0 and user1
        assert "HKQuantityTypeIdentifierStepCount" in result
        assert "HKQuantityTypeIdentifierHeartRate" in result

    def test_respects_user_limit(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_healthkit_observation_types respects user_limit parameter."""
        # Setup many mock users
        mock_user_docs = []
        for i in range(10):
            mock_doc = MagicMock()
            mock_doc.id = f"user{i}"
            mock_doc.to_dict.return_value = {}
            mock_user_docs.append(mock_doc)

        document_call_count = 0

        def make_doc_ref(user_id: str) -> MagicMock:
            nonlocal document_call_count
            document_call_count += 1
            mock_doc_ref = MagicMock()
            mock_doc_ref.collections.return_value = [
                MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            ]
            return mock_doc_ref

        mock_collection = MagicMock()
        mock_collection.stream.return_value = mock_user_docs
        mock_collection.document.side_effect = make_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        client.list_healthkit_observation_types(user_limit=3)

        # Should only query 3 users (the limit)
        assert document_call_count == 3


class TestMHC4ClientListObservationTypes:
    """Tests for MHC4Client.list_observation_types() method."""

    def test_returns_all_types_for_single_user(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_observation_types(user=...) returns all types for that user."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.heart.rate"),
            MagicMock(id="questionnaireResponses"),  # Should be filtered out
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_observation_types(user="user123")

        assert result == {
            "HKQuantityTypeIdentifierStepCount",
            "MHCCustomSampleTypeDietMEPAScore",
            "com.apple.SensorKit.heart.rate",
        }


class TestMHC4ClientListMHCObservationTypes:
    """Tests for MHC4Client.list_mhc_observation_types() method."""

    def test_returns_only_mhc_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_mhc_observation_types filters to only MHC* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
            MagicMock(id="HealthObservations_MHCSleepScore"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.heart.rate"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_mhc_observation_types(user="user123")

        assert result == {
            "MHCCustomSampleTypeDietMEPAScore",
            "MHCSleepScore",
        }


class TestMHC4ClientListSensorKitObservationTypes:
    """Tests for MHC4Client.list_sensorkit_observation_types() method."""

    def test_returns_only_sensorkit_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_sensorkit_observation_types filters to only com.apple.SensorKit.* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.heart.rate"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.steps"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_sensorkit_observation_types(user="user123")

        assert result == {
            "com.apple.SensorKit.heart.rate",
            "com.apple.SensorKit.steps",
        }


class TestObservationTypeCategoryFiltering:
    """Tests for observation type category filtering."""

    def test_category_methods_union_equals_all_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """Union of all category methods equals list_observation_types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierHeartRate"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.heart.rate"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        all_types = client.list_observation_types(user="user123")
        hk_types = client.list_healthkit_observation_types(user="user123")
        mhc_types = client.list_mhc_observation_types(user="user123")
        sensor_types = client.list_sensorkit_observation_types(user="user123")

        assert hk_types | mhc_types | sensor_types == all_types

    def test_category_methods_are_disjoint(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """Category methods return disjoint sets."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
            MagicMock(id="HealthObservations_com.apple.SensorKit.heart.rate"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        hk_types = client.list_healthkit_observation_types(user="user123")
        mhc_types = client.list_mhc_observation_types(user="user123")
        sensor_types = client.list_sensorkit_observation_types(user="user123")

        # All pairs should have empty intersection
        assert hk_types & mhc_types == set()
        assert hk_types & sensor_types == set()
        assert mhc_types & sensor_types == set()


class TestMHC4ClientListHKQuantityObservationTypes:
    """Tests for MHC4Client.list_hk_quantity_observation_types() method."""

    def test_returns_only_quantity_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_quantity_observation_types filters to only HKQuantityTypeIdentifier* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierHeartRate"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierBloodPressure"),
            MagicMock(id="HealthObservations_HKWorkoutTypeIdentifier"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_quantity_observation_types(user="user123")

        assert result == {
            "HKQuantityTypeIdentifierStepCount",
            "HKQuantityTypeIdentifierHeartRate",
        }


class TestMHC4ClientListHKCategoryObservationTypes:
    """Tests for MHC4Client.list_hk_category_observation_types() method."""

    def test_returns_only_category_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_category_observation_types filters to only HKCategoryTypeIdentifier* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierAppleStandHour"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierBloodPressure"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_category_observation_types(user="user123")

        assert result == {
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryTypeIdentifierAppleStandHour",
        }


class TestMHC4ClientListHKCorrelationObservationTypes:
    """Tests for MHC4Client.list_hk_correlation_observation_types() method."""

    def test_returns_only_correlation_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_correlation_observation_types filters to only HKCorrelationTypeIdentifier* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierBloodPressure"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierFood"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_correlation_observation_types(user="user123")

        assert result == {
            "HKCorrelationTypeIdentifierBloodPressure",
            "HKCorrelationTypeIdentifierFood",
        }


class TestMHC4ClientListHKWorkoutObservationTypes:
    """Tests for MHC4Client.list_hk_workout_observation_types() method."""

    def test_returns_only_workout_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_workout_observation_types filters to only HKWorkoutTypeIdentifier* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKWorkoutTypeIdentifier"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_workout_observation_types(user="user123")

        assert result == {"HKWorkoutTypeIdentifier"}


class TestMHC4ClientListHKClinicalObservationTypes:
    """Tests for MHC4Client.list_hk_clinical_observation_types() method."""

    def test_returns_only_clinical_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_clinical_observation_types filters to only HKClinicalTypeIdentifier* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKClinicalTypeIdentifierLabResultRecord"),
            MagicMock(id="HealthObservations_HKClinicalTypeIdentifierMedicationRecord"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_clinical_observation_types(user="user123")

        assert result == {
            "HKClinicalTypeIdentifierLabResultRecord",
            "HKClinicalTypeIdentifierMedicationRecord",
        }


class TestMHC4ClientListHKDataObservationTypes:
    """Tests for MHC4Client.list_hk_data_observation_types() method."""

    def test_returns_only_data_types(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """list_hk_data_observation_types filters to only HKDataType* types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKDataTypeIdentifierHeartbeatSeries"),
            MagicMock(id="HealthObservations_HKDataTypeStateOfMind"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        result = client.list_hk_data_observation_types(user="user123")

        assert result == {
            "HKDataTypeIdentifierHeartbeatSeries",
            "HKDataTypeStateOfMind",
        }


class TestHealthKitSubcategoryFiltering:
    """Tests for HealthKit subcategory filtering."""

    def test_subcategories_are_subsets_of_healthkit(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """HealthKit subcategory methods return subsets of list_healthkit_observation_types."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierHeartRate"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierBloodPressure"),
            MagicMock(id="HealthObservations_HKWorkoutTypeIdentifier"),
            MagicMock(id="HealthObservations_HKClinicalTypeIdentifierLabResultRecord"),
            MagicMock(id="HealthObservations_HKDataTypeIdentifierHeartbeatSeries"),
            MagicMock(id="HealthObservations_MHCCustomSampleTypeDietMEPAScore"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        hk_types = client.list_healthkit_observation_types(user="user123")
        quantity = client.list_hk_quantity_observation_types(user="user123")
        category = client.list_hk_category_observation_types(user="user123")
        correlation = client.list_hk_correlation_observation_types(user="user123")
        workout = client.list_hk_workout_observation_types(user="user123")
        clinical = client.list_hk_clinical_observation_types(user="user123")
        data = client.list_hk_data_observation_types(user="user123")

        # All subcategories should be subsets of HealthKit types
        assert quantity <= hk_types
        assert category <= hk_types
        assert correlation <= hk_types
        assert workout <= hk_types
        assert clinical <= hk_types
        assert data <= hk_types

    def test_healthkit_subcategories_are_disjoint(
        self, mock_firestore_client: MagicMock
    ) -> None:
        """HealthKit subcategory methods return disjoint sets."""
        mock_collections = [
            MagicMock(id="HealthObservations_HKQuantityTypeIdentifierStepCount"),
            MagicMock(id="HealthObservations_HKCategoryTypeIdentifierSleepAnalysis"),
            MagicMock(id="HealthObservations_HKCorrelationTypeIdentifierBloodPressure"),
            MagicMock(id="HealthObservations_HKWorkoutTypeIdentifier"),
            MagicMock(id="HealthObservations_HKClinicalTypeIdentifierLabResultRecord"),
            MagicMock(id="HealthObservations_HKDataTypeIdentifierHeartbeatSeries"),
        ]

        mock_doc_ref = MagicMock()
        mock_doc_ref.collections.return_value = mock_collections

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        quantity = client.list_hk_quantity_observation_types(user="user123")
        category = client.list_hk_category_observation_types(user="user123")
        correlation = client.list_hk_correlation_observation_types(user="user123")
        workout = client.list_hk_workout_observation_types(user="user123")
        clinical = client.list_hk_clinical_observation_types(user="user123")
        data = client.list_hk_data_observation_types(user="user123")

        subcategories = [quantity, category, correlation, workout, clinical, data]

        # All pairs should have empty intersection
        for i, s1 in enumerate(subcategories):
            for s2 in subcategories[i + 1 :]:
                assert s1 & s2 == set()


class TestMHC4ClientGetHKQuantity:
    """Tests for MHC4Client.get_hk_quantity() method."""

    def test_returns_dataframe_with_correct_columns(
        self,
        mock_firestore_client: MagicMock,
        sample_fhir_hk_quantity_doc: dict[str, Any],
    ) -> None:
        """get_hk_quantity returns DataFrame with expected columns."""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = sample_fhir_hk_quantity_doc

        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = [mock_doc]

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
        )

        expected_columns = [
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
        ]
        assert list(df.columns) == expected_columns

    def test_returns_empty_dataframe_when_no_data(
        self,
        mock_firestore_client: MagicMock,
    ) -> None:
        """get_hk_quantity returns empty DataFrame with correct columns when no data."""
        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = []

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_STEP_COUNT,
            user_id="user123",
        )

        assert len(df) == 0
        assert "start_time" in df.columns
        assert "value" in df.columns

    def test_extracts_fhir_values_correctly(
        self,
        mock_firestore_client: MagicMock,
        sample_fhir_hk_quantity_doc: dict[str, Any],
    ) -> None:
        """get_hk_quantity extracts FHIR values correctly."""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = sample_fhir_hk_quantity_doc

        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = [mock_doc]

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
        )

        assert len(df) == 1
        row = df.iloc[0]

        # Check sample ID
        assert row["sample_id"] == "037758F0-5944-43D1-B99A-398C4B10B05B"

        # Check timestamps are parsed correctly (naive, tz stripped)
        assert row["start_time"] == pd.Timestamp("2024-01-15 10:30:00.123456")
        assert row["end_time"] == pd.Timestamp("2024-01-15 10:30:05.987654")

        # Check value and unit
        assert row["value"] == 72.5
        assert row["unit"] == "count/min"

        # Check extracted sourceRevision fields
        assert row["source_timezone"] == "America/Chicago"
        assert row["source_name"] == "My App"
        assert row["source_bundle_id"] == "com.apple.health.123"
        assert row["source_version"] == "3068.0.7.0.1"
        assert row["source_product_type"] == "Watch6,12"
        assert row["source_os_version"] == "26.3.0"

        # Check extracted sourceDevice fields
        assert row["device_name"] == "Apple Watch"
        assert row["device_manufacturer"] == "Apple Inc."
        assert row["device_model"] == "Watch"
        assert row["device_hardware_version"] == "Watch6,12"
        assert row["device_software_version"] == "26.3"

        # Check extracted metadata
        assert row["metadata"] == {
            "HKMetadataKeyHeartRateMotionContext": 1,
            "HKMetadataKeyDevicePlacementSide": "left",
        }

    def test_filters_by_start_time(
        self,
        mock_firestore_client: MagicMock,
    ) -> None:
        """get_hk_quantity filters records by start_time."""
        # Create docs with different timestamps
        doc1_data = {
            "effectivePeriod": {
                "start": "2024-01-10T10:00:00Z",
                "end": "2024-01-10T10:00:05Z",
            },
            "valueQuantity": {"value": 70, "unit": "count/min"},
            "extension": [],
        }
        doc2_data = {
            "effectivePeriod": {
                "start": "2024-01-20T10:00:00Z",
                "end": "2024-01-20T10:00:05Z",
            },
            "valueQuantity": {"value": 75, "unit": "count/min"},
            "extension": [],
        }

        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = doc1_data
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = doc2_data

        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = [mock_doc1, mock_doc2]

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        # Filter to only include records >= Jan 15
        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
            start_time=datetime(2024, 1, 15),
        )

        assert len(df) == 1
        assert df.iloc[0]["value"] == 75

    def test_filters_by_end_time(
        self,
        mock_firestore_client: MagicMock,
    ) -> None:
        """get_hk_quantity filters records by end_time."""
        doc1_data = {
            "effectivePeriod": {
                "start": "2024-01-10T10:00:00Z",
                "end": "2024-01-10T10:00:05Z",
            },
            "valueQuantity": {"value": 70, "unit": "count/min"},
            "extension": [],
        }
        doc2_data = {
            "effectivePeriod": {
                "start": "2024-01-20T10:00:00Z",
                "end": "2024-01-20T10:00:05Z",
            },
            "valueQuantity": {"value": 75, "unit": "count/min"},
            "extension": [],
        }

        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = doc1_data
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = doc2_data

        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = [mock_doc1, mock_doc2]

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        # Filter to only include records < Jan 15
        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
            end_time=datetime(2024, 1, 15),
        )

        assert len(df) == 1
        assert df.iloc[0]["value"] == 70

    def test_handles_missing_extension_fields_gracefully(
        self,
        mock_firestore_client: MagicMock,
        sample_fhir_hk_quantity_doc_minimal: dict[str, Any],
    ) -> None:
        """get_hk_quantity handles missing extension fields gracefully."""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = sample_fhir_hk_quantity_doc_minimal

        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = [mock_doc]

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        df = client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_STEP_COUNT,
            user_id="user123",
        )

        assert len(df) == 1
        row = df.iloc[0]

        # Values should be extracted
        assert row["value"] == 100
        assert row["unit"] == "count"

        # Missing sample_id should be None
        assert row["sample_id"] is None

        # Missing sourceRevision fields should be None/NaN
        assert pd.isna(row["source_timezone"]) or row["source_timezone"] is None
        assert pd.isna(row["source_name"]) or row["source_name"] is None
        assert pd.isna(row["source_bundle_id"]) or row["source_bundle_id"] is None
        assert pd.isna(row["source_version"]) or row["source_version"] is None
        assert pd.isna(row["source_product_type"]) or row["source_product_type"] is None
        assert pd.isna(row["source_os_version"]) or row["source_os_version"] is None

        # Missing sourceDevice fields should be None/NaN
        assert pd.isna(row["device_name"]) or row["device_name"] is None
        assert pd.isna(row["device_manufacturer"]) or row["device_manufacturer"] is None
        assert pd.isna(row["device_model"]) or row["device_model"] is None
        assert pd.isna(row["device_hardware_version"]) or row["device_hardware_version"] is None
        assert pd.isna(row["device_software_version"]) or row["device_software_version"] is None

        # Missing metadata should be None
        assert row["metadata"] is None

    def test_queries_correct_firestore_collection_path(
        self,
        mock_firestore_client: MagicMock,
    ) -> None:
        """get_hk_quantity queries the correct Firestore collection path."""
        mock_subcollection = MagicMock()
        mock_subcollection.stream.return_value = []

        mock_user_doc = MagicMock()
        mock_user_doc.collection.return_value = mock_subcollection

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_user_doc
        mock_firestore_client.collection.return_value = mock_collection

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        client.get_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_STEP_COUNT,
            user_id="user123",
        )

        # Verify collection path
        mock_firestore_client.collection.assert_called_with("users")
        mock_collection.document.assert_called_with("user123")
        mock_user_doc.collection.assert_called_with(
            "HealthObservations_HKQuantityTypeIdentifierStepCount"
        )

    def test_raises_error_for_non_hk_quantity_type(
        self,
        mock_firestore_client: MagicMock,
    ) -> None:
        """get_hk_quantity raises ValueError for non-HK_QUANTITY_* types."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._db = mock_firestore_client

        with pytest.raises(ValueError) as exc_info:
            client.get_hk_quantity(
                DiscoveredObservationType.HK_CATEGORY_SLEEP_ANALYSIS,
                user_id="user123",
            )

        assert "must be an HK_QUANTITY_* type" in str(exc_info.value)
        assert "HK_CATEGORY_SLEEP_ANALYSIS" in str(exc_info.value)
