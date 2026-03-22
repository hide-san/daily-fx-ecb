"""
scripts/upload_notebook.py  --pair <BASEQUOTE>  [--kind eda|modeling]
======================================================================
Push one pair's notebook to Kaggle Kernels.

--kind eda       pushes the EDA notebook       (default)
--kind modeling  pushes the modeling notebook

`kaggle kernels push` reads kernel-metadata.json from the given path.
We store the two metadata files under distinct names and pass the
correct one directly via a temporary symlink — no fragile file-swapping.

Input
-----
notebooks/<PAIR>/
    <PAIR>_eda.ipynb              EDA notebook
    kernel-metadata.json          EDA kernel metadata
    <PAIR>_modeling.ipynb         modeling notebook
    kernel-metadata-modeling.json modeling kernel metadata
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
)

# ---------------------------------------------------------------------------
# Upload logic
# ---------------------------------------------------------------------------

_METADATA_FILE = {
    "eda":      "kernel-metadata.json",
    "modeling": "kernel-metadata-modeling.json",
}

_NOTEBOOK_FILE = {
    "eda":      lambda pair: f"{pair}_eda.ipynb",
    "modeling": lambda pair: f"{pair}_modeling.ipynb",
}


def push_notebook(pair: str, kind: str, dry_run: bool) -> bool:
    """
    Push the notebook for the given kind to Kaggle Kernels.

    To avoid fragile in-place file manipulation, we copy the two
    relevant files (notebook + metadata) into a clean temp directory
    and push from there.  Kaggle CLI always reads kernel-metadata.json
    from the push path, so the metadata is renamed in the temp copy.

    Returns True on success, False on failure.
    """
    notebook_dir  = NOTEBOOKS_ROOT / pair
    metadata_src  = notebook_dir / _METADATA_FILE[kind]
    notebook_src  = notebook_dir / _NOTEBOOK_FILE[kind](pair)

    if dry_run:
        print(f"[dry-run] Skipping {kind} notebook upload for {pair}.")
        return True

    for path in (notebook_dir, metadata_src, notebook_src):
        if not path.exists():
            print(f"ERROR: {path} does not exist.", file=sys.stderr)
            return False

    # Stage files in a temp directory so we never mutate the source tree.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy(notebook_src,  tmp_path / notebook_src.name)
        shutil.copy(metadata_src,  tmp_path / "kernel-metadata.json")

        result = run_command([
            "kaggle", "kernels", "push",
            "--path", str(tmp_path),
        ])

    if result.returncode == 0:
        output = result.stdout + result.stderr
        # "could not be added to the kernel" means dataset sources failed to link.
        # Tag warnings ("not valid tags") are harmless — do not treat as failure.
        if "could not be added to the kernel" in output:
            print(
                f"ERROR: {kind} notebook dataset source failed for {pair}:\n{output}",
                file=sys.stderr,
            )
            return False
        print(f"{pair} {kind} notebook: pushed successfully.")
        return True

    print(f"ERROR: {kind} notebook push failed for {pair}.", file=sys.stderr)
    return False

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push a Kaggle notebook for one currency pair."
    )
    parser.add_argument("--pair",  required=True,
                        help="Pair code, e.g. USDJPY")
    parser.add_argument("--kind",  choices=["eda", "modeling"], default="eda",
                        help="Which notebook to push (default: eda)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip the actual push — useful for testing.")
    args = parser.parse_args()
    pair = args.pair.upper()

    success = push_notebook(pair, kind=args.kind, dry_run=args.dry_run)
    status  = "success" if success else "FAILED"
    append_github_summary(f"| {pair} {args.kind} notebook | {status} |\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
