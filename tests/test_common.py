"""tests/test_common.py"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import (
    CURRENCY_META,
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
            assert "name" in meta,    f"{ccy}: 'name' missing"
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
