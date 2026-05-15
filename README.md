# What Makes a Fragrance Perform?
### Predicting Fragrance Performance Using Olfactory, Product, and Market Characteristics

**QM640: Data Analytics Capstone | Walsh College**  
**Author:** Priyanka Sharma  
**Mentor:** Shyam Venkatesh  
**Term:** 2 | May 2026

---

## Project Overview

This capstone project investigates what combination of olfactory, product, and market characteristics best predicts measurable fragrance performance — specifically **longevity** (how long a fragrance lasts on skin, scored 0–10) and **sillage** (the strength of its projection, scored 0–10).

The primary dataset is `fragrances-full.ndjson`, a structured fragrance database of **98,463 raw records** compiled from Fragrantica.com and supplementary sources. After parsing and cleaning all 29 source files, the final working dataset contains **96,145 records** with numeric performance scores available for 93.5% of records.

---

## Research Questions

| # | Research Question | Method |
|---|---|---|
| RQ1 | Which olfactory characteristics (top/heart/base notes, accords) most strongly predict longevity performance? | Ridge Regression, LASSO, SHAP |
| RQ2 | Do concentration levels (EDP, EDT, Parfum, EDC) produce significant differences in performance scores? | One-Way ANOVA + Tukey HSD |
| RQ3 | Do gender label and release-era cohort interact in their effect on longevity performance? | Two-Way ANOVA |
| RQ4 | Does fragrance family moderate the note composition–longevity relationship? | Moderated Multiple Regression |

---

## Repository Structure

```
walshCapstone/
│
├── README.md
├── requirements.txt
├── setup_repo.sh
│
├── src/
│   └── parse_and_clean.py        ← Parses all 29 NDJSON parts → clean + model-ready CSVs
│
├── data/
│   ├── raw/
│   │   ├── fragrances_part_1.ndjson
│   │   ├── fragrances_part_2.ndjson
│   │   │   ...
│   │   └── fragrances_part_29.ndjson
│   └── processed/
│       ├── fragrantica_clean_part_1.csv
        ├── fragrantica_clean_part_2.csv ← 96,145 rows × 22 cols
        ├── model_ready_part_1.csv
        ├── model_ready_part_2.csv
        ├── model_ready_part_3.csv
        ├── model_ready_part_4.csv    ← 96,145 rows × 209 cols (187 feature columns)
                                     
│
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_feature_engineering.ipynb
│   └── 05_modelling.ipynb
│
├── outputs/
│   ├── figures/
│   └── models/
│
└── reports/
    └── QM640_Interim_Report_v3_Sharma.pdf
```

---

## Dataset

### Primary — fragrances-full.ndjson (29 parts)

The source file was split into 29 parts (each under 25 MB) for GitHub compatibility. `src/parse_and_clean.py` reads all parts in a loop and produces two output files.

| Field | Description |
|---|---|
| `fragrance_id` | Unique UUID per fragrance |
| `name` | Commercial fragrance name |
| `brand_name` | Manufacturer / fragrance house |
| `brand_type` | Market tier (Niche / Luxury / Mass) |
| `dosage` | Concentration: EDP, EDT, Parfum, EDC, Eau Fraiche |
| `gender` | Women / Men / Unisex |
| `year_of_creation` | Launch year (1920–2026) |
| `era_cohort` | Pre-2000 / 2000s / 2010s / 2020s |
| `fragrance_family` | Floral, Woody, Amber, Citrus, Aromatic, Chypre, etc. |
| `top_notes` | Pipe-separated top note ingredients |
| `heart_notes` | Pipe-separated heart note ingredients |
| `base_notes` | Pipe-separated base note ingredients |
| `main_accords` | Pipe-separated accord labels |
| `longevity_score` | **PRIMARY OUTCOME** — numeric 0–10 (n=89,892; mean=6.907, SD=1.792) |
| `sillage_score` | **SECONDARY OUTCOME** — numeric 0–10 (n=89,858; mean=4.150, SD=1.631) |

### Secondary — Parfumo / TidyTuesday (December 2024)

Used for cross-validation and fragrance family taxonomy reference.  
URL: `https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2024/2024-12-10/parfumo_data_clean.csv`

---

## Setup & Usage

### 1. Clone the repo
```bash
git clone https://github.com/pyks/walshCapstone.git
cd walshCapstone
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Parse and clean all 29 data files
```bash
python src/parse_and_clean.py
```

This reads `fragrances_part_1.ndjson` through `fragrances_part_29.ndjson`, and writes:
- `data/processed/fragrantica_clean.csv` — 96,145 rows × 22 cols (cleaned flat data)
- `data/processed/model_ready.csv` — 96,145 rows × 209 cols (187 encoded feature columns)

### 4. Run notebooks in order
```bash
jupyter notebook
```

---

## Key Dataset Statistics

| Metric | Value |
|---|---|
| Raw records (29 parts) | 98,463 |
| After deduplication | 97,861 (−602) |
| After year-range filter | 96,145 (−1,716) |
| longevity_score coverage | 89,892 records (93.5%) |
| sillage_score coverage | 89,858 records (93.5%) |
| Unique top note ingredients | 2,583 |
| Unique heart note ingredients | 2,792 |
| Unique base note ingredients | 2,029 |
| Total encoded feature columns | 187 |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Pandas + NumPy | Data wrangling |
| Scikit-learn | ML models + MinMaxScaler |
| SciPy + Statsmodels + Pingouin | ANOVA, Tukey HSD |
| SHAP | Model interpretability |
| Matplotlib + Seaborn | Visualization |
| Jupyter Notebook | Analysis environment |

---

## License

This project is for academic purposes only. Data sourced from Fragrantica.com is subject to their Terms of Service. Do not redistribute the raw dataset.
