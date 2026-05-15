# What Makes a Fragrance Perform?

## Predicting Fragrance Performance Using Olfactory, Product, and Market Characteristics

This repository contains the data, code, documentation, and interim analysis outputs for the QM640 Data Analytics Capstone project.

**Author:** Priyanka Sharma  
**Course:** QM640 Data Analytics Capstone  
**Institution:** Walsh College  
**Mentor:** Shyam Venkatesh  
**Term:** Term 2, May 2026  

---

## 1. Project Overview

The global fragrance market is a large and fast-growing sector within beauty and personal care. Despite the availability of rich fragrance data from online fragrance platforms, there is limited systematic analysis of which olfactory, product, and market characteristics drive measurable fragrance performance.

This capstone project investigates which characteristics best predict fragrance performance, measured primarily through:

- `longevity_score`: how long a fragrance lasts on skin, scored from 0 to 10
- `sillage_score`: the strength of fragrance projection or trail, scored from 0 to 10

The study uses a structured fragrance dataset compiled from 29 Newline-Delimited JSON (NDJSON) source files. The full raw dataset contains 98,463 records. After cleaning and filtering, the final clean dataset contains 96,145 records and the model-ready dataset contains 209 columns.

The project applies statistical analysis and machine learning methods, including regression, Analysis of Variance (ANOVA), Random Forest, and SHAP-based model interpretation.

---

## 2. Research Questions

### RQ1: Olfactory Predictors of Longevity

Which olfactory characteristics — top notes, heart notes, base notes, and main accords — most strongly predict fragrance longevity performance?

**Hypothesis:** Specific note and accord categories will show statistically significant positive associations with `longevity_score` after controlling for concentration and gender label.

---

### RQ2: Concentration Level Effects

Do concentration levels such as Eau de Parfum, Eau de Toilette, Parfum, and Eau de Cologne produce statistically significant differences in longevity and sillage performance scores?

**Hypothesis:** At least one concentration group will show a significantly higher mean `longevity_score` or `sillage_score` than the others.

---

### RQ3: Gender Label and Era Cohort

Do gender labelling and release-era cohort interact in their effect on fragrance longevity performance?

**Hypothesis:** A statistically significant interaction effect between gender label and release-era cohort will be observed on `longevity_score`.

---

### RQ4: Fragrance Family Moderation

Does fragrance family moderate the relationship between olfactory note composition and longevity performance?

**Hypothesis:** Fragrance family will function as a significant moderator, such that the predictive relationship between note composition and `longevity_score` varies across family groups.

---

## 3. Repository Structure

```text
walshCapstone/
├── data/
│   ├── raw/
│   │   ├── fragrances_part_1.ndjson
│   │   ├── fragrances_part_2.ndjson
│   │   ├── ...
│   │   └── fragrances_part_29.ndjson
│   └── processed/
│       ├── fragrantica_clean.csv
│       └── model_ready.csv
│
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_exploratory_data_analysis.ipynb
│   ├── 04_feature_engineering.ipynb
│   └── 05_modelling.ipynb
│
├── src/
│   └── parse_and_clean.py
│
├── reports/
│   └── interim/
│       └── QM640_Interim_Report_v3_Sharma.pdf
│
├── outputs/
│   ├── figures/
│   ├── tables/
│   └── models/
│
├── README.md
├── requirements.txt
└── .gitignore
