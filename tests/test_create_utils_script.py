"""tests/test_create_utils_script.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import utils_slug
from create_utils_script import FX_UTILS_SOURCE
from create_utils_script import write_kernel_metadata as write_utils_metadata


class TestCreateUtilsScript:
    def test_fx_utils_source_is_nonempty_string(self) -> None:
        assert isinstance(FX_UTILS_SOURCE, str)
        assert len(FX_UTILS_SOURCE) > 0

    def test_fx_utils_source_has_read_csv(self) -> None:
        assert "def read_csv" in FX_UTILS_SOURCE

    def test_fx_utils_source_find_data_dir_is_private(self) -> None:
        assert "def _find_data_dir" in FX_UTILS_SOURCE
        assert "def find_data_dir" not in FX_UTILS_SOURCE

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


class TestMainCreateUtilsScript:
    def test_main_creates_script_and_metadata(self, tmp_path: Path) -> None:
        import create_utils_script

        summary = tmp_path / "summary.md"
        with (
            patch("create_utils_script.utils_output_dir", return_value=tmp_path),
            patch("create_utils_script.load_public_kernels", return_value={utils_slug()}),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_utils_script.main()
        assert (tmp_path / "fx_utils.py").exists()
        assert (tmp_path / "kernel-metadata-utils.json").exists()
