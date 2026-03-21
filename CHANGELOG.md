# Changelog

All structural changes are recorded here manually.
Daily data updates are appended automatically by the pipeline.

---

## 2026-03-21 — Initial release

- 20 currencies via ECB wildcard API (auto-discovered, no hardcoded list)
- Dataset columns: `date`, `rate`, `daily_return_pct`, `log_return`,
  `ma_7d`, `ma_21d`, `ma_63d`, `volatility_20d`, `year`, `month`, `day_of_week`
- Cover image (1280×640 PNG) per dataset
- EDA notebook + ARIMA/GARCH modeling notebook per pair
- GitHub Actions pipeline: fetch → resolve → calc + validate + upload
- Data quality gate: freshness, row count, gap check, spike guard, null check
