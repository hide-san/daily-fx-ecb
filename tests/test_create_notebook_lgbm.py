"""tests/test_create_notebook_lgbm.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import lgbm_notebook_slug
from create_notebook_lgbm import build_notebook
from create_notebook_lgbm import write_kernel_metadata as write_lgbm_metadata


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

    def test_contains_lightgbm_import(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        sources = " ".join(c["source"] for c in nb["cells"] if c["cell_type"] == "code")
        assert "lightgbm" in sources

    def test_contains_feature_engineering(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        sources = " ".join(c["source"] for c in nb["cells"] if c["cell_type"] == "code")
        assert "lag_1" in sources

    def test_contains_modeling_link(self) -> None:
        nb = build_notebook("USDJPY", "USD", "JPY")
        sources = " ".join(c["source"] for c in nb["cells"] if c["cell_type"] == "markdown")
        assert "arima-garch" in sources.lower()


class TestWriteKernelMetadataLgbm:
    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        with patch("create_notebook_lgbm.notebook_output_dir", return_value=tmp_path):
            write_lgbm_metadata("USDJPY")
        assert (tmp_path / "kernel-metadata-lgbm.json").exists()

    def test_metadata_has_required_keys(self, tmp_path: Path) -> None:
        with patch("create_notebook_lgbm.notebook_output_dir", return_value=tmp_path):
            write_lgbm_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-lgbm.json").read_text())
        for key in ("id", "title", "code_file", "language", "kernel_type"):
            assert key in meta, f"missing key: {key}"

    def test_code_file_is_lgbm_notebook(self, tmp_path: Path) -> None:
        with patch("create_notebook_lgbm.notebook_output_dir", return_value=tmp_path):
            write_lgbm_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-lgbm.json").read_text())
        assert meta["code_file"] == "USDJPY_lgbm.ipynb"

    def test_is_public(self, tmp_path: Path) -> None:
        with patch("create_notebook_lgbm.notebook_output_dir", return_value=tmp_path):
            write_lgbm_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata-lgbm.json").read_text())
        assert meta["is_private"] is False


class TestMainCreateNotebook:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_notebook_lgbm

        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["create_notebook_lgbm.py", "--pair", "USDJPY"]),
            patch("create_notebook_lgbm.notebook_output_dir", return_value=tmp_path),
            patch(
                "create_notebook_lgbm.load_public_kernels",
                return_value={lgbm_notebook_slug("USDJPY")},
            ),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_notebook_lgbm.main()
        assert (tmp_path / "USDJPY_lgbm.ipynb").exists()
        assert (tmp_path / "kernel-metadata-lgbm.json").exists()

    def test_main_skips_when_not_in_allowlist(self, tmp_path: Path) -> None:
        import create_notebook_lgbm

        with (
            patch("sys.argv", ["create_notebook_lgbm.py", "--pair", "USDJPY"]),
            patch("create_notebook_lgbm.load_public_kernels", return_value=set()),
        ):
            try:
                create_notebook_lgbm.main()
            except SystemExit as e:
                assert e.code == 0
