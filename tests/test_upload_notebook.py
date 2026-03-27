"""tests/test_upload_notebook.py"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from upload_notebook import push_notebook, wait_for_kernel


def make_result(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


def make_pair_dir(tmp_path: Path, pair: str, kind: str) -> Path:
    """Create the required notebook directory and files for a push test."""
    from upload_notebook import _METADATA_FILE, _NOTEBOOK_FILE

    pair_dir = tmp_path / pair
    pair_dir.mkdir(parents=True, exist_ok=True)
    (pair_dir / _METADATA_FILE[kind]).touch()
    (pair_dir / _NOTEBOOK_FILE[kind](pair)).touch()
    return pair_dir


class TestPushNotebookDryRun:
    def test_dry_run_returns_true(self, tmp_path: Path) -> None:
        with patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path):
            result = push_notebook("USDJPY", "eda", dry_run=True)
        assert result is True

    def test_dry_run_does_not_call_kaggle(self, tmp_path: Path) -> None:
        with (
            patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path),
            patch("upload_notebook.run_command") as mock_run,
        ):
            push_notebook("USDJPY", "eda", dry_run=True)
        mock_run.assert_not_called()

    def test_dry_run_modeling_returns_true(self, tmp_path: Path) -> None:
        with patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path):
            result = push_notebook("USDJPY", "modeling", dry_run=True)
        assert result is True


class TestPushNotebookMissingFiles:
    def test_missing_dir_returns_false(self, tmp_path: Path) -> None:
        with patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path):
            result = push_notebook("USDJPY", "eda", dry_run=False)
        assert result is False

    def test_missing_notebook_file_returns_false(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        (pair_dir / "kernel-metadata-eda.json").touch()
        # notebook file (.ipynb) is missing
        with patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path):
            result = push_notebook("USDJPY", "eda", dry_run=False)
        assert result is False

    def test_missing_metadata_returns_false(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        (pair_dir / "USDJPY_eda.ipynb").touch()
        # metadata file is missing
        with patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path):
            result = push_notebook("USDJPY", "eda", dry_run=False)
        assert result is False


class TestPushNotebookSuccess:
    def test_eda_success_returns_true(self, tmp_path: Path) -> None:
        make_pair_dir(tmp_path, "USDJPY", "eda")
        push_ok = make_result(0, stdout="Kernel version 1 successfully pushed.")
        status_ok = make_result(0, stdout="status: KernelWorkerStatus.COMPLETE")
        with (
            patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path),
            patch("upload_notebook.run_command", side_effect=[push_ok, status_ok]),
            patch("upload_notebook.time.sleep"),
        ):
            assert push_notebook("USDJPY", "eda", dry_run=False) is True

    def test_modeling_success_returns_true(self, tmp_path: Path) -> None:
        make_pair_dir(tmp_path, "USDJPY", "modeling")
        push_ok = make_result(0)
        status_ok = make_result(0, stdout="status: KernelWorkerStatus.COMPLETE")
        with (
            patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path),
            patch("upload_notebook.run_command", side_effect=[push_ok, status_ok]),
            patch("upload_notebook.time.sleep"),
        ):
            assert push_notebook("USDJPY", "modeling", dry_run=False) is True

    def test_push_error_string_returns_false(self, tmp_path: Path) -> None:
        make_pair_dir(tmp_path, "USDJPY", "eda")
        push_fail = make_result(0, stderr="Kernel push error: invalid notebook")
        with (
            patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path),
            patch("upload_notebook.run_command", return_value=push_fail),
        ):
            assert push_notebook("USDJPY", "eda", dry_run=False) is False

    def test_nonzero_exit_returns_false(self, tmp_path: Path) -> None:
        make_pair_dir(tmp_path, "USDJPY", "eda")
        push_fail = make_result(1)
        with (
            patch("upload_notebook.NOTEBOOKS_ROOT", tmp_path),
            patch("upload_notebook.run_command", return_value=push_fail),
        ):
            assert push_notebook("USDJPY", "eda", dry_run=False) is False


class TestWaitForKernel:
    def test_dry_run_returns_true(self) -> None:
        with patch("upload_notebook.run_command") as mock_run:
            result = wait_for_kernel("some/slug", dry_run=True)
        assert result is True
        mock_run.assert_not_called()

    def test_completes_returns_true(self) -> None:
        complete = make_result(0, stdout="status: KernelWorkerStatus.COMPLETE")
        with (
            patch("upload_notebook.run_command", return_value=complete),
            patch("upload_notebook.time.sleep"),
        ):
            assert wait_for_kernel("some/slug", dry_run=False) is True

    def test_error_returns_false(self) -> None:
        error = make_result(0, stdout="status: KernelWorkerStatus.ERROR")
        with (
            patch("upload_notebook.run_command", return_value=error),
            patch("upload_notebook.time.sleep"),
        ):
            assert wait_for_kernel("some/slug", dry_run=False) is False

    def test_timeout_returns_false(self) -> None:
        running = make_result(0, stdout="status: KernelWorkerStatus.RUNNING")
        with (
            patch("upload_notebook.run_command", return_value=running),
            patch("upload_notebook.time.sleep"),
            patch("upload_notebook.time.monotonic", side_effect=[0, 0, 9999, 9999]),
        ):
            assert wait_for_kernel("some/slug", dry_run=False, timeout_sec=100) is False

    def test_retries_until_complete(self) -> None:
        running = make_result(0, stdout="status: KernelWorkerStatus.RUNNING")
        complete = make_result(0, stdout="status: KernelWorkerStatus.COMPLETE")
        with (
            patch("upload_notebook.run_command", side_effect=[running, running, complete]),
            patch("upload_notebook.time.sleep") as mock_sleep,
            patch("upload_notebook.time.monotonic", return_value=0),
        ):
            result = wait_for_kernel("some/slug", dry_run=False, poll_sec=10)
        assert result is True
        assert mock_sleep.call_count == 2


class TestGetSlug:
    def test_eda_returns_notebook_slug(self) -> None:
        from common import notebook_slug
        from upload_notebook import _get_slug

        assert _get_slug("USDJPY", "eda") == notebook_slug("USDJPY")

    def test_modeling_returns_modeling_slug(self) -> None:
        from common import modeling_notebook_slug
        from upload_notebook import _get_slug

        assert _get_slug("USDJPY", "modeling") == modeling_notebook_slug("USDJPY")

    def test_utils_returns_utils_slug(self) -> None:
        from common import utils_slug
        from upload_notebook import _get_slug

        assert _get_slug("any", "utils") == utils_slug()

    def test_getting_started_returns_getting_started_slug(self) -> None:
        from create_notebook_getting_started import getting_started_slug
        from upload_notebook import _get_slug

        assert _get_slug("USDJPY", "getting-started") == getting_started_slug("USDJPY")

    def test_pipeline_returns_pipeline_slug(self) -> None:
        from common import pipeline_notebook_slug
        from upload_notebook import _get_slug

        assert _get_slug("any", "pipeline") == pipeline_notebook_slug()
