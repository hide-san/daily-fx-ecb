"""
scripts/create_notebook_eda.py  --pair <BASEQUOTE>
==================================================
Job 3 (notebook step) -- Generate a Kaggle-ready EDA notebook for one pair.

Output
------
notebooks/<PAIR>/
    <PAIR>_eda.ipynb       nbformat v4 notebook
    kernel-metadata.json   Kaggle Kernels API descriptor
"""

import argparse
import json
import sys
from typing import Any

from common import (
    append_github_summary,
    code,
    dataset_slug,
    lgbm_notebook_slug,
    load_public_kernels,
    make_notebook,
    md,
    modeling_notebook_slug,
    notebook_output_dir,
    notebook_slug,
    notebook_title,
    pair_display,
    parse_pair,
    pipeline_notebook_slug,
    series_search_url,
    utils_slug,
    write_notebook_kernel_metadata,
)

# ---------------------------------------------------------------------------
# Notebook content
# ---------------------------------------------------------------------------


def build_notebook(pair: str, base: str, quote: str) -> dict[str, Any]:
    slug = dataset_slug(pair)

    display = pair_display(pair)

    cells = [
        md(f"""# {notebook_title(pair)}

**Dataset**: [{slug}](https://www.kaggle.com/datasets/{slug})  
**Source**: European Central Bank (ECB) -- free reuse with attribution  
**Pair**: {display}
"""),
        md(f"""---

### Explore the full Daily FX series

| | Link |
|---|---|
| All datasets  | {series_search_url("datasets")} |
| All notebooks | {series_search_url("code")} |
| Pipeline overview | https://www.kaggle.com/code/{pipeline_notebook_slug()} |

---
"""),
        code("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys

# Shared Daily FX utilities
import daily_fx_utils as fu

fu.apply_plot_style()
log = fu.get_logger()"""),
        code(f"""df = fu.read_csv("{pair}")
fu.print_summary("{pair}", df)
df.tail()"""),
        md(f"""## Time series

**Goal**: Identify structural breaks, sustained trends, and regime changes (e.g. financial crises, policy shifts).
**How**: Plot the full history of the {display} spot rate on a single axis.
"""),
        code(f"""fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df["date"], df["rate"], linewidth=0.8, color=fu.COLOR_RATE)
ax.set_title("{display} spot rate (ECB reference)")
ax.set_ylabel("{quote} per {base}")
ax.xaxis.set_major_locator(mdates.YearLocator(5))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
plt.tight_layout()
plt.show()"""),
        md("""## Moving averages

**Goal**: Separate short-term noise from medium-term trend and spot momentum signals.
**How**: Overlay 21-day and 63-day MA (Moving Average) on the spot rate; crossovers between the two are a classic momentum signal.
"""),
        code("""fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df["date"], df["rate"],   linewidth=0.6, color=fu.COLOR_MUTED,  label="spot")
ax.plot(df["date"], df["ma_21d"], linewidth=1.2, color=fu.COLOR_RATE,   label="21-day MA")
ax.plot(df["date"], df["ma_63d"], linewidth=1.4, color=fu.COLOR_SIGNAL, label="63-day MA")
ax.set_title("Spot rate with moving averages")
ax.legend()
plt.tight_layout()
plt.show()"""),
        md("""## Daily return distribution

**Goal**: Understand the statistical shape of returns — fat tails and asymmetry matter for risk and model choice.
**How**: Plot a histogram of daily returns and compute summary statistics (mean, std, skewness (Skew), kurtosis (Kurt)).
"""),
        code("""returns = df["daily_return_pct"].dropna()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(returns, bins=80, color=fu.COLOR_RATE, edgecolor="white", linewidth=0.3)
axes[0].set_title("Histogram of daily returns (%)")
axes[0].set_xlabel("Return (%)")

axes[1].plot(df["date"], df["log_return"], linewidth=0.5, color=fu.COLOR_RATE, alpha=0.7)
axes[1].set_title("Log returns over time")
axes[1].axhline(0, color=fu.COLOR_SIGNAL, linewidth=0.8, linestyle="--")

plt.tight_layout()
plt.show()

print(f"Mean : {returns.mean():.4f}%")
print(f"Std  : {returns.std():.4f}%")
print(f"Skew : {returns.skew():.4f}")
print(f"Kurt : {returns.kurtosis():.4f}")"""),
        md("""## Rolling volatility (20-day)

**Goal**: Detect volatility clustering — the tendency for turbulent periods to follow turbulent ones — which motivates GARCH (Generalized AutoRegressive Conditional Heteroskedasticity) modelling.
**How**: Compute the 20-day rolling standard deviation of daily returns and plot it over time.
"""),
        code("""fig, ax = plt.subplots(figsize=(12, 4))
ax.fill_between(df["date"], df["volatility_20d"], alpha=0.4, color=fu.COLOR_SIGNAL)
ax.plot(df["date"], df["volatility_20d"], linewidth=0.8, color=fu.COLOR_SIGNAL)
ax.set_title("20-day rolling volatility of daily returns")
ax.set_ylabel("Std of daily return (%)")
plt.tight_layout()
plt.show()"""),
        md("""## Rolling-mean forecast baseline

**Goal**: Establish a benchmark RMSE (Root Mean Squared Error) that more sophisticated models must beat.
**How**: Predict tomorrow's rate as the 21-day rolling mean — a simple yet surprisingly hard baseline to outperform in FX markets.
"""),
        code("""cutoff = df["date"].max() - pd.DateOffset(years=2)
test   = df[df["date"] >= cutoff].copy()

df["pred_rolling"] = df["rate"].shift(1).rolling(21, min_periods=1).mean()
test_pred = df.loc[df["date"] >= cutoff, "pred_rolling"]

rmse = np.sqrt(((test["rate"].values - test_pred.values) ** 2).mean())
mae  = np.abs(test["rate"].values - test_pred.values).mean()
print(f"Baseline RMSE (Root Mean Squared Error) : {rmse:.6f}")
print(f"Baseline MAE  (Mean Absolute Error)      : {mae:.6f}")

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(test["date"], test["rate"],  linewidth=1.0, color=fu.COLOR_RATE,   label="actual")
ax.plot(test["date"], test_pred,     linewidth=1.0, color=fu.COLOR_SIGNAL,
        linestyle="--", label="rolling-mean forecast")
ax.set_title("Actual vs rolling-mean forecast (last 2 years)")
ax.legend()
plt.tight_layout()
plt.show()"""),
        md(f"""## Next steps

Ready to go further? Two companion notebooks apply more sophisticated models to this pair:

**[ARIMA / GARCH Modeling](https://www.kaggle.com/code/{modeling_notebook_slug(pair)})**

- **ARIMA (AutoRegressive Integrated Moving Average) / SARIMA (Seasonal ARIMA)** -- capture autocorrelation in the return series
- **GARCH (Generalized AutoRegressive Conditional Heteroskedasticity)** -- model time-varying volatility

**[LightGBM Forecast](https://www.kaggle.com/code/{lgbm_notebook_slug(pair)})**

- **LightGBM** -- gradient-boosted trees using lag, moving-average (MA), volatility, and calendar features
- **Multivariate** -- combine several pairs from other ECB datasets *(coming soon)*

---

Dataset updated every business day.
Source: (c) European Central Bank -- https://data.ecb.europa.eu
"""),
    ]

    return make_notebook(cells)


# ---------------------------------------------------------------------------
# Kaggle kernel metadata
# ---------------------------------------------------------------------------


def write_kernel_metadata(pair: str) -> None:
    write_notebook_kernel_metadata(
        output_dir=notebook_output_dir(pair),
        filename="kernel-metadata-eda.json",
        id=notebook_slug(pair),
        title=notebook_title(pair),
        code_file=f"{pair}_eda.ipynb",
        enable_internet=False,
        dataset_sources=[dataset_slug(pair)],
        kernel_sources=[utils_slug()],
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Kaggle EDA notebook for one currency pair."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args = parser.parse_args()
    pair = args.pair.upper()
    base, quote = parse_pair(pair)

    slug = notebook_slug(pair)
    if slug not in load_public_kernels():
        print(f"Skipping '{slug}': not listed in public_kernels.txt.")
        sys.exit(0)

    output_dir = notebook_output_dir(pair)

    nb_path = output_dir / f"{pair}_eda.ipynb"
    with open(nb_path, "w", encoding="utf-8") as fh:
        json.dump(build_notebook(pair, base, quote), fh, indent=1, ensure_ascii=False)

    write_kernel_metadata(pair)

    print(f"Notebook : {nb_path}")
    print(f"Metadata : {output_dir / 'kernel-metadata-eda.json'}")
    append_github_summary(f"| {pair} notebook | generated |\n")


if __name__ == "__main__":
    main()
