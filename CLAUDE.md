# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Lint & format
ruff check scripts/ tests/
ruff format --check scripts/ tests/

# Type check
mypy scripts/

# Run all tests with coverage
pytest tests/ --cov=scripts --cov-report=term-missing

# Run a single test file
pytest tests/test_calc_pair.py -v

# Run tests matching a name pattern
pytest tests/ -k "calc_pair" -v
```

Coverage minimum is 80% (enforced in CI). `generate_cover.py` is excluded from coverage.

## Architecture

This is a fully automated pipeline that fetches ECB FX data and publishes per-pair datasets and notebooks to Kaggle via GitHub Actions.

### Pipeline flow

**Daily update** (weekdays 15:30 UTC):
1. `fetch_ecb.py` — pulls EUR reference rates for 20 currencies from the ECB API → `ecb_raw/all_currencies.csv`
2. `resolve_pairs.py` — resolves `pairs.txt` (or all permutations) into a GitHub Actions matrix
3. Per pair (parallelized): `calc_pair.py` → `validate_pair.py` → `upload_kaggle.py`
4. `generate_cover.py` — generates 1280×640 PNG cover image (independent, continue-on-error)

**Notebook update** (Mondays 16:00 UTC):
- `create_utils_script.py` → `upload_notebook.py --kind utils` (once)
- `create_getting_started.py` → `upload_notebook.py --kind getting-started` (per pair)
- `create_notebook.py` → `upload_notebook.py --kind eda` (per pair)
- `create_modeling_notebook.py` → `upload_notebook.py --kind modeling` (per pair)

### Cross-rate computation

All ECB rates are EUR-based. Cross rates are computed as:
```
cross_rate = QUOTE_vs_EUR / BASE_vs_EUR
```
EUR base is special-cased to 1.0.

### Data shape

Every dataset CSV has 11 columns:
```
date, rate, daily_return_pct, log_return, ma_7d, ma_21d, ma_63d, volatility_20d, year, month, day_of_week
```

### Validation gates (`validate_pair.py`)

Five checks run before upload (exit code 1 if any fail):
1. Latest date ≤ 5 days old
2. ≥ 1,000 rows
3. No gap > 7 calendar days in the last 30 days
4. `abs(daily_return_pct) ≤ 20%` on all rows
5. No feature column entirely NaN

### Shared utilities (`scripts/common.py`)

All scripts import helpers from here: `parse_pair()`, slug/title/metadata builders, `notebook_output_dir()`, `utils_output_dir()`, `append_github_summary()`, `run_command()`, and Kaggle metadata constants/validators. The `KAGGLE_USER` is read from the `KAGGLE_USERNAME` or `KAGGLE_USER` env var.

### Kaggle metadata constraints

- Title: 6–50 chars
- Subtitle: 20–80 chars
- Keywords: ≤ 20

These are validated in `common.validate_kaggle_metadata()` and used across all upload scripts.

### Test file conventions

Each test file corresponds 1:1 with a script: `test_{script_name}.py`. The test files in `tests/` mirror the scripts in `scripts/`.

### Environment variables used at runtime

| Variable | Purpose |
|---|---|
| `KAGGLE_USERNAME` / `KAGGLE_USER` | Kaggle identity |
| `KAGGLE_API_TOKEN` | Auth for Kaggle CLI |
| `GITHUB_OUTPUT` | Workflow outputs (pairs_json, pair_count) |
| `GITHUB_STEP_SUMMARY` | Markdown appended by each job |
