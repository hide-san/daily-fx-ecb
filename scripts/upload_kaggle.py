"""
scripts/upload_kaggle.py  --pair <BASEQUOTE>
=============================================
Job 3 (upload step) — Upload one pair's dataset to Kaggle.

Behaviour
---------
1. Try create — if the dataset is new it gets created.
2. If the dataset already exists, fall back to version update.

Note on Kaggle CLI 2.0
-----------------------
Exit code 0 is returned even when stdout contains an error message.
We inspect stdout to detect real failures.
"""

import argparse
import sys
from datetime import datetime

from common import (
    DATASETS_ROOT,
    append_github_summary,
    run_command,
)

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_dataset(pair: str, dry_run: bool) -> bool:
    """
    Upload datasets/<pair>/ to Kaggle.

    Tries create first; if the dataset already exists falls back to
    adding a new version.  Handles Kaggle CLI 2.0 quirk where exit code
    is 0 even when stdout contains an error message.

    Returns True on success, False on failure.
    """
    dataset_dir  = DATASETS_ROOT / pair
    version_note = f"Daily update: {datetime.utcnow().strftime('%Y-%m-%d')}"

    if dry_run:
        print(f"[dry-run] Skipping dataset upload for {pair}.")
        return True

    if not dataset_dir.exists():
        print(f"ERROR: {dataset_dir} does not exist.", file=sys.stderr)
        return False

    # --- Try create (works for first-time upload) ---------------------------
    result    = run_command([
        "kaggle", "datasets", "create",
        "--path",     str(dataset_dir),
        "--dir-mode", "zip",
    ])
    output    = (result.stdout + result.stderr).lower()
    create_ok = result.returncode == 0 and "error" not in output

    if create_ok:
        print(f"{pair}: dataset created successfully.")
        return True

    # --- Fall back to version update (dataset already exists) ---------------
    print(f"{pair}: dataset exists — adding new version ...")
    result     = run_command([
        "kaggle", "datasets", "version",
        "--path",     str(dataset_dir),
        "--message",  version_note,
        "--dir-mode", "zip",
    ])
    output     = (result.stdout + result.stderr).lower()
    version_ok = result.returncode == 0 and "error" not in output

    if version_ok:
        print(f"{pair}: version update submitted.")
        return True

    print(f"ERROR: dataset upload failed for {pair}.", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a currency pair dataset to Kaggle."
    )
    parser.add_argument("--pair",    required=True,
                        help="Pair code, e.g. USDJPY")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip upload — useful for testing.")
    args = parser.parse_args()
    pair = args.pair.upper()

    success = upload_dataset(pair, dry_run=args.dry_run)

    status = "uploaded" if success else "upload FAILED"
    append_github_summary(f"| {pair} dataset | {status} |\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
