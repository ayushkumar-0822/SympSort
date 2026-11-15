"""
SympSort — Configuration Constants
===================================
Central configuration for the Medical Cost & Lifestyle Factors analysis project.
All project-wide constants, paths, column names, color palettes, and chart
settings live here so that every other module imports from one place.
"""

import os
from pathlib import Path

# ── Project metadata ──────────────────────────────────────────────────────────
PROJECT_NAME: str = "SympSort"
PROJECT_TITLE: str = "Medical Cost & Lifestyle Factors"
COURSE_NAME: str = "B.Tech IT Workshop Lab (PCC CS 393), Academic Year 2026–27"
COURSE_CODE: str = "PCC CS 393"
ACADEMIC_YEAR: str = "2026–27"

ASSIGNED_PROBLEM_STATEMENT: str = (
    "Find the average insurance charge for smokers vs. non-smokers using Pandas. "
    "Create a Seaborn barplot to visually compare the average costs between the two groups."
)

PROBLEM_STATEMENT: str = (
    "Analyze and visualize the relationship between smoking status and "
    "medical insurance charges using real-world data to quantify the "
    "financial impact of smoking on healthcare costs."
)

DATASET_SOURCE_URL: str = (
    "https://www.kaggle.com/datasets/mirichoi0218/insurance"
)

# ── File paths ────────────────────────────────────────────────────────────────
_PROJECT_ROOT: Path = Path(__file__).parent
DEFAULT_DATA_PATH: Path = _PROJECT_ROOT / "data" / "insurance.csv"
SAMPLE_DATA_PATH: Path = _PROJECT_ROOT / "data" / "insurance_sample.csv"
OUTPUT_DIR: Path = Path("/tmp/outputs") if os.environ.get("VERCEL") else _PROJECT_ROOT / "outputs"

# ── Dataset column names ─────────────────────────────────────────────────────
COLUMN_AGE: str = "age"
COLUMN_SEX: str = "sex"
COLUMN_BMI: str = "bmi"
COLUMN_CHILDREN: str = "children"
COLUMN_SMOKER: str = "smoker"
COLUMN_REGION: str = "region"
COLUMN_CHARGES: str = "charges"

REQUIRED_COLUMNS: list[str] = [COLUMN_SMOKER, COLUMN_CHARGES]
ALL_COLUMNS: list[str] = [
    COLUMN_AGE,
    COLUMN_SEX,
    COLUMN_BMI,
    COLUMN_CHILDREN,
    COLUMN_SMOKER,
    COLUMN_REGION,
    COLUMN_CHARGES,
]

# ── Valid values ──────────────────────────────────────────────────────────────
VALID_SMOKER_VALUES: set[str] = {"yes", "no"}
VALID_REGIONS: list[str] = ["northeast", "northwest", "southeast", "southwest"]

# ── Color palettes ────────────────────────────────────────────────────────────
# Teal for non-smoker, brick-red for smoker — consistent across light/dark.
COLOR_NON_SMOKER: str = "#1F6F63"
COLOR_SMOKER: str = "#B5442E"

PALETTE_LIGHT: dict[str, str] = {
    "no": COLOR_NON_SMOKER,
    "yes": COLOR_SMOKER,
}

PALETTE_DARK: dict[str, str] = {
    "no": COLOR_NON_SMOKER,
    "yes": COLOR_SMOKER,
}

# Chart background colors
CHART_BG_LIGHT: str = "#FAF8F4"
CHART_BG_DARK: str = "#1E1F22"

# Text / axis colors
CHART_TEXT_LIGHT: str = "#333333"
CHART_TEXT_DARK: str = "#E0E0E0"
CHART_AXIS_LIGHT: str = "#CCCCCC"
CHART_AXIS_DARK: str = "#444444"

# ── Chart settings ────────────────────────────────────────────────────────────
CHART_DPI_SCREEN: int = 150
CHART_DPI_DOWNLOAD: int = 300
CHART_WIDTH: float = 9.6
CHART_HEIGHT: float = 5.4

# ── Flask defaults ────────────────────────────────────────────────────────────
DEFAULT_PORT: int = 5000
DEFAULT_PAGE_SIZE: int = 25
MAX_PAGE_SIZE: int = 200
