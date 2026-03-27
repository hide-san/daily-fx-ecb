"""tests/test_create_notebook_eda.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import notebook_slug
from create_notebook_eda import build_notebook
from create_notebook_eda import write_kernel_metadata as write_eda_metadata


class TestBuildNotebook:
    def test_returns_nbformat_4(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        assert nb["nbformat"] == 4

    def test_has_cells(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        assert len(nb["cells"]) > 0

    def test_first_cell_contains_pair(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        assert "USD/JPY" in nb["cells"][0]["source"]

    def test_has_kernelspec(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        assert "kernelspec" in nb["metadata"]

    def test_cells_have_valid_types(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        for cell in nb["cells"]:
            assert cell["cell_type"] in ("markdown", "code")


class TestWriteKernelMetadataEda:
    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        with patch("create_notebook_eda.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        assert (tmp_path / "kernel-metadata.json").exists()

    def test_metadata_has_required_keys(self, tmp_path: Path) -> None:
        with patch("create_notebook_eda.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata.json").read_text())
        for key in ("id", "title", "code_file", "language", "kernel_type"):
            assert key in meta, f"missing key: {key}"

    def test_code_file_is_eda_notebook(self, tmp_path: Path) -> None:
        with patch("create_notebook_eda.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata.json").read_text())
        assert meta["code_file"] == "USDJPY_eda.ipynb"


class TestMainCreateNotebook:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_notebook_eda

        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["create_notebook_eda.py", "--pair", "USDJPY"]),
            patch("create_notebook_eda.notebook_output_dir", return_value=tmp_path),
            patch("create_notebook_eda.load_public_kernels", return_value={notebook_slug("USDJPY")}),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_notebook_eda.main()
        assert (tmp_path / "USDJPY_eda.ipynb").exists()
        assert (tmp_path / "kernel-metadata.json").exists()
