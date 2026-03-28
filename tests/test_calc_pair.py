"""tests/test_calc_pair.py"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from calc_pair import compute_pair, load_eur_rates, write_dataset_metadata


def make_wide(data: dict, dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(data, index=pd.to_datetime(dates))


@pytest.fixture()
def simple_wide() -> pd.DataFrame:
    return make_wide(
        data={
            "USD": [1.0, 1.1, 1.2, 1.1, 1.0],
            "JPY": [100.0, 110.0, 120.0, 110.0, 100.0],
            "GBP": [0.8, 0.85, 0.9, 0.85, 0.8],
        },
        dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    )


class TestLoadEurRates:
    def test_returns_wide_dataframe(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text(
            "date,currency,rate_vs_eur\n"
            "2024-01-01,USD,1.1\n"
            "2024-01-01,JPY,130.0\n"
            "2024-01-02,USD,1.2\n"
            "2024-01-02,JPY,132.0\n"
        )
        wide = load_eur_rates(csv)
        assert "USD" in wide.columns
        assert "JPY" in wide.columns
        assert wide.index.name == "date"

    def test_sorted_by_date(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text(
            "date,currency,rate_vs_eur\n"
            "2024-01-03,USD,1.3\n"
            "2024-01-01,USD,1.1\n"
            "2024-01-02,USD,1.2\n"
        )
        wide = load_eur_rates(csv)
        assert list(wide.index) == sorted(wide.index)


class TestComputePair:
    def test_required_columns_present(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        expected = {
            "date",
            "rate",
            "daily_return_pct",
            "log_return",
            "ma_7d",
            "ma_21d",
            "ma_63d",
            "volatility_20d",
            "year",
            "month",
            "day_of_week",
        }
        assert expected.issubset(set(df.columns))

    def test_cross_rate_is_flat_100(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        assert np.allclose(df["rate"], 100.0)

    def test_row_count_matches_input(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        assert len(df) == 5

    def test_unknown_base_raises(self, simple_wide: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="XXX"):
            compute_pair(simple_wide, "XXX", "JPY")

    def test_unknown_quote_raises(self, simple_wide: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="ZZZ"):
            compute_pair(simple_wide, "USD", "ZZZ")

    def test_first_row_return_is_nan(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "GBP")
        assert pd.isna(df["daily_return_pct"].iloc[0])

    def test_ma_7d_has_no_nans(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        assert not df["ma_7d"].isna().any()

    def test_result_sorted_by_date(self, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        assert list(df["date"]) == sorted(df["date"])

    def test_eur_as_base_requires_injection(self, simple_wide: pd.DataFrame) -> None:
        # EUR must be injected by the caller before compute_pair is invoked
        with pytest.raises(ValueError, match="EUR"):
            compute_pair(simple_wide, "EUR", "JPY")

    def test_eur_as_base_works_after_injection(self, simple_wide: pd.DataFrame) -> None:
        wide = simple_wide.copy()
        wide["EUR"] = 1.0
        df = compute_pair(wide, "EUR", "JPY")
        assert len(df) == 5
        assert np.allclose(df["rate"], simple_wide["JPY"].values)


class TestWriteDatasetMetadata:
    def test_creates_json_file(self, tmp_path: Path, simple_wide: pd.DataFrame) -> None:
        df = compute_pair(simple_wide, "USD", "JPY")
        import common

        original = common.DATASETS_ROOT
        common.DATASETS_ROOT = tmp_path
        (tmp_path / "USDJPY").mkdir()
        write_dataset_metadata("USDJPY", "USD", "JPY", df)
        common.DATASETS_ROOT = original
        assert (tmp_path / "USDJPY" / "dataset-metadata.json").exists()

    def test_title_follows_naming_convention(
        self, tmp_path: Path, simple_wide: pd.DataFrame
    ) -> None:
        import common

        original = common.DATASETS_ROOT
        common.DATASETS_ROOT = tmp_path
        (tmp_path / "USDJPY").mkdir()
        df = compute_pair(simple_wide, "USD", "JPY")
        write_dataset_metadata("USDJPY", "USD", "JPY", df)
        common.DATASETS_ROOT = original
        with open(tmp_path / "USDJPY" / "dataset-metadata.json") as fh:
            meta = json.load(fh)
        assert meta["title"] == "Daily FX: USD/JPY"

    def test_raises_on_invalid_metadata(self, tmp_path: Path, simple_wide: pd.DataFrame) -> None:
        import common

        original = common.DATASETS_ROOT
        common.DATASETS_ROOT = tmp_path
        (tmp_path / "USDJPY").mkdir()
        df = compute_pair(simple_wide, "USD", "JPY")
        with (
            pytest.raises(ValueError, match="Invalid Kaggle metadata"),
            pytest.MonkeyPatch.context() as mp,
        ):
            mp.setattr("calc_pair.validate_kaggle_metadata", lambda **_: ["title too long"])
            write_dataset_metadata("USDJPY", "USD", "JPY", df)
        common.DATASETS_ROOT = original

    def test_is_public(self, tmp_path: Path, simple_wide: pd.DataFrame) -> None:
        import common

        original = common.DATASETS_ROOT
        common.DATASETS_ROOT = tmp_path
        (tmp_path / "USDJPY").mkdir()
        df = compute_pair(simple_wide, "USD", "JPY")
        write_dataset_metadata("USDJPY", "USD", "JPY", df)
        common.DATASETS_ROOT = original
        with open(tmp_path / "USDJPY" / "dataset-metadata.json") as fh:
            meta = json.load(fh)
        assert meta["isPrivate"] is False
