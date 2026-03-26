"""
scripts/resolve_pairs.py
=========================
Job 2 -- Resolve the list of currency pairs to process.
"""

import argparse
import itertools
import json
import os
import sys
from pathlib import Path

import pandas as pd
from common import ECB_RAW_PATH, GITHUB_MATRIX_LIMIT, append_github_summary

PAIRS_FILE = Path("pairs.txt")


def load_available_currencies() -> list[str]:
    df = pd.read_csv(ECB_RAW_PATH, usecols=["currency"])
    return sorted(df["currency"].unique().tolist())


def all_pairs(currencies: list[str]) -> list[str]:
    return [f"{b}{q}" for b, q in itertools.permutations(currencies, 2)]


def load_pairs_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return list(
        dict.fromkeys(
            line.strip().upper()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        )
    )


def parse_pair_input(raw: str) -> list[str]:
    return list(dict.fromkeys(p.strip().upper() for p in raw.split(",") if p.strip()))


def filter_valid_pairs(pairs: list[str], valid_set: set[str]) -> list[str]:
    known = [p for p in pairs if p in valid_set]
    unknown = [p for p in pairs if p not in valid_set]
    if unknown:
        print(f"WARNING: Unrecognised pairs will be skipped: {unknown}", file=sys.stderr)
    return known


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default="")
    args = parser.parse_args()

    currencies_info = "n/a"

    if args.pairs.strip():
        source = "--pairs argument"
        resolved = parse_pair_input(args.pairs)
    elif PAIRS_FILE.exists():
        source = str(PAIRS_FILE)
        resolved = load_pairs_file(PAIRS_FILE)
        print(f"Using {PAIRS_FILE} ({len(resolved)} pairs listed).")
    else:
        source = "all combinations (no pairs.txt found)"
        currencies = load_available_currencies()
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
            f"ERROR: {len(resolved)} pairs exceeds GitHub matrix limit of {GITHUB_MATRIX_LIMIT}.",
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
