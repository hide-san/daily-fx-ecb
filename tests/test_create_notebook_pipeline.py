"""tests/test_create_notebook_pipeline.py"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import pipeline_notebook_slug
from create_notebook_pipeline import build_pipeline_notebook, write_kernel_metadata


class TestBuildPipelineNotebook:
    def test_returns_nbformat_4(self) -> None:
        nb = build_pipeline_notebook()
        assert nb["nbformat"] == 4

    def test_has_cells(self) -> None:
        nb = build_pipeline_notebook()
        assert len(nb["cells"]) > 0

    def test_cells_have_valid_types(self) -> None:
        nb = build_pipeline_notebook()
        for cell in nb["cells"]:
            assert cell["cell_type"] in ("markdown", "code")

    def test_github_url_present_in_cells(self) -> None:
        nb = build_pipeline_notebook()
        sources = " ".join(cell["source"] for cell in nb["cells"])
        assert "raw.githubusercontent.com/hide-san/daily-fx-ecb" in sources

    def test_kaggle_readme_fetched(self) -> None:
        nb = build_pipeline_notebook()
        sources = " ".join(cell["source"] for cell in nb["cells"])
        assert "KAGGLE_README.md" in sources

    def test_changelog_fetched(self) -> None:
        nb = build_pipeline_notebook()
        sources = " ".join(cell["source"] for cell in nb["cells"])
        assert "CHANGELOG.md" in sources

    def test_readme_fetched_and_displayed(self) -> None:
        nb = build_pipeline_notebook()
        sources = " ".join(cell["source"] for cell in nb["cells"])
        assert "KAGGLE_README.md" in sources
        assert "display(Markdown(" in sources

    def test_has_kernelspec(self) -> None:
        nb = build_pipeline_notebook()
        assert "kernelspec" in nb["metadata"]


class TestWriteKernelMetadata:
    def test_creates_metadata_file(self, tmp_path: Path) -> None:
        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        assert (tmp_path / "kernel-metadata-pipeline.json").exists()

    def test_enable_internet_is_true(self, tmp_path: Path) -> None:
        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-pipeline.json").read_text())
        assert meta["enable_internet"] is True

    def test_kernel_type_is_notebook(self, tmp_path: Path) -> None:
        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-pipeline.json").read_text())
        assert meta["kernel_type"] == "notebook"

    def test_code_file_is_pipeline_notebook(self, tmp_path: Path) -> None:
        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-pipeline.json").read_text())
        assert meta["code_file"] == "pipeline_overview.ipynb"

    def test_dataset_sources_contains_all_pairs(self, tmp_path: Path) -> None:
        from common import dataset_slug, load_pairs_file

        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-pipeline.json").read_text())
        expected = [dataset_slug(p) for p in load_pairs_file()]
        assert meta["dataset_sources"] == expected

    def test_dataset_sources_is_not_empty(self, tmp_path: Path) -> None:
        with patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path):
            write_kernel_metadata()
        meta = json.loads((tmp_path / "kernel-metadata-pipeline.json").read_text())
        assert len(meta["dataset_sources"]) > 0


class TestMainCreatePipelineNotebook:
    def test_main_creates_notebook_and_metadata(self, tmp_path: Path) -> None:
        import create_notebook_pipeline

        summary = tmp_path / "summary.md"
        with (
            patch("create_notebook_pipeline.pipeline_notebook_output_dir", return_value=tmp_path),
            patch("create_notebook_pipeline.load_public_kernels", return_value={pipeline_notebook_slug()}),
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}),
        ):
            create_notebook_pipeline.main()
        assert (tmp_path / "pipeline_overview.ipynb").exists()
        assert (tmp_path / "kernel-metadata-pipeline.json").exists()
