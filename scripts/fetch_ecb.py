"""
scripts/fetch_ecb.py
====================
Job 1 — Fetch all EUR-based daily rates from the ECB API.

Currency discovery
------------------
Instead of maintaining a hardcoded currency list, this script uses the
ECB wildcard key `D.*.EUR.SP00.A` to fetch every currency the ECB
currently publishes.  The resulting CSV becomes the single source of
truth for which currencies are available — downstream scripts read it
rather than relying on any manually maintained list.

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
def fetch_raw_csv(start: str) -> str:
    """
    Request daily EUR spot rates for ALL currencies in one API call.

    Uses the wildcard key `D.*.EUR.SP00.A` so the ECB itself determines
    which currencies are included — no manual list needed.

      D    = daily frequency
      *    = all available currencies (ECB wildcard)
      SP00 = spot rate type
      A    = average rate series

    5xx errors trigger a retry; 4xx errors fail immediately.
    """
    url    = f"{ECB_API_URL}/D.*.EUR.SP00.A"
    params = {"startPeriod": start, "format": "csvdata"}

    log.info("Requesting ECB data for all available currencies ...")
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
    raw_csv = fetch_raw_csv(ECB_START_DATE)
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

