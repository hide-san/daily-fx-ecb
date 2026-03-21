"""
tests/test_upload_kaggle.py
============================
Unit tests for scripts/upload_kaggle.py

Kaggle CLI calls and time.sleep are mocked so no credentials,
network access, or real waiting are needed.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from upload_kaggle import upload_dataset, wait_until_ready

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_result(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.returncode = returncode
    r.stdout     = stdout
    r.stderr     = stderr
    return r


# ---------------------------------------------------------------------------
# upload_dataset — dry run
# ---------------------------------------------------------------------------

class TestUploadDryRun:
    def test_returns_true_without_calling_kaggle(self, tmp_path: Path) -> None:
        with patch("upload_kaggle.run_command") as mock_run:
            result = upload_dataset("USDJPY", dry_run=True)
        assert result is True
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# upload_dataset — version update
# ---------------------------------------------------------------------------

class TestVersionUpdate:
    def test_success_returns_true(self, tmp_path: Path) -> None:
        (tmp_path / "USDJPY").mkdir()
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path), \
             patch("upload_kaggle.run_command", return_value=make_result(0)):
            assert upload_dataset("USDJPY", dry_run=False) is True

    def test_unknown_error_returns_false(self, tmp_path: Path) -> None:
        (tmp_path / "USDJPY").mkdir()
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path), \
             patch("upload_kaggle.run_command", return_value=make_result(1, stderr="500")):
            assert upload_dataset("USDJPY", dry_run=False) is False


# ---------------------------------------------------------------------------
# upload_dataset — first-time creation
# ---------------------------------------------------------------------------

class TestFirstTimeCreation:
    def test_falls_back_to_create_on_404(self, tmp_path: Path) -> None:
        (tmp_path / "USDJPY").mkdir()
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path), \
             patch("upload_kaggle.run_command",
                   side_effect=[make_result(1, stderr="404"), make_result(0)]):
            assert upload_dataset("USDJPY", dry_run=False) is True

    def test_returns_false_when_create_fails(self, tmp_path: Path) -> None:
        (tmp_path / "USDJPY").mkdir()
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path), \
             patch("upload_kaggle.run_command",
                   side_effect=[make_result(1, stderr="404"),
                                 make_result(1, stderr="permission denied")]):
            assert upload_dataset("USDJPY", dry_run=False) is False


# ---------------------------------------------------------------------------
# upload_dataset — missing directory
# ---------------------------------------------------------------------------

class TestMissingDirectory:
    def test_returns_false_when_dir_missing(self, tmp_path: Path) -> None:
        with patch("upload_kaggle.DATASETS_ROOT", tmp_path):
            assert upload_dataset("USDJPY", dry_run=False) is False


# ---------------------------------------------------------------------------
# wait_until_ready — dry run
# ---------------------------------------------------------------------------

class TestWaitDryRun:
    def test_returns_true_without_polling(self) -> None:
        with patch("upload_kaggle.run_command") as mock_run:
            result = wait_until_ready("USDJPY", dry_run=True)
        assert result is True
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# wait_until_ready — polling behaviour
# ---------------------------------------------------------------------------

class TestWaitUntilReady:
    def test_returns_true_when_immediately_ready(self) -> None:
        ready_result = make_result(0, stdout="Status: ready")
        with patch("upload_kaggle.run_command", return_value=ready_result), \
             patch("upload_kaggle.time.sleep"):
            assert wait_until_ready("USDJPY", dry_run=False) is True

    def test_retries_until_ready(self) -> None:
        """Returns True after two 'not ready' responses followed by 'ready'."""
        not_ready = make_result(0, stdout="Status: running")
        ready     = make_result(0, stdout="Status: ready")
        with patch("upload_kaggle.run_command",
                   side_effect=[not_ready, not_ready, ready]), \
             patch("upload_kaggle.time.sleep") as mock_sleep:
            result = wait_until_ready("USDJPY", dry_run=False, poll_sec=30)
        assert result is True
        assert mock_sleep.call_count == 2   # slept twice before ready

    def test_returns_false_on_processing_error(self) -> None:
        error_result = make_result(0, stdout="Status: error — processing failed")
        with patch("upload_kaggle.run_command", return_value=error_result), \
             patch("upload_kaggle.time.sleep"):
            assert wait_until_ready("USDJPY", dry_run=False) is False

    def test_returns_false_on_timeout(self) -> None:
        """Never becomes ready — should fail after timeout."""
        not_ready = make_result(0, stdout="Status: running")
        with patch("upload_kaggle.run_command", return_value=not_ready), \
             patch("upload_kaggle.time.sleep"), \
             patch("upload_kaggle.time.monotonic",
                   side_effect=[0, 0, 9999, 9999]):
            # monotonic: start=0, loop-check=0 (enter), loop-check=9999 (exit)
            result = wait_until_ready("USDJPY", dry_run=False, timeout_sec=100)
        assert result is False
