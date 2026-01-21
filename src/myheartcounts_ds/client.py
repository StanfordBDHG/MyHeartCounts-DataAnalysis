"""Client for accessing MyHeartCounts Firebase data."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore_v1 as firestore

from myheartcounts_ds.config import MHCConfig
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
