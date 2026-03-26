"""tests/test_upload_kaggle.py"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from upload_kaggle import upload_dataset, wait_until_ready


def make_result(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


class TestUploadDryRun:
    def test_returns_true_without_calling_kaggle(self, tmp_path: Path) -> None:
        with patch("upload_kaggle.run_command") as mock_run:
            result = upload_dataset("USDJPY", dry_run=True)
        assert result is True
        mock_run.assert_not_called()


class TestVersionUpdate:
    def test_success_returns_true(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        (pair_dir / "USDJPY.csv").touch()
        (pair_dir / "dataset-metadata.json").write_text("{}")
        with (
            patch("upload_kaggle.DATASETS_ROOT", tmp_path),
            patch("upload_kaggle.run_command", return_value=make_result(0)),
        ):
            assert upload_dataset("USDJPY", dry_run=False) is True

    def test_unknown_error_returns_false(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        (pair_dir / "USDJPY.csv").touch()
        (pair_dir / "dataset-metadata.json").write_text("{}")
        with (
            patch("upload_kaggle.DATASETS_ROOT", tmp_path),
            patch("upload_kaggle.run_command", return_value=make_result(1, stderr="500")),
        ):
            assert upload_dataset("USDJPY", dry_run=False) is False


class TestVersionPath:
    def test_version_update_success_returns_true(self, tmp_path: Path) -> None:
        pair_dir = tmp_path / "USDJPY"
        pair_dir.mkdir()
        (pair_dir / "USDJPY.csv").touch()
        (pair_dir / "dataset-metadata.json").write_text("{}")
        create_fail = make_result(1, stderr="already exists")
        version_ok = make_result(0)
        with (
            patch("upload_kaggle.DATASETS_ROOT", tmp_path),
            patch("upload_kaggle.run_command", side_effect=[create_fail, version_ok]),
        ):
            assert upload_dataset("USDJPY", dry_run=False) is True


class TestMissingDirectory:
    def test_returns_false_when_dir_missing(self, tmp_path: Path) -> None:
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path):
            assert upload_dataset("USDJPY", dry_run=False) is False


class TestWaitDryRun:
    def test_returns_true_without_polling(self) -> None:
        with patch("upload_kaggle.run_command") as mock_run:
            result = wait_until_ready("USDJPY", dry_run=True)
        assert result is True
        mock_run.assert_not_called()


class TestWaitUntilReady:
    def test_returns_true_when_immediately_ready(self) -> None:
        ready_result = make_result(0, stdout="Status: ready")
        with (
            patch("upload_kaggle.run_command", return_value=ready_result),
            patch("upload_kaggle.time.sleep"),
        ):
            assert wait_until_ready("USDJPY", dry_run=False) is True

    def test_retries_until_ready(self) -> None:
        not_ready = make_result(0, stdout="Status: running")
        ready = make_result(0, stdout="Status: ready")
        with (
            patch("upload_kaggle.run_command", side_effect=[not_ready, not_ready, ready]),
            patch("upload_kaggle.time.sleep") as mock_sleep,
        ):
            result = wait_until_ready("USDJPY", dry_run=False, poll_sec=30)
        assert result is True
        assert mock_sleep.call_count == 2

    def test_returns_false_on_processing_error(self) -> None:
        error_result = make_result(0, stdout="Status: error -- processing failed")
        with (
            patch("upload_kaggle.run_command", return_value=error_result),
            patch("upload_kaggle.time.sleep"),
        ):
            assert wait_until_ready("USDJPY", dry_run=False) is False

    def test_returns_false_on_timeout(self) -> None:
        not_ready = make_result(0, stdout="Status: running")
        with (
            patch("upload_kaggle.run_command", return_value=not_ready),
            patch("upload_kaggle.time.sleep"),
            patch("upload_kaggle.time.monotonic", side_effect=[0, 0, 9999, 9999]),
        ):
            result = wait_until_ready("USDJPY", dry_run=False, timeout_sec=100)
        assert result is False
