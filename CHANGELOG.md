# Changelog

## 2026-03-31 -- Daily update (22 pairs)

## 2026-03-30 -- Daily update (22 pairs)

## 2026-03-28 -- Daily update (22 pairs)

## 2026-03-27 -- Daily update (22 pairs)

## 2026-03-26 -- Daily update (1 pairs)

## 2026-03-25 -- Daily update (1 pairs)

All structural changes are recorded here manually.
Daily data updates are appended automatically by the pipeline.

---

## 2026-03-21 -- Initial release

- 20 currencies via ECB API
- ML-ready feature columns per pair
- Cover image (1280x640 PNG) per dataset
- EDA notebook + ARIMA/GARCH modeling notebook per pair
- Shared utility script (fx_utils.py) on Kaggle
- GitHub Actions pipeline: fetch -> resolve -> calc + validate + upload
- Data quality gate: freshness, row count, gap check, spike guard, null check
