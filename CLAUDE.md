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

Coverage minimum is 80% (enforced in CI). `create_cover.py` is excluded from coverage.

## Coding constraints

- **Comments must be in English.** No Japanese or other non-ASCII languages in comments, docstrings, or string literals inside code.
- **No multi-byte characters in source files.** All `.py` and workflow `.yml` files must use ASCII only. Multi-byte characters in data files (e.g. CSVs) are out of scope for this rule.

## Architecture

This is a fully automated pipeline that fetches ECB FX data and publishes per-pair datasets and notebooks to Kaggle via GitHub Actions.

### Pipeline flow

**Daily update** (weekdays 15:30 UTC):
1. `fetch_ecb.py` — pulls EUR reference rates for 20 currencies from the ECB API → `ecb_raw/all_currencies.csv`
2. `resolve_pairs.py` — resolves `pairs.txt` (or all permutations) into a GitHub Actions matrix
3. Per pair (parallelized): `calc_pair.py` → `validate_pair.py` → `upload_dataset.py`
4. `create_cover.py` — generates 1280×640 PNG cover image (independent, continue-on-error)

**Notebook update** (Mondays 16:00 UTC):
- `create_utils_script.py` → `upload_notebook.py --kind utils` (once)
- `create_notebook_pipeline.py` → `upload_notebook.py --kind pipeline` (once)
- Per pair: getting-started → eda → modeling pushed sequentially within one job

**Kaggle CPU session limit — do not break this constraint:**
Kaggle allows a limited number of concurrent CPU kernel sessions. The notebook
pipeline is intentionally structured so that all three notebook kinds
(getting-started, eda, modeling) are pushed **sequentially within a single
per-pair job**, and the number of parallel pairs is capped by `max-parallel`
(default 3). This keeps concurrent Kaggle sessions at `max-parallel` at most.
Do NOT split the notebook kinds into separate parallel jobs or workflows —
doing so multiplies the concurrent session count by the number of kinds and
will exceed the Kaggle CPU limit.

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
