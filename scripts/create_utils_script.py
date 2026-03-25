"""
scripts/create_utils_script.py
================================
Generate the shared utility script pushed to Kaggle as a Utility Script kernel.

Attached as a kernel source in every EDA and modeling notebook.
Available inside notebooks at:

    /kaggle/input/daily-fx-utils/fx_utils.py

Output
------
notebooks/utils/
    fx_utils.py                 the utility module
    kernel-metadata-utils.json  Kaggle Kernels API descriptor
"""

import json

from common import (
    UTILS_KERNEL_TITLE,
    append_github_summary,
    utils_output_dir,
    utils_slug,
)

# ---------------------------------------------------------------------------
# Source code of the generated utility module
# ---------------------------------------------------------------------------

FX_UTILS_SOURCE = '''\
"""
fx_utils.py -- Daily FX shared utilities
==========================================
Attach this Utility Script as a kernel source to any Daily FX notebook.

    import sys
    sys.path.insert(0, "/kaggle/input/daily-fx-utils")
    from fx_utils import find_data_dir, apply_plot_style, FEATURE_COLUMNS, get_logger
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Section 1 -- Data path resolver
# ---------------------------------------------------------------------------

def find_data_dir(pair: str) -> Path:
    """
    Locate <pair>.csv under /kaggle/input regardless of path layout.

    Known patterns:
        /kaggle/input/<slug>/<PAIR>.csv                   (most common)
        /kaggle/input/datasets/<owner>/<slug>/<PAIR>.csv  (legacy / org)
        /kaggle/input/<slug>/<PAIR>/<PAIR>.csv            (nested)
    """
    csv_name = f"{pair}.csv"

    # Fast path -- most common layout
    fast = Path(f"/kaggle/input/daily-fx-{pair.lower()}/{csv_name}")
    if fast.exists():
        return fast.parent

    # Recursive fallback
    matches = glob.glob(f"/kaggle/input/**/{csv_name}", recursive=True)
    if not matches:
        raise FileNotFoundError(
            f"{csv_name} not found under /kaggle/input/. "
            "Make sure the dataset is attached to this notebook."
        )
    if len(matches) > 1:
        print(f"[warn] Multiple matches for {csv_name}: {matches} -- using {matches[0]}")
    return Path(matches[0]).parent


# ---------------------------------------------------------------------------
# Section 2 -- Common constants
# ---------------------------------------------------------------------------

# ML-ready feature columns present in every Daily FX CSV.
FEATURE_COLUMNS: list[str] = [
    "rate",
    "daily_return_pct",
    "log_return",
    "ma_7d",
    "ma_21d",
    "ma_63d",
    "volatility_20d",
]

# Calendar columns added by calc_pair.py.
CALENDAR_COLUMNS: list[str] = ["year", "month", "day_of_week"]

# All non-date columns.
ALL_FEATURE_COLUMNS: list[str] = FEATURE_COLUMNS + CALENDAR_COLUMNS

# Brand colours used across all Daily FX charts.
COLOR_RATE   = "#185FA5"   # blue   -- spot rate / actual
COLOR_SIGNAL = "#E8593C"   # orange -- forecast / highlight
COLOR_MUTED  = "#B4B2A9"   # grey   -- secondary series


# ---------------------------------------------------------------------------
# Section 3 -- Plot style
# ---------------------------------------------------------------------------

def apply_plot_style() -> None:
    """
    Apply the shared Daily FX matplotlib style to the current session.

    Call once at the top of a notebook after importing matplotlib:

        import matplotlib.pyplot as plt
        from fx_utils import apply_plot_style
        apply_plot_style()
    """
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.dpi":        120,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.alpha":        0.3,
        "axes.prop_cycle":   plt.cycler(
            color=[COLOR_RATE, COLOR_SIGNAL, COLOR_MUTED,
                   "#1D9E75", "#8B5CF6", "#F59E0B"]
        ),
    })


# ---------------------------------------------------------------------------
# Section 4 -- Logging and notebook summary helpers
# ---------------------------------------------------------------------------

def get_logger(name: str = "daily_fx") -> logging.Logger:
    """
    Return a logger with a consistent format for use inside notebooks.

        log = get_logger()
        log.info("Data loaded: %d rows", len(df))
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                              datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def print_summary(pair: str, df: object) -> None:
    """
    Print a standardised dataset summary block.

    Parameters
    ----------
    pair : str           Currency pair code, e.g. \'USDJPY\'.
    df   : pd.DataFrame  The loaded Daily FX DataFrame.
    """
    import pandas as pd  # type: ignore[import]
    assert isinstance(df, pd.DataFrame)

    latest: str   = df["date"].max().strftime("%Y-%m-%d")
    earliest: str = df["date"].min().strftime("%Y-%m-%d")
    n_rows: int   = len(df)

    print("-" * 40)
    print(f"  Pair     : {pair}")
    print(f"  Rows     : {n_rows:,}")
    print(f"  Period   : {earliest} -> {latest}")
    print(f"  Columns  : {list(df.columns)}")

    if "daily_return_pct" in df.columns:
        returns = df["daily_return_pct"].dropna()
        print(f"  Return   : mean={returns.mean():.4f}%  std={returns.std():.4f}%")

    print("-" * 40)
'''

# ---------------------------------------------------------------------------
# Kaggle kernel metadata
# ---------------------------------------------------------------------------

def write_kernel_metadata() -> None:
    metadata = {
        "id":                  utils_slug(),
        "title":               UTILS_KERNEL_TITLE,
        "code_file":           "fx_utils.py",
        "language":            "python",
        "kernel_type":         "script",
        "util-script":         True,
        "is_private":          True,
        "enable_gpu":          False,
        "enable_internet":     False,
        "keywords":            ["finance", "economics"],
        "dataset_sources":     [],
        "competition_sources": [],
        "kernel_sources":      [],
    }
    output_dir = utils_output_dir()
    with open(output_dir / "kernel-metadata-utils.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    output_dir  = utils_output_dir()
    script_path = output_dir / "fx_utils.py"
    script_path.write_text(FX_UTILS_SOURCE, encoding="utf-8")

    write_kernel_metadata()

    print(f"Script   : {script_path}")
    print(f"Metadata : {output_dir / 'kernel-metadata-utils.json'}")
    append_github_summary("| Utils script | generated |\n")


if __name__ == "__main__":
    main()
