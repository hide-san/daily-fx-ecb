# Daily FX

A fully automated pipeline that fetches daily FX cross rates from the
European Central Bank, computes per-pair datasets, and publishes both
a dataset and a companion EDA notebook to Kaggle for every currency pair.

**Kaggle series**

- All datasets  → https://www.kaggle.com/datasets?search=YOUR_USERNAME+Daily+FX
- All notebooks → https://www.kaggle.com/code?searchQuery=YOUR_USERNAME+Daily+FX

---

## Pipeline overview

```
Trigger (cron 15:30 UTC weekdays  |  workflow_dispatch)
│
├─ CI (push / PR) ──────────────────── lint · typecheck · test
│
▼
Job 1  fetch          fetch_ecb.py          1 runner
       ECB API → ecb_raw/all_currencies.csv (artifact)
│
▼
Job 2  resolve        resolve_pairs.py      1 runner
       pairs input → pairs_json (GITHUB_OUTPUT)
│
▼
Job 3  calc-and-upload                      N runners  (max-parallel = upload_concurrency)
       For each pair in parallel:
         calc_pair.py        → <PAIR>_daily.csv + dataset-metadata.json
         upload_kaggle.py    → Kaggle dataset  "Daily FX: <PAIR>"
         create_notebook.py  → <PAIR>_eda.ipynb + kernel-metadata.json
         upload_notebook.py  → Kaggle notebook "Daily FX: <PAIR> — EDA & Baseline Forecast"
│
▼
Job 4  summary                              1 runner  (always)
       Markdown result table → GITHUB_STEP_SUMMARY
```

---

## Repository layout

```
.github/
  workflows/
    ci.yml              lint, type-check, and unit tests on every push / PR
    daily_update.yml    the main pipeline (fetch → resolve → calc+upload → summary)

scripts/
  fetch_ecb.py          Job 1 — fetch all EUR rates from the ECB API
  resolve_pairs.py      Job 2 — resolve the pair list into a dynamic matrix JSON
  calc_pair.py          Job 3 — compute one pair's cross rates and ML features
  upload_kaggle.py      Job 3 — upload one pair's dataset to Kaggle
  create_notebook.py    Job 3 — generate the EDA notebook (.ipynb)
  upload_notebook.py    Job 3 — push the notebook to Kaggle Kernels

tests/
  test_resolve_pairs.py
  test_calc_pair.py
  test_upload_kaggle.py

pyproject.toml          ruff, mypy, and pytest configuration
```

---

## Dataset columns

Each pair produces `<PAIR>_daily.csv` with these columns.

| Column | Description |
|---|---|
| `date` | Business day |
| `rate` | Cross rate (units of quote per 1 unit of base) |
| `daily_return_pct` | Day-over-day percentage change |
| `log_return` | Natural log return |
| `ma_7d` | 7-day rolling mean (~1 week) |
| `ma_21d` | 21-day rolling mean (~1 month) |
| `ma_63d` | 63-day rolling mean (~1 quarter) |
| `volatility_20d` | 20-day rolling std of daily returns |
| `year` / `month` / `day_of_week` | Calendar features |

---

## Supported currencies

20 currencies, producing up to 380 directed pairs (e.g. USDJPY and JPYUSD are distinct datasets).

| Code | Name | Country |
|---|---|---|
| USD | US Dollar | United States |
| JPY | Japanese Yen | Japan |
| GBP | Pound Sterling | United Kingdom |
| CHF | Swiss Franc | Switzerland |
| AUD | Australian Dollar | Australia |
| CAD | Canadian Dollar | Canada |
| CNY | Chinese Renminbi | China |
| KRW | South Korean Won | South Korea |
| HKD | Hong Kong Dollar | Hong Kong |
| SGD | Singapore Dollar | Singapore |
| SEK | Swedish Krona | Sweden |
| NOK | Norwegian Krone | Norway |
| DKK | Danish Krone | Denmark |
| NZD | New Zealand Dollar | New Zealand |
| MXN | Mexican Peso | Mexico |
| BRL | Brazilian Real | Brazil |
| INR | Indian Rupee | India |
| ZAR | South African Rand | South Africa |
| TRY | Turkish Lira | Turkey |
| PLN | Polish Zloty | Poland |

---

## Setup

### 1. Fork and clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/daily-fx-ecb.git
cd daily-fx-ecb
```

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Where to get it |
|---|---|
| `KAGGLE_USERNAME` | Your Kaggle username |
| `KAGGLE_KEY` | Kaggle → Account → API → Create New Token |

### 3. Update the Kaggle username in scripts

Replace `YOUR_KAGGLE_USERNAME` in `calc_pair.py` and `create_notebook.py`,
or set it via the `KAGGLE_USERNAME` environment variable (already injected by the workflow).

### 4. Run the pipeline

**Manually** via the GitHub Actions UI:

1. Go to **Actions → Daily ECB FX Pair Pipeline → Run workflow**
2. Fill in the inputs:

| Input | Description | Default |
|---|---|---|
| `pairs` | Comma-separated pairs to process, e.g. `USDJPY,EURUSD` | all pairs |
| `upload_concurrency` | Max parallel Kaggle uploads (1–20) | `5` |
| `dry_run` | `true` to skip Kaggle upload (smoke test) | `false` |

**Automatically** — runs every weekday at 15:30 UTC (00:30 JST), shortly
after ECB publishes rates at ~15:00 UTC.

### 5. Control dataset and notebook visibility

Datasets and notebooks are created with `isPrivate` unset in
`dataset-metadata.json` (Kaggle defaults to private).  
Make them public manually from the Kaggle dataset or notebook page when ready.

---

## Local development

```bash
pip install pandas numpy requests kaggle ruff mypy pytest pytest-cov

# Run all checks
ruff check scripts/ tests/
ruff format --check scripts/ tests/
mypy scripts/
pytest tests/ --cov=scripts --cov-report=term-missing
```

---

## Data source and license

© European Central Bank  
https://data.ecb.europa.eu

Free reuse with attribution under the ECB open data policy.  
Machine learning use (commercial and non-commercial) is permitted.

---

## GitHub migration

### 1. リポジトリを作成する

GitHub で新しいリポジトリを作成します（名前例: `daily-fx-ecb`）。  
「Initialize this repository」は**チェックしない**（空のまま作る）。

### 2. ローカルに clone して push する

```bash
# このチャットで生成したファイル一式をローカルに展開済みとする
cd ecb_fx_collector

git init
git add .
git commit -m "Initial commit: Daily FX ECB pipeline"

git remote add origin https://github.com/YOUR_USERNAME/daily-fx-ecb.git
git branch -M main
git push -u origin main
```

### 3. GitHub Secrets を登録する

**Settings → Secrets and variables → Actions → New repository secret** で2つ追加：

| Secret name | 値の取得先 |
|---|---|
| `KAGGLE_USERNAME` | Kaggle アカウント名 |
| `KAGGLE_KEY` | Kaggle → Account → API → Create New Token |

### 4. 動作確認（dry run）

**Actions → Daily ECB FX Pair Pipeline → Run workflow** で以下を設定して実行：

```
pairs           : USDJPY          ← 1ペアだけで試す
upload_concurrency : 1
dry_run         : true            ← Kaggle へのアップロードをスキップ
```

全ジョブが ✅ になれば設定完了です。

### 5. `KAGGLE_USERNAME` をスクリプトに反映する

`common.py` の `YOUR_KAGGLE_USERNAME` はコードに書かず、  
環境変数 `KAGGLE_USERNAME` から読むようになっています（GitHub Secrets 経由で自動注入）。  
ローカルで実行する場合のみ `.env` などで設定してください。

### 6. 本番実行

`dry_run: false` で再度 Run workflow を実行。  
毎営業日 15:30 UTC（00:30 JST）以降は cron で自動実行されます。
