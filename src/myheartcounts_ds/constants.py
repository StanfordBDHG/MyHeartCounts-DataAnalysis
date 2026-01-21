"""Constants for MyHeartCounts data structures."""

from enum import Enum

HEALTHKIT_COLLECTION_PREFIX = "HealthObservations_"


class ObservationType(Enum):
    """Categories of observation types."""

    # Top-level categories
    HEALTHKIT = "HK"
    MHC_CUSTOM = "MHC"
    SENSORKIT = "com.apple.SensorKit"
    ALL = None  # No filtering

    # HealthKit subcategories
    HK_QUANTITY = "HKQuantityTypeIdentifier"
    HK_CATEGORY = "HKCategoryTypeIdentifier"
    HK_CORRELATION = "HKCorrelationTypeIdentifier"
    HK_WORKOUT = "HKWorkoutTypeIdentifier"
    HK_CLINICAL = "HKClinicalTypeIdentifier"
    HK_DATA = "HKDataType"
