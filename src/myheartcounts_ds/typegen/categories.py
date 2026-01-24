"""Category definitions for HealthObservation types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TypeCategory:
    """A category for grouping observation types.

    Attributes:
        name: The enum-style name for this category (e.g., "HK_QUANTITY").
        prefix: The raw identifier prefix (e.g., "HKQuantityTypeIdentifier").
        description: Human-readable description of this category.
    """

    name: str
    prefix: str
    description: str


SUPPORTED_CATEGORIES: tuple[TypeCategory, ...] = (
    TypeCategory(
        "HK_QUANTITY",
        "HKQuantityTypeIdentifier",
        "HealthKit quantity types (e.g., step count, heart rate)",
    ),
    TypeCategory(
        "HK_CATEGORY",
        "HKCategoryTypeIdentifier",
        "HealthKit category types (e.g., sleep analysis)",
    ),
    TypeCategory(
        "HK_CORRELATION",
        "HKCorrelationTypeIdentifier",
        "HealthKit correlation types (e.g., blood pressure)",
    ),
    TypeCategory(
        "HK_WORKOUT",
        "HKWorkoutTypeIdentifier",
        "HealthKit workout types",
    ),
    TypeCategory(
        "HK_CLINICAL",
        "HKClinicalTypeIdentifier",
        "HealthKit clinical types (e.g., lab results)",
    ),
    TypeCategory(
        "HK_DATA",
        "HKDataType",
        "HealthKit data types (e.g., heartbeat series)",
    ),
    TypeCategory(
        "SENSORKIT",
        "com.apple.SensorKit",
        "Apple SensorKit types",
    ),
    TypeCategory(
        "MHC_CUSTOM",
        "MHC",
        "MyHeartCounts custom sample types",
    ),
)


def get_category_by_prefix(raw_identifier: str) -> TypeCategory | None:
    """Find the category that matches a raw identifier's prefix.

    Args:
        raw_identifier: The raw observation type identifier.

    Returns:
        The matching TypeCategory, or None if no match found.
    """
    for category in SUPPORTED_CATEGORIES:
        if raw_identifier.startswith(category.prefix):
            return category
    return None
