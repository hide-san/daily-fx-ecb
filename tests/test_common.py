"""tests/test_common.py"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import (
    CURRENCY_META,
    KAGGLE_KEYWORDS_MAX,
    KAGGLE_SUBTITLE_MAX,
    KAGGLE_SUBTITLE_MIN,
    KAGGLE_TITLE_MAX,
    KAGGLE_TITLE_MIN,
    KAGGLE_USER,
    append_github_summary,
    code,
    dataset_slug,
    dataset_title,
    emit_github_warning,
    md,
    modeling_notebook_slug,
    modeling_notebook_title,
    notebook_output_dir,
    notebook_slug,
    notebook_title,
    parse_pair,
    run_command,
    series_search_url,
    utils_output_dir,
    utils_slug,
    validate_kaggle_metadata,
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
        assert dataset_title("USDJPY") == "Daily FX: USD/JPY"

    def test_dataset_slug_contains_pair(self) -> None:
        assert "usd-jpy" in dataset_slug("USDJPY")

    def test_notebook_slug_contains_pair(self) -> None:
        assert "usd-jpy" in notebook_slug("USDJPY")

    def test_dataset_slug_contains_username(self) -> None:
        assert KAGGLE_USER in dataset_slug("USDJPY")

    def test_notebook_slug_distinct_from_dataset_slug(self) -> None:
        assert dataset_slug("USDJPY") != notebook_slug("USDJPY")

    def test_utils_slug_contains_username(self) -> None:
        assert KAGGLE_USER in utils_slug()

    def test_utils_slug_contains_utils(self) -> None:
        assert "utils" in utils_slug()

    def test_modeling_notebook_slug_contains_pair(self) -> None:
        assert "usd-jpy" in modeling_notebook_slug("USDJPY")

    def test_notebook_title_contains_pair(self) -> None:
        assert "USD/JPY" in notebook_title("USDJPY")

    def test_modeling_notebook_title_contains_pair(self) -> None:
        assert "USD/JPY" in modeling_notebook_title("USDJPY")


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
            assert "name" in meta, f"{ccy}: 'name' missing"
            assert "country" in meta, f"{ccy}: 'country' missing"

    def test_meta_covers_common_currencies(self) -> None:
        for ccy in ["USD", "JPY", "GBP", "CHF"]:
            assert ccy in CURRENCY_META, f"{ccy} missing from CURRENCY_META"


class TestCellBuilders:
    def test_md_cell_type(self) -> None:
        cell = md("# Hello")
        assert cell["cell_type"] == "markdown"

    def test_md_source(self) -> None:
        cell = md("# Hello")
        assert cell["source"] == "# Hello"

    def test_code_cell_type(self) -> None:
        cell = code("print('hi')")
        assert cell["cell_type"] == "code"

    def test_code_source(self) -> None:
        cell = code("x = 1")
        assert cell["source"] == "x = 1"

    def test_md_has_id(self) -> None:
        cell = md("test")
        assert "id" in cell

    def test_code_has_outputs(self) -> None:
        cell = code("x = 1")
        assert cell["outputs"] == []


class TestDirHelpers:
    def test_notebook_output_dir_creates_directory(self, tmp_path: Path) -> None:
        with patch("common.NOTEBOOKS_ROOT", tmp_path):
            path = notebook_output_dir("USDJPY")
        assert path.exists()
        assert path == tmp_path / "USDJPY"

    def test_utils_output_dir_creates_directory(self, tmp_path: Path) -> None:
        with patch("common.UTILS_DIR", tmp_path / "utils"):
            path = utils_output_dir()
        assert path.exists()


class TestSideEffects:
    def test_append_github_summary(self, tmp_path: Path) -> None:
        summary_file = tmp_path / "summary.md"
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            append_github_summary("hello\n")
        assert summary_file.read_text() == "hello\n"

    def test_emit_github_warning_prints(self, capsys: object) -> None:
        emit_github_warning("test warning")
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "test warning" in captured.out

    def test_run_command_returns_result(self) -> None:
        import subprocess

        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        with patch("common.subprocess.run", return_value=mock_result):
            result = run_command(["echo", "test"])
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# validate_kaggle_metadata
# ---------------------------------------------------------------------------

VALID_TITLE = "Daily FX: USDJPY"
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
        assert not any(
            "keywords" in e for e in validate_kaggle_metadata(VALID_TITLE, VALID_SUBTITLE, kws)
        )


class TestValidateKaggleMetadataFails:
    def test_title_too_short(self) -> None:
        errors = validate_kaggle_metadata(
            "A" * (KAGGLE_TITLE_MIN - 1), VALID_SUBTITLE, VALID_KEYWORDS
        )
        assert any("title" in e for e in errors)

    def test_title_too_long(self) -> None:
        errors = validate_kaggle_metadata(
            "A" * (KAGGLE_TITLE_MAX + 1), VALID_SUBTITLE, VALID_KEYWORDS
        )
        assert any("title" in e for e in errors)

    def test_subtitle_too_short(self) -> None:
        errors = validate_kaggle_metadata(
            VALID_TITLE, "A" * (KAGGLE_SUBTITLE_MIN - 1), VALID_KEYWORDS
        )
        assert any("subtitle" in e for e in errors)

    def test_subtitle_too_long(self) -> None:
        errors = validate_kaggle_metadata(
            VALID_TITLE, "A" * (KAGGLE_SUBTITLE_MAX + 1), VALID_KEYWORDS
        )
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
            title=dataset_title(pair),
            subtitle=make_subtitle(base, quote),
            keywords=VALID_KEYWORDS,
        )
        assert errors == [], f"{pair}: {errors}"
