"""Shared pytest fixtures for SympSort test suite."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `import config`, `import app`, etc.
# resolve without installing the package.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Fixtures — Data
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """Small, deterministic DataFrame with known smoker / non-smoker rows.

    Contains 6 rows: 2 smokers and 4 non-smokers.
    Smoker mean  = (30000 + 40000) / 2 = 35000.0
    Non-smoker mean = (5000 + 6000 + 7000 + 8000) / 4 = 6500.0
    """
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 45, 50],
        "sex": ["male", "female", "male", "female", "male", "female"],
        "bmi": [22.0, 28.5, 30.1, 25.0, 27.3, 31.0],
        "children": [0, 1, 2, 0, 3, 1],
        "smoker": ["no", "no", "yes", "no", "yes", "no"],
        "smoker_clean": ["no", "no", "yes", "no", "yes", "no"],
        "smoker_label": [
            "Non-Smoker", "Non-Smoker", "Smoker",
            "Non-Smoker", "Smoker", "Non-Smoker",
        ],
        "region": ["southwest", "southeast", "northwest", "northeast",
                   "southwest", "southeast"],
        "charges": [5000.0, 6000.0, 30000.0, 7000.0, 40000.0, 8000.0],
    })


@pytest.fixture()
def valid_df() -> pd.DataFrame:
    """Load the real *insurance.csv* through the project's data loader.

    Returns the cleaned DataFrame that ``load_dataset`` produces.
    Skips the test if the CSV file is not present on disk.
    """
    from data_loader import load_dataset
    from config import DEFAULT_DATA_PATH

    if not DEFAULT_DATA_PATH.exists():
        pytest.skip("insurance.csv not found — skipping integration fixture")

    df_valid, _, report = load_dataset(DEFAULT_DATA_PATH)
    assert report.is_valid, f"Dataset validation failed: {report.error_message}"
    return df_valid


# ---------------------------------------------------------------------------
# Fixtures — Flask test client
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Create a Flask application instance configured for testing."""
    from app import create_app

    application = create_app()
    application.config.update({
        "TESTING": True,
    })
    return application


@pytest.fixture()
def client(app):
    """Flask test client backed by the test application."""
    return app.test_client()
