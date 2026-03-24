"""tests/test_fetch_ecb.py"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_ecb import fetch_raw_csv, parse_ecb_csv


def make_response(status_code: int, text: str = "") -> MagicMock:
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.ok          = status_code < 400
    r.text        = text
    r.raise_for_status.side_effect = (
        None if status_code < 400
        else requests.HTTPError(response=r)
    )
    return r


SAMPLE_CSV = (
    "TIME_PERIOD,CURRENCY,OBS_VALUE\n"
    "2024-01-01,USD,1.1\n"
    "2024-01-01,JPY,130.0\n"
    "2024-01-02,USD,1.2\n"
    "2024-01-02,JPY,132.0\n"
)


class TestFetchRawCsvSuccess:
    def test_returns_response_text_on_200(self) -> None:
        ok = make_response(200, text=SAMPLE_CSV)
        with patch("fetch_ecb.requests.get", return_value=ok):
            result = fetch_raw_csv(["USD", "JPY"], "1999-01-01")
        assert result == SAMPLE_CSV

    def test_constructs_correct_url(self) -> None:
        ok = make_response(200, text=SAMPLE_CSV)
        with patch("fetch_ecb.requests.get", return_value=ok) as mock_get:
            fetch_raw_csv(["USD", "JPY"], "1999-01-01")
        url = mock_get.call_args[0][0]
        assert "USD+JPY" in url
        assert "EXR" in url


class TestFetchRawCsvRetry:
    def test_retries_on_timeout_then_succeeds(self) -> None:
        ok = make_response(200, text=SAMPLE_CSV)
        with patch("fetch_ecb.requests.get", side_effect=[requests.Timeout(), ok]):
            result = fetch_raw_csv(["USD"], "1999-01-01")
        assert result == SAMPLE_CSV

    def test_retries_on_500_then_succeeds(self) -> None:
        server_error = make_response(500)
        ok = make_response(200, text=SAMPLE_CSV)
        with patch("fetch_ecb.requests.get", side_effect=[server_error, ok]):
            result = fetch_raw_csv(["USD"], "1999-01-01")
        assert result == SAMPLE_CSV

    def test_raises_immediately_on_400(self) -> None:
        bad_request = make_response(400)
        with patch("fetch_ecb.requests.get", return_value=bad_request):
            with pytest.raises(requests.HTTPError):
                fetch_raw_csv(["USD"], "1999-01-01")

    def test_raises_after_max_attempts(self) -> None:
        with patch("fetch_ecb.requests.get", side_effect=requests.Timeout()):
            with pytest.raises(requests.Timeout):
                fetch_raw_csv(["USD"], "1999-01-01")


class TestParseEcbCsv:
    def test_returns_expected_columns(self) -> None:
        df = parse_ecb_csv(SAMPLE_CSV)
        assert set(df.columns) == {"date", "currency", "rate_vs_eur"}

    def test_row_count(self) -> None:
        df = parse_ecb_csv(SAMPLE_CSV)
        assert len(df) == 4

    def test_sorted_by_currency_then_date(self) -> None:
        df = parse_ecb_csv(SAMPLE_CSV)
        assert list(df["currency"]) == sorted(df["currency"])

    def test_drops_missing_rates(self) -> None:
        csv_with_missing = SAMPLE_CSV + "2024-01-03,USD,\n"
        df = parse_ecb_csv(csv_with_missing)
        assert len(df) == 4
