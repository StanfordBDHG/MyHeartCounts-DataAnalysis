# MyHeartCounts Data Client

The `myheartcounts_ds` package provides a Python client for accessing MyHeartCounts Firebase/Firestore data.

## Installation

The package is installed as part of the project dependencies:

```bash
uv sync
```

## Authentication

The client uses Google Cloud Application Default Credentials (ADC). Before using the client, authenticate with:

```bash
gcloud auth application-default login
```

## Configuration

### MHCConfig

Configuration is managed through the `MHCConfig` dataclass:

```python
from myheartcounts_ds import MHCConfig

# Create config for development environment
config = MHCConfig.dev()

# Create config for production environment
config = MHCConfig.prod()

# Create config from environment variables
config = MHCConfig.from_env()

# Create custom config
config = MHCConfig(
    project_id="my-project-id",
    storage_bucket="my-bucket"  # Optional, defaults to {project_id}.firebasestorage.app
)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MHC_PROJECT_ID` | Google Cloud project ID | `som-rit-phi-mhc-prod` (for `from_env()`) |
| `MHC_STORAGE_BUCKET` | GCS bucket for file storage | `{project_id}.firebasestorage.app` |

### Default Project IDs

- **Development:** `som-rit-phi-mhc-dev`
- **Production:** `som-rit-phi-mhc-prod`

## Client Usage

### Initialization

```python
from myheartcounts_ds import MHC4Client, MHCConfig

# Use default config (from environment, defaults to production)
client = MHC4Client()

# Use specific environment
client = MHC4Client(config=MHCConfig.dev())

# Use custom config
client = MHC4Client(config=MHCConfig(project_id="my-project"))
```

### Listing Users

```python
# List all users
users = client.list_users()

# List with a limit
users = client.list_users(limit=100)

for user in users:
    print(f"{user.id}: enrolled {user.date_of_enrollment}")
```

### Getting a Specific User

```python
# Get user by ID
user = client.get_user("firebase-uid-123")

if user:
    print(f"Found user: {user.id}")
    print(f"Language: {user.language}")
    print(f"Time zone: {user.time_zone}")
else:
    print("User not found")
```

## User Model

The `User` dataclass represents a MyHeartCounts user profile with the following attributes:

### Identity

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Firebase Auth UID (document ID) |
| `disabled` | `bool` | Whether the account is disabled |

### Dates

| Attribute | Type | Description |
|-----------|------|-------------|
| `date_of_birth` | `datetime \| None` | User's date of birth |
| `date_of_enrollment` | `datetime \| None` | When user enrolled in study |
| `last_active_date` | `datetime \| None` | Last activity timestamp |

### Preferences

| Attribute | Type | Description |
|-----------|------|-------------|
| `language` | `str \| None` | Preferred language code |
| `time_zone` | `str \| None` | IANA timezone identifier |
| `participant_group` | `int \| None` | Study group assignment |

### Demographics

| Attribute | Type | Description |
|-----------|------|-------------|
| `biological_sex_at_birth` | `int \| None` | Coded biological sex |
| `blood_type` | `int \| None` | Coded blood type |
| `height_in_cm` | `float \| None` | Height in centimeters |
| `weight_in_kg` | `float \| None` | Weight in kilograms |
| `us_region` | `str \| None` | US state/region code |
| `education_us` | `str \| None` | Education level |
| `household_income_us` | `int \| None` | Coded household income |
| `race_ethnicity` | `int \| None` | Coded race/ethnicity |
| `latino_status` | `int \| None` | Coded Latino/Hispanic status |
| `mhc_gender_identity` | `int \| None` | Coded gender identity |

### Health & Study

| Attribute | Type | Description |
|-----------|------|-------------|
| `comorbidities` | `dict \| None` | Dictionary of comorbidity data |
| `stage_of_change` | `str \| None` | Current stage of change |
| `did_opt_in_to_trial` | `bool \| None` | Whether user opted into trial |
| `future_studies` | `bool \| None` | Consent to future studies |

### Consent

| Attribute | Type | Description |
|-----------|------|-------------|
| `last_signed_consent_date` | `datetime \| None` | When consent was last signed |
| `last_signed_consent_version` | `str \| None` | Version of consent signed |
| `most_recent_onboarding_step` | `str \| None` | Last completed onboarding step |

### Notifications

| Attribute | Type | Description |
|-----------|------|-------------|
| `preferred_notification_time` | `str \| None` | Preferred notification time |
| `preferred_workout_types` | `str \| None` | Preferred workout types |

## Example: Complete Workflow

```python
from myheartcounts_ds import MHC4Client, MHCConfig

# Connect to development environment
config = MHCConfig.dev()
client = MHC4Client(config=config)

# Get a sample of users
users = client.list_users(limit=10)

print(f"Found {len(users)} users")

for user in users:
    print(f"\nUser: {user.id}")
    print(f"  Enrolled: {user.date_of_enrollment}")
    print(f"  Last active: {user.last_active_date}")
    print(f"  Language: {user.language}")
    print(f"  Group: {user.participant_group}")
```
