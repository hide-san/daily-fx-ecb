# Kaggle Dataset Setup — Per Pair Checklist

Complete this checklist once after a new pair dataset is first created.  
None of these settings are overwritten by daily `datasets version` updates.

Open the dataset page → click **Edit** → work top to bottom.

---

## About this file

**Data Explorer → select the CSV → Edit description**

```
Daily BASE/QUOTE cross rate (1999–present) computed from ECB EUR reference rates.
Includes ML-ready features: moving averages (7d / 21d / 63d), log returns, 20-day rolling volatility, and calendar columns.
Updated every business day.
```

---

## Column Descriptions

**Data Explorer → select the CSV → pencil icon next to each column name**

| Column | Description |
|---|---|
| `date` | Trading date (business days only, ECB reference) |
| `rate` | BASE/QUOTE spot rate derived from ECB EUR reference rates |
| `daily_return_pct` | Day-over-day percentage change in the spot rate |
| `log_return` | Natural log of the ratio of consecutive daily rates |
| `ma_7d` | 7-day simple moving average of the spot rate |
| `ma_21d` | 21-day simple moving average of the spot rate |
| `ma_63d` | 63-day simple moving average of the spot rate (~1 quarter) |
| `volatility_20d` | 20-day rolling standard deviation of daily_return_pct |
| `year` | Calendar year extracted from date |
| `month` | Calendar month (1–12) extracted from date |
| `day_of_week` | ISO weekday index: 0=Monday, 4=Friday |

> Replace `BASE/QUOTE` in the `rate` description with the actual pair codes.  
> e.g. for USDJPY → `USD/JPY spot rate derived from ECB EUR reference rates`

---

## See what others are saying about this dataset

Check all **except** `Original` (this is a derived dataset).

- [ ] Clean data ✔
- [ ] Well-documented ✔
- [ ] Ready to use ✔
- [ ] Original — leave unchecked

---

## Coverage

**Edit → Settings → Coverage**

| Field | Value |
|---|---|
| Start date | `1999-01-04` |
| End date | (leave blank) |
| Geographic coverage | see table below |

| Pair | Geo Coverage |
|---|---|
| USDJPY | `United States, Japan` |
| EURUSD | `Eurozone, United States` |
| GBPUSD | `United Kingdom, United States` |
| USDCHF | `United States, Switzerland` |
| AUDUSD | `Australia, United States` |
| USDCAD | `United States, Canada` |
| NZDUSD | `New Zealand, United States` |
| EURJPY | `Eurozone, Japan` |
| EURGBP | `Eurozone, United Kingdom` |
| EURCHF | `Eurozone, Switzerland` |
| EURAUD | `Eurozone, Australia` |
| EURCAD | `Eurozone, Canada` |
| EURNZD | `Eurozone, New Zealand` |
| GBPJPY | `United Kingdom, Japan` |
| GBPCHF | `United Kingdom, Switzerland` |
| GBPAUD | `United Kingdom, Australia` |
| GBPCAD | `United Kingdom, Canada` |
| GBPNZD | `United Kingdom, New Zealand` |
| AUDJPY | `Australia, Japan` |
| CADJPY | `Canada, Japan` |
| CHFJPY | `Switzerland, Japan` |
| NZDJPY | `New Zealand, Japan` |
| AUDCAD | `Australia, Canada` |
| AUDNZD | `Australia, New Zealand` |

---

## Provenance

**Edit → Settings → Provenance**

**Sources:**
```
European Central Bank (ECB) — EUR Foreign Exchange Reference Rates
```

**Collection Methodology:**
```
Daily EUR reference rates published by the European Central Bank via the ECB Data Portal API.
Cross rates are computed as QUOTE/BASE from EUR-based rates.
Data is fetched automatically every business day at approximately 15:00 UTC via GitHub Actions.
```

**Citation — Title:**
```
ECB Foreign Exchange Reference Rates
```

**Citation — URL:**
```
https://data.ecb.europa.eu/data/datasets/EXR
```

---

## Settings

**Edit → Settings**

| Item | Action |
|---|---|
| Expected Update Frequency | Select **Daily** |
| Link Sharing | Turn **ON** |
| Visibility | Set manually (Public or Private as needed) |
| Cover Image | Upload `datasets/<PAIR>/<PAIR>.png` — also available under GitHub Actions → latest run → Artifacts → `<PAIR>-cover-<run_id>` |

---

## Notebooks

Make each notebook public manually if needed.

| Notebook | URL pattern |
|---|---|
| EDA | `kaggle.com/code/YOUR_USERNAME/daily-fx-PAIR-eda-baseline-forecast` |
| Modeling | `kaggle.com/code/YOUR_USERNAME/daily-fx-PAIR-arima-garch-modeling` |
| Utils (once only) | `kaggle.com/code/YOUR_USERNAME/daily-fx-utils` |
