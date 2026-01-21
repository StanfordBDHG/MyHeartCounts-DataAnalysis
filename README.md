# MyHeartCounts Data Analysis

Data science package focused on quality control and validation of new MHC 4.0 app data stored in backend services as defined in https://github.com/StanfordBDHG/MyHeartCounts-Firebase.

## Documentation

- [Data Architecture](DATA_ARCHITECTURE.md) - Comprehensive documentation of the Firebase data structure, including Firestore collections, Cloud Storage paths, and FHIR data formats

## Project Structure

```
MyHeartCounts-DataAnalysis/
├── src/
│   └── myheartcounts_ds/       # Main package (src layout)
│       └── __init__.py
├── tests/                      # Test directory
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── test_placeholder.py
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
