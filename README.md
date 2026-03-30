# Daily FX

A fully automated pipeline that fetches daily FX cross rates from the
European Central Bank, computes per-pair datasets, and publishes both
a dataset and companion notebooks to Kaggle for every currency pair.

**Kaggle series**

- All datasets  -> https://www.kaggle.com/datasets?search=YOUR_USERNAME+Daily+FX
- All notebooks -> https://www.kaggle.com/code?searchQuery=YOUR_USERNAME+Daily+FX

---

## Pipeline overview

```
Trigger (cron 15:30 UTC weekdays  |  workflow_dispatch)
|
+- CI (push / PR) ---- lint / typecheck / test
|
v
Job 1  fetch          fetch_ecb.py          1 runner
       ECB API -> ecb_raw/all_currencies.csv
|
v
Job 2  resolve        resolve_pairs.py      1 runner
       pairs input -> pairs_json (GITHUB_OUTPUT)
|
v
Job 3  calc-and-upload                      N runners
       calc_pair.py / validate_pair.py / upload_dataset.py
|
v
Job 4  summary                              1 runner (always)
```

Notebook pipeline (weekly, Mondays 16:00 UTC):

```
resolve -> push-utils (fx_utils.py, once) -> push-notebooks (per pair)
```

---

## Repository layout

```
scripts/
  common.py                 shared constants and helpers
  fetch_ecb.py              Job 1 -- fetch ECB rates
  resolve_pairs.py          Job 2 -- resolve pair list
  calc_pair.py              Job 3 -- compute cross rates + features
  validate_pair.py          Job 3 -- data quality gate
  upload_dataset.py                  Job 3 -- upload dataset to Kaggle
  create_utils_script.py             generate shared fx_utils.py
  create_notebook_eda.py             generate EDA notebook
  create_notebook_modeling.py        generate ARIMA/GARCH notebook
  create_notebook_getting_started.py generate beginner notebook
  upload_notebook.py                 push notebook or utils script to Kaggle

tests/
  test_calc_pair.py
  test_common.py
  test_fetch_ecb.py
  test_resolve_pairs.py
  test_upload_dataset.py
  test_validate_pair.py
```

---

## Shared utility script (fx_utils.py)

All notebooks import helpers from a shared Kaggle Utility Script:

```python
import sys
sys.path.insert(0, "/kaggle/input/daily-fx-utils")
from fx_utils import find_data_dir, apply_plot_style, FEATURE_COLUMNS, get_logger
```

The script is regenerated and pushed automatically by the notebook pipeline.

---

## Setup

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/daily-fx-ecb.git
cd daily-fx-ecb
```

### 2. Add GitHub Secrets

Settings -> Secrets and variables -> Actions:

| Secret | Description |
|---|---|
| `KAGGLE_USERNAME` | Your Kaggle username |
| `KAGGLE_API_TOKEN` | Kaggle -> Account -> API -> Create New Token |

### 3. Dry-run test

Actions -> Daily ECB FX Pair Pipeline -> Run workflow:

```
pairs              : USDJPY
upload_concurrency : 1
dry_run            : true
```

---

## Local development

```bash
pip install -r requirements-dev.txt
ruff check scripts/ tests/
ruff format --check scripts/ tests/
mypy scripts/
pytest tests/ --cov=scripts --cov-report=term-missing
```

---

## Data source

(c) European Central Bank -- https://data.ecb.europa.eu
Free reuse with attribution under the ECB open data policy.
