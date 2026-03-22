"""
scripts/create_modeling_notebook.py  --pair <BASEQUOTE>
========================================================
Job 3 - Generate the modeling notebook for one currency pair.

This is the second notebook in the Daily FX series.  It picks up
where the EDA notebook leaves off and fits two statistical models:

  1. ARIMA  - captures autocorrelation in the return series
  2. GARCH  - models time-varying volatility (heteroskedasticity)

The notebook is self-contained and links back to the EDA notebook
and the dataset, so readers can navigate the full series easily.

Output
------
notebooks/<PAIR>/
    <PAIR>_modeling.ipynb    nbformat v4 notebook
    kernel-metadata.json     updated to include both notebooks as sources
"""

import argparse
import json

from common import (
    append_github_summary,
    code,
    dataset_slug,
    md,
    modeling_notebook_slug,
    modeling_notebook_title,
    notebook_output_dir,
    notebook_slug,
    notebook_title,
    parse_pair,
    series_search_url,
)

# ---------------------------------------------------------------------------
# Notebook content
# ---------------------------------------------------------------------------

def build_modeling_notebook(pair: str, base: str, quote: str) -> dict:
    """
    Return a complete nbformat v4 notebook as a plain Python dict.

    Sections
    --------
    0. Title + links
    1. Series navigation
    2. Imports
    3. Load data
    4. Stationarity check (ADF test)
    5. ACF / PACF - choosing ARIMA order
    6. ARIMA fit and diagnostics
    7. ARIMA forecast (30-day horizon)
    8. GARCH - motivation (volatility clustering)
    9. GARCH fit and conditional volatility plot
    10. GARCH volatility forecast
    11. Summary and next steps
    """
    eda_slug      = dataset_slug(pair)
    eda_nb_title  = notebook_title(pair)
    eda_nb_slug   = notebook_slug(pair)

    cells = [

        # ── 0. Title ─────────────────────────────────────────────────────
        md(f"""\
# {modeling_notebook_title(pair)}

**Dataset** : [{eda_slug}](https://www.kaggle.com/datasets/{eda_slug})
**Part 1**  : [{eda_nb_title}](https://www.kaggle.com/code/{eda_nb_slug})
**Pair**    : {base} / {quote}
**Source**  : European Central Bank (ECB) - free reuse with attribution
"""),

        # ── 1. Series navigation ─────────────────────────────────────────
        md(f"""\
---

### Explore the full Daily FX series

| | Link |
|---|---|
| All datasets  | {series_search_url("datasets")} |
| All notebooks | {series_search_url("code")} |

---
"""),

        # ── 2. Imports ───────────────────────────────────────────────────
        code("""\
# Install packages not available in the default Kaggle environment
import subprocess
subprocess.run(["pip", "install", "arch", "--quiet"], check=True)"""),

        code("""\
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model

plt.rcParams.update({
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})"""),

        # ── 3. Load data ─────────────────────────────────────────────────
        md("## Load data"),
        code(f"""\
DATA_DIR = Path("/kaggle/input/daily-fx-{pair.lower()}")
df = pd.read_csv(DATA_DIR / "{pair}.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

# Work with log returns - stationary by construction and preferred for modelling
returns = df["log_return"].dropna().reset_index(drop=True)

print(f"Rows    : {{len(df):,}}")
print(f"Period  : {{df['date'].min().date()}} → {{df['date'].max().date()}}")
print(f"Returns : {{len(returns):,}}")
df.tail()"""),

        # ── 4. Stationarity ──────────────────────────────────────────────
        md("""\
## Stationarity check (ADF test)

ARIMA requires a stationary series.  We test the log return series with the
Augmented Dickey-Fuller (ADF) test.  A p-value below 0.05 rejects the unit-root
hypothesis and confirms stationarity.
"""),
        code("""\
adf_result = adfuller(returns, autolag="AIC")
print(f"ADF statistic : {adf_result[0]:.4f}")
print(f"p-value       : {adf_result[1]:.4f}")
print(f"Lags used     : {adf_result[2]}")
print()
if adf_result[1] < 0.05:
    print("Series is stationary (p < 0.05) - suitable for ARIMA.")
else:
    print("Series may not be stationary - consider differencing.")"""),

        # ── 5. ACF / PACF ────────────────────────────────────────────────
        md("""\
## ACF / PACF - choosing ARIMA order

The autocorrelation function (ACF) and partial ACF (PACF) guide the choice
of ARIMA(p, d, q):

- **p** (AR order) - where PACF cuts off
- **d** (differencing) - 0, since log returns are already stationary
- **q** (MA order) - where ACF cuts off
"""),
        code("""\
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf( returns, lags=30, ax=axes[0], title="ACF  (log returns)")
plot_pacf(returns, lags=30, ax=axes[1], title="PACF (log returns)", method="ywm")
plt.tight_layout()
plt.show()"""),

        # ── 6. ARIMA fit ─────────────────────────────────────────────────
        md("""\
## ARIMA model

We fit ARIMA(1, 0, 1) as a starting point - a common choice for daily FX
log returns.  Adjust p and q based on the ACF / PACF above.
"""),
        code(f"""\
TRAIN_CUTOFF = df["date"].max() - pd.DateOffset(years=2)
train_returns = returns.iloc[:len(df[df["date"] < TRAIN_CUTOFF])]
test_returns  = returns.iloc[len(train_returns):]

arima = ARIMA(train_returns, order=(1, 0, 1)).fit()
print(arima.summary())"""),

        code("""\
# In-sample residual diagnostics
fig = arima.plot_diagnostics(figsize=(14, 8))
plt.suptitle("ARIMA(1,0,1) - residual diagnostics", y=1.01)
plt.tight_layout()
plt.show()"""),

        # ── 7. ARIMA forecast ────────────────────────────────────────────
        md("## ARIMA 30-day forecast"),
        code(f"""\
HORIZON = 30

forecast = arima.get_forecast(steps=HORIZON)
fc_mean  = forecast.predicted_mean
fc_ci    = forecast.conf_int(alpha=0.05)

# Reconstruct rate forecast from log returns
last_rate    = df.loc[df["date"] < TRAIN_CUTOFF, "rate"].iloc[-1]
rate_fc      = last_rate * np.exp(fc_mean.cumsum())
rate_ci_low  = last_rate * np.exp(fc_ci.iloc[:, 0].cumsum())
rate_ci_high = last_rate * np.exp(fc_ci.iloc[:, 1].cumsum())

fig, ax = plt.subplots(figsize=(12, 4))
# Show last 90 days of actual data for context
actual_tail = df.tail(90)
ax.plot(actual_tail["date"], actual_tail["rate"],
        color="#185FA5", linewidth=1.0, label="actual")
fc_dates = pd.date_range(
    start=df["date"].max() + pd.Timedelta(days=1),
    periods=HORIZON, freq="B"
)
ax.plot(fc_dates, rate_fc, color="#E8593C", linestyle="--",
        linewidth=1.2, label="ARIMA forecast")
ax.fill_between(fc_dates, rate_ci_low, rate_ci_high,
                color="#E8593C", alpha=0.15, label="95% CI")
ax.set_title(f"{{HORIZON}}-day {pair} rate forecast (ARIMA)")
ax.set_ylabel("{quote} per {base}")
ax.legend()
plt.tight_layout()
plt.show()

n = min(HORIZON, len(test_returns), len(fc_mean))

rmse = np.sqrt(((test_returns.values[:n] - fc_mean.values[:n]) ** 2).mean())
print(f"ARIMA RMSE (log returns, {n}-day overlap) : {rmse:.6f}")

        # ── 8. GARCH motivation ──────────────────────────────────────────
        md("""\
## GARCH - volatility clustering

ARIMA models the conditional mean but assumes constant variance.
In FX markets, volatility clusters - calm periods are followed by calm,
turbulent periods by turbulent.  The GARCH(1,1) model captures this
by letting the variance evolve over time.
"""),
        code(f"""\
fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
axes[0].plot(df["date"], df["log_return"],
             linewidth=0.5, color="#185FA5", alpha=0.8)
axes[0].set_title("{pair} log returns")
axes[0].axhline(0, color="#E8593C", linewidth=0.6, linestyle="--")

axes[1].plot(df["date"], df["volatility_20d"],
             linewidth=0.8, color="#E8593C")
axes[1].set_title("20-day rolling volatility")
plt.tight_layout()
plt.show()"""),

        # ── 9. GARCH fit ─────────────────────────────────────────────────
        md("## GARCH(1,1) fit"),
        code("""\
# arch_model expects returns in percentage terms
returns_pct = train_returns * 100

garch = arch_model(returns_pct, vol="Garch", p=1, q=1, dist="normal").fit(disp="off")
print(garch.summary())"""),

        code("""\
# Conditional volatility (annualised) vs rolling realised volatility
cond_vol = garch.conditional_volatility / 100   # back to decimal

# Align with train dates
train_dates = df.loc[df["date"] < TRAIN_CUTOFF, "date"].reset_index(drop=True)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(train_dates, cond_vol,
        color="#E8593C", linewidth=0.8, label="GARCH conditional vol")
ax.plot(
    df.loc[df["date"] < TRAIN_CUTOFF, "date"],
    df.loc[df["date"] < TRAIN_CUTOFF, "volatility_20d"] / 100,
    color="#185FA5", linewidth=0.8, alpha=0.6, label="20-day realised vol"
)
ax.set_title("Conditional vs realised volatility")
ax.set_ylabel("Volatility (log return std)")
ax.legend()
plt.tight_layout()
plt.show()"""),

        # ── 10. GARCH forecast ───────────────────────────────────────────
        md("## GARCH volatility forecast (30-day)"),
        code(f"""\
garch_fc = garch.forecast(horizon=HORIZON, reindex=False)
fc_vol   = np.sqrt(garch_fc.variance.values[-1]) / 100  # annualise if needed

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(range(1, HORIZON + 1), fc_vol,
       color="#E8593C", alpha=0.7, width=0.7)
ax.set_title(f"GARCH(1,1) {{HORIZON}}-step volatility forecast")
ax.set_xlabel("Days ahead")
ax.set_ylabel("Forecast conditional std (log returns)")
plt.tight_layout()
plt.show()

print(f"Day-1 forecast std : {{fc_vol[0]:.6f}}")
print(f"Day-30 forecast std: {{fc_vol[-1]:.6f}}")"""),

        # ── 11. Summary ──────────────────────────────────────────────────
        md(f"""\
## Summary and next steps

| Model | Purpose | Key result |
|---|---|---|
| ARIMA(1,0,1) | Conditional mean forecast | 30-day rate projection with 95% CI |
| GARCH(1,1)   | Conditional variance       | Time-varying volatility forecast |

### Ideas to extend this notebook

- **Auto-ARIMA** (`pmdarima`) - automated order selection via AIC/BIC
- **EGARCH / GJR-GARCH** - asymmetric volatility (leverage effect)
- **Multivariate GARCH (DCC)** - model co-volatility across pairs
- **Combining ARIMA + GARCH** - ARIMA-GARCH joint estimation

---

Dataset updated every business day.
Source: © European Central Bank - https://data.ecb.europa.eu
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
    """
    Write kernel-metadata.json for the modeling notebook.

    Links to the dataset and lists the EDA notebook as a kernel source
    so readers can navigate between the two.
    """
    metadata = {
        "id":                  modeling_notebook_slug(pair),
        "title":               modeling_notebook_title(pair),
        "code_file":           f"{pair}_modeling.ipynb",
        "language":            "python",
        "kernel_type":         "notebook",
        "is_private":          True,
        "enable_gpu":          False,
        "enable_internet":     True,
        "keywords":            ["finance", "economics"],
        "dataset_sources":     [dataset_slug(pair)],
        "competition_sources": [],
        "kernel_sources":      [notebook_slug(pair)],
    }

    output_dir = notebook_output_dir(pair)
    with open(output_dir / "kernel-metadata-modeling.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Kaggle modeling notebook for one currency pair."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args        = parser.parse_args()
    pair        = args.pair.upper()
    base, quote = parse_pair(pair)

    output_dir = notebook_output_dir(pair)

    nb_path = output_dir / f"{pair}_modeling.ipynb"
    with open(nb_path, "w", encoding="utf-8") as fh:
        json.dump(
            build_modeling_notebook(pair, base, quote),
            fh, indent=1, ensure_ascii=False,
        )

    write_kernel_metadata(pair)

    print(f"Notebook : {nb_path}")
    print(f"Metadata : {output_dir / 'kernel-metadata-modeling.json'}")

    append_github_summary(f"| {pair} modeling notebook | generated |\n")


if __name__ == "__main__":
    main()
