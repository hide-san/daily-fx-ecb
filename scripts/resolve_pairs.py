"""
scripts/resolve_pairs.py
=========================
Job 2 — Resolve the list of currency pairs to process.

Reads the ECB raw CSV produced by Job 1 to discover which currencies
were successfully fetched, then builds the pair list from that.

Inputs (via CLI args)
---------------------
--pairs   Comma-separated pair codes (e.g. USDJPY,EURUSD).
          Leave empty to process all combinations.

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

import pandas as pd

from common import ECB_RAW_PATH, GITHUB_MATRIX_LIMIT, append_github_summary

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
    Return only recognised pairs; print a warning for any unknown ones.

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
        help="Comma-separated pair codes (e.g. USDJPY,EURUSD). Empty = all pairs.",
    )
    args = parser.parse_args()

    # Discover available currencies from the ECB raw data (produced by Job 1).
    currencies = load_available_currencies()
    print(f"Available currencies ({len(currencies)}): {currencies}")

    valid_set = set(all_pairs(currencies))

    if args.pairs.strip():
        requested = parse_pair_input(args.pairs)
        resolved  = filter_valid_pairs(requested, valid_set)
    else:
        resolved = all_pairs(currencies)

    if not resolved:
        print("ERROR: No valid pairs to process.", file=sys.stderr)
        sys.exit(1)

    if len(resolved) > GITHUB_MATRIX_LIMIT:
        print(
            f"ERROR: {len(resolved)} pairs exceeds GitHub's matrix limit of "
            f"{GITHUB_MATRIX_LIMIT}. Use --pairs to narrow the list.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Resolved {len(resolved)} pairs.")

    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/null")
    with open(output_path, "a") as fh:
        fh.write(f"pairs_json={json.dumps(resolved)}\n")
        fh.write(f"pair_count={len(resolved)}\n")

    append_github_summary(
        f"### Resolved pairs\n"
        f"- Currencies available: {len(currencies)}\n"
        f"- Pairs resolved      : {len(resolved)}\n"
        f"- Pairs               : {', '.join(resolved)}\n"
    )


if __name__ == "__main__":
    main()

