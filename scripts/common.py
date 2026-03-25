"""
scripts/common.py
=================
Shared constants and utilities used across the pipeline scripts.
"""

import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Currency metadata  (display only)
# ---------------------------------------------------------------------------

CURRENCY_META: dict[str, dict[str, str]] = {
    "USD": {"country": "United States",  "name": "US Dollar"},
    "JPY": {"country": "Japan",          "name": "Japanese Yen"},
    "GBP": {"country": "United Kingdom", "name": "Pound Sterling"},
    "CHF": {"country": "Switzerland",    "name": "Swiss Franc"},
    "AUD": {"country": "Australia",      "name": "Australian Dollar"},
    "CAD": {"country": "Canada",         "name": "Canadian Dollar"},
    "CNY": {"country": "China",          "name": "Chinese Renminbi"},
    "KRW": {"country": "South Korea",    "name": "South Korean Won"},
    "HKD": {"country": "Hong Kong",      "name": "Hong Kong Dollar"},
    "SGD": {"country": "Singapore",      "name": "Singapore Dollar"},
    "SEK": {"country": "Sweden",         "name": "Swedish Krona"},
    "NOK": {"country": "Norway",         "name": "Norwegian Krone"},
    "DKK": {"country": "Denmark",        "name": "Danish Krone"},
    "NZD": {"country": "New Zealand",    "name": "New Zealand Dollar"},
    "MXN": {"country": "Mexico",         "name": "Mexican Peso"},
    "BRL": {"country": "Brazil",         "name": "Brazilian Real"},
    "INR": {"country": "India",          "name": "Indian Rupee"},
    "ZAR": {"country": "South Africa",   "name": "South African Rand"},
    "TRY": {"country": "Turkey",         "name": "Turkish Lira"},
    "PLN": {"country": "Poland",         "name": "Polish Zloty"},
}

# ---------------------------------------------------------------------------
# ECB API
# ---------------------------------------------------------------------------

ECB_API_URL    = "https://data-api.ecb.europa.eu/service/data/EXR"
ECB_START_DATE = "1999-01-01"

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

ECB_RAW_PATH   = Path("ecb_raw/all_currencies.csv")
DATASETS_ROOT  = Path("datasets")
NOTEBOOKS_ROOT = Path("notebooks")

# ---------------------------------------------------------------------------
# Kaggle identity
# ---------------------------------------------------------------------------

KAGGLE_USER = (
    os.environ.get("KAGGLE_USERNAME")
    or os.environ.get("KAGGLE_USER")
    or "YOUR_KAGGLE_USERNAME"
)

GITHUB_MATRIX_LIMIT = 256

# ---------------------------------------------------------------------------
# Pair helpers
# ---------------------------------------------------------------------------

def parse_pair(pair: str) -> tuple[str, str]:
    """Split a 6-character pair code into (base, quote)."""
    pair = pair.upper()
    return pair[:3], pair[3:]


def dataset_slug(pair: str) -> str:
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}"


def notebook_slug(pair: str) -> str:
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}-eda-baseline-forecast"


def modeling_notebook_slug(pair: str) -> str:
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}-arima-garch-modeling"


def dataset_title(pair: str) -> str:
    return f"Daily FX: {pair}"


def notebook_title(pair: str) -> str:
    return f"Daily FX: {pair} -- EDA & Baseline Forecast"


def modeling_notebook_title(pair: str) -> str:
    return f"Daily FX: {pair} -- ARIMA & GARCH Modeling"


def series_search_url(resource: str) -> str:
    if resource == "datasets":
        return f"https://www.kaggle.com/datasets?search={KAGGLE_USER}+Daily+FX"
    return f"https://www.kaggle.com/code?searchQuery={KAGGLE_USER}+Daily+FX"


def pair_output_dir(pair: str) -> Path:
    path = DATASETS_ROOT / pair
    path.mkdir(parents=True, exist_ok=True)
    return path


def notebook_output_dir(pair: str) -> Path:
    path = NOTEBOOKS_ROOT / pair
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Subprocess wrapper
# ---------------------------------------------------------------------------

def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# GitHub Actions helpers
# ---------------------------------------------------------------------------

def append_github_summary(text: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null")
    with open(summary_path, "a") as fh:
        fh.write(text)


def emit_github_warning(message: str, script: str = "scripts/common.py") -> None:
    print(f"::warning file={script}::{message}")


# ---------------------------------------------------------------------------
# Kaggle metadata constraints
# ---------------------------------------------------------------------------

KAGGLE_TITLE_MIN    = 6
KAGGLE_TITLE_MAX    = 50
KAGGLE_SUBTITLE_MIN = 20
KAGGLE_SUBTITLE_MAX = 80
KAGGLE_KEYWORDS_MAX = 20


def validate_kaggle_metadata(title: str, subtitle: str, keywords: list[str]) -> list[str]:
    errors = []
    if not (KAGGLE_TITLE_MIN <= len(title) <= KAGGLE_TITLE_MAX):
        errors.append(
            f"title length {len(title)} is outside [{KAGGLE_TITLE_MIN}, {KAGGLE_TITLE_MAX}]: "
            f"\'{title}\'"
        )
    if not (KAGGLE_SUBTITLE_MIN <= len(subtitle) <= KAGGLE_SUBTITLE_MAX):
        errors.append(
            f"subtitle length {len(subtitle)} is outside "
            f"[{KAGGLE_SUBTITLE_MIN}, {KAGGLE_SUBTITLE_MAX}]: \'{subtitle}\'"
        )
    if len(keywords) > KAGGLE_KEYWORDS_MAX:
        errors.append(
            f"keywords count {len(keywords)} exceeds limit {KAGGLE_KEYWORDS_MAX}"
        )
    return errors


# ---------------------------------------------------------------------------
# Notebook cell builders
# ---------------------------------------------------------------------------

def md(source: str) -> dict:
    import hashlib
    return {
        "cell_type": "markdown",
        "id": hashlib.md5(source.encode()).hexdigest()[:8],
        "metadata": {},
        "source": source,
    }


def code(source: str) -> dict:
    import hashlib
    return {
        "cell_type": "code",
        "id": hashlib.md5(source.encode()).hexdigest()[:8],
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source,
    }


# ---------------------------------------------------------------------------
# Utils kernel
# ---------------------------------------------------------------------------

UTILS_KERNEL_TITLE = "Daily FX: Utils"
UTILS_DIR = NOTEBOOKS_ROOT / "utils"


def utils_slug() -> str:
    """Kaggle kernel identifier for the shared utility script."""
    return f"{KAGGLE_USER}/daily-fx-utils"


def utils_output_dir() -> Path:
    """Return (and create) the output directory for the utils script."""
    UTILS_DIR.mkdir(parents=True, exist_ok=True)
    return UTILS_DIR
