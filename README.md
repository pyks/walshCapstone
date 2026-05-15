# What Makes a Perfume Highly Rated?
### Predicting Consumer Ratings of Fragrances Using Olfactory, Product, and Market Characteristics

**QM640: Data Analytics Capstone | Walsh College**  
**Author:** Priyanka Sharma  
**Mentor:** Shyam Venkatesh  
**Term:** 2 | May 2026

---

## Project Overview

This capstone project investigates what drives high consumer ratings on Fragrantica.com — one of the world's largest fragrance communities (over 1.2 million registered users). Using a dataset of ~22,450 perfume records scraped from the platform, the project applies statistical analysis and machine learning to identify which olfactory, product, and market factors best predict consumer satisfaction.

---

## Research Questions

| # | Research Question | Method |
|---|---|---|
| RQ1 | Which olfactory characteristics (top/heart/base notes, main accords) most strongly predict consumer ratings? | Multiple Linear Regression + SHAP |
| RQ2 | Do perfume concentration levels (EDP, EDT, Parfum, etc.) significantly affect ratings? | One-Way ANOVA + Tukey HSD |
| RQ3 | Do gender labelling and release-era cohort interact in influencing ratings? | Two-Way ANOVA |
| RQ4 | Does popularity (vote count) confound or moderate the relationship between notes and ratings? | Moderated Multiple Regression |

---

## Repository Structure

```
walshCapstone/
│
├── README.md
├── requirements.txt
├── setup_repo.sh              ← Run once to create all folders
│
├── src/
│   └── scraper.py             ← Fragrantica web scraper (BeautifulSoup)
│
├── data/
│   ├── raw/
│   │   └── fragrantica_raw.csv       ← Scraped dataset (~22,450 rows)
│   └── processed/
│       └── fragrantica_clean.csv     ← Cleaned & encoded dataset
│
├── notebook/
│   ├── 01_data_collection.ipynb      ← Scraping walkthrough
│   ├── 02_data_cleaning.ipynb        ← Cleaning, deduplication, outliers
│   ├── 03_eda.ipynb                  ← Exploratory data analysis
│   ├── 04_feature_engineering.ipynb  ← Encoding & normalization
│   └── 05_modelling.ipynb            ← Regression, Random Forest, SHAP
│
├── outputs/
│   ├── figures/               ← Saved charts & plots
│   └── models/                ← Saved model files (.pkl)
│
└── reports/
    └── QM640_Interim_Report_Sharma.docx
```

---

## Dataset

| Field | Description |
|---|---|
| `perfume_name` | Name of the fragrance |
| `brand` | Manufacturer / designer house |
| `rating_score` | Average consumer rating (0–5 scale) |
| `num_votes` | Number of consumer votes |
| `concentration` | EDP / EDT / Parfum / EDC / Body Mist |
| `gender_label` | For women / For men / Unisex |
| `release_year` | Year of launch |
| `top_notes` | Top notes (pipe-separated) |
| `heart_notes` | Heart / middle notes (pipe-separated) |
| `base_notes` | Base / dry-down notes (pipe-separated) |
| `main_accords` | Main scent accords (pipe-separated) |
| `longevity_votes` | Distribution of longevity ratings |
| `sillage_votes` | Distribution of sillage (projection) ratings |
| `season_votes` | Season preference distribution |

**Source:** [Fragrantica.com](https://www.fragrantica.com) (scraped via `src/scraper.py`)  
**Secondary dataset:** [Parfumo / TidyTuesday December 2024](https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2024/2024-12-10/parfumo_data_clean.csv)

---

## Setup & Usage

### 1. Clone the repo
```bash
git clone https://github.com/pyks/walshCapstone.git
cd walshCapstone
```

### 2. Create folder structure
```bash
bash setup_repo.sh
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the scraper
```bash
# Scrape 50 pages (~600 records) — quick test
python src/scraper.py --pages 50

# Scrape full dataset (~1900 pages)
python src/scraper.py --pages 1900 --delay 2
```
> Output is saved to `data/raw/fragrantica_raw.csv`. The scraper is resumable — if interrupted, re-run and it will append new records.

### 5. Run notebooks in order
Open Jupyter and run notebooks `01` through `05` sequentially.

```bash
jupyter notebook
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| BeautifulSoup4 + Requests | Web scraping |
| Pandas + NumPy | Data wrangling |
| Matplotlib + Seaborn | Visualization |
| Scikit-learn | Machine learning models |
| SciPy | Statistical tests (ANOVA, Tukey HSD) |
| SHAP | Model interpretability |
| Jupyter Notebook | Analysis environment |

---

## Key Findings (Interim)

- **Floral and fresh accords** show a modest positive association with higher ratings in preliminary EDA
- **Eau de Parfum** concentrations tend to receive higher ratings than Eau de Toilette formulations
- **Vote count** has a strong positive skew; high-vote perfumes show compression toward mid-range ratings (popularity bias)
- Baseline regression model (R² ≈ 0.38) confirms olfactory predictors explain a meaningful share of rating variance

*(Full results to be updated in the final report)*

---

## License

This project is for academic purposes only. Data scraped from Fragrantica.com is subject to their [Terms of Service](https://www.fragrantica.com/terms.html). Do not redistribute the raw dataset.
