"""
scripts/create_modeling_notebook.py  --pair <BASEQUOTE>
========================================================
Job 3 -- Generate the modeling notebook for one currency pair.

Output
------
notebooks/<PAIR>/
    <PAIR>_modeling.ipynb         nbformat v4 notebook
    kernel-metadata-modeling.json Kaggle Kernels API descriptor
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
    utils_slug,
)


def build_modeling_notebook(pair: str, base: str, quote: str) -> dict:
    eda_slug     = dataset_slug(pair)
    eda_nb_title = notebook_title(pair)
    eda_nb_slug  = notebook_slug(pair)

    cells = [

        md(f"""\
# {modeling_notebook_title(pair)}

**Dataset** : [{eda_slug}](https://www.kaggle.com/datasets/{eda_slug})
**Part 1**  : [{eda_nb_title}](https://www.kaggle.com/code/{eda_nb_slug})
**Pair**    : {base} / {quote}
**Source**  : European Central Bank (ECB) -- free reuse with attribution
"""),

        md(f"""\
---

### Explore the full Daily FX series

| | Link |
|---|---|
| All datasets  | {series_search_url("datasets")} |
| All notebooks | {series_search_url("code")} |

---
"""),

        code("""\
!pip install arch --quiet)"""),

        code("""\
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys

# Shared Daily FX utilities
from daily_fx_utils import (
    find_data_dir,
    apply_plot_style,
    FEATURE_COLUMNS,
    COLOR_RATE,
    COLOR_SIGNAL,
    COLOR_MUTED,
    get_logger,
    print_summary,
)

from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model

apply_plot_style()
log = get_logger()"""),

        md("## Load data"),
        code(f"""\
DATA_DIR = find_data_dir("{pair}")
log.info("DATA_DIR resolved to: %s", DATA_DIR)

df = pd.read_csv(DATA_DIR / "{pair}.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

returns = df["log_return"].dropna().reset_index(drop=True)
print_summary("{pair}", df)
df.tail()"""),

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
    print("Series is stationary (p < 0.05) -- suitable for ARIMA.")
else:
    print("Series may not be stationary -- consider differencing.")"""),

        md("""\
## ACF / PACF -- choosing ARIMA order
"""),
        code("""\
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf( returns, lags=30, ax=axes[0], title="ACF  (log returns)")
plot_pacf(returns, lags=30, ax=axes[1], title="PACF (log returns)", method="ywm")
plt.tight_layout()
plt.show()"""),

        md("## ARIMA model"),
        code(f"""\
TRAIN_CUTOFF = df["date"].max() - pd.DateOffset(years=2)
train_returns = returns.iloc[:len(df[df["date"] < TRAIN_CUTOFF])]
test_returns  = returns.iloc[len(train_returns):]

arima = ARIMA(train_returns, order=(1, 0, 1)).fit()
print(arima.summary())"""),

        code("""\
fig = arima.plot_diagnostics(figsize=(14, 8))
plt.suptitle("ARIMA(1,0,1) -- residual diagnostics", y=1.01)
plt.tight_layout()
plt.show()"""),

        md("## ARIMA 30-day forecast"),
        code(f"""\
HORIZON = 30

forecast = arima.get_forecast(steps=HORIZON)
fc_mean  = forecast.predicted_mean
fc_ci    = forecast.conf_int(alpha=0.05)

last_rate    = df.loc[df["date"] < TRAIN_CUTOFF, "rate"].iloc[-1]
rate_fc      = last_rate * np.exp(fc_mean.cumsum())
rate_ci_low  = last_rate * np.exp(fc_ci.iloc[:, 0].cumsum())
rate_ci_high = last_rate * np.exp(fc_ci.iloc[:, 1].cumsum())

fig, ax = plt.subplots(figsize=(12, 4))
actual_tail = df.tail(90)
ax.plot(actual_tail["date"], actual_tail["rate"],
        color=COLOR_RATE, linewidth=1.0, label="actual")
fc_dates = pd.date_range(
    start=df["date"].max() + pd.Timedelta(days=1),
    periods=HORIZON, freq="B"
)
ax.plot(fc_dates, rate_fc, color=COLOR_SIGNAL, linestyle="--",
        linewidth=1.2, label="ARIMA forecast")
ax.fill_between(fc_dates, rate_ci_low, rate_ci_high,
                color=COLOR_SIGNAL, alpha=0.15, label="95% CI")
ax.set_title(f"{{HORIZON}}-day {pair} rate forecast (ARIMA)")
ax.set_ylabel("{quote} per {base}")
ax.legend()
plt.tight_layout()
plt.show()

rmse = np.sqrt(((test_returns.values[:HORIZON] - fc_mean.values[:HORIZON]) ** 2).mean())
print(f"ARIMA RMSE (log returns, {{HORIZON}}-day) : {{rmse:.6f}}")"""),

        md("""\
## GARCH -- volatility clustering
"""),
        code(f"""\
fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
axes[0].plot(df["date"], df["log_return"],
             linewidth=0.5, color=COLOR_RATE, alpha=0.8)
axes[0].set_title("{pair} log returns")
axes[0].axhline(0, color=COLOR_SIGNAL, linewidth=0.6, linestyle="--")

axes[1].plot(df["date"], df["volatility_20d"],
             linewidth=0.8, color=COLOR_SIGNAL)
axes[1].set_title("20-day rolling volatility")
plt.tight_layout()
plt.show()"""),

        md("## GARCH(1,1) fit"),
        code("""\
returns_pct = train_returns * 100
garch = arch_model(returns_pct, vol="Garch", p=1, q=1, dist="normal").fit(disp="off")
print(garch.summary())"""),

        code("""\
cond_vol    = garch.conditional_volatility / 100
train_dates = df.loc[df["date"] < TRAIN_CUTOFF, "date"].reset_index(drop=True)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(train_dates, cond_vol,
        color=COLOR_SIGNAL, linewidth=0.8, label="GARCH conditional vol")
ax.plot(
    df.loc[df["date"] < TRAIN_CUTOFF, "date"],
    df.loc[df["date"] < TRAIN_CUTOFF, "volatility_20d"] / 100,
    color=COLOR_RATE, linewidth=0.8, alpha=0.6, label="20-day realised vol"
)
ax.set_title("Conditional vs realised volatility")
ax.set_ylabel("Volatility (log return std)")
ax.legend()
plt.tight_layout()
plt.show()"""),

        md("## GARCH volatility forecast (30-day)"),
        code(f"""\
garch_fc = garch.forecast(horizon=HORIZON, reindex=False)
fc_vol   = np.sqrt(garch_fc.variance.values[-1]) / 100

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(range(1, HORIZON + 1), fc_vol,
       color=COLOR_SIGNAL, alpha=0.7, width=0.7)
ax.set_title(f"GARCH(1,1) {{HORIZON}}-step volatility forecast")
ax.set_xlabel("Days ahead")
ax.set_ylabel("Forecast conditional std (log returns)")
plt.tight_layout()
plt.show()

print(f"Day-1 forecast std : {{fc_vol[0]:.6f}}")
print(f"Day-30 forecast std: {{fc_vol[-1]:.6f}}")"""),

        md(f"""\
## Summary and next steps

| Model | Purpose | Key result |
|---|---|---|
| ARIMA(1,0,1) | Conditional mean forecast | 30-day rate projection with 95% CI |
| GARCH(1,1)   | Conditional variance       | Time-varying volatility forecast |

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


def write_kernel_metadata(pair: str) -> None:
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
        "kernel_sources":      [utils_slug()],
    }
    output_dir = notebook_output_dir(pair)
    with open(output_dir / "kernel-metadata-modeling.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


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
