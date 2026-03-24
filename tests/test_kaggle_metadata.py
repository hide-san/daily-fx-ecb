"""tests/test_kaggle_metadata.py"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import (
    KAGGLE_KEYWORDS_MAX,
    KAGGLE_SUBTITLE_MAX,
    KAGGLE_SUBTITLE_MIN,
    KAGGLE_TITLE_MAX,
    KAGGLE_TITLE_MIN,
    dataset_title,
    parse_pair,
    validate_kaggle_metadata,
)

VALID_TITLE    = "Daily FX: USDJPY"
VALID_SUBTITLE = "ECB daily USD/JPY cross rates 1999-present, ML-ready features"
VALID_KEYWORDS = ["finance", "economics", "currencies-and-foreign-exchange"]


def make_subtitle(base: str, quote: str) -> str:
    return f"ECB daily {base}/{quote} cross rates 1999-present, ML-ready features"


class TestValidateKaggleMetadataPasses:
    def test_valid_metadata_returns_no_errors(self) -> None:
        assert validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, VALID_KEYWORDS) == []

    def test_title_at_minimum_length(self) -> None:
        errors = validate_kaggle_metadata("A" * KAGGLE_TITLE_MIN, VALID_SUBTITLE, VALID_KEYWORDS)
        assert not any("title" in e for e in errors)

    def test_title_at_maximum_length(self) -> None:
        errors = validate_kaggle_metadata("A" * KAGGLE_TITLE_MAX, VALID_SUBTITLE, VALID_KEYWORDS)
        assert not any("title" in e for e in errors)

    def test_subtitle_at_minimum_length(self) -> None:
        errors = validate_kaggle_metadata(VALID_TITLE, "A" * KAGGLE_SUBTITLE_MIN, VALID_KEYWORDS)
        assert not any("subtitle" in e for e in errors)

    def test_keywords_at_maximum_count(self) -> None:
        kws = [f"tag-{i}" for i in range(KAGGLE_KEYWORDS_MAX)]
        assert not any("keywords" in e for e in validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, kws))


class TestValidateKaggleMetadataFails:
    def test_title_too_short(self) -> None:
        errors = validate_kaggle_metadata("A" * (KAGGLE_TITLE_MIN - 1), VALID_SUBTITLE, VALID_KEYWORDS)
        assert any("title" in e for e in errors)

    def test_title_too_long(self) -> None:
        errors = validate_kaggle_metadata("A" * (KAGGLE_TITLE_MAX + 1), VALID_SUBTITLE, VALID_KEYWORDS)
        assert any("title" in e for e in errors)

    def test_subtitle_too_short(self) -> None:
        errors = validate_kaggle_metadata(VALID_TITLE, "A" * (KAGGLE_SUBTITLE_MIN - 1), VALID_KEYWORDS)
        assert any("subtitle" in e for e in errors)

    def test_subtitle_too_long(self) -> None:
        errors = validate_kaggle_metadata(VALID_TITLE, "A" * (KAGGLE_SUBTITLE_MAX + 1), VALID_KEYWORDS)
        assert any("subtitle" in e for e in errors)

    def test_too_many_keywords(self) -> None:
        kws = [f"tag-{i}" for i in range(KAGGLE_KEYWORDS_MAX + 1)]
        errors = validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, kws)
        assert any("keywords" in e for e in errors)

    def test_multiple_violations_reported(self) -> None:
        errors = validate_kaggle_metadata("X", "Y", VALID_KEYWORDS)
        assert len(errors) >= 2


class TestAllPairsSatisfyConstraints:
    SAMPLE_PAIRS = ["USDJPY", "EURGBP", "GBPCHF", "AUDNZD"]

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_title_within_limits(self, pair: str) -> None:
        title = dataset_title(pair)
        assert KAGGLE_TITLE_MIN <= len(title) <= KAGGLE_TITLE_MAX

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_subtitle_within_limits(self, pair: str) -> None:
        base, quote = parse_pair(pair)
        subtitle = make_subtitle(base, quote)
        assert KAGGLE_SUBTITLE_MIN <= len(subtitle) <= KAGGLE_SUBTITLE_MAX

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_no_validation_errors(self, pair: str) -> None:
        base, quote = parse_pair(pair)
        errors = validate_kaggle_metadata(
            title    = dataset_title(pair),
            subtitle = make_subtitle(base, quote),
            keywords = VALID_KEYWORDS,
        )
        assert errors == [], f"{pair}: {errors}"
