"""tests/test_create_modeling_notebook.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_modeling_notebook import build_modeling_notebook
from create_modeling_notebook import write_kernel_metadata as write_modeling_metadata


class TestBuildModelingNotebook:
    def test_returns_nbformat_4(self) -> None:
        nb = build_modeling_notebook("USDJPY", "USD", "JPY")
        assert nb["nbformat"] == 4

    def test_has_cells(self) -> None:
        nb = build_modeling_notebook("USDJPY", "USD", "JPY")
        assert len(nb["cells"]) > 0

    def test_first_cell_contains_pair(self) -> None:
        nb = build_modeling_notebook("USDJPY", "USD", "JPY")
        assert "USD/JPY" in nb["cells"][0]["source"]

    def test_has_kernelspec(self) -> None:
        nb = build_modeling_notebook("USDJPY", "USD", "JPY")
        assert "kernelspec" in nb["metadata"]


class TestWriteKernelMetadataModeling:
    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        with patch("create_modeling_notebook.notebook_output_dir", return_value=tmp_path):
            write_modeling_metadata("USDJPY")
        assert (tmp_path / "kernel-metadata-modeling.json").exists()

    def test_code_file_is_modeling_notebook(self, tmp_path: Path) -> None:
        with patch("create_modeling_notebook.notebook_output_dir", return_value=tmp_path):
            write_modeling_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-modeling.json").read_text())
        assert meta["code_file"] == "USDJPY_modeling.ipynb"

    def test_internet_enabled_for_modeling(self, tmp_path: Path) -> None:
        with patch("create_modeling_notebook.notebook_output_dir", return_value=tmp_path):
            write_modeling_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-modeling.json").read_text())
        assert meta["enable_internet"] is True


class TestMainCreateModelingNotebook:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_modeling_notebook

        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["create_modeling_notebook.py", "--pair", "USDJPY"]),
            patch("create_modeling_notebook.notebook_output_dir", return_value=tmp_path),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_modeling_notebook.main()
        assert (tmp_path / "USDJPY_modeling.ipynb").exists()
        assert (tmp_path / "kernel-metadata-modeling.json").exists()
