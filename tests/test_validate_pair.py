"""tests/test_validate_pair.py"""

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_pair import (
    MAX_RETURN_PCT,
    check_freshness,
    check_minimum_rows,
    check_no_all_null_columns,
    check_no_unexpected_gap,
    check_spike_guard,
    run_checks,
)


def make_df(
    n_rows: int = 2000,
    latest_offset_days: int = 1,
    spike_index: int | None = None,
    gap_after_index: int | None = None,
) -> pd.DataFrame:
    latest = date.today() - timedelta(days=latest_offset_days)
    dates = pd.date_range(end=latest, periods=n_rows, freq="B")
    rates = np.full(len(dates), 150.0)

    if spike_index is not None:
        rates[spike_index] = rates[spike_index - 1] * 1.30

    df = pd.DataFrame({"date": dates, "rate": rates})
    df.loc[df.index[-1], "date"] = pd.Timestamp(latest)
    df["daily_return_pct"] = df["rate"].pct_change() * 100
    df["log_return"] = np.log(df["rate"]).diff()
    df["ma_7d"] = df["rate"].rolling(7, min_periods=1).mean()
    df["ma_21d"] = df["rate"].rolling(21, min_periods=1).mean()
    df["ma_63d"] = df["rate"].rolling(63, min_periods=1).mean()
    df["volatility_20d"] = df["daily_return_pct"].rolling(20, min_periods=1).std()

    if gap_after_index is not None:
        df.loc[df.index > gap_after_index, "date"] += timedelta(days=8)

    return df


class TestCheckFreshness:
    def test_passes_when_yesterday(self) -> None:
        assert check_freshness(make_df(latest_offset_days=1)) == []

    def test_passes_at_limit(self) -> None:
        assert check_freshness(make_df(latest_offset_days=5)) == []

    def test_fails_when_too_stale(self) -> None:
        assert len(check_freshness(make_df(latest_offset_days=6))) == 1


class TestCheckMinimumRows:
    def test_passes_with_enough_rows(self) -> None:
        assert check_minimum_rows(make_df(n_rows=2000)) == []

    def test_fails_at_boundary(self) -> None:
        assert len(check_minimum_rows(make_df(n_rows=999))) == 1

    def test_passes_at_boundary(self) -> None:
        assert check_minimum_rows(make_df(n_rows=1000)) == []


class TestCheckNoUnexpectedGap:
    def test_passes_clean_series(self) -> None:
        assert check_no_unexpected_gap(make_df()) == []

    def test_fails_with_large_gap(self) -> None:
        df = make_df(n_rows=2000, gap_after_index=1990)
        assert len(check_no_unexpected_gap(df)) == 1


class TestCheckSpikeGuard:
    def test_passes_no_spikes(self) -> None:
        assert check_spike_guard(make_df()) == []

    def test_fails_with_spike(self) -> None:
        assert len(check_spike_guard(make_df(spike_index=1000))) == 1

    def test_passes_just_below_threshold(self) -> None:
        df = make_df()
        df.loc[500, "daily_return_pct"] = MAX_RETURN_PCT - 0.01
        assert check_spike_guard(df) == []

    def test_fails_just_above_threshold(self) -> None:
        df = make_df()
        df.loc[500, "daily_return_pct"] = MAX_RETURN_PCT + 0.01
        assert len(check_spike_guard(df)) == 1


class TestCheckNoAllNullColumns:
    def test_passes_valid_data(self) -> None:
        assert check_no_all_null_columns(make_df()) == []

    def test_fails_when_rate_is_all_nan(self) -> None:
        df = make_df()
        df["rate"] = np.nan
        assert any("rate" in e for e in check_no_all_null_columns(df))

    def test_partial_nans_are_allowed(self) -> None:
        assert check_no_all_null_columns(make_df()) == []


class TestRunChecks:
    def test_missing_csv_returns_false(self, tmp_path: Path) -> None:
        with patch("validate_pair.DATASETS_ROOT", tmp_path):
            passed, errors = run_checks("USDJPY")
        assert passed is False
        assert any("not found" in e for e in errors)

    def test_valid_csv_passes_all_checks(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        make_df().to_csv(pair_dir / "USDJPY.csv", index=False)
        with patch("validate_pair.DATASETS_ROOT", tmp_path):
            passed, errors = run_checks("USDJPY")
        assert passed is True
        assert errors == []

    def test_stale_csv_returns_errors(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        make_df(latest_offset_days=10).to_csv(pair_dir / "USDJPY.csv", index=False)
        with patch("validate_pair.DATASETS_ROOT", tmp_path):
            passed, errors = run_checks("USDJPY")
        assert passed is False
        assert len(errors) >= 1
