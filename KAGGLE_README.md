# Daily FX — ECB Pipeline Overview

Daily exchange rates for 20 currency pairs derived from the
[European Central Bank](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
(ECB) EUR reference rates.
Datasets are published every weekday and updated automatically via a GitHub Actions pipeline.

---

## Data source

The ECB publishes daily reference exchange rates for ~40 currencies against the Euro (EUR).
This pipeline fetches those rates and computes cross-rates for every configured pair.

---

## How cross-rates are computed

All ECB rates are quoted as *units of currency X per 1 EUR*.
Cross-rates are derived with a single division:

```
BASE/QUOTE = QUOTE_vs_EUR / BASE_vs_EUR
```

EUR itself is defined as 1.0 (EUR/EUR ≡ 1 by definition).

---

## Dataset columns

| Column | Type | Description |
|---|---|---|
| `date` | date | ECB business day |
| `rate` | float | BASE/QUOTE spot rate |
| `daily_return_pct` | float | Day-over-day % change |
| `log_return` | float | ln(rate[t] / rate[t-1]) |
| `ma_7d` | float | 7-day simple moving average of rate |
| `ma_21d` | float | 21-day simple moving average of rate |
| `ma_63d` | float | 63-day simple moving average of rate (~3 months) |
| `volatility_20d` | float | 20-day rolling std dev of daily returns |
| `year` | int | Calendar year |
| `month` | int | Calendar month (1–12) |
| `day_of_week` | int | Day of week (0 = Monday, 4 = Friday) |

Coverage: **1999-01-04 to present** (ECB data begins 4 January 1999).

---

## Data quality gates

Every dataset passes five automated checks before upload:

| # | Check | Threshold |
|---|---|---|
| 1 | Freshness | Latest date ≤ 5 calendar days old |
| 2 | Minimum rows | ≥ 1,000 rows |
| 3 | No large gaps | No gap > 7 calendar days in the last 30 days |
| 4 | Spike guard | `\|daily_return_pct\|` ≤ 20 % on all rows |
| 5 | No null features | No feature column entirely NaN |

---

## Pipeline architecture

```
ECB API (15:00 UTC)
  └─ fetch_ecb.py          →  ecb_raw/all_currencies.csv
       └─ calc_pair.py     →  datasets/{PAIR}/{PAIR}.csv
            └─ validate_pair.py          (quality gate)
                 └─ upload_dataset.py   →  Kaggle dataset
```

The pipeline runs on GitHub Actions every weekday at 15:30 UTC,
shortly after the ECB publishes its daily reference rates.

Source code: <https://github.com/hide-san/daily-fx-ecb>

---

## Update schedule

| What | When |
|---|---|
| Datasets (rates + features) | Every weekday at 15:30 UTC |
| Notebooks (EDA, modeling, getting started) | Every Monday at 16:00 UTC |

---

## Quick start

```python
import pandas as pd

df = pd.read_csv("/kaggle/input/daily-fx-usd-jpy/USDJPY.csv", parse_dates=["date"])
print(df.tail())
```

---

## License

Data © European Central Bank.
Free reuse with attribution under the
[ECB open data policy](https://www.ecb.europa.eu/home/disclaimer/html/index.en.html).
