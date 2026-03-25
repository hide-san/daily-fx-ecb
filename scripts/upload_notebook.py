"""
scripts/upload_notebook.py  --pair <BASEQUOTE>  [--kind eda|modeling|getting-started|utils]
=============================================================================================
Push one pair's notebook (or the shared utils script) to Kaggle Kernels.

--kind eda              pushes the EDA notebook          (default)
--kind modeling         pushes the modeling notebook
--kind getting-started  pushes the Getting Started notebook
--kind utils            pushes the shared fx_utils.py    (--pair not required)

Input
-----
notebooks/<PAIR>/
    <PAIR>_eda.ipynb
    kernel-metadata.json
    <PAIR>_modeling.ipynb
    kernel-metadata-modeling.json
    <PAIR>_getting_started.ipynb
    kernel-metadata-getting-started.json

notebooks/utils/
    fx_utils.py
    kernel-metadata-utils.json
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from common import (
    NOTEBOOKS_ROOT,
    append_github_summary,
    run_command,
    utils_output_dir,
)

# ---------------------------------------------------------------------------
# Kind -> file mapping
# ---------------------------------------------------------------------------

_METADATA_FILE = {
    "eda":             "kernel-metadata.json",
    "modeling":        "kernel-metadata-modeling.json",
    "getting-started": "kernel-metadata-getting-started.json",
    "utils":           "kernel-metadata-utils.json",
}

_NOTEBOOK_FILE = {
    "eda":             lambda pair: f"{pair}_eda.ipynb",
    "modeling":        lambda pair: f"{pair}_modeling.ipynb",
    "getting-started": lambda pair: f"{pair}_getting_started.ipynb",
    "utils":           lambda _: "fx_utils.py",
}


# ---------------------------------------------------------------------------
# Upload logic
# ---------------------------------------------------------------------------

def push_notebook(pair: str, kind: str, dry_run: bool) -> bool:
    """Push the notebook/script for the given kind to Kaggle Kernels."""
    if kind == "utils":
        notebook_dir = utils_output_dir()
    else:
        notebook_dir = NOTEBOOKS_ROOT / pair

    metadata_src = notebook_dir / _METADATA_FILE[kind]
    notebook_src = notebook_dir / _NOTEBOOK_FILE[kind](pair)

    if dry_run:
        print(f"[dry-run] Skipping {kind} upload for {pair}.")
        return True

    for path in (notebook_dir, metadata_src, notebook_src):
        if not path.exists():
            print(f"ERROR: {path} does not exist.", file=sys.stderr)
            return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy(notebook_src,  tmp_path / notebook_src.name)
        shutil.copy(metadata_src,  tmp_path / "kernel-metadata.json")

        result = run_command([
            "kaggle", "kernels", "push",
            "--path", str(tmp_path),
        ])

    output = result.stdout + result.stderr

    # Kaggle CLI sometimes exits 0 but prints an error on stdout/stderr.
    # Collect every known error pattern here so none are silently swallowed.
    _PUSH_ERRORS = (
        "Kernel push error:",
        "could not be added to the kernel",
    )
    push_error = next((msg for msg in _PUSH_ERRORS if msg.lower() in output.lower()), None)

    if result.returncode == 0 and push_error is None:
        print(f"{pair} {kind}: pushed successfully.")
        return True

    reason = push_error or f"exit code {result.returncode}"
    print(f"ERROR: {kind} push failed for {pair} ({reason}).", file=sys.stderr)
    if output.strip():
        print(output.strip(), file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push a Kaggle notebook or script for a currency pair."
    )
    parser.add_argument("--pair",    default="",
                        help="Pair code, e.g. USDJPY (not required for --kind utils)")
    parser.add_argument("--kind",
                        choices=["eda", "modeling", "getting-started", "utils"],
                        default="eda",
                        help="Which asset to push (default: eda)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip the actual push.")
    args = parser.parse_args()

    if args.kind != "utils" and not args.pair:
        parser.error("--pair is required for --kind eda, modeling, and getting-started")

    pair    = args.pair.upper() if args.pair else "UTILS"
    success = push_notebook(pair, kind=args.kind, dry_run=args.dry_run)
    status  = "success" if success else "FAILED"
    append_github_summary(f"| {args.kind} {pair} | {status} |\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
