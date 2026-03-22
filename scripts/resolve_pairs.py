"""
scripts/resolve_pairs.py
=========================
Job 2 — Resolve the list of currency pairs to process.

Priority order for pair selection
----------------------------------
1. --pairs argument  — explicit list (workflow_dispatch)
2. pairs.txt         — default list for scheduled runs
3. all combinations  — fallback (requires ECB CSV)

ECB CSV is only loaded for priority 3 (fallback).
Priorities 1 and 2 work without the ECB CSV, so this script
can run in the notebook pipeline without a fetch step.

Inputs (via CLI args)
---------------------
--pairs   Comma-separated pair codes (e.g. USDJPY,EURUSD).
          Empty = use pairs.txt (if present) or all combinations.

Output (written to $GITHUB_OUTPUT)
-----------------------------------
pairs_json   JSON array of pair strings
pair_count   Total number of pairs to process
"""

import argparse
import itertools
import json
import os
import sys
from pathlib import Path

import pandas as pd

from common import ECB_RAW_PATH, GITHUB_MATRIX_LIMIT, append_github_summary

# Path to the default pairs file — relative to the repo root.
PAIRS_FILE = Path("pairs.txt")

# ---------------------------------------------------------------------------
# Currency discovery — only used as fallback when no pairs source is set
# ---------------------------------------------------------------------------

def load_available_currencies() -> list[str]:
    """Read currencies from the ECB raw CSV produced by fetch_ecb.py."""
    df = pd.read_csv(ECB_RAW_PATH, usecols=["currency"])
    return sorted(df["currency"].unique().tolist())

# ---------------------------------------------------------------------------
# Pair generation and validation
# ---------------------------------------------------------------------------

def all_pairs(currencies: list[str]) -> list[str]:
    """Return every directed pair (USDJPY and JPYUSD are treated as distinct)."""
    return [f"{b}{q}" for b, q in itertools.permutations(currencies, 2)]


def load_pairs_file(path: Path) -> list[str]:
    """
    Read pairs.txt and return a clean, deduplicated list.

    Lines starting with # and blank lines are ignored.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    return list(dict.fromkeys(
        line.strip().upper()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ))


def parse_pair_input(raw: str) -> list[str]:
    """
    Parse a comma-separated pair string into a clean, deduplicated list.

    Accepts mixed case and surrounding whitespace.
    """
    return list(dict.fromkeys(
        p.strip().upper()
        for p in raw.split(",")
        if p.strip()
    ))


def filter_valid_pairs(pairs: list[str], valid_set: set[str]) -> list[str]:
    """Return only recognised pairs; warn about any unknown ones."""
    known   = [p for p in pairs if p in valid_set]
    unknown = [p for p in pairs if p not in valid_set]

    if unknown:
        print(f"WARNING: Unrecognised pairs will be skipped: {unknown}", file=sys.stderr)

    return known

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve currency pairs and write a GitHub Actions matrix."
    )
    parser.add_argument(
        "--pairs", default="",
        help=(
            "Comma-separated pair codes (e.g. USDJPY,EURUSD). "
            "Empty = use pairs.txt (if present) or all combinations."
        ),
    )
    args = parser.parse_args()

    currencies_info = "n/a"   # shown in summary; only set when ECB CSV is read

    if args.pairs.strip():
        # Priority 1: --pairs argument — no ECB CSV needed.
        source   = "--pairs argument"
        resolved = parse_pair_input(args.pairs)

    elif PAIRS_FILE.exists():
        # Priority 2: pairs.txt — no ECB CSV needed.
        source   = str(PAIRS_FILE)
        resolved = load_pairs_file(PAIRS_FILE)
        print(f"Using {PAIRS_FILE} ({len(resolved)} pairs listed).")

    else:
        # Priority 3: all combinations — requires ECB CSV.
        source          = "all combinations (no pairs.txt found)"
        currencies      = load_available_currencies()
        currencies_info = str(len(currencies))
        print(f"Available currencies ({len(currencies)}): {currencies}")
        resolved = all_pairs(currencies)

    print(f"Source  : {source}")
    print(f"Resolved: {len(resolved)} pairs.")

    if not resolved:
        print("ERROR: No valid pairs to process.", file=sys.stderr)
        sys.exit(1)

    if len(resolved) > GITHUB_MATRIX_LIMIT:
        print(
            f"ERROR: {len(resolved)} pairs exceeds GitHub's matrix limit of "
            f"{GITHUB_MATRIX_LIMIT}. Narrow the list in pairs.txt or use --pairs.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/null")
    with open(output_path, "a") as fh:
        fh.write(f"pairs_json={json.dumps(resolved)}\n")
        fh.write(f"pair_count={len(resolved)}\n")

    append_github_summary(
        f"### Resolved pairs\n"
        f"- Source              : {source}\n"
        f"- Currencies available: {currencies_info}\n"
        f"- Pairs resolved      : {len(resolved)}\n"
        f"- Pairs               : {', '.join(resolved)}\n"
    )


if __name__ == "__main__":
    main()
