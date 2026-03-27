"""
scripts/upload_notebook.py  --pair <BASEQUOTE>  [--kind eda|modeling|lgbm|getting-started|utils|pipeline]
==========================================================================================================
Push one pair's notebook (or a shared kernel) to Kaggle Kernels.

--kind eda              pushes the EDA notebook          (--pair required)
--kind modeling         pushes the modeling notebook     (--pair required)
--kind lgbm             pushes the LightGBM notebook     (--pair required)
--kind getting-started  pushes the Getting Started notebook (--pair required)
--kind utils            pushes the shared fx_utils.py    (--pair not required)
--kind pipeline         pushes the pipeline overview notebook (--pair not required)

Input
-----
notebooks/<PAIR>/
    <PAIR>_eda.ipynb
    kernel-metadata-eda.json
    <PAIR>_modeling.ipynb
    kernel-metadata-modeling.json
    <PAIR>_lgbm.ipynb
    kernel-metadata-lgbm.json
    <PAIR>_getting_started.ipynb
    kernel-metadata-getting-started.json

notebooks/utils/
    fx_utils.py
    kernel-metadata-utils.json

notebooks/pipeline/
    pipeline_overview.ipynb
    kernel-metadata-pipeline.json
"""

import argparse
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from common import (
    NOTEBOOKS_ROOT,
    append_github_summary,
    lgbm_notebook_slug,
    load_public_kernels,
    modeling_notebook_slug,
    notebook_slug,
    pipeline_notebook_output_dir,
    pipeline_notebook_slug,
    run_command,
    utils_output_dir,
    utils_slug,
)

# ---------------------------------------------------------------------------
# Kind -> file mapping
# ---------------------------------------------------------------------------

_METADATA_FILE = {
    "eda": "kernel-metadata-eda.json",
    "modeling": "kernel-metadata-modeling.json",
    "lgbm": "kernel-metadata-lgbm.json",
    "getting-started": "kernel-metadata-getting-started.json",
    "utils": "kernel-metadata-utils.json",
    "pipeline": "kernel-metadata-pipeline.json",
}

_NOTEBOOK_FILE: dict[str, Callable[[str], str]] = {
    "eda": lambda pair: f"{pair}_eda.ipynb",
    "modeling": lambda pair: f"{pair}_modeling.ipynb",
    "lgbm": lambda pair: f"{pair}_lgbm.ipynb",
    "getting-started": lambda pair: f"{pair}_getting_started.ipynb",
    "utils": lambda _: "fx_utils.py",
    "pipeline": lambda _: "pipeline_overview.ipynb",
}


# ---------------------------------------------------------------------------
# Slug resolver
# ---------------------------------------------------------------------------


def _get_slug(pair: str, kind: str) -> str:
    """Return the Kaggle kernel slug for the given pair and kind."""
    from create_notebook_getting_started import getting_started_slug

    if kind == "eda":
        return notebook_slug(pair)
    elif kind == "modeling":
        return modeling_notebook_slug(pair)
    elif kind == "lgbm":
        return lgbm_notebook_slug(pair)
    elif kind == "getting-started":
        return getting_started_slug(pair)
    elif kind == "pipeline":
        return pipeline_notebook_slug()
    else:
        return utils_slug()


# ---------------------------------------------------------------------------
# Wait for kernel to finish
# ---------------------------------------------------------------------------


def wait_for_kernel(
    slug: str,
    dry_run: bool,
    poll_sec: int = 30,
    timeout_sec: int = 600,
) -> bool:
    """
    Poll Kaggle until the kernel finishes processing after a push.

    Kaggle queues kernels and runs them asynchronously, so waiting for
    completion before the next push prevents CPU quota errors.

    Returns True if kernel completed successfully, False otherwise.
    """
    if dry_run:
        print(f"[dry-run] Skipping wait for {slug}.")
        return True

    start = time.monotonic()

    while True:
        result = run_command(["kaggle", "kernels", "status", slug])
        output = result.stdout + result.stderr

        # Match exact Kaggle status strings to avoid false positives.
        # e.g. "404 Client Error" contains "error" but means "not ready yet".
        if "KernelWorkerStatus.COMPLETE" in output:
            print(f"{slug}: kernel completed successfully.")
            return True

        if "KernelWorkerStatus.ERROR" in output:
            print(f"ERROR: kernel processing failed for {slug}.", file=sys.stderr)
            return False

        if time.monotonic() - start > timeout_sec:
            print(
                f"ERROR: timed out waiting for {slug} to complete (>{timeout_sec}s).",
                file=sys.stderr,
            )
            return False

        elapsed = int(time.monotonic() - start)
        print(f"{slug}: still running (elapsed {elapsed}s) -- waiting {poll_sec}s ...")
        time.sleep(poll_sec)


# ---------------------------------------------------------------------------
# Upload logic
# ---------------------------------------------------------------------------


def push_notebook(pair: str, kind: str, dry_run: bool) -> bool:
    """Push the notebook/script for the given kind to Kaggle Kernels."""
    if kind == "utils":
        notebook_dir = utils_output_dir()
    elif kind == "pipeline":
        notebook_dir = pipeline_notebook_output_dir()
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
        shutil.copy(notebook_src, tmp_path / notebook_src.name)
        shutil.copy(metadata_src, tmp_path / "kernel-metadata.json")

        print(f"Files in tmp dir: {list(tmp_path.iterdir())}")
        result = run_command(
            [
                "kaggle",
                "kernels",
                "push",
                "--path",
                str(tmp_path),
            ]
        )

    output = result.stdout + result.stderr

    # Kaggle CLI sometimes exits 0 but prints an error on stdout/stderr.
    # Collect every known error pattern here so none are silently swallowed.
    _PUSH_ERRORS = (
        "Kernel push error:",
        "could not be added to the kernel",
    )
    push_error = next((msg for msg in _PUSH_ERRORS if msg.lower() in output.lower()), None)

    if result.returncode != 0 or push_error is not None:
        reason = push_error or f"exit code {result.returncode}"
        print(f"ERROR: {kind} push failed for {pair} ({reason}).", file=sys.stderr)
        if output.strip():
            print(output.strip(), file=sys.stderr)
        return False

    print(f"{pair} {kind}: pushed successfully.")

    # Wait for Kaggle to finish processing the kernel before returning.
    # This prevents CPU quota errors when pushing multiple notebooks in sequence.
    slug = _get_slug(pair, kind)
    return wait_for_kernel(slug, dry_run=dry_run)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push a Kaggle notebook or script for a currency pair."
    )
    parser.add_argument(
        "--pair", default="", help="Pair code, e.g. USDJPY (not required for --kind utils)"
    )
    parser.add_argument(
        "--kind",
        choices=["eda", "modeling", "lgbm", "getting-started", "utils", "pipeline"],
        default="eda",
        help="Which asset to push (default: eda)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip the actual push.")
    parser.add_argument(
        "--poll-sec",
        type=int,
        default=30,
        help="Polling interval in seconds while waiting for kernel (default: 30)",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=600,
        help="Max wait time in seconds for kernel completion (default: 600)",
    )
    args = parser.parse_args()

    if args.kind not in ("utils", "pipeline") and not args.pair:
        parser.error("--pair is required for --kind eda, modeling, lgbm, and getting-started")

    pair = args.pair.upper() if args.pair else args.kind.upper()
    slug = _get_slug(pair, args.kind)
    if slug not in load_public_kernels():
        print(f"Skipping '{slug}': not listed in public_kernels.txt.")
        sys.exit(0)

    success = push_notebook(pair, kind=args.kind, dry_run=args.dry_run)
    status = "success" if success else "FAILED"
    append_github_summary(f"| {args.kind} {pair} | {status} |\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
