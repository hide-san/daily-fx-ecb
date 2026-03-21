"""
scripts/fetch_ecb.py
====================
Job 1 — Fetch all EUR-based daily rates from the ECB API.

The ECB SDMX API does not support wildcards in the currency key.
Currencies are listed explicitly in CURRENCIES below.  When the ECB
adds a new currency, add its ISO 4217 code to that list.

Retry policy
------------
The ECB API occasionally times out or returns 5xx errors, especially
around 16:00 CET when rates are first published.  tenacity retries the
request up to 5 times with exponential backoff (2 s → 4 s → 8 s → 16 s),
so transient failures resolve automatically without failing the run.

Output
------
ecb_raw/all_currencies.csv
    date        : business day (YYYY-MM-DD)
    currency    : ISO 4217 code (e.g. USD, JPY)
    rate_vs_eur : spot rate quoted against EUR
"""

import logging
from io import StringIO

import pandas as pd
import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common import (
    ECB_API_URL,
    ECB_START_DATE,
    ECB_RAW_PATH,
    append_github_summary,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Currency list
#
# The ECB SDMX API requires an explicit currency list — wildcards are not
# supported.  Add new ISO 4217 codes here when the ECB introduces them.
# ---------------------------------------------------------------------------

CURRENCIES = [
    "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "CNY", "KRW",
    "HKD", "SGD", "SEK", "NOK", "DKK", "NZD", "MXN", "BRL",
    "INR", "ZAR", "TRY", "PLN",
]

# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------

_RETRYABLE_EXCEPTIONS = (
    requests.Timeout,
    requests.ConnectionError,
    requests.HTTPError,
)

_retry = retry(
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)

# ---------------------------------------------------------------------------
# Fetch and parse
# ---------------------------------------------------------------------------

@_retry
def fetch_raw_csv(currencies: list[str], start: str) -> str:
    """
    Request daily EUR spot rates for the given currencies in one API call.

    ECB SDMX key format:  D.<currencies>.EUR.SP00.A
      D    = daily frequency
      SP00 = spot rate type
      A    = average rate series

    Multiple currencies are joined with '+' (e.g. USD+JPY+GBP).
    5xx errors trigger a retry; 4xx errors fail immediately.
    """
    key    = "+".join(currencies)
    url    = f"{ECB_API_URL}/D.{key}.EUR.SP00.A"
    params = {"startPeriod": start, "format": "csvdata"}

    log.info(f"Requesting ECB data for {len(currencies)} currencies ...")
    response = requests.get(url, params=params, timeout=60)

    if response.status_code >= 500:
        response.raise_for_status()   # triggers retry
    elif not response.ok:
        response.raise_for_status()   # 4xx — fail immediately, no retry

    return response.text


def parse_ecb_csv(raw_csv: str) -> pd.DataFrame:
    """
    Parse the ECB response into a tidy long-format DataFrame.

    Drops rows where the rate is missing (e.g. public holidays).
    """
    df = pd.read_csv(StringIO(raw_csv))

    df = (
        df[["TIME_PERIOD", "CURRENCY", "OBS_VALUE"]]
        .copy()
        .rename(columns={
            "TIME_PERIOD": "date",
            "CURRENCY":    "currency",
            "OBS_VALUE":   "rate_vs_eur",
        })
    )

    df["date"]        = pd.to_datetime(df["date"])
    df["rate_vs_eur"] = pd.to_numeric(df["rate_vs_eur"], errors="coerce")

    return (
        df
        .dropna(subset=["rate_vs_eur"])
        .sort_values(["currency", "date"])
        .reset_index(drop=True)
    )

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    raw_csv = fetch_raw_csv(CURRENCIES, ECB_START_DATE)
    df      = parse_ecb_csv(raw_csv)

    ECB_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ECB_RAW_PATH, index=False)

    discovered = sorted(df["currency"].unique().tolist())
    log.info(f"Saved     : {ECB_RAW_PATH}")
    log.info(f"Rows      : {len(df):,}")
    log.info(f"Currencies: {discovered}")
    log.info(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")

    append_github_summary(
        f"### ECB Fetch\n"
        f"- Currencies : {len(discovered)} — {', '.join(discovered)}\n"
        f"- Latest date: {df['date'].max().date()}\n"
        f"- Total rows : {len(df):,}\n"
    )


if __name__ == "__main__":
    main()

