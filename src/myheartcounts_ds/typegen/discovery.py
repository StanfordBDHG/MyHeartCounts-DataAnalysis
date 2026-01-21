"""Type discovery and categorization logic for HealthObservation types."""

from __future__ import annotations

import re
from dataclasses import dataclass

from myheartcounts_ds.typegen.categories import (
    SUPPORTED_CATEGORIES,
    TypeCategory,
    get_category_by_prefix,
)


@dataclass(frozen=True)
class DiscoveredType:
    """A discovered observation type with its categorization.

    Attributes:
        raw_identifier: The raw identifier as found in the database
            (e.g., "HKQuantityTypeIdentifierStepCount").
        category: The category name (e.g., "HK_QUANTITY").
        enum_name: The generated enum member name
            (e.g., "HK_QUANTITY_STEP_COUNT").
    """

    raw_identifier: str
    category: str
    enum_name: str


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to SCREAMING_SNAKE_CASE.

    Args:
        name: CamelCase string (e.g., "StepCount").

    Returns:
        SCREAMING_SNAKE_CASE string (e.g., "STEP_COUNT").
    """
    # Insert underscore before uppercase letters (except at start)
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper()


def _sanitize_for_enum(name: str) -> str:
    """Sanitize a string to be a valid Python enum member name.

    Args:
        name: String to sanitize.

    Returns:
        A valid Python identifier using only [A-Z0-9_].
    """
    # Replace dots with underscores (for SensorKit types)
    result = name.replace(".", "_")
    # Replace hyphens with underscores
    result = result.replace("-", "_")
    # Remove any remaining invalid characters
    result = re.sub(r"[^A-Za-z0-9_]", "", result)
    # Ensure it doesn't start with a digit
    if result and result[0].isdigit():
        result = "_" + result
    return result.upper()


def _generate_enum_name(raw_identifier: str, category: TypeCategory) -> str:
    """Generate an enum member name from a raw identifier.

    Args:
        raw_identifier: The raw identifier (e.g., "HKQuantityTypeIdentifierStepCount").
        category: The TypeCategory this identifier belongs to.

    Returns:
        The enum member name (e.g., "HK_QUANTITY_STEP_COUNT").
    """
    # Strip the prefix to get the specific type name
    suffix = raw_identifier[len(category.prefix) :]

    # Strip leading dots (for SensorKit types like "com.apple.SensorKit.heart.rate")
    suffix = suffix.lstrip(".")

    if suffix:
        # Convert the suffix to SCREAMING_SNAKE_CASE
        suffix_snake = _camel_to_snake(suffix)
        suffix_clean = _sanitize_for_enum(suffix_snake)
        return f"{category.name}_{suffix_clean}"
    else:
        # No suffix, just use the category name (e.g., HKWorkoutTypeIdentifier)
        return category.name


def categorize_type(raw_identifier: str) -> DiscoveredType | None:
    """Categorize a single raw identifier into a DiscoveredType.

    Args:
        raw_identifier: The raw observation type identifier.

    Returns:
        A DiscoveredType if the identifier matches a known category,
        None otherwise.
    """
    category = get_category_by_prefix(raw_identifier)
    if category is None:
        return None

    enum_name = _generate_enum_name(raw_identifier, category)
    return DiscoveredType(
        raw_identifier=raw_identifier,
        category=category.name,
        enum_name=enum_name,
    )


def categorize_types(raw_identifiers: set[str]) -> list[DiscoveredType]:
    """Categorize multiple raw identifiers.

    Args:
        raw_identifiers: Set of raw observation type identifiers.

    Returns:
        List of DiscoveredType objects, sorted by category then enum_name.
        Identifiers that don't match any category are skipped.
    """
    discovered: list[DiscoveredType] = []

    for raw_id in raw_identifiers:
        dt = categorize_type(raw_id)
        if dt is not None:
            discovered.append(dt)

    # Sort by category order, then by enum name within category
    category_order = {cat.name: i for i, cat in enumerate(SUPPORTED_CATEGORIES)}
    discovered.sort(
        key=lambda d: (category_order.get(d.category, 999), d.enum_name)
    )

    return discovered


def discover_types_from_client(
    client: "MHC4Client",  # type: ignore[name-defined]
    user_limit: int = 100,
) -> list[DiscoveredType]:
    """Discover and categorize all observation types from the database.

    This function queries the database to find all observation types
    across sampled users and categorizes them.

    Args:
        client: An MHC4Client instance to use for database queries.
        user_limit: Maximum number of users to sample.

    Returns:
        List of DiscoveredType objects, sorted by category then enum_name.
    """
    # Import here to avoid circular imports
    from myheartcounts_ds.client import MHC4Client as MHC4ClientClass

    if not isinstance(client, MHC4ClientClass):
        raise TypeError(f"Expected MHC4Client, got {type(client)}")

    raw_types = client.list_observation_types(user_limit=user_limit)
    return categorize_types(raw_types)
