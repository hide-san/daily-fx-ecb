"""
scripts/upload_kaggle.py  --pair <BASEQUOTE>
=============================================
Job 3 (upload step) — Upload one pair's dataset to Kaggle and wait
until Kaggle has finished processing it before returning.

Behaviour
---------
1. Upload (version update or first-time create)
2. Poll `kaggle datasets status` until status == "ready"
3. Return True only when the dataset is confirmed ready

The ready-check ensures the dataset is fully indexed before the
notebook push step runs, avoiding a race condition where the notebook
references a dataset that Kaggle is still processing.
"""

import argparse
import sys
import time
from datetime import datetime

from common import (
    DATASETS_ROOT,
    append_github_summary,
    dataset_slug,
    run_command,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# How long to wait for Kaggle to process the upload before giving up.
READY_TIMEOUT_SEC  = 300   # 5 minutes

# How often to poll the status endpoint.
READY_POLL_SEC     = 30

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_dataset(pair: str, dry_run: bool) -> bool:
    """
    Push datasets/<pair>/ to Kaggle as a versioned dataset.

    Returns True if the upload command succeeded, False otherwise.
    Does not wait for processing — call wait_until_ready() after this.
    """
    dataset_dir  = DATASETS_ROOT / pair
    version_note = f"Daily update: {datetime.utcnow().strftime('%Y-%m-%d')}"

    if dry_run:
        print(f"[dry-run] Skipping dataset upload for {pair}.")
        return True

    if not dataset_dir.exists():
        print(f"ERROR: {dataset_dir} does not exist.", file=sys.stderr)
        return False

    # Try create first — works for both new and existing datasets.
    result = run_command(["kaggle", "datasets", "create", ...])
    if result.returncode == 0:
        return True

    # Dataset already exists — add a new version.
    result = run_command(["kaggle", "datasets", "version", ...])
    if result.returncode == 0:
        return True
    print(f"ERROR: dataset upload failed for {pair}.", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Readiness polling
# ---------------------------------------------------------------------------

def wait_until_ready(
    pair: str,
    dry_run: bool,
    timeout_sec: int = READY_TIMEOUT_SEC,
    poll_sec: int    = READY_POLL_SEC,
) -> bool:
    """
    Poll `kaggle datasets status` until the dataset is ready.

    Kaggle processes uploaded files asynchronously (unzipping, indexing).
    This function blocks until the status is "ready" or the timeout
    is reached, which prevents the notebook push from racing against
    an incomplete dataset.

    Returns True when ready, False on timeout or error.
    """
    if dry_run:
        print(f"[dry-run] Skipping readiness check for {pair}.")
        return True

    slug     = dataset_slug(pair)
    deadline = time.monotonic() + timeout_sec
    attempt  = 0

    print(f"Waiting for dataset {slug} to become ready ...")

    while time.monotonic() < deadline:
        attempt += 1
        result = run_command(["kaggle", "datasets", "status", slug])
        output = (result.stdout + result.stderr).lower()

        if "ready" in output:
            print(f"{pair}: dataset is ready (attempt {attempt}).")
            return True

        if "error" in output or "failed" in output:
            print(f"ERROR: dataset processing failed for {pair}:\n{result.stdout}",
                  file=sys.stderr)
            return False

        remaining = int(deadline - time.monotonic())
        print(
            f"  Status: not ready yet — "
            f"retrying in {poll_sec}s (timeout in {remaining}s) ..."
        )
        time.sleep(poll_sec)

    print(
        f"ERROR: {pair} dataset did not become ready within {timeout_sec}s.",
        file=sys.stderr,
    )
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a currency pair dataset to Kaggle and wait until ready."
    )
    parser.add_argument("--pair", required=True, help="Pair code, e.g. USDJPY")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip upload and readiness check — for testing.")
    parser.add_argument("--timeout", type=int, default=READY_TIMEOUT_SEC,
                        help=f"Readiness timeout in seconds (default: {READY_TIMEOUT_SEC})")
    args = parser.parse_args()
    pair = args.pair.upper()

    # Step 1: upload
    uploaded = upload_dataset(pair, dry_run=args.dry_run)
    if not uploaded:
        append_github_summary(f"| {pair} dataset | upload FAILED |\n")
        sys.exit(1)

    # Step 2: wait until Kaggle has finished processing
    ready = wait_until_ready(pair, dry_run=args.dry_run, timeout_sec=args.timeout)

    status = "ready" if ready else "FAILED (timeout)"
    append_github_summary(f"| {pair} dataset | {status} |\n")

    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
