# Mamaearth returns and revenue pipeline: SQL -> Python -> GenAI

## Overview
This project processes Mamaearth customer, product, and order data through a three-layer pipeline:
1. **SQL Layer**: Defines the database schema and loads seed data to manage the raw records.
2. **Analysis Layer (Python)**: Uses pandas to load, clean, deduplicate, and analyze data to find return rates, time-series trends, and outliers. It strictly ensures no hardcoded numbers are used.
3. **GenAI Layer (Narrator)**: Uses the Google GenAI SDK to generate a final business report. 
Crucially, **no layer reports a number it did not compute or receive from the previous layer.**

## Repo Structure
```
capstone-project-prakitesh/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── generate_narrative.py
    ├── findings.json
    └── sample_output.txt (generated later)
```

## Data Flow Between Layers
- `data/*.csv` -> **SQL Layer** (`sql/`, `mamaearth.db`, `reports.sql`): Validates and stores raw data structure.
- `data/*.csv` -> `analysis/clean_and_eda.py` -> `narrator/findings.json` & `visualizations/*.png`: Part 2 reads the raw CSVs directly, not the database, performs data cleaning, calculates metrics, and produces visual reports and a JSON of key findings.
- `narrator/findings.json` -> `narrator/generate_narrative.py` -> `narrative` & `sample_output.txt`: Generates the automated Situation-Complication-Resolution narrative.

## How to Run (SQL, Analysis, Narrator)

**1. SQL Layer**
First, create the database and seed it. From the repo root, run the generation script (optional if seed_data.sql exists) and execute the SQL scripts using sqlite3:
```bash
python sql/generate_seed.py
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

**2. Analysis Layer**
Run the analysis scripts sequentially:
```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```
`clean_and_eda.py` will output computations and write out `narrator/findings.json`. `visualize.py` will reuse the logic and save charts to `visualizations/`.

**3. GenAI Narrator Layer**
First, install the requirements:
```bash
pip install -r requirements.txt
```
To run the narrative generator, set your free-tier Google AI Studio API key (never use a paid key).
- macOS/Linux: `export GEMINI_API_KEY="your-key-here"`
- Windows PowerShell: `$env:GEMINI_API_KEY="your-key-here"`

You can optionally set the model:
`export GEMINI_MODEL="gemini-3.8-flash"`

Run with Gemini:
```bash
python narrator/generate_narrative.py
```
To save the generated narrative, add the `--save` flag (only works when using the real Gemini API):
```bash
python narrator/generate_narrative.py --save
```
To force the offline template without needing an API key:
```bash
python narrator/generate_narrative.py --offline
```

## Key Findings
- **Cleaned Total Revenue:** INR 97,358.30
- **Duplicate Reconciliation Delta:** INR 2,501.90
- **Overall Return Rates:** COD at 44.4%, UPI at 18.9%, CARD at 14.7%
- **Highest-Risk Segment:** COD in Tier 2 cities faces a severe return rate of 54.5%
- **True Peak Month:** March 2026, generating INR 20,318.90
- **Outlier-Inflated Month:** January 2026 originally appeared to have INR 29,582.10, but its true corrected revenue is INR 11,637.10.

## Numeric Accuracy Check
| Metric | Source Value | Status | Gemini Sample |
| :--- | :--- | :--- | :--- |
| Cleaned Total Revenue | 97358.30 | PASS | PASS |
| COD Return Rate | 44.4% | PASS | PASS |
| Highest-Risk Segment Rate | 54.5% | PASS | PASS |
| Duplicate Delta | 2501.90 | PASS | PASS |
| Peak Month Name & Revenue | March 2026, 20318.90 | PASS | PASS |

## Design Decisions
- **temperature=0.0**: Used because this is a factual business report requiring deterministic logic, not creative writing.
- **timeout=30000**: Ensures robustness over slow network connections by allowing up to 30 seconds for a response.
- **max_output_tokens=2048**: Explicitly and generously set to accommodate both the length of the report and the potential internal thinking tokens of the model that count against the quota.
- **Offline Fallback**: Ensures the pipeline remains reliable and functional even if the API quota is exhausted, internet is disconnected, or the key is invalid.
