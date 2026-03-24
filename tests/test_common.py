"""tests/test_common.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import (
    CURRENCY_META,
    KAGGLE_USER,
    dataset_slug,
    dataset_title,
    notebook_slug,
    notebook_title,
    parse_pair,
    series_search_url,
    utils_slug,
)


class TestParsePair:
    def test_splits_correctly(self) -> None:
        assert parse_pair("USDJPY") == ("USD", "JPY")

    def test_uppercases(self) -> None:
        assert parse_pair("usdjpy") == ("USD", "JPY")

    def test_eur_pair(self) -> None:
        assert parse_pair("EURGBP") == ("EUR", "GBP")


class TestNamingConventions:
    def test_dataset_title(self) -> None:
        assert dataset_title("USDJPY") == "Daily FX: USDJPY"

    def test_dataset_slug_contains_pair(self) -> None:
        assert "usdjpy" in dataset_slug("USDJPY")

    def test_notebook_slug_contains_pair(self) -> None:
        assert "usdjpy" in notebook_slug("USDJPY")

    def test_dataset_slug_contains_username(self) -> None:
        assert KAGGLE_USER in dataset_slug("USDJPY")

    def test_notebook_slug_distinct_from_dataset_slug(self) -> None:
        assert dataset_slug("USDJPY") != notebook_slug("USDJPY")

    def test_utils_slug_contains_username(self) -> None:
        assert KAGGLE_USER in utils_slug()

    def test_utils_slug_contains_utils(self) -> None:
        assert "utils" in utils_slug()


class TestSeriesSearchUrl:
    def test_datasets_url(self) -> None:
        url = series_search_url("datasets")
        assert "kaggle.com/datasets" in url
        assert "Daily+FX" in url

    def test_code_url(self) -> None:
        url = series_search_url("code")
        assert "kaggle.com/code" in url
        assert "Daily+FX" in url


class TestCurrencyMeta:
    def test_metadata_has_required_keys(self) -> None:
        for ccy, meta in CURRENCY_META.items():
            assert "name" in meta,    f"{ccy}: 'name' missing"
            assert "country" in meta, f"{ccy}: 'country' missing"

    def test_meta_covers_common_currencies(self) -> None:
        for ccy in ["USD", "JPY", "GBP", "CHF"]:
            assert ccy in CURRENCY_META, f"{ccy} missing from CURRENCY_META"
