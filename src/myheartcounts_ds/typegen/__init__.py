"""Type generation subpackage for dynamic enum discovery.

This package provides tools to discover observation types from the
Firestore database and generate a Python enum with full IDE support.

Usage:
    # Command-line generation
    mhc-ds generate-types --project <project-id>

    # Programmatic use
    from myheartcounts_ds.typegen import DiscoveredObservationType
    step_count = DiscoveredObservationType.HK_QUANTITY_STEP_COUNT
"""

from myheartcounts_ds.typegen.categories import (
    SUPPORTED_CATEGORIES,
    TypeCategory,
    get_category_by_prefix,
)
from myheartcounts_ds.typegen.codegen import (
    generate_enum_code,
    get_default_output_path,
    write_enum_file,
)
from myheartcounts_ds.typegen.discovery import (
    DiscoveredType,
    categorize_type,
    categorize_types,
    discover_types_from_client,
)
from myheartcounts_ds.typegen.generated_types import (
    DiscoveredObservationType,
    get_observation_type_by_identifier,
)

__all__ = [
    # Categories
    "TypeCategory",
    "SUPPORTED_CATEGORIES",
    "get_category_by_prefix",
    # Discovery
    "DiscoveredType",
    "categorize_type",
    "categorize_types",
    "discover_types_from_client",
    # Code generation
    "generate_enum_code",
    "write_enum_file",
    "get_default_output_path",
    # Generated types
    "DiscoveredObservationType",
    "get_observation_type_by_identifier",
]
