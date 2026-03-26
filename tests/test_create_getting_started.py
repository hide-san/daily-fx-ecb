"""tests/test_create_getting_started.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_getting_started import (
    build_getting_started_notebook,
    getting_started_slug,
    getting_started_title,
)
from create_getting_started import write_kernel_metadata as write_gs_metadata


class TestGettingStartedHelpers:
    def test_slug_contains_base_and_quote(self) -> None:
        slug = getting_started_slug("USDJPY")
        assert "usd" in slug
        assert "jpy" in slug

    def test_title_contains_pair_display(self) -> None:
        assert "USD/JPY" in getting_started_title("USDJPY")

    def test_title_contains_getting_started(self) -> None:
        assert "Getting Started" in getting_started_title("USDJPY")


class TestBuildGettingStartedNotebook:
    def test_returns_nbformat_4(self) -> None:
        nb = build_getting_started_notebook("USDJPY", "USD", "JPY")
        assert nb["nbformat"] == 4

    def test_has_cells(self) -> None:
        nb = build_getting_started_notebook("USDJPY", "USD", "JPY")
        assert len(nb["cells"]) > 0

    def test_first_cell_contains_pair(self) -> None:
        nb = build_getting_started_notebook("USDJPY", "USD", "JPY")
        assert "USD/JPY" in nb["cells"][0]["source"]

    def test_has_kernelspec(self) -> None:
        nb = build_getting_started_notebook("USDJPY", "USD", "JPY")
        assert "kernelspec" in nb["metadata"]


class TestWriteKernelMetadataGettingStarted:
    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        with patch("create_getting_started.notebook_output_dir", return_value=tmp_path):
            write_gs_metadata("USDJPY")
        assert (tmp_path / "kernel-metadata-getting-started.json").exists()

    def test_code_file_is_getting_started_notebook(self, tmp_path: Path) -> None:
        with patch("create_getting_started.notebook_output_dir", return_value=tmp_path):
            write_gs_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-getting-started.json").read_text())
        assert meta["code_file"] == "USDJPY_getting_started.ipynb"


class TestMainCreateGettingStarted:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_getting_started

        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["create_getting_started.py", "--pair", "USDJPY"]),
            patch("create_getting_started.notebook_output_dir", return_value=tmp_path),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_getting_started.main()
        assert (tmp_path / "USDJPY_getting_started.ipynb").exists()
        assert (tmp_path / "kernel-metadata-getting-started.json").exists()
