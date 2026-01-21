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
