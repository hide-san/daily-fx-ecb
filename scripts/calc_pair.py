"""
scripts/calc_pair.py  --pair <BASEQUOTE>
=========================================
Job 3 (calc step) — Compute the time series for one currency pair.

Cross-rate formula
------------------
Since ECB rates are always quoted vs EUR, we derive any X/Y pair as:

    X / Y  =  (Y per EUR)  /  (X per EUR)

Example:  USD/JPY  =  JPY_per_EUR  /  USD_per_EUR

Input
-----
ecb_raw/all_currencies.csv   (produced by fetch_ecb.py)

Output
------
datasets/<PAIR>/
    <PAIR>_daily.csv         single-pair time series with ML-ready features
    dataset-metadata.json    Kaggle dataset descriptor
"""

import argparse
import json

import numpy as np
import pandas as pd

from common import (
    CURRENCY_META,
    ECB_RAW_PATH,
    append_github_summary,
    dataset_slug,
    dataset_title,
    emit_github_warning,
    pair_output_dir,
    parse_pair,
    validate_kaggle_metadata,
)

# ---------------------------------------------------------------------------
# Load ECB data
# ---------------------------------------------------------------------------

def load_eur_rates(path=ECB_RAW_PATH) -> pd.DataFrame:
    """
    Read the long-format ECB CSV and pivot to wide format.

    Returns a DataFrame indexed by date where each column is a currency
    and each cell is the EUR spot rate for that day.
    """
    df   = pd.read_csv(path, parse_dates=["date"])
    wide = df.pivot(index="date", columns="currency", values="rate_vs_eur")
    wide.columns.name = None
    return wide.sort_index()

# ---------------------------------------------------------------------------
# Compute one pair
# ---------------------------------------------------------------------------

def compute_pair(wide: pd.DataFrame, base: str, quote: str) -> pd.DataFrame:
    """
    Derive the base/quote cross rate and add ML-ready feature columns.

    Feature columns
    ---------------
    daily_return_pct  : percentage change from the previous business day
    log_return        : natural log of the daily return ratio
    ma_7d / 21d / 63d : rolling means (~1 week / 1 month / 1 quarter)
    volatility_20d    : 20-day rolling std of daily_return_pct
    year/month/dow    : calendar features for seasonal models
    """
    for ccy in (base, quote):
        if ccy not in wide.columns:
            raise ValueError(f"Currency '{ccy}' not found in ECB data.")

    df = (wide[quote] / wide[base]).dropna().rename("rate").reset_index()
    df.columns = ["date", "rate"]

    df["daily_return_pct"] = df["rate"].pct_change() * 100
    df["log_return"]       = np.log(df["rate"]).diff()
    df["ma_7d"]            = df["rate"].rolling(window=7,  min_periods=1).mean()
    df["ma_21d"]           = df["rate"].rolling(window=21, min_periods=1).mean()
    df["ma_63d"]           = df["rate"].rolling(window=63, min_periods=1).mean()
    df["volatility_20d"]   = df["daily_return_pct"].rolling(window=20, min_periods=1).std()
    df["year"]             = df["date"].dt.year
    df["month"]            = df["date"].dt.month
    df["day_of_week"]      = df["date"].dt.dayofweek   # 0 = Monday

    return df

# ---------------------------------------------------------------------------
# Kaggle dataset metadata
# ---------------------------------------------------------------------------

def write_dataset_metadata(pair: str, base: str, quote: str, df: pd.DataFrame) -> None:
    """
    Write dataset-metadata.json for the Kaggle Datasets API.

    Visibility (public / private) is left unset — control it manually
    in the Kaggle GUI after the first upload.
    """
    base_meta  = CURRENCY_META.get(base,  {"country": "Unknown", "name": base})
    quote_meta = CURRENCY_META.get(quote, {"country": "Unknown", "name": quote})
    latest     = df["date"].max().strftime("%Y-%m-%d")

    description = "\n".join([
        f"## {pair} Daily Exchange Rate (ECB, 1999–present)",
        "",
        f"Daily **{base}/{quote}** cross rate derived from ECB EUR reference rates.",
        "",
        "| | |",
        "|---|---|",
        f"| Base currency  | {base} — {base_meta['name']} ({base_meta['country']}) |",
        f"| Quote currency | {quote} — {quote_meta['name']} ({quote_meta['country']}) |",
        f"| Period         | 1999-01-04 to {latest} (updated every business day) |",
        "",
        "### Columns",
        "| Column | Description |",
        "|---|---|",
        "| `date` | Business day |",
        "| `rate` | Cross rate (units of quote per 1 unit of base) |",
        "| `daily_return_pct` | Day-over-day percentage change |",
        "| `log_return` | Natural log return |",
        "| `ma_7d` / `ma_21d` / `ma_63d` | Rolling means (~1 wk / 1 mo / 1 qtr) |",
        "| `volatility_20d` | 20-day rolling std of daily returns |",
        "| `year` / `month` / `day_of_week` | Calendar features |",
        "",
        "### Source",
        "(c) European Central Bank",
        "https://data.ecb.europa.eu",
        "Free reuse with attribution under the ECB open data policy.",
    ])

    metadata = {
        "title":    dataset_title(pair),
        "subtitle": f"ECB daily {base}/{quote} cross rates 1999-present, ML-ready features",
        "id":       dataset_slug(pair),
        "licenses": [{"name": "other",
                      "uri": "https://www.ecb.europa.eu/home/disclaimer/html/index.en.html",
                      "description": "ECB open data - free reuse with attribution"}],
        # Tag slugs must match existing Kaggle tags exactly.
        # Invalid slugs are silently ignored by the Kaggle API.
        "keywords": [
            "finance",
            "economics",
            "currencies-and-foreign-exchange",
            "time-series",
        ],
        "description": description,
        # isPrivate is intentionally omitted — set visibility in the Kaggle GUI.
    }

    # Guard against Kaggle API rejecting metadata that violates documented limits.
    errors = validate_kaggle_metadata(
        title    = metadata["title"],
        subtitle = metadata["subtitle"],
        keywords = metadata["keywords"],
    )
    for msg in errors:
        emit_github_warning(msg, script="scripts/calc_pair.py")
    if errors:
        raise ValueError(f"Invalid Kaggle metadata for {pair}: {errors}")

    output_dir = pair_output_dir(pair)
    with open(output_dir / "dataset-metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute a single currency pair time series from ECB EUR data."
    )
    parser.add_argument("--pair", required=True,
                        help="Currency pair code, e.g. USDJPY")
    args        = parser.parse_args()
    pair        = args.pair.upper()
    base, quote = parse_pair(pair)

    print(f"Pair : {pair}  ({base} / {quote})")

    wide = load_eur_rates()
    print(f"ECB data loaded: {len(wide)} days x {len(wide.columns)} currencies")

    df = compute_pair(wide, base, quote)
    print(f"Rows computed  : {len(df):,}  "
          f"({df['date'].min().date()} to {df['date'].max().date()})")

    output_dir = pair_output_dir(pair)
    csv_path   = output_dir / f"{pair}_daily.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV      : {csv_path}  ({csv_path.stat().st_size / 1024:.1f} KB)")

    write_dataset_metadata(pair, base, quote, df)
    print("Metadata       : dataset-metadata.json written")

    append_github_summary(f"| {pair} | {len(df):,} rows | {df['date'].max().date()} |\n")


if __name__ == "__main__":
    main()
