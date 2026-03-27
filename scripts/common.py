"""
scripts/common.py
=================
Shared constants and utilities used across the pipeline scripts.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Currency metadata  (display only)
# ---------------------------------------------------------------------------

CURRENCY_META: dict[str, dict[str, str]] = {
    "USD": {"country": "United States", "name": "US Dollar"},
    "JPY": {"country": "Japan", "name": "Japanese Yen"},
    "GBP": {"country": "United Kingdom", "name": "Pound Sterling"},
    "CHF": {"country": "Switzerland", "name": "Swiss Franc"},
    "AUD": {"country": "Australia", "name": "Australian Dollar"},
    "CAD": {"country": "Canada", "name": "Canadian Dollar"},
    "CNY": {"country": "China", "name": "Chinese Renminbi"},
    "KRW": {"country": "South Korea", "name": "South Korean Won"},
    "HKD": {"country": "Hong Kong", "name": "Hong Kong Dollar"},
    "SGD": {"country": "Singapore", "name": "Singapore Dollar"},
    "SEK": {"country": "Sweden", "name": "Swedish Krona"},
    "NOK": {"country": "Norway", "name": "Norwegian Krone"},
    "DKK": {"country": "Denmark", "name": "Danish Krone"},
    "NZD": {"country": "New Zealand", "name": "New Zealand Dollar"},
    "MXN": {"country": "Mexico", "name": "Mexican Peso"},
    "BRL": {"country": "Brazil", "name": "Brazilian Real"},
    "INR": {"country": "India", "name": "Indian Rupee"},
    "ZAR": {"country": "South Africa", "name": "South African Rand"},
    "TRY": {"country": "Turkey", "name": "Turkish Lira"},
    "PLN": {"country": "Poland", "name": "Polish Zloty"},
}

# ---------------------------------------------------------------------------
# ECB API
# ---------------------------------------------------------------------------

ECB_API_URL = "https://data-api.ecb.europa.eu/service/data/EXR"
ECB_START_DATE = "1999-01-01"

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

ECB_RAW_PATH = Path("ecb_raw/all_currencies.csv")
DATASETS_ROOT = Path("datasets")
NOTEBOOKS_ROOT = Path("notebooks")
PAIRS_FILE = Path("pairs.txt")
PUBLIC_KERNELS_FILE = Path("public_kernels.txt")

# ---------------------------------------------------------------------------
# Kaggle identity
# ---------------------------------------------------------------------------

KAGGLE_USER = (
    os.environ.get("KAGGLE_USERNAME") or os.environ.get("KAGGLE_USER") or "YOUR_KAGGLE_USERNAME"
)

GITHUB_MATRIX_LIMIT = 256
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/hide-san/daily-fx-ecb"
KAGGLE_KEYWORDS: list[str] = ["finance", "economics"]

# ---------------------------------------------------------------------------
# Pair helpers
# ---------------------------------------------------------------------------


def load_public_kernels(path: Path = PUBLIC_KERNELS_FILE) -> set[str]:
    """Return the set of fully-qualified Kaggle kernel slugs from public_kernels.txt.

    Each non-blank, non-comment line is a kernel name (without username prefix).
    KAGGLE_USER is prepended automatically so the file stays username-agnostic.
    Scripts call this to verify their slug is explicitly approved before writing
    any files.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    names = {line.strip() for line in lines if line.strip() and not line.startswith("#")}
    return {f"{KAGGLE_USER}/{name}" for name in names}


def load_pairs_file(path: Path = PAIRS_FILE) -> list[str]:
    """Return pairs from a pairs.txt file, ignoring blank lines and comments."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return list(
        dict.fromkeys(
            line.strip().upper()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        )
    )


def parse_pair(pair: str) -> tuple[str, str]:
    """Split a 6-character pair code into (base, quote)."""
    pair = pair.upper()
    return pair[:3], pair[3:]


def pair_display(pair: str) -> str:
    """Return human-readable pair display string e.g. 'NZD/JPY'."""
    base, quote = parse_pair(pair)
    return f"{base}/{quote}"


def dataset_slug(pair: str) -> str:
    base, quote = parse_pair(pair)
    return f"{KAGGLE_USER}/daily-fx-{base.lower()}-{quote.lower()}"


def notebook_slug(pair: str) -> str:
    base, quote = parse_pair(pair)
    return f"{KAGGLE_USER}/daily-fx-{base.lower()}-{quote.lower()}-eda-baseline-forecast"


def modeling_notebook_slug(pair: str) -> str:
    base, quote = parse_pair(pair)
    return f"{KAGGLE_USER}/daily-fx-{base.lower()}-{quote.lower()}-arima-garch-modeling"


def dataset_title(pair: str) -> str:
    return f"Daily FX: {pair_display(pair)}"


def notebook_title(pair: str) -> str:
    return f"Daily FX: {pair_display(pair)} - EDA & Baseline Forecast"


def modeling_notebook_title(pair: str) -> str:
    return f"Daily FX: {pair_display(pair)} - ARIMA & GARCH Modeling"


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


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
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

KAGGLE_TITLE_MIN = 6
KAGGLE_TITLE_MAX = 50
KAGGLE_SUBTITLE_MIN = 20
KAGGLE_SUBTITLE_MAX = 80
KAGGLE_KEYWORDS_MAX = 20


def validate_kaggle_metadata(title: str, subtitle: str, keywords: list[str]) -> list[str]:
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
        errors.append(f"keywords count {len(keywords)} exceeds limit {KAGGLE_KEYWORDS_MAX}")
    return errors


# ---------------------------------------------------------------------------
# Notebook cell builders
# ---------------------------------------------------------------------------


def make_notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a minimal nbformat v4 notebook dict with the given cells."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": cells,
    }


def md(source: str) -> dict[str, Any]:
    import hashlib

    return {
        "cell_type": "markdown",
        "id": hashlib.md5(source.encode()).hexdigest()[:8],
        "metadata": {},
        "source": source,
    }


def code(source: str) -> dict[str, Any]:
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
# Shared notebook kernel metadata writer
# ---------------------------------------------------------------------------


def write_notebook_kernel_metadata(
    output_dir: Path,
    filename: str,
    id: str,
    title: str,
    code_file: str,
    enable_internet: bool,
    dataset_sources: list[str],
    kernel_sources: list[str],
) -> None:
    """Write a kernel-metadata JSON file for a standard notebook kernel."""
    import json

    metadata = {
        "id": id,
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": False,
        "enable_internet": enable_internet,
        "keywords": KAGGLE_KEYWORDS,
        "dataset_sources": dataset_sources,
        "competition_sources": [],
        "kernel_sources": kernel_sources,
    }
    with open(output_dir / filename, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


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


# ---------------------------------------------------------------------------
# Pipeline overview notebook
# ---------------------------------------------------------------------------

PIPELINE_NOTEBOOK_TITLE = "Daily FX: ECB Pipeline Overview"
PIPELINE_DIR = NOTEBOOKS_ROOT / "pipeline"


def pipeline_notebook_slug() -> str:
    """Kaggle kernel identifier for the pipeline overview notebook."""
    return f"{KAGGLE_USER}/daily-fx-ecb-pipeline-overview"


def pipeline_notebook_output_dir() -> Path:
    """Return (and create) the output directory for the pipeline notebook."""
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    return PIPELINE_DIR
