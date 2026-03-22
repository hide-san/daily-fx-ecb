"""
scripts/resolve_pairs.py
=========================
Job 2 — Resolve the list of currency pairs to process.

Priority order for pair selection
----------------------------------
1. --pairs argument  (workflow_dispatch — manual override)
2. pairs.txt         (scheduled runs — default list)
3. all combinations  (fallback if pairs.txt does not exist)

Inputs (via CLI args)
---------------------
--pairs   Comma-separated pair codes (e.g. USDJPY,EURUSD).
          Leave empty to fall back to pairs.txt or all combinations.

Output (written to $GITHUB_OUTPUT)
-----------------------------------
pairs_json   JSON array of pair strings, e.g. ["USDJPY","EURUSD","GBPJPY"]
pair_count   Total number of pairs to process (for the summary log)
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
# Currency discovery — read from the artifact produced by Job 1
# ---------------------------------------------------------------------------

def load_available_currencies() -> list[str]:
    """
    Read the currencies that were actually fetched from the ECB CSV.

    Using the Job 1 artifact as the source ensures the pair list always
    reflects what was successfully retrieved, not a hardcoded assumption.
    """
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
    Returns uppercase pair codes like ["USDJPY", "EURUSD"].
    """
    return list(dict.fromkeys(
        p.strip().upper()
        for p in raw.split(",")
        if p.strip()
    ))


def filter_valid_pairs(pairs: list[str], valid_set: set[str]) -> list[str]:
    """
    Return only recognised pairs; warn about any unknown ones.

    Unknown pairs are printed to stderr so they appear as warnings in
    the GitHub Actions log without failing the job.
    """
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

    # Discover available currencies from the ECB raw data (produced by Job 1).
    currencies = load_available_currencies()
    print(f"Available currencies ({len(currencies)}): {currencies}")

    valid_set = set(all_pairs(currencies))

    if args.pairs.strip():
        # Priority 1: explicit --pairs argument (workflow_dispatch)
        source    = "--pairs argument"
        requested = parse_pair_input(args.pairs)
        resolved  = filter_valid_pairs(requested, valid_set)

    elif PAIRS_FILE.exists():
        # Priority 2: pairs.txt (scheduled runs)
        source    = str(PAIRS_FILE)
        requested = load_pairs_file(PAIRS_FILE)
        resolved  = filter_valid_pairs(requested, valid_set)
        print(f"Using {PAIRS_FILE} ({len(requested)} pairs listed).")

    else:
        # Priority 3: all combinations (fallback)
        source   = "all combinations (no pairs.txt found)"
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
        f"- Currencies available: {len(currencies)}\n"
        f"- Pairs resolved      : {len(resolved)}\n"
        f"- Pairs               : {', '.join(resolved)}\n"
    )


if __name__ == "__main__":
    main()
