# MyHeartCounts Data Analysis

Data science package focused on quality control and validation of new MHC 4.0 app data stored in backend services as defined in https://github.com/StanfordBDHG/MyHeartCounts-Firebase.

## Documentation

- [Data Architecture](DATA_ARCHITECTURE.md) - Comprehensive documentation of the Firebase data structure, including Firestore collections, Cloud Storage paths, and FHIR data formats

## CLI Commands

The package provides a command-line interface via the `mhc-ds` command.

### Generate Observation Types

Discovers HealthObservation types from the Firestore database and generates a Python enum with full IDE autocomplete support.

```bash
# Generate types from production database
mhc-ds generate-types

# Specify a different project
mhc-ds generate-types --project som-rit-phi-mhc-dev

# Sample more users for better coverage (default: 100)
mhc-ds generate-types --user-limit 500

# Write to a custom output path
mhc-ds generate-types --output ./my_types.py
```

After generation, use the enum in your code:

```python
from myheartcounts_ds import DiscoveredObservationType

# Full IDE autocomplete support
step_count = DiscoveredObservationType.HK_QUANTITY_STEP_COUNT
print(step_count.value)  # "HKQuantityTypeIdentifierStepCount"

# Lookup by raw identifier
from myheartcounts_ds.typegen import get_observation_type_by_identifier
obs_type = get_observation_type_by_identifier("HKQuantityTypeIdentifierHeartRate")
```

## Project Structure

```
MyHeartCounts-DataAnalysis/
├── src/
│   └── myheartcounts_ds/       # Main package (src layout)
│       ├── __init__.py
│       ├── client.py           # MHC4Client for Firestore access
│       ├── config.py           # Configuration management
│       ├── constants.py        # Constants and category enums
│       ├── models.py           # Data models (User, etc.)
│       ├── cli.py              # Command-line interface
│       └── typegen/            # Type generation subpackage
│           ├── __init__.py
│           ├── categories.py   # Category definitions
│           ├── discovery.py    # Type discovery logic
│           ├── codegen.py      # Enum code generator
│           └── generated_types.py  # Generated observation types enum
├── tests/                      # Test directory
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── test_*.py               # Test modules
├── notebooks/                  # Jupyter notebooks for data analysis
├── scripts/                    # Utility scripts
├── pyproject.toml              # Project configuration
└── README.md
```

## Setup

This project uses uv for package management, ruff for linting, and mypy for type checking.

### Notebook Output Security

This project automatically strips outputs from Jupyter notebooks before committing to prevent accidental exposure of sensitive data. This is handled by `nbstripout`, which is configured as a Git filter.

- **Local development**: Notebook outputs are preserved for your workflow
- **Version control**: Outputs are automatically stripped when staging/committing
- **Security**: Prevents sensitive data in cell outputs from being committed

The configuration is already set up - no additional action should be needed but please test after first setting things up from scratch, just to be sure this is working correctly!

### Installation

```bash
uv sync
```

### Development

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run linting
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Run type checking
mypy src/

# Run tests
pytest
```

## Why src/ Layout?

This project uses the `src/` layout, which is the recommended approach by the Python Packaging Authority (PyPA):

- Prevents accidental imports of the development version
- Forces proper installation for testing
- Provides clear separation between source code and project root


## Cloud functions for ETL
project_id: myheart-counts-development 
## To deploy functions:
## firestore_search_for_new_variables:
`gcloud functions deploy firestore-search-for-new-variables \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=main\
  --trigger-http\
  --memory=256MB \
  --cpu=0.5`

### schedulling
`gcloud functions add-invoker-policy-binding firestore-search-for-new-variables \
  --region=us-central1 \
  --member="serviceAccount:scheduler-etl@myheart-counts-development.iam.gserviceaccount.com"`

`gcloud scheduler jobs create http firestore-search-for-new-variables \
  --schedule="0 5 * * 0" \
  --uri="https://us-central1-myheart-counts-development.cloudfunctions.net/firestore-search-for-new-variables" \
  --http-method=POST \
  --oidc-service-account-email="scheduler-etl@myheart-counts-development.iam.gserviceaccount.com" \
  --location=us-central1`

## firestore_to_BQ_parser:
`gcloud functions deploy firestore-to-BQ-parser \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --entry-point=main \
  --source=. \
  --trigger-http \
  --memory=512MB \
  --cpu=1`

`gcloud functions add-invoker-policy-binding firestore-to-BQ-parser \
  --region=us-central1 \
  --member="serviceAccount:scheduler-etl@myheart-counts-development.iam.gserviceaccount.com"`

  `gcloud scheduler jobs create http firestore-to-BQ-parser \
  --schedule="0 5 * * *" \
  --uri="https://us-central1-myheart-counts-development.cloudfunctions.net/firestore-to-BQ-parser" \
  --http-method=POST \
  --oidc-service-account-email="scheduler-etl@myheart-counts-development.iam.gserviceaccount.com" \
  --location=us-central1`

