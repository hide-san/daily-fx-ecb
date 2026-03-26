"""tests/test_create_scripts.py"""

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
from create_getting_started import (
    write_kernel_metadata as write_gs_metadata,
)
from create_modeling_notebook import (
    build_modeling_notebook,
)
from create_modeling_notebook import (
    write_kernel_metadata as write_modeling_metadata,
)
from create_notebook import build_notebook
from create_notebook import write_kernel_metadata as write_eda_metadata
from create_utils_script import FX_UTILS_SOURCE
from create_utils_script import write_kernel_metadata as write_utils_metadata

# ---------------------------------------------------------------------------
# create_notebook
# ---------------------------------------------------------------------------


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
        with patch("create_notebook.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        assert (tmp_path / "kernel-metadata.json").exists()

    def test_metadata_has_required_keys(self, tmp_path: Path) -> None:
        with patch("create_notebook.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata.json").read_text())
        for key in ("id", "title", "code_file", "language", "kernel_type"):
            assert key in meta, f"missing key: {key}"

    def test_code_file_is_eda_notebook(self, tmp_path: Path) -> None:
        with patch("create_notebook.notebook_output_dir", return_value=tmp_path):
            write_eda_metadata("USDJPY")
        meta = json.loads((tmp_path / "kernel-metadata.json").read_text())
        assert meta["code_file"] == "USDJPY_eda.ipynb"


# ---------------------------------------------------------------------------
# create_modeling_notebook
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# create_utils_script
# ---------------------------------------------------------------------------


class TestCreateUtilsScript:
    def test_fx_utils_source_is_nonempty_string(self) -> None:
        assert isinstance(FX_UTILS_SOURCE, str)
        assert len(FX_UTILS_SOURCE) > 0

    def test_fx_utils_source_has_find_data_dir(self) -> None:
        assert "find_data_dir" in FX_UTILS_SOURCE

    def test_fx_utils_source_has_feature_columns(self) -> None:
        assert "FEATURE_COLUMNS" in FX_UTILS_SOURCE

    def test_write_utils_metadata_creates_file(self, tmp_path: Path) -> None:
        with patch("create_utils_script.utils_output_dir", return_value=tmp_path):
            write_utils_metadata()
        assert (tmp_path / "kernel-metadata-utils.json").exists()

    def test_utils_metadata_is_script_type(self, tmp_path: Path) -> None:
        with patch("create_utils_script.utils_output_dir", return_value=tmp_path):
            write_utils_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-utils.json").read_text())
        assert meta["kernel_type"] == "script"

    def test_utils_metadata_code_file(self, tmp_path: Path) -> None:
        with patch("create_utils_script.utils_output_dir", return_value=tmp_path):
            write_utils_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-utils.json").read_text())
        assert meta["code_file"] == "fx_utils.py"


# ---------------------------------------------------------------------------
# create_getting_started
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# main() entry points
# ---------------------------------------------------------------------------


class TestMainCreateNotebook:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_notebook

        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["create_notebook.py", "--pair", "USDJPY"]),
            patch("create_notebook.notebook_output_dir", return_value=tmp_path),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_notebook.main()
        assert (tmp_path / "USDJPY_eda.ipynb").exists()
        assert (tmp_path / "kernel-metadata.json").exists()


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


class TestMainCreateUtilsScript:
    def test_main_creates_script_and_metadata(self, tmp_path: Path) -> None:
        import create_utils_script

        summary = tmp_path / "summary.md"
        with (
            patch("create_utils_script.utils_output_dir", return_value=tmp_path),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_utils_script.main()
        assert (tmp_path / "fx_utils.py").exists()
        assert (tmp_path / "kernel-metadata-utils.json").exists()
