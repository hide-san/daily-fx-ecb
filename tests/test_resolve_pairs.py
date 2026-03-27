"""tests/test_resolve_pairs.py"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import load_pairs_file
from resolve_pairs import (
    all_pairs,
    filter_valid_pairs,
    load_available_currencies,
    parse_pair_input,
)


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


class TestAllPairs:
    def test_count_is_n_times_n_minus_1(self) -> None:
        assert len(all_pairs(["USD", "JPY", "GBP"])) == 3 * 2

    def test_no_self_pairs(self) -> None:
        assert not any(p[:3] == p[3:] for p in all_pairs(["USD", "JPY"]))

    def test_both_directions_present(self) -> None:
        pairs = all_pairs(["USD", "JPY"])
        assert "USDJPY" in pairs
        assert "JPYUSD" in pairs


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


class TestLoadAvailableCurrencies:
    def test_returns_sorted_unique_list(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text(
            "date,currency,rate_vs_eur\n"
            "2024-01-01,USD,1.1\n"
            "2024-01-02,USD,1.2\n"
            "2024-01-01,JPY,130.0\n"
        )
        with patch("resolve_pairs.ECB_RAW_PATH", csv):
            currencies = load_available_currencies()
        assert currencies == sorted(set(currencies))
        assert "USD" in currencies
        assert "JPY" in currencies

    def test_deduplicates_currencies(self, tmp_path: Path) -> None:
        csv = tmp_path / "all_currencies.csv"
        csv.write_text("date,currency,rate_vs_eur\n2024-01-01,USD,1.1\n2024-01-02,USD,1.2\n")
        with patch("resolve_pairs.ECB_RAW_PATH", csv):
            currencies = load_available_currencies()
        assert currencies.count("USD") == 1


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


class TestMain:
    def test_main_with_pairs_arg_writes_output(self, tmp_path: Path) -> None:
        import resolve_pairs

        output = tmp_path / "github_output.txt"
        output.touch()
        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["resolve_pairs.py", "--pairs", "USDJPY"]),
            patch.dict(
                os.environ,
                {"GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)},
            ),
        ):
            resolve_pairs.main()
        content = output.read_text()
        assert "USDJPY" in content
        assert "pair_count=1" in content

    def test_main_with_pairs_file(self, tmp_path: Path) -> None:
        import resolve_pairs

        pairs_file = tmp_path / "pairs.txt"
        pairs_file.write_text("USDJPY\n")
        output = tmp_path / "github_output.txt"
        output.touch()
        summary = tmp_path / "summary.md"
        with (
            patch("sys.argv", ["resolve_pairs.py"]),
            patch("resolve_pairs.PAIRS_FILE", pairs_file),
            patch.dict(
                os.environ,
                {"GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": str(summary)},
            ),
        ):
            resolve_pairs.main()
        assert "USDJPY" in output.read_text()
