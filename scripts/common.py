"""
scripts/common.py
=================
Shared constants and utilities used across the pipeline scripts.

Single source of truth for:
  - currency metadata (display only — not used to control what is fetched)
  - directory layout
  - Kaggle naming conventions
  - GitHub Actions helpers
  - subprocess wrapper

Note on currency discovery
--------------------------
The list of currencies actually fetched is determined dynamically by the
ECB API (via the wildcard key in fetch_ecb.py) and written to
ecb_raw/all_currencies.csv.  There is no hardcoded CURRENCIES list here.
CURRENCY_META is used only for display purposes (names, country labels).
"""

import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Currency metadata  (display only — names and countries for UI/docs)
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
ECB_START_DATE = "1999-01-01"   # EUR launch date — earliest available data

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
    os.environ.get("KAGGLE_USERNAME")          # legacy API key method
    or os.environ.get("KAGGLE_USER")           # explicit override
    or "YOUR_KAGGLE_USERNAME"                  # fallback (set before push)
)

# GitHub Actions hard limit for a single dynamic matrix.
GITHUB_MATRIX_LIMIT = 256

# ---------------------------------------------------------------------------
# Pair helpers
# ---------------------------------------------------------------------------

def parse_pair(pair: str) -> tuple[str, str]:
    """Split a 6-character pair code into (base, quote). e.g. 'USDJPY' → ('USD', 'JPY')."""
    pair = pair.upper()
    return pair[:3], pair[3:]


def dataset_slug(pair: str) -> str:
    """Kaggle dataset identifier. e.g. 'USDJPY' → 'user/ecb-fx-usdjpy-daily'."""
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}"


def notebook_slug(pair: str) -> str:
    """Kaggle kernel identifier for the EDA notebook."""
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}-eda-baseline-forecast"


def modeling_notebook_slug(pair: str) -> str:
    """Kaggle kernel identifier for the modeling notebook."""
    return f"{KAGGLE_USER}/daily-fx-{pair.lower()}-arima-garch-modeling"


def dataset_title(pair: str) -> str:
    """Kaggle dataset display title."""
    return f"Daily FX: {pair}"


def notebook_title(pair: str) -> str:
    """Kaggle EDA notebook display title."""
    return f"Daily FX: {pair} — EDA & Baseline Forecast"


def modeling_notebook_title(pair: str) -> str:
    """Kaggle modeling notebook display title."""
    return f"Daily FX: {pair} — ARIMA & GARCH Modeling"


def series_search_url(resource: str) -> str:
    """
    Return a Kaggle search URL for the full Daily FX series.

    resource : "datasets" or "code"
    """
    if resource == "datasets":
        return f"https://www.kaggle.com/datasets?search={KAGGLE_USER}+Daily+FX"
    return f"https://www.kaggle.com/code?searchQuery={KAGGLE_USER}+Daily+FX"


def pair_output_dir(pair: str) -> Path:
    """Return (and create) the dataset output directory for one pair."""
    path = DATASETS_ROOT / pair
    path.mkdir(parents=True, exist_ok=True)
    return path


def notebook_output_dir(pair: str) -> Path:
    """Return (and create) the notebook output directory for one pair."""
    path = NOTEBOOKS_ROOT / pair
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Subprocess wrapper
# ---------------------------------------------------------------------------

def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a shell command, print its output, and return the result."""
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
    """Append Markdown text to the GitHub Actions job summary page."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null")
    with open(summary_path, "a") as fh:
        fh.write(text)


def emit_github_warning(message: str, script: str = "scripts/common.py") -> None:
    """Emit a ::warning:: annotation visible in the Actions log and PR checks."""
    print(f"::warning file={script}::{message}")


# ---------------------------------------------------------------------------
# Kaggle metadata constraints
# (source: https://github.com/Kaggle/kaggle-api/wiki/Dataset-Metadata)
# ---------------------------------------------------------------------------

KAGGLE_TITLE_MIN    = 6
KAGGLE_TITLE_MAX    = 50
KAGGLE_SUBTITLE_MIN = 20
KAGGLE_SUBTITLE_MAX = 80

# The API documentation does not specify a tag count limit.
# We cap at 20 as a conservative safe limit based on observed behaviour.
KAGGLE_KEYWORDS_MAX = 20


def validate_kaggle_metadata(title: str, subtitle: str, keywords: list[str]) -> list[str]:
    """
    Validate Kaggle dataset metadata against documented constraints.

    Returns a list of error messages.  An empty list means all fields are valid.
    Raises nothing — callers decide how to handle errors.
    """
    errors = []

    if not (KAGGLE_TITLE_MIN <= len(title) <= KAGGLE_TITLE_MAX):
        errors.append(
            f"title length {len(title)} is outside [{KAGGLE_TITLE_MIN}, {KAGGLE_TITLE_MAX}]: "
            f"'{title}'"
        )

    if not (KAGGLE_SUBTITLE_MIN <= len(subtitle) <= KAGGLE_SUBTITLE_MAX):
        errors.append(
            f"subtitle length {len(subtitle)} is outside "
            f"[{KAGGLE_SUBTITLE_MIN}, {KAGGLE_SUBTITLE_MAX}]: '{subtitle}'"
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
    """Return an nbformat v4 markdown cell."""
    import hashlib
    return {
        "cell_type": "markdown",
        "id": hashlib.md5(source.encode()).hexdigest()[:8],
        "metadata": {},
        "source": source,
    }


def code(source: str) -> dict:
    """Return an nbformat v4 code cell."""
    import hashlib
    return {
        "cell_type": "code",
        "id": hashlib.md5(source.encode()).hexdigest()[:8],
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source,
    }
