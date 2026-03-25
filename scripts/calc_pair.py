"""
scripts/calc_pair.py  --pair <BASEQUOTE>
=========================================
Job 3 (calc step) -- Compute the time series for one currency pair.
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


def load_eur_rates(path=ECB_RAW_PATH) -> pd.DataFrame:
    df   = pd.read_csv(path, parse_dates=["date"])
    wide = df.pivot(index="date", columns="currency", values="rate_vs_eur")
    wide.columns.name = None
    return wide.sort_index()


def compute_pair(wide: pd.DataFrame, base: str, quote: str) -> pd.DataFrame:
    EURO_CCY = "EUR"
    for ccy in (base, quote):
        if ccy == EURO_CCY:
            continue
        if ccy not in wide.columns:
            raise ValueError(f"Currency '{ccy}' not found in ECB data.")

    if base == EURO_CCY:
        wide = wide.copy()
        wide[base] = 1

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
    df["day_of_week"]      = df["date"].dt.dayofweek

    return df


def write_dataset_metadata(pair: str, base: str, quote: str, df: pd.DataFrame) -> None:
    base_meta  = CURRENCY_META.get(base,  {"country": "Unknown", "name": base})
    quote_meta = CURRENCY_META.get(quote, {"country": "Unknown", "name": quote})
    latest     = df["date"].max().strftime("%Y-%m-%d")

    description = "\n".join([
        f"## {pair} Daily Exchange Rate (ECB, 1999-present)",
        "",
        f"Daily **{base}/{quote}** cross rate derived from the European Central Bank (ECB) EUR reference rates.",
        f"Base: **{base}** — {base_meta['name']} ({base_meta['country']})",
        f"Quote: **{quote}** — {quote_meta['name']} ({quote_meta['country']})",
        f"Period: 1999-01-04 to {latest} · Updated every business day (~15:00 UTC).",
        "",
        "### License",
        "© European Central Bank. Free reuse with attribution under the ECB open data policy.",
        "Source: https://www.ecb.europa.eu/home/disclaimer/html/index.en.html",
    ])

    metadata = {
        "title":    dataset_title(pair),
        "subtitle": f"ECB daily {base}/{quote} cross rates 1999-present, ML-ready features",
        "id":       dataset_slug(pair),
        "licenses": [{
            "name": "other",
            "uri":  "https://www.ecb.europa.eu/home/disclaimer/html/index.en.html",
            "description": (
                "© European Central Bank. Free reuse with attribution "
                "under the ECB open data policy. "
                "https://www.ecb.europa.eu/home/disclaimer/html/index.en.html"
            ),
        }],
        "keywords": [
            "finance",
            "economics",
            "tabular",
            "currencies-and-foreign-exchange",
            "time-series",
        ],
        "resources": [{
            "path":        f"{pair}.csv",
            "description": f"Daily {base}/{quote} cross rate, 1999-01-04 to {latest}.",
        }],
        "description": description,
    }

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True)
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
    csv_path   = output_dir / f"{pair}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV      : {csv_path}  ({csv_path.stat().st_size / 1024:.1f} KB)")

    write_dataset_metadata(pair, base, quote, df)
    print("Metadata       : dataset-metadata.json written")

    append_github_summary(f"| {pair} | {len(df):,} rows | {df['date'].max().date()} |\n")


if __name__ == "__main__":
    main()
