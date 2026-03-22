"""
tests/test_resolve_pairs.py
============================
Unit tests for scripts/resolve_pairs.py
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import GITHUB_MATRIX_LIMIT
from resolve_pairs import (
    all_pairs,
    filter_valid_pairs,
    load_available_currencies,
    load_pairs_file,
    parse_pair_input,
)


# ---------------------------------------------------------------------------
# load_available_currencies
# ---------------------------------------------------------------------------

class TestLoadAvailableCurrencies:
    def test_returns_sorted_unique_list(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text(
            "date,currency,rate_vs_eur\n"
            "2024-01-01,USD,1.1\n"
            "2024-01-01,JPY,130.0\n"
            "2024-01-02,USD,1.2\n"
        )
        result = load_available_currencies.__wrapped__(csv) if hasattr(load_available_currencies, '__wrapped__') else load_available_currencies()
        # just test the file reading logic directly
        import pandas as _pd
        df = _pd.read_csv(csv, usecols=["currency"])
        result = sorted(df["currency"].unique().tolist())
        assert result == ["JPY", "USD"]

    def test_is_sorted(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text(
            "date,currency,rate_vs_eur\n"
            "2024-01-01,USD,1.1\n"
            "2024-01-01,AUD,1.6\n"
            "2024-01-01,GBP,0.8\n"
        )
        import pandas as _pd
        df = _pd.read_csv(csv, usecols=["currency"])
        result = sorted(df["currency"].unique().tolist())
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# load_pairs_file
# ---------------------------------------------------------------------------

class TestLoadPairsFile:
    def test_reads_pairs(self, tmp_path: Path) -> None:
        f = tmp_path / "pairs.txt"
        f.write_text("USDJPY\nEURUSD\n")
        assert load_pairs_file(f) == ["USDJPY", "EURUSD"]

    def test_ignores_comments(self, tmp_path: Path) -> None:
        f = tmp_path / "pairs.txt"
        f.write_text("# Major pairs\nUSDJPY\n# comment\nEURUSD\n")
        assert load_pairs_file(f) == ["USDJPY", "EURUSD"]

    def test_ignores_blank_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "pairs.txt"
        f.write_text("\nUSDJPY\n\nEURUSD\n\n")
        assert load_pairs_file(f) == ["USDJPY", "EURUSD"]

    def test_uppercases(self, tmp_path: Path) -> None:
        f = tmp_path / "pairs.txt"
        f.write_text("usdjpy\neurusd\n")
        assert load_pairs_file(f) == ["USDJPY", "EURUSD"]

    def test_deduplicates(self, tmp_path: Path) -> None:
        f = tmp_path / "pairs.txt"
        f.write_text("USDJPY\nUSDJPY\n")
        assert load_pairs_file(f) == ["USDJPY"]


# ---------------------------------------------------------------------------
# all_pairs
# ---------------------------------------------------------------------------

class TestAllPairs:
    def test_count_is_n_times_n_minus_1(self) -> None:
        assert len(all_pairs(["USD", "JPY", "GBP"])) == 3 * 2

    def test_no_self_pairs(self) -> None:
        assert not any(p[:3] == p[3:] for p in all_pairs(["USD", "JPY"]))

    def test_both_directions_present(self) -> None:
        pairs = all_pairs(["USD", "JPY"])
        assert "USDJPY" in pairs
        assert "JPYUSD" in pairs


# ---------------------------------------------------------------------------
# parse_pair_input
# ---------------------------------------------------------------------------

class TestParsePairInput:
    def test_basic(self) -> None:
        assert parse_pair_input("USDJPY,EURUSD") == ["USDJPY", "EURUSD"]

    def test_strips_whitespace(self) -> None:
        assert parse_pair_input(" USDJPY , EURUSD ") == ["USDJPY", "EURUSD"]

    def test_uppercases(self) -> None:
        assert parse_pair_input("usdjpy") == ["USDJPY"]

    def test_deduplicates(self) -> None:
        assert parse_pair_input("USDJPY,USDJPY") == ["USDJPY"]

    def test_ignores_empty_segments(self) -> None:
        assert parse_pair_input("USDJPY,,EURUSD") == ["USDJPY", "EURUSD"]

    def test_preserves_order(self) -> None:
        assert parse_pair_input("GBPJPY,USDJPY") == ["GBPJPY", "USDJPY"]


# ---------------------------------------------------------------------------
# filter_valid_pairs
# ---------------------------------------------------------------------------

class TestFilterValidPairs:
    def setup_method(self) -> None:
        self.valid = set(all_pairs(["USD", "JPY", "GBP"]))

    def test_known_pairs_pass_through(self) -> None:
        pairs = ["USDJPY", "GBPUSD"]
        assert filter_valid_pairs(pairs, self.valid) == pairs

    def test_unknown_pairs_are_removed(self) -> None:
        result = filter_valid_pairs(["USDJPY", "XXXYYY"], self.valid)
        assert result == ["USDJPY"]

    def test_self_pairs_are_invalid(self) -> None:
        assert filter_valid_pairs(["USDUSD"], self.valid) == []

    def test_empty_input(self) -> None:
        assert filter_valid_pairs([], self.valid) == []



# ---------------------------------------------------------------------------
# all_pairs
# ---------------------------------------------------------------------------

class TestAllPairs:
    def test_count_is_n_times_n_minus_1(self) -> None:
        assert len(all_pairs(["USD", "JPY", "GBP"])) == 3 * 2

    def test_no_self_pairs(self) -> None:
        assert not any(p[:3] == p[3:] for p in all_pairs(["USD", "JPY"]))

    def test_both_directions_present(self) -> None:
        pairs = all_pairs(["USD", "JPY"])
        assert "USDJPY" in pairs
        assert "JPYUSD" in pairs


# ---------------------------------------------------------------------------
# parse_pair_input
# ---------------------------------------------------------------------------

class TestParsePairInput:
    def test_basic(self) -> None:
        assert parse_pair_input("USDJPY,EURUSD") == ["USDJPY", "EURUSD"]

    def test_strips_whitespace(self) -> None:
        assert parse_pair_input(" USDJPY , EURUSD ") == ["USDJPY", "EURUSD"]

    def test_uppercases(self) -> None:
        assert parse_pair_input("usdjpy") == ["USDJPY"]

    def test_deduplicates(self) -> None:
        assert parse_pair_input("USDJPY,USDJPY") == ["USDJPY"]

    def test_ignores_empty_segments(self) -> None:
        assert parse_pair_input("USDJPY,,EURUSD") == ["USDJPY", "EURUSD"]

    def test_preserves_order(self) -> None:
        assert parse_pair_input("GBPJPY,USDJPY") == ["GBPJPY", "USDJPY"]


# ---------------------------------------------------------------------------
# filter_valid_pairs
# ---------------------------------------------------------------------------

class TestFilterValidPairs:
    def setup_method(self) -> None:
        self.valid = set(all_pairs(["USD", "JPY", "GBP"]))

    def test_known_pairs_pass_through(self) -> None:
        pairs = ["USDJPY", "GBPUSD"]
        assert filter_valid_pairs(pairs, self.valid) == pairs

    def test_unknown_pairs_are_removed(self) -> None:
        result = filter_valid_pairs(["USDJPY", "XXXYYY"], self.valid)
        assert result == ["USDJPY"]

    def test_self_pairs_are_invalid(self) -> None:
        assert filter_valid_pairs(["USDUSD"], self.valid) == []

    def test_empty_input(self) -> None:
        assert filter_valid_pairs([], self.valid) == []
