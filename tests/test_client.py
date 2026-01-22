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


class TestMHC4ClientGetHistoricHKQuantity:
    """Tests for MHC4Client.get_historic_hk_quantity() method."""

    def test_returns_dataframe_with_correct_columns(
        self,
        mock_storage_client: MagicMock,
        sample_historic_hk_records: list[dict[str, Any]],
    ) -> None:
        """get_historic_hk_quantity returns DataFrame with expected columns."""
        import json
        import zstandard

        # Compress the sample records
        json_data = json.dumps(sample_historic_hk_records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(json_data)

        # Setup mock blob
        mock_blob = MagicMock()
        mock_blob.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_abc123.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed_data

        # Setup mock bucket
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
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

    def test_returns_empty_dataframe_when_no_files(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity returns empty DataFrame when no GCS files exist."""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_STEP_COUNT,
            user_id="user123",
        )

        assert len(df) == 0
        assert "start_time" in df.columns
        assert "value" in df.columns

    def test_extracts_values_correctly(
        self,
        mock_storage_client: MagicMock,
        sample_historic_hk_records: list[dict[str, Any]],
    ) -> None:
        """get_historic_hk_quantity extracts values correctly from compressed JSON."""
        import json
        import zstandard

        json_data = json.dumps(sample_historic_hk_records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(json_data)

        mock_blob = MagicMock()
        mock_blob.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_abc.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed_data

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
        )

        assert len(df) == 2

        # Check first record
        row1 = df.iloc[0]
        assert row1["sample_id"] == "historic-sample-1"
        assert row1["value"] == 65.0
        assert row1["unit"] == "count/min"
        assert row1["source_timezone"] == "America/New_York"

        # Check second record
        row2 = df.iloc[1]
        assert row2["sample_id"] == "historic-sample-2"
        assert row2["value"] == 72.0

    def test_merges_multiple_files(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity merges records from multiple GCS files."""
        import json
        import zstandard

        # First file with one record
        records1 = [
            {
                "identifier": [{"id": "file1-sample"}],
                "effectivePeriod": {"start": "2024-01-01T10:00:00Z", "end": "2024-01-01T10:00:05Z"},
                "valueQuantity": {"value": 60.0, "unit": "count/min"},
                "extension": [],
            }
        ]
        json1 = json.dumps(records1).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed1 = cctx.compress(json1)

        # Second file with two records
        records2 = [
            {
                "identifier": [{"id": "file2-sample1"}],
                "effectivePeriod": {"start": "2024-01-02T10:00:00Z", "end": "2024-01-02T10:00:05Z"},
                "valueQuantity": {"value": 70.0, "unit": "count/min"},
                "extension": [],
            },
            {
                "identifier": [{"id": "file2-sample2"}],
                "effectivePeriod": {"start": "2024-01-03T10:00:00Z", "end": "2024-01-03T10:00:05Z"},
                "valueQuantity": {"value": 80.0, "unit": "count/min"},
                "extension": [],
            },
        ]
        json2 = json.dumps(records2).encode("utf-8")
        compressed2 = cctx.compress(json2)

        mock_blob1 = MagicMock()
        mock_blob1.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_uuid1.json.zstd"
        mock_blob1.download_as_bytes.return_value = compressed1

        mock_blob2 = MagicMock()
        mock_blob2.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_uuid2.json.zstd"
        mock_blob2.download_as_bytes.return_value = compressed2

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
        )

        # Should have 3 records total (1 + 2)
        assert len(df) == 3
        sample_ids = set(df["sample_id"])
        assert sample_ids == {"file1-sample", "file2-sample1", "file2-sample2"}

    def test_filters_by_start_time(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity filters records by start_time."""
        import json
        import zstandard

        records = [
            {
                "identifier": [{"id": "early"}],
                "effectivePeriod": {"start": "2024-01-10T10:00:00Z", "end": "2024-01-10T10:00:05Z"},
                "valueQuantity": {"value": 60.0, "unit": "count/min"},
                "extension": [],
            },
            {
                "identifier": [{"id": "late"}],
                "effectivePeriod": {"start": "2024-01-20T10:00:00Z", "end": "2024-01-20T10:00:05Z"},
                "valueQuantity": {"value": 70.0, "unit": "count/min"},
                "extension": [],
            },
        ]
        json_data = json.dumps(records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed = cctx.compress(json_data)

        mock_blob = MagicMock()
        mock_blob.name = "test.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
            start_time=datetime(2024, 1, 15),
        )

        assert len(df) == 1
        assert df.iloc[0]["sample_id"] == "late"

    def test_filters_by_end_time(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity filters records by end_time."""
        import json
        import zstandard

        records = [
            {
                "identifier": [{"id": "early"}],
                "effectivePeriod": {"start": "2024-01-10T10:00:00Z", "end": "2024-01-10T10:00:05Z"},
                "valueQuantity": {"value": 60.0, "unit": "count/min"},
                "extension": [],
            },
            {
                "identifier": [{"id": "late"}],
                "effectivePeriod": {"start": "2024-01-20T10:00:00Z", "end": "2024-01-20T10:00:05Z"},
                "valueQuantity": {"value": 70.0, "unit": "count/min"},
                "extension": [],
            },
        ]
        json_data = json.dumps(records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed = cctx.compress(json_data)

        mock_blob = MagicMock()
        mock_blob.name = "test.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
            end_time=datetime(2024, 1, 15),
        )

        assert len(df) == 1
        assert df.iloc[0]["sample_id"] == "early"

    def test_queries_correct_gcs_path(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity queries the correct GCS path."""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project", storage_bucket="my-bucket")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_STEP_COUNT,
            user_id="user123",
        )

        mock_storage_client.bucket.assert_called_with("my-bucket")
        mock_bucket.list_blobs.assert_called_with(
            prefix="users/user123/historicalHealthSamples/HKQuantityTypeIdentifierStepCount_"
        )

    def test_raises_error_for_non_hk_quantity_type(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity raises ValueError for non-HK_QUANTITY_* types."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        with pytest.raises(ValueError) as exc_info:
            client.get_historic_hk_quantity(
                DiscoveredObservationType.HK_CATEGORY_SLEEP_ANALYSIS,
                user_id="user123",
            )

        assert "must be an HK_QUANTITY_* type" in str(exc_info.value)
        assert "HK_CATEGORY_SLEEP_ANALYSIS" in str(exc_info.value)

    def test_continues_on_file_error(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """get_historic_hk_quantity skips files that fail to download/parse."""
        import json
        import zstandard

        # Valid file
        valid_records = [
            {
                "identifier": [{"id": "valid-sample"}],
                "effectivePeriod": {"start": "2024-01-01T10:00:00Z", "end": "2024-01-01T10:00:05Z"},
                "valueQuantity": {"value": 60.0, "unit": "count/min"},
                "extension": [],
            }
        ]
        json_data = json.dumps(valid_records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed = cctx.compress(json_data)

        # Mock blob that fails
        mock_bad_blob = MagicMock()
        mock_bad_blob.name = "bad.json.zstd"
        mock_bad_blob.download_as_bytes.side_effect = Exception("Download failed")

        # Mock blob that succeeds
        mock_good_blob = MagicMock()
        mock_good_blob.name = "good.json.zstd"
        mock_good_blob.download_as_bytes.return_value = compressed

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_bad_blob, mock_good_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        # Should not raise, should return data from good file
        df = client.get_historic_hk_quantity(
            DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
            user_id="user123",
        )

        assert len(df) == 1
        assert df.iloc[0]["sample_id"] == "valid-sample"

    def test_warns_when_timezone_present(
        self,
        mock_storage_client: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_historic_hk_quantity warns if records have source_timezone set."""
        import json
        import logging
        import zstandard

        # Records with timezone info (unexpected for historic data)
        records = [
            {
                "identifier": [{"id": "sample-with-tz"}],
                "effectivePeriod": {"start": "2024-01-10T10:00:00Z", "end": "2024-01-10T10:00:05Z"},
                "valueQuantity": {"value": 70.0, "unit": "count/min"},
                "extension": [
                    {
                        "url": "https://bdh.stanford.edu/fhir/defs/sampleUploadTimeZone",
                        "valueString": "America/New_York",
                    },
                ],
            },
        ]
        json_data = json.dumps(records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed = cctx.compress(json_data)

        mock_blob = MagicMock()
        mock_blob.name = "test.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        with caplog.at_level(logging.WARNING):
            df = client.get_historic_hk_quantity(
                DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
                user_id="user123",
            )

        # Data should still be returned
        assert len(df) == 1
        assert df.iloc[0]["source_timezone"] == "America/New_York"

        # Warning should be logged
        assert "source_timezone" in caplog.text
        assert "1 records" in caplog.text
        assert "not expected to have timezone" in caplog.text

    def test_no_warning_when_timezone_absent(
        self,
        mock_storage_client: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_historic_hk_quantity does not warn if records have no source_timezone."""
        import json
        import logging
        import zstandard

        # Records without timezone info (expected for historic data)
        records = [
            {
                "identifier": [{"id": "sample-no-tz"}],
                "effectivePeriod": {"start": "2024-01-10T10:00:00Z", "end": "2024-01-10T10:00:05Z"},
                "valueQuantity": {"value": 70.0, "unit": "count/min"},
                "extension": [],
            },
        ]
        json_data = json.dumps(records).encode("utf-8")
        cctx = zstandard.ZstdCompressor()
        compressed = cctx.compress(json_data)

        mock_blob = MagicMock()
        mock_blob.name = "test.json.zstd"
        mock_blob.download_as_bytes.return_value = compressed

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        with caplog.at_level(logging.WARNING):
            df = client.get_historic_hk_quantity(
                DiscoveredObservationType.HK_QUANTITY_HEART_RATE,
                user_id="user123",
            )

        # Data should be returned
        assert len(df) == 1

        # No warning should be logged about timezone
        assert "source_timezone" not in caplog.text


class TestMHC4ClientListHistoricObservationTypes:
    """Tests for MHC4Client.list_historic_observation_types() and list_historic_hk_quantity_observation_types() methods."""

    def test_list_historic_hk_quantity_observation_types_returns_unique_types(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """list_historic_hk_quantity_observation_types returns unique HK quantity types."""
        # Setup mock blobs with different types
        mock_blob1 = MagicMock()
        mock_blob1.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_abc123.json.zstd"

        mock_blob2 = MagicMock()
        mock_blob2.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_def456.json.zstd"

        mock_blob3 = MagicMock()
        mock_blob3.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierStepCount_ghi789.json.zstd"

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2, mock_blob3]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project", storage_bucket="my-bucket")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        result = client.list_historic_hk_quantity_observation_types(user_id="user123")

        assert result == {
            "HKQuantityTypeIdentifierHeartRate",
            "HKQuantityTypeIdentifierStepCount",
        }
        mock_bucket.list_blobs.assert_called_once_with(
            prefix="users/user123/historicalHealthSamples/HKQuantityTypeIdentifier"
        )

    def test_list_historic_hk_quantity_observation_types_returns_empty_set_when_no_files(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """list_historic_hk_quantity_observation_types returns empty set when no files exist."""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        result = client.list_historic_hk_quantity_observation_types(user_id="user123")

        assert result == set()

    def test_list_historic_observation_types_returns_all_types(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """list_historic_observation_types returns all observation types including non-quantity."""
        # Setup mock blobs with different type prefixes
        mock_blob1 = MagicMock()
        mock_blob1.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_abc.json.zstd"

        mock_blob2 = MagicMock()
        mock_blob2.name = "users/user123/historicalHealthSamples/HKCategoryTypeIdentifierSleepAnalysis_def.json.zstd"

        mock_blob3 = MagicMock()
        mock_blob3.name = "users/user123/historicalHealthSamples/HKCorrelationTypeIdentifierBloodPressure_ghi.json.zstd"

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2, mock_blob3]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project", storage_bucket="my-bucket")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        result = client.list_historic_observation_types(user_id="user123")

        assert result == {
            "HKQuantityTypeIdentifierHeartRate",
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCorrelationTypeIdentifierBloodPressure",
        }
        mock_bucket.list_blobs.assert_called_once_with(
            prefix="users/user123/historicalHealthSamples/"
        )

    def test_list_historic_observation_types_returns_empty_set_when_no_files(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """list_historic_observation_types returns empty set when no files exist."""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        result = client.list_historic_observation_types(user_id="user123")

        assert result == set()

    def test_skips_blobs_with_invalid_pattern(
        self,
        mock_storage_client: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Methods skip blobs that don't match expected pattern and log warning."""
        import logging

        # Valid blob
        mock_blob1 = MagicMock()
        mock_blob1.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_abc.json.zstd"

        # Invalid blob - no UUID suffix
        mock_blob2 = MagicMock()
        mock_blob2.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierStepCount.json.zstd"

        # Invalid blob - wrong extension
        mock_blob3 = MagicMock()
        mock_blob3.name = "users/user123/historicalHealthSamples/HKQuantityTypeIdentifierVO2Max_xyz.json"

        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2, mock_blob3]
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        with caplog.at_level(logging.WARNING):
            result = client.list_historic_observation_types(user_id="user123")

        # Only valid blob should be extracted
        assert result == {"HKQuantityTypeIdentifierHeartRate"}

        # Warnings should be logged for invalid blobs
        assert "Could not extract type from blob name" in caplog.text

    def test_queries_correct_gcs_bucket(
        self,
        mock_storage_client: MagicMock,
    ) -> None:
        """Methods query the correct GCS bucket from config."""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []
        mock_storage_client.bucket.return_value = mock_bucket

        config = MHCConfig(project_id="test-project", storage_bucket="custom-bucket")
        client = MHC4Client(config=config)
        client._storage = mock_storage_client

        client.list_historic_hk_quantity_observation_types(user_id="user123")

        mock_storage_client.bucket.assert_called_with("custom-bucket")


class TestExtractTypeFromHistoricBlobName:
    """Tests for MHC4Client._extract_type_from_historic_blob_name() helper method."""

    def test_extracts_type_from_valid_blob_name(self) -> None:
        """Extracts type correctly from valid blob name."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)

        blob_name = "users/abc123/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_550e8400-e29b.json.zstd"
        result = client._extract_type_from_historic_blob_name(blob_name)

        assert result == "HKQuantityTypeIdentifierHeartRate"

    def test_handles_types_with_underscores(self) -> None:
        """Handles types that contain underscores (uses rsplit)."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)

        # Hypothetical type with underscore
        blob_name = "users/abc/historicalHealthSamples/Some_Type_With_Underscores_uuid123.json.zstd"
        result = client._extract_type_from_historic_blob_name(blob_name)

        assert result == "Some_Type_With_Underscores"

    def test_returns_none_for_wrong_extension(self) -> None:
        """Returns None for files without .json.zstd extension."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)

        blob_name = "users/abc/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate_uuid.json"
        result = client._extract_type_from_historic_blob_name(blob_name)

        assert result is None

    def test_returns_none_for_no_underscore(self) -> None:
        """Returns None for filenames without underscore separator."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)

        blob_name = "users/abc/historicalHealthSamples/HKQuantityTypeIdentifierHeartRate.json.zstd"
        result = client._extract_type_from_historic_blob_name(blob_name)

        assert result is None

    def test_extracts_from_simple_path(self) -> None:
        """Extracts type from simplified path."""
        config = MHCConfig(project_id="test-project")
        client = MHC4Client(config=config)

        blob_name = "HKQuantityTypeIdentifierStepCount_abc.json.zstd"
        result = client._extract_type_from_historic_blob_name(blob_name)

        assert result == "HKQuantityTypeIdentifierStepCount"
