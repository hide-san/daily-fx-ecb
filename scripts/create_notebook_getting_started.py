"""
scripts/create_notebook_getting_started.py  --pair <BASEQUOTE>
===============================================================
Generate a beginner-friendly "Getting Started" notebook for one pair.

Output
------
notebooks/<PAIR>/
    <PAIR>_getting_started.ipynb     nbformat v4 notebook
    kernel-metadata-getting-started.json  Kaggle Kernels API descriptor
"""

import argparse
import json
import sys
from typing import Any

from common import (
    KAGGLE_USER,
    append_github_summary,
    code,
    dataset_slug,
    load_public_kernels,
    md,
    notebook_output_dir,
    pair_display,
    parse_pair,
    pipeline_notebook_slug,
    series_search_url,
    utils_slug,
)

# ---------------------------------------------------------------------------
# Kaggle kernel slug / title helpers (Getting Started variant)
# ---------------------------------------------------------------------------


def getting_started_slug(pair: str) -> str:
    base, quote = parse_pair(pair)
    return f"{KAGGLE_USER}/daily-fx-{base.lower()}-{quote.lower()}-getting-started"


def getting_started_title(pair: str) -> str:
    return f"Daily FX: {pair_display(pair)} - Getting Started"


# ---------------------------------------------------------------------------
# Notebook content
# ---------------------------------------------------------------------------


def build_getting_started_notebook(pair: str, base: str, quote: str) -> dict[str, Any]:
    slug = dataset_slug(pair)

    display = pair_display(pair)

    cells = [
        # ------------------------------------------------------------------ #
        # Title & intro
        # ------------------------------------------------------------------ #
        md(f"""# {getting_started_title(pair)}

Welcome! This is the quickest way to get up and running with the
**{display}** daily exchange-rate dataset.

In just a few cells you will:
1. Load the CSV into a pandas DataFrame
2. See the first and last rows of the data
3. Plot the full rate history

**Dataset**: [{slug}](https://www.kaggle.com/datasets/{slug})  
**Source**: European Central Bank (ECB) -- free reuse with attribution  
**Pair**: {display}
"""),
        # ------------------------------------------------------------------ #
        # Series navigation
        # ------------------------------------------------------------------ #
        md(f"""---

### Explore the full Daily FX series

| | Link |
|---|---|
| All datasets  | {series_search_url("datasets")} |
| All notebooks | {series_search_url("code")} |
| Pipeline overview | https://www.kaggle.com/code/{pipeline_notebook_slug()} |

---
"""),
        # ------------------------------------------------------------------ #
        # Imports
        # ------------------------------------------------------------------ #
        md("## 1. Imports"),
        code("""import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Shared Daily FX utilities
import daily_fx_utils as fu

fu.apply_plot_style()
log = fu.get_logger()
print("Libraries loaded successfully.")"""),
        # ------------------------------------------------------------------ #
        # Load data
        # ------------------------------------------------------------------ #
        md("## 2. Load the data"),
        code(f"""df = fu.read_csv("{pair}")

print(f"Rows    : {{len(df):,}}")
print(f"Columns : {{list(df.columns)}}")
print(f"Period  : {{df['date'].min().date()}} -> {{df['date'].max().date()}}")
print()
df.head()"""),
        code("""# Last 5 rows -- confirm the data is up to date
df.tail()"""),
        # ------------------------------------------------------------------ #
        # Plot 1 -- full history
        # ------------------------------------------------------------------ #
        md("## 3. Full rate history"),
        code(f"""fig, ax = plt.subplots(figsize=(12, 4))

ax.plot(df["date"], df["rate"], linewidth=0.8, color=fu.COLOR_RATE)

ax.set_title("{display} daily spot rate - full history (ECB reference)")
ax.set_ylabel("{quote} per {base}")
ax.set_xlabel("")

ax.xaxis.set_major_locator(mdates.YearLocator(5))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.autofmt_xdate(rotation=0, ha="center")

plt.tight_layout()
plt.show()"""),
        # ------------------------------------------------------------------ #
        # Next steps
        # ------------------------------------------------------------------ #
        md(f"""## 4. What's next?

You've confirmed the data loads and plots correctly. Here are a few natural next steps:

| Notebook | What you'll find |
|---|---|
| **EDA & Baseline Forecast** | Moving averages, return distribution, rolling volatility, rolling-mean forecast |
| **ARIMA & GARCH Modeling** | Stationarity tests, ARIMA mean forecast, GARCH volatility model |

Search for them on Kaggle: {series_search_url("code")}

---

Dataset updated every business day.  
Source: (c) European Central Bank -- https://data.ecb.europa.eu
"""),
    ]

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


# ---------------------------------------------------------------------------
# Kaggle kernel metadata
# ---------------------------------------------------------------------------


def write_kernel_metadata(pair: str) -> None:
    metadata = {
        "id": getting_started_slug(pair),
        "title": getting_started_title(pair),
        "code_file": f"{pair}_getting_started.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": False,
        "enable_internet": False,
        "keywords": ["finance", "economics"],
        "dataset_sources": [dataset_slug(pair)],
        "competition_sources": [],
        "kernel_sources": [utils_slug()],
    }
    output_dir = notebook_output_dir(pair)
    with open(output_dir / "kernel-metadata-getting-started.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a beginner Getting Started notebook for one currency pair."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args = parser.parse_args()
    pair = args.pair.upper()
    base, quote = parse_pair(pair)

    slug = getting_started_slug(pair)
    if slug not in load_public_kernels():
        print(f"ERROR: '{slug}' is not listed in public_kernels.txt.", file=sys.stderr)
        sys.exit(1)

    output_dir = notebook_output_dir(pair)

    nb_path = output_dir / f"{pair}_getting_started.ipynb"
    with open(nb_path, "w", encoding="utf-8") as fh:
        json.dump(
            build_getting_started_notebook(pair, base, quote),
            fh,
            indent=1,
            ensure_ascii=False,
        )

    write_kernel_metadata(pair)

    print(f"Notebook : {nb_path}")
    print(f"Metadata : {output_dir / 'kernel-metadata-getting-started.json'}")
    append_github_summary(f"| {pair} getting-started notebook | generated |\n")


if __name__ == "__main__":
    main()
