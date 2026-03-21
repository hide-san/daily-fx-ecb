"""
scripts/validate_pair.py  --pair <BASEQUOTE>
=============================================
Data quality gate between calc_pair.py and upload_kaggle.py.

Exits with a non-zero code if any check fails, blocking the runner
before an invalid dataset reaches Kaggle.

Checks
------
1. Freshness      — latest date is within 3 calendar days of today
2. Minimum rows   — at least 1000 rows (ECB data goes back to 1999)
3. No gap         — no unexpected multi-day gap in the last 30 days
4. Spike guard    — no single daily return exceeds ±20%
5. No all-NaN col — no feature column is entirely null
"""

import argparse
import sys
from datetime import date

import pandas as pd

from common import (
    DATASETS_ROOT,
    append_github_summary,
    emit_github_warning,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

MIN_ROWS              = 1_000
MAX_RETURN_PCT        = 20.0
MAX_GAP_CALENDAR_DAYS = 7       # 5 business days ≈ 7 calendar days

# 5 calendar days covers:
#   - normal weekends       (Fri → Mon = 3 days)
#   - long weekends         (Fri → Tue = 4 days)
#   - ECB publication delay (rates published ~16:00 CET, pipeline runs 15:30 UTC)
FRESHNESS_LAG_DAYS    = 5

FEATURE_COLUMNS = [
    "rate", "daily_return_pct", "log_return",
    "ma_7d", "ma_21d", "ma_63d", "volatility_20d",
]

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_freshness(df: pd.DataFrame) -> list[str]:
    """Latest date must be within FRESHNESS_LAG_DAYS of today."""
    latest = df["date"].max().date()
    lag    = (date.today() - latest).days
    if lag > FRESHNESS_LAG_DAYS:
        return [f"Stale data: latest date is {latest} ({lag} days ago, limit {FRESHNESS_LAG_DAYS})"]
    return []


def check_minimum_rows(df: pd.DataFrame) -> list[str]:
    """Dataset must have at least MIN_ROWS rows."""
    if len(df) < MIN_ROWS:
        return [f"Too few rows: {len(df)} (minimum {MIN_ROWS})"]
    return []


def check_no_unexpected_gap(df: pd.DataFrame) -> list[str]:
    """No gap larger than MAX_GAP_CALENDAR_DAYS in the last 30 days."""
    cutoff  = df["date"].max() - pd.Timedelta(days=30)
    recent  = df[df["date"] >= cutoff].sort_values("date")
    deltas  = recent["date"].diff().dropna()
    large   = deltas[deltas > pd.Timedelta(days=MAX_GAP_CALENDAR_DAYS)]
    if not large.empty:
        return [f"Unexpected gap in last 30 days: {large.max().days} calendar days"]
    return []


def check_spike_guard(df: pd.DataFrame) -> list[str]:
    """No single daily return should exceed ±MAX_RETURN_PCT."""
    returns = df["daily_return_pct"].dropna()
    spikes  = returns[returns.abs() > MAX_RETURN_PCT]
    if not spikes.empty:
        worst      = spikes.abs().max()
        worst_date = df.loc[spikes.abs().idxmax(), "date"].date()
        return [f"Implausible spike: {worst:.2f}% on {worst_date} (limit ±{MAX_RETURN_PCT}%)"]
    return []


def check_no_all_null_columns(df: pd.DataFrame) -> list[str]:
    """No feature column should be entirely NaN."""
    return [
        f"Column '{col}' is entirely NaN"
        for col in FEATURE_COLUMNS
        if col in df.columns and df[col].isna().all()
    ]


ALL_CHECKS = [
    check_freshness,
    check_minimum_rows,
    check_no_unexpected_gap,
    check_spike_guard,
    check_no_all_null_columns,
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_checks(pair: str) -> tuple[bool, list[str]]:
    """
    Load the pair CSV and run all checks.

    Returns (passed, errors).
    """
    csv_path = DATASETS_ROOT / pair / f"{pair}.csv"

    if not csv_path.exists():
        return False, [f"{csv_path} not found — did calc_pair.py run?"]

    df     = pd.read_csv(csv_path, parse_dates=["date"])
    errors = []
    for check in ALL_CHECKS:
        errors.extend(check(df))

    print(f"Pair      : {pair}")
    print(f"Rows      : {len(df):,}")
    print(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Checks    : {len(ALL_CHECKS)} run, {len(errors)} failed")

    if errors:
        print("\nFailed checks:", file=sys.stderr)
        for msg in errors:
            print(f"  ✗ {msg}", file=sys.stderr)

    return len(errors) == 0, errors

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run data quality checks on a generated pair CSV."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    args        = parser.parse_args()
    pair        = args.pair.upper()

    passed, errors = run_checks(pair)

    for msg in errors:
        emit_github_warning(msg, script="scripts/validate_pair.py")

    status = "passed" if passed else "FAILED"
    append_github_summary(f"| {pair} validation | {status} |\n")
    for msg in errors:
        append_github_summary(f"  - {msg}\n")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
