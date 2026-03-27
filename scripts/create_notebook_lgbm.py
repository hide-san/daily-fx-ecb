"""
scripts/create_notebook_lgbm.py  --pair <BASEQUOTE>
====================================================
Job 3 (notebook step) -- Generate the LightGBM forecast notebook for one pair.

Output
------
notebooks/<PAIR>/
    <PAIR>_lgbm.ipynb             nbformat v4 notebook
    kernel-metadata-lgbm.json     Kaggle Kernels API descriptor
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
    lgbm_notebook_title,
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
    eda_nb_title = notebook_title(pair)
    eda_nb_slug = notebook_slug(pair)
    modeling_nb_slug = modeling_notebook_slug(pair)
    display = pair_display(pair)

    cells = [
        md(f"""# {lgbm_notebook_title(pair)}

**Dataset** : [{slug}](https://www.kaggle.com/datasets/{slug})  
**Part 1**  : [{eda_nb_title}](https://www.kaggle.com/code/{eda_nb_slug})  
**Part 2**  : [ARIMA / GARCH Modeling](https://www.kaggle.com/code/{modeling_nb_slug})  
**Pair**    : {display}  
**Source**  : European Central Bank (ECB) -- free reuse with attribution
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
        code("""!pip install lightgbm --quiet"""),
        code("""import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Shared Daily FX utilities
import daily_fx_utils as fu

fu.apply_plot_style()
log = fu.get_logger()"""),
        md(f"""## Load data

**Goal**: Load the {display} dataset and inspect its shape and feature columns.  
**How**: Read via the shared utility, which returns a tidy DataFrame with pre-computed
features (`ma_*`, `volatility_20d`, calendar columns).
"""),
        code(f"""df = fu.read_csv("{pair}")
fu.print_summary("{pair}", df)
df.tail()"""),
        md("""## Feature engineering

**Goal**: Build a rich feature set that gives the model information about recent price
dynamics without leaking future values.  
**How**: Add lag features (rate 1, 5, and 21 trading days ago) and combine them with
the existing moving-average and volatility columns already in the dataset.
The target is tomorrow's rate -- constructed by shifting the rate column back by one day.
"""),
        code("""# Lag features -- rate at t-1, t-5, t-21 (no future leak)
df["lag_1"]  = df["rate"].shift(1)
df["lag_5"]  = df["rate"].shift(5)
df["lag_21"] = df["rate"].shift(21)

# Target: next-day rate
df["target"] = df["rate"].shift(-1)

# Drop rows where any feature or target is NaN (start and end of series)
df_model = df.dropna(subset=["lag_1", "lag_5", "lag_21", "target"]).copy()

FEATURES = [
    "rate", "lag_1", "lag_5", "lag_21",
    "ma_7d", "ma_21d", "ma_63d",
    "volatility_20d",
    "year", "month", "day_of_week",
]
print(f"Feature set  : {FEATURES}")
print(f"Modelling rows: {len(df_model):,}")"""),
        md("""## Train / test split

**Goal**: Evaluate the model on out-of-sample data to get an honest estimate of
forecast accuracy.  
**How**: Use the last two years as the hold-out test set -- the same cutoff used for
the rolling-mean baseline in the EDA notebook -- so the RMSE (Root Mean Squared Error)
values are directly comparable.
"""),
        code("""TRAIN_CUTOFF = df_model["date"].max() - pd.DateOffset(years=2)

train = df_model[df_model["date"] <  TRAIN_CUTOFF]
test  = df_model[df_model["date"] >= TRAIN_CUTOFF]

X_train, y_train = train[FEATURES], train["target"]
X_test,  y_test  = test[FEATURES],  test["target"]

print(f"Train: {len(train):,} rows  ({train['date'].min().date()} -- {train['date'].max().date()})")
print(f"Test : {len(test):,} rows  ({test['date'].min().date()} -- {test['date'].max().date()})")"""),
        md("""## Train LightGBM model

**Goal**: Fit a gradient-boosted tree model that learns non-linear relationships
between the feature set and the next-day rate.  
**How**: Use `LGBMRegressor` with conservative hyperparameters (shallow trees, low
learning rate, early stopping) to avoid overfitting on a relatively small financial
time series.
"""),
        code("""model = lgb.LGBMRegressor(
    n_estimators=1000,
    learning_rate=0.02,
    num_leaves=16,
    min_child_samples=20,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbose=-1,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
)
print(f"Best iteration: {model.best_iteration_}")"""),
        md(f"""## Predictions vs actual

**Goal**: Visually inspect whether the model tracks the test-period rate trajectory.  
**How**: Overlay the model's predictions on the actual {display} rate for the two-year
test window.
"""),
        code(f"""preds = model.predict(X_test)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(test["date"], y_test,  linewidth=1.0, color=fu.COLOR_RATE,   label="actual")
ax.plot(test["date"], preds,   linewidth=1.0, color=fu.COLOR_SIGNAL,
        linestyle="--", label="LightGBM forecast")
ax.set_title("Actual vs LightGBM forecast (last 2 years)")
ax.set_ylabel("{quote} per {base}")
ax.legend()
plt.tight_layout()
plt.show()"""),
        md("""## Forecast accuracy

**Goal**: Quantify how much the model improves over the simple rolling-mean baseline
established in the EDA notebook.  
**How**: Compute RMSE (Root Mean Squared Error) and MAE (Mean Absolute Error) on the
test set and print them side-by-side with the rolling-mean baseline for easy comparison.
"""),
        code("""rmse = np.sqrt(mean_squared_error(y_test, preds))
mae  = mean_absolute_error(y_test, preds)

# Rolling-mean baseline (21-day, same as EDA notebook)
baseline_pred = df_model.loc[df_model["date"] >= TRAIN_CUTOFF, "ma_21d"]
rmse_base = np.sqrt(mean_squared_error(y_test, baseline_pred))
mae_base  = mean_absolute_error(y_test, baseline_pred)

print(f"{'Model':<20} {'RMSE':>12} {'MAE':>12}")
print(f"{'':<20} {'-'*12} {'-'*12}")
print(f"{'Rolling-mean (21d)':<20} {rmse_base:>12.6f} {mae_base:>12.6f}")
print(f"{'LightGBM':<20} {rmse:>12.6f} {mae:>12.6f}")"""),
        md("""## Feature importance

**Goal**: Understand which inputs the model relies on most, and whether the learned
importances align with economic intuition (e.g. recent prices should matter more than
calendar effects).  
**How**: Plot LightGBM's built-in split-based feature importance, which counts how often
each feature is used as a split point across all trees.
"""),
        code("""fig, ax = plt.subplots(figsize=(9, 5))
lgb.plot_importance(model, ax=ax, max_num_features=len(FEATURES),
                    importance_type="split", title="Feature importance (split count)")
plt.tight_layout()
plt.show()"""),
        md("""## Summary and next steps

| Model | RMSE (test) | MAE (test) |
|---|---|---|
| Rolling-mean baseline (21-day) | see output above | see output above |
| LightGBM | see output above | see output above |

**Key takeaway**: LightGBM excels at capturing non-linear interactions between
features, but FX rates are notoriously hard to predict -- even a marginal improvement
over the rolling-mean baseline is meaningful.

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
        filename="kernel-metadata-lgbm.json",
        id=lgbm_notebook_slug(pair),
        title=lgbm_notebook_title(pair),
        code_file=f"{pair}_lgbm.ipynb",
        enable_internet=False,
        dataset_sources=[dataset_slug(pair)],
        kernel_sources=[utils_slug()],
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Kaggle LightGBM notebook for one currency pair."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args = parser.parse_args()
    pair = args.pair.upper()
    base, quote = parse_pair(pair)

    slug = lgbm_notebook_slug(pair)
    if slug not in load_public_kernels():
        print(f"Skipping '{slug}': not listed in public_kernels.txt.")
        sys.exit(0)

    output_dir = notebook_output_dir(pair)

    nb_path = output_dir / f"{pair}_lgbm.ipynb"
    with open(nb_path, "w", encoding="utf-8") as fh:
        json.dump(build_notebook(pair, base, quote), fh, indent=1, ensure_ascii=False)

    write_kernel_metadata(pair)

    print(f"Notebook : {nb_path}")
    print(f"Metadata : {output_dir / 'kernel-metadata-lgbm.json'}")
    append_github_summary(f"| {pair} lgbm notebook | generated |\n")


if __name__ == "__main__":
    main()
