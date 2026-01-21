"""Tests for MHC4Client."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

from myheartcounts_ds.client import MHC4Client
from myheartcounts_ds.config import MHCConfig
from myheartcounts_ds.models import User


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
