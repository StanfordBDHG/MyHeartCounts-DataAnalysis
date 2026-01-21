"""Configuration for MyHeartCounts data access."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_DEFAULT_DEV_PROJECT = "som-rit-phi-mhc-dev"
_DEFAULT_PROD_PROJECT = "som-rit-phi-mhc-prod"


@dataclass(frozen=True)
class MHCConfig:
    """Configuration for connecting to MyHeartCounts Firebase backend.

    Attributes:
        project_id: Google Cloud project ID.
        storage_bucket: GCS bucket name for file storage. Defaults to
            {project_id}.firebasestorage.app if not specified.
    """

    project_id: str
    storage_bucket: str = field(default="")

    def __post_init__(self) -> None:
        if not self.storage_bucket:
            object.__setattr__(
                self, "storage_bucket", f"{self.project_id}.firebasestorage.app"
            )

    @classmethod
    def dev(cls) -> MHCConfig:
        """Create configuration for the development environment."""
        project_id = os.environ.get("MHC_PROJECT_ID", _DEFAULT_DEV_PROJECT)
        return cls(project_id=project_id)

    @classmethod
    def prod(cls) -> MHCConfig:
        """Create configuration for the production environment."""
        project_id = os.environ.get("MHC_PROJECT_ID", _DEFAULT_PROD_PROJECT)
        return cls(project_id=project_id)

    @classmethod
    def from_env(cls) -> MHCConfig:
        """Create configuration from environment variables.

        Uses MHC_PROJECT_ID if set, otherwise defaults to production.
        """
        project_id = os.environ.get("MHC_PROJECT_ID", _DEFAULT_PROD_PROJECT)
        storage_bucket = os.environ.get("MHC_STORAGE_BUCKET", "")
        return cls(project_id=project_id, storage_bucket=storage_bucket)
