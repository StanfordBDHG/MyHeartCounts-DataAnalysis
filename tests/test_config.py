"""Tests for MHCConfig."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from myheartcounts_ds.config import MHCConfig


class TestMHCConfig:
    """Tests for MHCConfig dataclass."""

    def test_default_storage_bucket_derived_from_project_id(self) -> None:
        """Storage bucket defaults to {project_id}.firebasestorage.app."""
        config = MHCConfig(project_id="my-project")
        assert config.storage_bucket == "my-project.firebasestorage.app"

    def test_explicit_storage_bucket_overrides_default(self) -> None:
        """Explicitly provided storage bucket is used."""
        config = MHCConfig(project_id="my-project", storage_bucket="custom-bucket")
        assert config.storage_bucket == "custom-bucket"

    def test_config_is_frozen(self) -> None:
        """Config should be immutable (frozen dataclass)."""
        config = MHCConfig(project_id="my-project")
        with pytest.raises(AttributeError):
            config.project_id = "other-project"  # type: ignore[misc]


class TestMHCConfigDev:
    """Tests for MHCConfig.dev() class method."""

    def test_dev_returns_dev_project_id(self) -> None:
        """dev() returns config with dev project ID."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove MHC_PROJECT_ID if present
            os.environ.pop("MHC_PROJECT_ID", None)
            config = MHCConfig.dev()
            assert config.project_id == "som-rit-phi-mhc-dev"

    def test_dev_respects_env_override(self) -> None:
        """dev() uses MHC_PROJECT_ID environment variable if set."""
        with patch.dict(os.environ, {"MHC_PROJECT_ID": "custom-dev-project"}):
            config = MHCConfig.dev()
            assert config.project_id == "custom-dev-project"


class TestMHCConfigProd:
    """Tests for MHCConfig.prod() class method."""

    def test_prod_returns_prod_project_id(self) -> None:
        """prod() returns config with prod project ID."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MHC_PROJECT_ID", None)
            config = MHCConfig.prod()
            assert config.project_id == "som-rit-phi-mhc-prod"

    def test_prod_respects_env_override(self) -> None:
        """prod() uses MHC_PROJECT_ID environment variable if set."""
        with patch.dict(os.environ, {"MHC_PROJECT_ID": "custom-prod-project"}):
            config = MHCConfig.prod()
            assert config.project_id == "custom-prod-project"


class TestMHCConfigFromEnv:
    """Tests for MHCConfig.from_env() class method."""

    def test_from_env_defaults_to_prod(self) -> None:
        """from_env() defaults to production project when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MHC_PROJECT_ID", None)
            os.environ.pop("MHC_STORAGE_BUCKET", None)
            config = MHCConfig.from_env()
            assert config.project_id == "som-rit-phi-mhc-prod"

    def test_from_env_reads_project_id(self) -> None:
        """from_env() reads MHC_PROJECT_ID from environment."""
        with patch.dict(os.environ, {"MHC_PROJECT_ID": "env-project"}):
            config = MHCConfig.from_env()
            assert config.project_id == "env-project"

    def test_from_env_reads_storage_bucket(self) -> None:
        """from_env() reads MHC_STORAGE_BUCKET from environment."""
        with patch.dict(
            os.environ,
            {"MHC_PROJECT_ID": "env-project", "MHC_STORAGE_BUCKET": "env-bucket"},
        ):
            config = MHCConfig.from_env()
            assert config.storage_bucket == "env-bucket"

    def test_from_env_derives_storage_bucket_when_not_set(self) -> None:
        """from_env() derives storage bucket from project ID when not set."""
        with patch.dict(os.environ, {"MHC_PROJECT_ID": "env-project"}):
            os.environ.pop("MHC_STORAGE_BUCKET", None)
            config = MHCConfig.from_env()
            assert config.storage_bucket == "env-project.firebasestorage.app"
