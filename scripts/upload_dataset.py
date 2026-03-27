"""
scripts/upload_dataset.py  --pair <BASEQUOTE>
=============================================
Job 3 (upload step) -- Upload one pair's dataset to Kaggle.
"""

import argparse
import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from common import (
    DATASETS_ROOT,
    append_github_summary,
    dataset_slug,
    run_command,
)


def upload_dataset(pair: str, dry_run: bool) -> bool:
    dataset_dir = DATASETS_ROOT / pair
    version_note = f"Daily update: {datetime.now(UTC).strftime('%Y-%m-%d')}"

    if dry_run:
        print(f"[dry-run] Skipping dataset upload for {pair}.")
        return True

    if not dataset_dir.exists():
        print(f"ERROR: {dataset_dir} does not exist.", file=sys.stderr)
        return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy(dataset_dir / f"{pair}.csv", tmp_path / f"{pair}.csv")
        shutil.copy(dataset_dir / "dataset-metadata.json", tmp_path / "dataset-metadata.json")

        result = run_command(
            [
                "kaggle",
                "datasets",
                "create",
                "--path",
                str(tmp_path),
                "--dir-mode",
                "zip",
            ]
        )
        output = (result.stdout + result.stderr).lower()
        create_ok = result.returncode == 0 and "error" not in output

        if create_ok:
            print(f"{pair}: dataset created successfully.")
            return True

        print(f"{pair}: dataset exists -- adding new version ...")
        result = run_command(
            [
                "kaggle",
                "datasets",
                "version",
                "--path",
                str(tmp_path),
                "--message",
                version_note,
                "--dir-mode",
                "zip",
            ]
        )
        output = (result.stdout + result.stderr).lower()
        version_ok = result.returncode == 0 and "error" not in output

        if version_ok:
            print(f"{pair}: version update submitted.")
            return True

    print(f"ERROR: dataset upload failed for {pair}.", file=sys.stderr)
    return False


def wait_until_ready(
    pair: str,
    dry_run: bool,
    poll_sec: int = 30,
    timeout_sec: int = 600,
) -> bool:
    if dry_run:
        print(f"[dry-run] Skipping wait for {pair}.")
        return True

    slug = dataset_slug(pair)
    start = time.monotonic()

    while True:
        result = run_command(["kaggle", "datasets", "status", slug])
        output = (result.stdout + result.stderr).lower()

        if "ready" in output:
            print(f"{pair}: dataset is ready.")
            return True
        if "error" in output:
            print(f"ERROR: dataset processing failed for {pair}.", file=sys.stderr)
            return False
        if time.monotonic() - start > timeout_sec:
            print(f"ERROR: timed out waiting for {pair} to become ready.", file=sys.stderr)
            return False

        print(f"{pair}: not ready yet -- waiting {poll_sec}s ...")
        time.sleep(poll_sec)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    pair = args.pair.upper()

    success = upload_dataset(pair, dry_run=args.dry_run)
    status = "uploaded" if success else "upload FAILED"
    append_github_summary(f"| {pair} dataset | {status} |\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
