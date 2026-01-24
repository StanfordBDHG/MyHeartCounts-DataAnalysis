"""Tests for typegen package."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myheartcounts_ds.typegen import (
    SUPPORTED_CATEGORIES,
    DiscoveredObservationType,
    DiscoveredType,
    TypeCategory,
    categorize_type,
    categorize_types,
    generate_enum_code,
    get_category_by_prefix,
    get_observation_type_by_identifier,
    write_enum_file,
)
from myheartcounts_ds.typegen.discovery import (
    _camel_to_snake,
    _generate_enum_name,
    _sanitize_for_enum,
)


class TestTypeCategory:
    """Tests for TypeCategory dataclass."""

    def test_type_category_is_frozen(self) -> None:
        """TypeCategory should be immutable."""
        category = TypeCategory("TEST", "TestPrefix", "Test category")
        with pytest.raises(AttributeError):
            category.name = "CHANGED"  # type: ignore[misc]

    def test_type_category_equality(self) -> None:
        """TypeCategories with same values should be equal."""
        cat1 = TypeCategory("TEST", "TestPrefix", "Test category")
        cat2 = TypeCategory("TEST", "TestPrefix", "Test category")
        assert cat1 == cat2


class TestSupportedCategories:
    """Tests for SUPPORTED_CATEGORIES constant."""

    def test_supported_categories_is_tuple(self) -> None:
        """SUPPORTED_CATEGORIES should be a tuple (immutable)."""
        assert isinstance(SUPPORTED_CATEGORIES, tuple)

    def test_supported_categories_contains_expected_categories(self) -> None:
        """SUPPORTED_CATEGORIES should contain all expected HealthKit categories."""
        category_names = {cat.name for cat in SUPPORTED_CATEGORIES}
        expected = {
            "HK_QUANTITY",
            "HK_CATEGORY",
            "HK_CORRELATION",
            "HK_WORKOUT",
            "HK_CLINICAL",
            "HK_DATA",
            "SENSORKIT",
            "MHC_CUSTOM",
        }
        assert expected == category_names

    def test_supported_categories_have_unique_prefixes(self) -> None:
        """Each category should have a unique prefix."""
        prefixes = [cat.prefix for cat in SUPPORTED_CATEGORIES]
        assert len(prefixes) == len(set(prefixes))


class TestGetCategoryByPrefix:
    """Tests for get_category_by_prefix function."""

    def test_matches_hk_quantity(self) -> None:
        """Should match HKQuantityTypeIdentifier prefix."""
        result = get_category_by_prefix("HKQuantityTypeIdentifierStepCount")
        assert result is not None
        assert result.name == "HK_QUANTITY"

    def test_matches_hk_category(self) -> None:
        """Should match HKCategoryTypeIdentifier prefix."""
        result = get_category_by_prefix("HKCategoryTypeIdentifierSleepAnalysis")
        assert result is not None
        assert result.name == "HK_CATEGORY"

    def test_matches_sensorkit(self) -> None:
        """Should match com.apple.SensorKit prefix."""
        result = get_category_by_prefix("com.apple.SensorKit.heart.rate")
        assert result is not None
        assert result.name == "SENSORKIT"

    def test_matches_mhc_custom(self) -> None:
        """Should match MHC prefix for custom types."""
        result = get_category_by_prefix("MHCCustomSampleTypeDietMEPAScore")
        assert result is not None
        assert result.name == "MHC_CUSTOM"

    def test_returns_none_for_unknown_prefix(self) -> None:
        """Should return None for unknown prefixes."""
        result = get_category_by_prefix("UnknownTypeIdentifier")
        assert result is None


class TestCamelToSnake:
    """Tests for _camel_to_snake helper function."""

    def test_simple_camel_case(self) -> None:
        """Should convert simple CamelCase to SCREAMING_SNAKE_CASE."""
        assert _camel_to_snake("StepCount") == "STEP_COUNT"

    def test_acronyms(self) -> None:
        """Should handle acronyms correctly."""
        assert _camel_to_snake("BMI") == "BMI"
        assert _camel_to_snake("VO2Max") == "VO2_MAX"

    def test_multiple_words(self) -> None:
        """Should handle multiple words."""
        assert _camel_to_snake("HeartRateVariabilitySDNN") == "HEART_RATE_VARIABILITY_SDNN"

    def test_single_word(self) -> None:
        """Should handle single lowercase word."""
        assert _camel_to_snake("Sleep") == "SLEEP"


class TestSanitizeForEnum:
    """Tests for _sanitize_for_enum helper function."""

    def test_replaces_dots(self) -> None:
        """Should replace dots with underscores."""
        assert _sanitize_for_enum("com.apple.test") == "COM_APPLE_TEST"

    def test_replaces_hyphens(self) -> None:
        """Should replace hyphens with underscores."""
        assert _sanitize_for_enum("some-identifier") == "SOME_IDENTIFIER"

    def test_removes_invalid_chars(self) -> None:
        """Should remove invalid characters."""
        assert _sanitize_for_enum("test@value!") == "TESTVALUE"

    def test_handles_leading_digit(self) -> None:
        """Should prefix with underscore if starts with digit."""
        assert _sanitize_for_enum("123test") == "_123TEST"


class TestGenerateEnumName:
    """Tests for _generate_enum_name helper function."""

    def test_hk_quantity_type(self) -> None:
        """Should generate correct enum name for HK quantity type."""
        category = TypeCategory("HK_QUANTITY", "HKQuantityTypeIdentifier", "")
        result = _generate_enum_name("HKQuantityTypeIdentifierStepCount", category)
        assert result == "HK_QUANTITY_STEP_COUNT"

    def test_sensorkit_type(self) -> None:
        """Should generate correct enum name for SensorKit type."""
        category = TypeCategory("SENSORKIT", "com.apple.SensorKit", "")
        result = _generate_enum_name("com.apple.SensorKit.heart.rate", category)
        assert result == "SENSORKIT_HEART_RATE"

    def test_no_suffix(self) -> None:
        """Should handle identifier that matches prefix exactly."""
        category = TypeCategory("HK_WORKOUT", "HKWorkoutTypeIdentifier", "")
        result = _generate_enum_name("HKWorkoutTypeIdentifier", category)
        assert result == "HK_WORKOUT"


class TestDiscoveredType:
    """Tests for DiscoveredType dataclass."""

    def test_discovered_type_is_frozen(self) -> None:
        """DiscoveredType should be immutable."""
        dt = DiscoveredType(
            raw_identifier="HKQuantityTypeIdentifierStepCount",
            category="HK_QUANTITY",
            enum_name="HK_QUANTITY_STEP_COUNT",
        )
        with pytest.raises(AttributeError):
            dt.raw_identifier = "changed"  # type: ignore[misc]


class TestCategorizeType:
    """Tests for categorize_type function."""

    def test_categorizes_hk_quantity_type(self) -> None:
        """Should correctly categorize HK quantity type."""
        result = categorize_type("HKQuantityTypeIdentifierStepCount")
        assert result is not None
        assert result.raw_identifier == "HKQuantityTypeIdentifierStepCount"
        assert result.category == "HK_QUANTITY"
        assert result.enum_name == "HK_QUANTITY_STEP_COUNT"

    def test_categorizes_sensorkit_type(self) -> None:
        """Should correctly categorize SensorKit type."""
        result = categorize_type("com.apple.SensorKit.heart.rate")
        assert result is not None
        assert result.category == "SENSORKIT"
        assert result.enum_name == "SENSORKIT_HEART_RATE"

    def test_returns_none_for_unknown_type(self) -> None:
        """Should return None for unknown type."""
        result = categorize_type("UnknownTypeIdentifier")
        assert result is None


class TestCategorizeTypes:
    """Tests for categorize_types function."""

    def test_categorizes_multiple_types(self) -> None:
        """Should categorize multiple types correctly."""
        raw_ids = {
            "HKQuantityTypeIdentifierStepCount",
            "HKQuantityTypeIdentifierHeartRate",
            "HKCategoryTypeIdentifierSleepAnalysis",
        }
        results = categorize_types(raw_ids)
        assert len(results) == 3

    def test_sorts_by_category_then_name(self) -> None:
        """Should sort results by category order, then by enum name."""
        raw_ids = {
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKQuantityTypeIdentifierStepCount",
            "HKQuantityTypeIdentifierHeartRate",
        }
        results = categorize_types(raw_ids)

        # HK_QUANTITY comes before HK_CATEGORY in SUPPORTED_CATEGORIES
        assert results[0].category == "HK_QUANTITY"
        assert results[1].category == "HK_QUANTITY"
        assert results[2].category == "HK_CATEGORY"

    def test_skips_unknown_types(self) -> None:
        """Should skip types that don't match any category."""
        raw_ids = {
            "HKQuantityTypeIdentifierStepCount",
            "UnknownTypeIdentifier",
        }
        results = categorize_types(raw_ids)
        assert len(results) == 1
        assert results[0].raw_identifier == "HKQuantityTypeIdentifierStepCount"


class TestGenerateEnumCode:
    """Tests for generate_enum_code function."""

    def test_generates_valid_python(self) -> None:
        """Generated code should be valid Python."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
        ]
        code = generate_enum_code(discovered)

        # Should be compilable
        compile(code, "<string>", "exec")

    def test_includes_header_comment(self) -> None:
        """Generated code should include auto-generation header."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
        ]
        code = generate_enum_code(discovered)

        assert "DO NOT EDIT MANUALLY" in code
        assert "mhc-ds generate-types" in code

    def test_includes_project_id_when_provided(self) -> None:
        """Generated code should include project ID in header."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
        ]
        code = generate_enum_code(discovered, project_id="test-project")

        assert "test-project" in code

    def test_includes_enum_members(self) -> None:
        """Generated code should include all enum members."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
            DiscoveredType(
                "HKCategoryTypeIdentifierSleepAnalysis",
                "HK_CATEGORY",
                "HK_CATEGORY_SLEEP_ANALYSIS",
            ),
        ]
        code = generate_enum_code(discovered)

        assert "HK_QUANTITY_STEP_COUNT" in code
        assert '"HKQuantityTypeIdentifierStepCount"' in code
        assert "HK_CATEGORY_SLEEP_ANALYSIS" in code
        assert '"HKCategoryTypeIdentifierSleepAnalysis"' in code

    def test_includes_lookup_function(self) -> None:
        """Generated code should include lookup function."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
        ]
        code = generate_enum_code(discovered)

        assert "def get_observation_type_by_identifier" in code


class TestWriteEnumFile:
    """Tests for write_enum_file function."""

    def test_writes_file(self) -> None:
        """Should write enum code to file."""
        discovered = [
            DiscoveredType(
                "HKQuantityTypeIdentifierStepCount",
                "HK_QUANTITY",
                "HK_QUANTITY_STEP_COUNT",
            ),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result_path = write_enum_file(discovered, temp_path)
            assert result_path == temp_path
            assert temp_path.exists()

            content = temp_path.read_text()
            assert "HK_QUANTITY_STEP_COUNT" in content
        finally:
            temp_path.unlink()


class TestDiscoveredObservationType:
    """Tests for the DiscoveredObservationType enum (placeholder)."""

    def test_enum_exists(self) -> None:
        """DiscoveredObservationType should be importable."""
        # This is the placeholder enum
        assert DiscoveredObservationType is not None

    def test_get_observation_type_by_identifier_returns_none_for_unknown(self) -> None:
        """Lookup function should return None for unknown identifiers."""
        result = get_observation_type_by_identifier("UnknownTypeIdentifier")
        assert result is None


class TestDiscoverTypesFromClient:
    """Tests for discover_types_from_client function."""

    def test_raises_type_error_for_invalid_client(self) -> None:
        """Should raise TypeError if not given MHC4Client."""
        from myheartcounts_ds.typegen import discover_types_from_client

        with pytest.raises(TypeError):
            discover_types_from_client("not a client")  # type: ignore[arg-type]

    def test_discovers_types_from_mocked_client(self) -> None:
        """Should discover and categorize types from a real MHC4Client."""
        from myheartcounts_ds.client import MHC4Client
        from myheartcounts_ds.typegen import discover_types_from_client

        # Create a real client instance, then mock its method
        with patch.object(
            MHC4Client,
            "__init__",
            lambda self, config=None: setattr(self, "_config", config)
            or setattr(self, "_db", None),
        ):
            client = MHC4Client()
            client.list_observation_types = MagicMock(  # type: ignore[method-assign]
                return_value={
                    "HKQuantityTypeIdentifierStepCount",
                    "HKQuantityTypeIdentifierHeartRate",
                }
            )

            results = discover_types_from_client(client, user_limit=10)

        assert len(results) == 2
        assert all(isinstance(r, DiscoveredType) for r in results)
        raw_ids = {r.raw_identifier for r in results}
        assert "HKQuantityTypeIdentifierStepCount" in raw_ids
        assert "HKQuantityTypeIdentifierHeartRate" in raw_ids
