"""
tests/test_kaggle_metadata.py
==============================
Tests for Kaggle dataset metadata constraints.

Documented limits (source: https://github.com/Kaggle/kaggle-api/wiki/Dataset-Metadata):
  title    : 6–50 characters
  subtitle : 20–80 characters
  keywords : no official limit (we cap at KAGGLE_KEYWORDS_MAX as a safeguard)
"""

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TITLE    = "Daily FX: USDJPY"                                          # 16 chars
VALID_SUBTITLE = "ECB daily USD/JPY cross rates 1999-present, ML-ready features"  # 61 chars
VALID_KEYWORDS = ["finance", "economics", "currencies-and-foreign-exchange", "time-series"]


def make_subtitle(base: str, quote: str) -> str:
    return f"ECB daily {base}/{quote} cross rates 1999-present, ML-ready features"


# ---------------------------------------------------------------------------
# validate_kaggle_metadata — passing cases
# ---------------------------------------------------------------------------

class TestValidateKaggleMetadataPasses:
    def test_valid_metadata_returns_no_errors(self) -> None:
        errors = validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, VALID_KEYWORDS)
        assert errors == []

    def test_title_at_minimum_length(self) -> None:
        title = "A" * KAGGLE_TITLE_MIN
        errors = validate_kaggle_metadata(title, VALID_SUBTITLE, VALID_KEYWORDS)
        assert not any("title" in e for e in errors)

    def test_title_at_maximum_length(self) -> None:
        title = "A" * KAGGLE_TITLE_MAX
        errors = validate_kaggle_metadata(title, VALID_SUBTITLE, VALID_KEYWORDS)
        assert not any("title" in e for e in errors)

    def test_subtitle_at_minimum_length(self) -> None:
        subtitle = "A" * KAGGLE_SUBTITLE_MIN
        errors = validate_kaggle_metadata(VALID_TITLE, subtitle, VALID_KEYWORDS)
        assert not any("subtitle" in e for e in errors)

    def test_subtitle_at_maximum_length(self) -> None:
        subtitle = "A" * KAGGLE_SUBTITLE_MAX
        errors = validate_kaggle_metadata(VALID_TITLE, subtitle, VALID_KEYWORDS)
        assert not any("subtitle" in e for e in errors)

    def test_keywords_at_maximum_count(self) -> None:
        keywords = [f"tag-{i}" for i in range(KAGGLE_KEYWORDS_MAX)]
        errors = validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, keywords)
        assert not any("keywords" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_kaggle_metadata — failing cases
# ---------------------------------------------------------------------------

class TestValidateKaggleMetadataFails:
    def test_title_too_short(self) -> None:
        title = "A" * (KAGGLE_TITLE_MIN - 1)
        errors = validate_kaggle_metadata(title, VALID_SUBTITLE, VALID_KEYWORDS)
        assert any("title" in e for e in errors)

    def test_title_too_long(self) -> None:
        title = "A" * (KAGGLE_TITLE_MAX + 1)
        errors = validate_kaggle_metadata(title, VALID_SUBTITLE, VALID_KEYWORDS)
        assert any("title" in e for e in errors)

    def test_subtitle_too_short(self) -> None:
        subtitle = "A" * (KAGGLE_SUBTITLE_MIN - 1)
        errors = validate_kaggle_metadata(VALID_TITLE, subtitle, VALID_KEYWORDS)
        assert any("subtitle" in e for e in errors)

    def test_subtitle_too_long(self) -> None:
        subtitle = "A" * (KAGGLE_SUBTITLE_MAX + 1)
        errors = validate_kaggle_metadata(VALID_TITLE, subtitle, VALID_KEYWORDS)
        assert any("subtitle" in e for e in errors)

    def test_too_many_keywords(self) -> None:
        keywords = [f"tag-{i}" for i in range(KAGGLE_KEYWORDS_MAX + 1)]
        errors = validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, keywords)
        assert any("keywords" in e for e in errors)

    def test_multiple_violations_reported(self) -> None:
        """All constraint violations are reported at once, not just the first."""
        title    = "X"                           # too short
        subtitle = "Y"                           # too short
        errors   = validate_kaggle_metadata(title, subtitle, VALID_KEYWORDS)
        assert len(errors) >= 2


# ---------------------------------------------------------------------------
# All real pairs satisfy the constraints
# ---------------------------------------------------------------------------

class TestAllPairsSatisfyConstraints:
    """
    Parametrize over a sample of real pairs to confirm that the
    generated title and subtitle always fall within Kaggle limits.
    """

    SAMPLE_PAIRS = ["USDJPY", "EURGBP", "GBPCHF", "AUDNZD", "MXNBRL"]

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_title_within_limits(self, pair: str) -> None:
        title = dataset_title(pair)
        assert KAGGLE_TITLE_MIN <= len(title) <= KAGGLE_TITLE_MAX, (
            f"{pair}: title '{title}' is {len(title)} chars "
            f"(limit {KAGGLE_TITLE_MIN}–{KAGGLE_TITLE_MAX})"
        )

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_subtitle_within_limits(self, pair: str) -> None:
        base, quote = parse_pair(pair)
        subtitle = make_subtitle(base, quote)
        assert KAGGLE_SUBTITLE_MIN <= len(subtitle) <= KAGGLE_SUBTITLE_MAX, (
            f"{pair}: subtitle '{subtitle}' is {len(subtitle)} chars "
            f"(limit {KAGGLE_SUBTITLE_MIN}–{KAGGLE_SUBTITLE_MAX})"
        )

    @pytest.mark.parametrize("pair", SAMPLE_PAIRS)
    def test_no_validation_errors(self, pair: str) -> None:
        base, quote = parse_pair(pair)
        errors = validate_kaggle_metadata(
            title    = dataset_title(pair),
            subtitle = make_subtitle(base, quote),
            keywords = VALID_KEYWORDS,
        )
        assert errors == [], f"{pair}: {errors}"
