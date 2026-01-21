# Firebase Data Architecture

This document describes the data architecture for the MyHeartCounts 4.0 application as implemented in the [MyHeartCounts-Firebase](https://github.com/StanfordBDHG/MyHeartCounts-Firebase) backend.

## Overview

MyHeartCounts uses a dual storage system:

- **Firestore**: Primary database for user profiles, questionnaire responses, health observations, and structured data
- **Cloud Storage**: Temporary storage for large health sample uploads (compressed JSON files) that are processed and moved to Firestore

## Firestore Collections

### Root Collections

| Collection | Path | Description |
|------------|------|-------------|
| users | `/users/{userId}` | User profiles and enrollment data |
| questionnaires | `/questionnaires` | FHIR Questionnaire definitions |
| history | `/history` | System change history |
| devices | Collection group across all users | User device registrations |

### User Subcollections

Located under `/users/{userId}/`:

| Subcollection | Description |
|---------------|-------------|
| `questionnaireResponses/{uuid}` | FHIR QuestionnaireResponse documents |
| `devices/{deviceId}` | Registered user devices |
| `messages/{uuid}` | User notification messages |
| `scores/{uuid}` | Computed health scores |
| `HealthObservations_{TYPE}/{uuid}` | Dynamic health observation collections |
| `SensorKitObservations_{TYPE}/{uuid}` | SensorKit data collections |

#### Dynamic Collection Naming

Health observation collections are named dynamically based on the data type:

- `HealthObservations_HKQuantityTypeIdentifierStepCount`
- `HealthObservations_HKQuantityTypeIdentifierHeartRate`
- `SensorKitObservations_ambientPressure`
- `SensorKitObservations_accelerometer`

## Cloud Storage Paths

```
/public/
  └── mhcStudyBundle.spezistudybundle.aar    # Study definition bundle

/user/{userId}/
  ├── consent/                                # PDF consent forms
  ├── historicalHealthSamples/               # Pre-enrollment HealthKit data
  │   └── {HealthKitIdentifier}_{UUID}.json.zstd
  ├── liveHealthSamples/                     # Post-enrollment HealthKit data
  │   └── {HealthKitIdentifier}_{UUID}.json.zstd
  └── SensorKit/                             # SensorKit sensor data
      └── com.apple.SensorKit.{dataType}_{UUID}.json.zstd
```

### Storage Processing Pipeline

1. **Upload**: Client uploads compressed JSON to Cloud Storage
2. **Decompress**: Cloud Function decompresses the zstd file
3. **Parse**: JSON content is parsed into FHIR Observations
4. **Write**: Observations are written to appropriate Firestore collection
5. **Delete**: Original file is deleted from Cloud Storage

## Data Formats

### Health Sample Archives

- **Format**: zstd-compressed JSON
- **Structure**: Array of FHIR Observations or wrapper object with `data` array
- **Compression**: Zstandard (zstd) for efficient compression of repetitive health data

### HealthKit Identifiers

Common HealthKit data types collected:

| Category | Identifiers |
|----------|-------------|
| Activity | `HKQuantityTypeIdentifierStepCount`, `HKQuantityTypeIdentifierDistanceWalkingRunning`, `HKQuantityTypeIdentifierActiveEnergyBurned` |
| Heart | `HKQuantityTypeIdentifierHeartRate`, `HKQuantityTypeIdentifierRestingHeartRate`, `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` |
| Sleep | `HKCategoryTypeIdentifierSleepAnalysis` |
| Clinical | `HKClinicalTypeIdentifierAllergyRecord`, `HKClinicalTypeIdentifierConditionRecord`, `HKClinicalTypeIdentifierMedicationRecord` |

### SensorKit Identifiers

SensorKit data types use the `com.apple.SensorKit.` prefix:

- `com.apple.SensorKit.ambientPressure`
- `com.apple.SensorKit.accelerometer`
- `com.apple.SensorKit.rotationRate`
- `com.apple.SensorKit.visits`
- `com.apple.SensorKit.deviceUsageReport`
- `com.apple.SensorKit.phoneUsageReport`

## FHIR Data Structures

### User Profile

Stored at `/users/{userId}`:

```json
{
  "disabled": false,
  "dateOfBirth": "1985-06-15T00:00:00Z",
  "language": "en",
  "timeZone": "America/Los_Angeles",
  "participantGroup": 1,
  "dateOfEnrollment": "2024-01-15T10:30:00Z",
  "lastActiveDate": "2024-03-20T14:22:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| disabled | boolean | Yes | Whether user account is disabled |
| dateOfBirth | Date | No | User's date of birth |
| language | string | No | Preferred language code |
| timeZone | string | No | IANA timezone identifier |
| participantGroup | number | No | Study group assignment |
| dateOfEnrollment | Date | Yes | When user enrolled in study |
| lastActiveDate | Date | Yes | Last activity timestamp |

### FHIR Observation

Health data stored as FHIR R4 Observations:

```json
{
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "55423-8",
        "display": "Number of steps"
      }
    ],
    "text": "Step Count"
  },
  "subject": {
    "reference": "Patient/vqzvMTfki9hD0yqTcVVW8XsKf6g2"
  },
  "effectiveDateTime": "2024-03-20T14:22:00Z",
  "valueQuantity": {
    "value": 8542,
    "unit": "steps",
    "system": "http://unitsofmeasure.org",
    "code": "{steps}"
  }
}
```

For time-range data, `effectivePeriod` replaces `effectiveDateTime`:

```json
{
  "effectivePeriod": {
    "start": "2024-03-20T00:00:00Z",
    "end": "2024-03-20T23:59:59Z"
  }
}
```

### FHIR QuestionnaireResponse

Survey responses stored as FHIR QuestionnaireResponse:

```json
{
  "resourceType": "QuestionnaireResponse",
  "questionnaire": "http://myheartcounts.stanford.edu/questionnaires/daily-checkin",
  "status": "completed",
  "authored": "2024-03-20T08:15:00Z",
  "item": [
    {
      "linkId": "mood",
      "answer": [
        {
          "valueCoding": {
            "system": "http://myheartcounts.stanford.edu/mood",
            "code": "good",
            "display": "Good"
          }
        }
      ]
    },
    {
      "linkId": "sleep-quality",
      "answer": [
        {
          "valueInteger": 7
        }
      ]
    },
    {
      "linkId": "notes",
      "answer": [
        {
          "valueString": "Felt well rested today"
        }
      ]
    }
  ]
}
```

Answer types include:
- `valueCoding`: Coded/categorical responses
- `valueString`: Free text responses
- `valueInteger`: Numeric responses
- `valueBoolean`: Yes/no responses
- `valueDate`: Date responses

## Key Variables Reference

| Variable | Source | Example |
|----------|--------|---------|
| `{userId}` | Firebase Auth UID | `vqzvMTfki9hD0yqTcVVW8XsKf6g2` |
| `{uuid}` | System-generated UUID | `BCD7D622-0CDC-4194-A008-3452C9C95546` |
| `{HealthKitIdentifier}` | Apple HealthKit API | `HKQuantityTypeIdentifierStepCount` |
| `{SensorKitDataType}` | Apple SensorKit API | `ambientPressure` |
| `{deviceId}` | Device registration | `iPhone14_A1B2C3D4` |

## Data Access Patterns

### Querying User Health Data

To retrieve all step count observations for a user:

```
/users/{userId}/HealthObservations_HKQuantityTypeIdentifierStepCount
```

### Querying Questionnaire Responses

To retrieve all questionnaire responses for a user:

```
/users/{userId}/questionnaireResponses
```

Filter by questionnaire using the `questionnaire` field.

### Collection Group Queries

The `devices` collection can be queried across all users using Firestore collection group queries.

## Related Resources

- [MyHeartCounts-Firebase Repository](https://github.com/StanfordBDHG/MyHeartCounts-Firebase)
- [FHIR R4 Observation](https://www.hl7.org/fhir/observation.html)
- [FHIR R4 QuestionnaireResponse](https://www.hl7.org/fhir/questionnaireresponse.html)
- [Apple HealthKit Documentation](https://developer.apple.com/documentation/healthkit)
- [Apple SensorKit Documentation](https://developer.apple.com/documentation/sensorkit)
