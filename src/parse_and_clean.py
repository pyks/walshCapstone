"""
src/parse_and_clean.py
======================
Loops through fragrances_part_1.ndjson … fragrances_part_29.ndjson,
parses every nested field, cleans the data, engineers features, and
writes two CSVs:

    data/processed/fragrantica_clean.csv   — cleaned flat data (pre-encoding)
    data/processed/model_ready.csv         — fully encoded, normalised, model-ready

Usage
-----
    python src/parse_and_clean.py
    python src/parse_and_clean.py --input data/raw --output data/processed
    python src/parse_and_clean.py --top-notes 50 --top-accords 25 --parts 29

Requires
--------
    pip install pandas numpy scikit-learn tqdm
"""

import argparse
import json
import re
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


# ═══════════════════════════════════════════════════════════════
# 1.  CONSTANTS
# ═══════════════════════════════════════════════════════════════

PARTS         = 29
TOP_NOTES_N   = 50
TOP_ACCORDS_N = 25

DOSAGE_MAP = {
    "edp":               "Eau de Parfum",
    "eau de parfum":     "Eau de Parfum",
    "edt":               "Eau de Toilette",
    "eau de toilette":   "Eau de Toilette",
    "parfum":            "Parfum",
    "extrait":           "Parfum",
    "extrait de parfum": "Parfum",
    "edc":               "Eau de Cologne",
    "eau de cologne":    "Eau de Cologne",
    "edf":               "Eau Fraiche",
    "eau fraiche":       "Eau Fraiche",
    "solid perfume":     "Other",
    "perfume oil":       "Other",
    "body mist":         "Other",
    "body spray":        "Other",
    "as lotion":         "Other",
    "as":                "Other",
}

GENDER_MAP = {
    "women":             "Women",
    "female":            "Women",
    "for women":         "Women",
    "men":               "Men",
    "male":              "Men",
    "for men":           "Men",
    "unisex":            "Unisex",
    "male/female":       "Unisex",
    "for women and men": "Unisex",
    "women and men":     "Unisex",
    "both":              "Unisex",
}

ERA_BINS   = [0,    1999, 2009, 2019, 2030]
ERA_LABELS = ["Pre-2000", "2000s", "2010s", "2020s"]

OUTCOME_VARS = ["longevity_score", "sillage_score"]


# ═══════════════════════════════════════════════════════════════
# 2.  RECORD PARSER
# ═══════════════════════════════════════════════════════════════

def _pipe(lst):
    clean = [s.strip() for s in lst if s and str(s).strip()]
    return "|".join(clean) if clean else None


def parse_record(rec: dict) -> dict:
    row = {
        "fragrance_id":        rec.get("fragranceId"),
        "name":                (rec.get("name") or "").strip() or None,
        "dosage_raw":          rec.get("dosage"),
        "gender_raw":          rec.get("gender"),
        "season":              rec.get("season"),
        "year_of_creation":    rec.get("yearOfCreation"),
        "fragrance_family":    rec.get("fragranceFamily"),
        "fragrance_subfamily": rec.get("fragranceSubfamily"),
        "is_discontinued":     rec.get("isDiscontinued", False),
        "is_limited_edition":  rec.get("isLimitedEdition", False),
        "fragrantica_url":     rec.get("fragranticaUrl"),
    }

    brand = rec.get("Brand") or {}
    row["brand_name"]        = (brand.get("name") or "").strip() or None
    row["brand_type"]        = brand.get("brandType")
    row["country_of_origin"] = brand.get("countryOfOrigin")
    row["market_position"]   = brand.get("marketPosition")

    top_notes, heart_notes, base_notes = [], [], []
    for n in (rec.get("FragranceNote") or []):
        ntype = (n.get("noteType") or "").strip().lower()
        nname = (n.get("noteName") or "").strip()
        if not nname:
            continue
        if ntype == "top":
            top_notes.append(nname)
        elif ntype in ("heart", "middle"):
            heart_notes.append(nname)
        elif ntype == "base":
            base_notes.append(nname)

    row["top_notes"]   = _pipe(top_notes)
    row["heart_notes"] = _pipe(heart_notes)
    row["base_notes"]  = _pipe(base_notes)

    primary, secondary = [], []
    for a in (rec.get("FragranceAccord") or []):
        aname = (a.get("accordName") or "").strip()
        if not aname:
            continue
        (primary if a.get("isPrimary") else secondary).append(aname)
    row["main_accords"] = _pipe(primary + secondary)

    pm = rec.get("PerformanceMetrics") or {}
    row["longevity_score"] = pm.get("longevity")
    row["sillage_score"]   = pm.get("sillage")

    return row


# ═══════════════════════════════════════════════════════════════
# 3.  LOAD ALL PARTS
# ═══════════════════════════════════════════════════════════════

def load_all_parts(input_dir: Path, n_parts: int) -> pd.DataFrame:
    rows, errors = [], 0
    for part_num in range(1, n_parts + 1):
        fpath = input_dir / f"fragrances_part_{part_num}.ndjson"
        if not fpath.exists():
            print(f"  [SKIP] {fpath.name} not found")
            continue
        part_rows = 0
        with open(fpath, encoding="utf-8") as f:
            for line_num, line in enumerate(tqdm(f, desc=f"Part {part_num:02d}", leave=False), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(parse_record(json.loads(line)))
                    part_rows += 1
                except Exception as exc:
                    errors += 1
                    if errors <= 5:
                        print(f"\n  [WARN] Part {part_num} line {line_num}: {exc}")
        print(f"  Part {part_num:02d}: {part_rows:,} records loaded")
    print(f"\nTotal raw records : {len(rows):,}  |  Parse errors: {errors}")
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# 4.  CLEAN
# ═══════════════════════════════════════════════════════════════

def clean(df: pd.DataFrame) -> pd.DataFrame:
    print("\n── Step 1: Deduplication")
    n0 = len(df)
    df = df.drop_duplicates()
    df["_key"] = (df["name"].fillna("").str.strip().str.lower()
                  + "||" + df["brand_name"].fillna("").str.strip().str.lower())
    df = df.drop_duplicates(subset="_key").drop(columns="_key")
    print(f"  Removed {n0 - len(df):,} duplicates → {len(df):,} remain")

    print("\n── Step 2: Drop nameless records")
    n0 = len(df)
    df = df[df["name"].notna() & (df["name"] != "")]
    print(f"  Removed {n0 - len(df):,} → {len(df):,} remain")

    print("\n── Step 3: Standardise dosage")
    def clean_dosage(val):
        if pd.isna(val) or str(val).strip().lower() in ("none", "nan", ""):
            return None
        return DOSAGE_MAP.get(str(val).strip().lower(), str(val).strip().title())
    df["dosage"] = df["dosage_raw"].apply(clean_dosage)
    df.drop(columns=["dosage_raw"], inplace=True)
    print(df["dosage"].value_counts(dropna=False).to_string())

    print("\n── Step 4: Standardise gender")
    def clean_gender(val):
        if pd.isna(val) or str(val).strip().lower() in ("none", "nan", ""):
            return None
        return GENDER_MAP.get(str(val).strip().lower(), "Unknown")
    df["gender"] = df["gender_raw"].apply(clean_gender)
    df.drop(columns=["gender_raw"], inplace=True)
    print(df["gender"].value_counts(dropna=False).to_string())

    print("\n── Step 5: Numeric types & year filter")
    df["year_of_creation"] = pd.to_numeric(df["year_of_creation"], errors="coerce")
    df["longevity_score"]  = pd.to_numeric(df["longevity_score"],  errors="coerce").round(4)
    df["sillage_score"]    = pd.to_numeric(df["sillage_score"],    errors="coerce").round(4)
    n0 = len(df)
    df = df[(df["year_of_creation"].between(1920, 2026)) | df["year_of_creation"].isna()]
    print(f"  Removed {n0 - len(df):,} out-of-range years → {len(df):,} remain")

    print("\n── Step 6: Clean pipe strings")
    for col in ["top_notes", "heart_notes", "base_notes", "main_accords"]:
        df[col] = (df[col].fillna("").str.strip("|")
                   .str.replace(r"\|{2,}", "|", regex=True))
        df[col] = df[col].replace("", None)

    print("\n── Step 7: Standardise text categoricals")
    for col in ["fragrance_family", "fragrance_subfamily", "brand_type",
                "market_position", "country_of_origin"]:
        df[col] = (df[col].astype(str).str.strip().str.title()
                   .replace({"None": None, "Nan": None, "": None}))

    # Era cohort — added here so it's available in clean CSV too
    df["era_cohort"] = pd.cut(
        df["year_of_creation"], bins=ERA_BINS, labels=ERA_LABELS, right=True
    ).astype(str).replace("nan", None)

    print(f"\nClean shape: {df.shape}")
    return df


# ═══════════════════════════════════════════════════════════════
# 5.  FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════

def count_pipe_col(series: pd.Series) -> Counter:
    c = Counter()
    for val in series.dropna():
        for item in str(val).split("|"):
            item = item.strip()
            if item:
                c[item] += 1
    return c


def one_hot_pipe(df: pd.DataFrame, col: str, prefix: str, top_n: int) -> pd.DataFrame:
    """Build all binary columns for a pipe-separated field and concat at once."""
    top_vals = [v for v, _ in count_pipe_col(df[col]).most_common(top_n)]
    print(f"  {col}: top-{top_n} of {len(count_pipe_col(df[col]))} unique values")

    new_cols = {}
    for val in top_vals:
        safe = re.sub(r"[^a-z0-9]+", "_", val.lower()).strip("_")
        col_name = f"{prefix}__{safe}"
        new_cols[col_name] = df[col].fillna("").apply(
            lambda x, v=val: 1 if v in [s.strip() for s in x.split("|")] else 0
        )
    return pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)


def engineer_features(df: pd.DataFrame, top_notes_n: int, top_accords_n: int) -> pd.DataFrame:
    print("\n── Feature engineering")

    # One-hot: notes + accords (built efficiently with concat)
    df = one_hot_pipe(df, "top_notes",    "top",    top_notes_n)
    df = one_hot_pipe(df, "heart_notes",  "heart",  top_notes_n)
    df = one_hot_pipe(df, "base_notes",   "base",   top_notes_n)
    df = one_hot_pipe(df, "main_accords", "accord", top_accords_n)

    # Drop near-constant accord cols (>=85% of records contain them)
    accord_cols = [c for c in df.columns if c.startswith("accord__")]
    near_const  = [c for c in accord_cols if df[c].mean() >= 0.85]
    if near_const:
        print(f"  Dropping {len(near_const)} near-constant accord col(s): {near_const}")
        df.drop(columns=near_const, inplace=True)

    # Dummy: dosage
    dosage_keep = ["Eau de Parfum", "Eau de Toilette", "Parfum",
                   "Eau de Cologne", "Eau Fraiche"]
    dosage_clean = df["dosage"].where(df["dosage"].isin(dosage_keep), "Other/Unknown")
    df = pd.concat([df, pd.get_dummies(dosage_clean, prefix="dosage")], axis=1)

    # Dummy: gender
    df = pd.concat([df, pd.get_dummies(df["gender"].fillna("Unknown"), prefix="gender")], axis=1)

    # Dummy: fragrance_family (top 10 + Other)
    top_fam = df["fragrance_family"].value_counts().head(10).index.tolist()
    family_clean = df["fragrance_family"].where(
        df["fragrance_family"].isin(top_fam), "Other"
    ).fillna("Unknown")
    df = pd.concat([df, pd.get_dummies(family_clean, prefix="family")], axis=1)

    # Dummy: era_cohort
    df = pd.concat([df, pd.get_dummies(df["era_cohort"].fillna("Unknown"), prefix="era")], axis=1)

    # Normalise year
    scaler = MinMaxScaler()
    df["year_norm"] = np.nan
    valid = df["year_of_creation"].notna()
    df.loc[valid, "year_norm"] = scaler.fit_transform(df.loc[valid, ["year_of_creation"]])

    # Boolean → int
    for col in ["is_discontinued", "is_limited_edition"]:
        df[col] = df[col].map({True: 1, False: 0, "True": 1, "False": 0}).fillna(0).astype(int)

    print(f"\n  Model-ready shape: {df.shape}")
    return df


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    metadata = [
        "fragrance_id", "name", "brand_name", "brand_type", "country_of_origin",
        "market_position", "dosage", "gender", "season", "year_of_creation",
        "era_cohort", "fragrance_family", "fragrance_subfamily",
        "top_notes", "heart_notes", "base_notes", "main_accords",
        "is_discontinued", "is_limited_edition", "fragrantica_url",
    ]
    outcomes = ["longevity_score", "sillage_score"]
    feat_pfx = ("top__", "heart__", "base__", "accord__",
                "dosage_", "gender_", "family_", "era_")
    features = [c for c in df.columns if any(c.startswith(p) for p in feat_pfx)]
    features += ["year_norm"]
    other    = [c for c in df.columns if c not in metadata + outcomes + features]
    return df[
        [c for c in metadata if c in df.columns]
      + [c for c in outcomes  if c in df.columns]
      + [c for c in features  if c in df.columns]
      + [c for c in other     if c in df.columns]
    ]


# ═══════════════════════════════════════════════════════════════
# 6.  SUMMARY
# ═══════════════════════════════════════════════════════════════

def print_summary(df_clean: pd.DataFrame, df_model: pd.DataFrame):
    print("\n" + "═" * 60)
    print("  FINAL SUMMARY")
    print("═" * 60)
    print(f"  fragrantica_clean.csv : {df_clean.shape[0]:,} rows × {df_clean.shape[1]} cols")
    print(f"  model_ready.csv       : {df_model.shape[0]:,} rows × {df_model.shape[1]} cols")

    print("\n  ── Outcome variables ─────────────────────────────")
    for col in OUTCOME_VARS:
        s = df_model[col].dropna()
        print(f"  {col:<20}  n={len(s):,}  mean={s.mean():.3f}  "
              f"std={s.std():.3f}  range=[{s.min():.2f}, {s.max():.2f}]")

    print("\n  ── Gender ────────────────────────────────────────")
    print(df_clean["gender"].value_counts(dropna=False).to_string())

    print("\n  ── Dosage ────────────────────────────────────────")
    print(df_clean["dosage"].value_counts(dropna=False).head(8).to_string())

    print("\n  ── Fragrance family (top 8) ──────────────────────")
    print(df_clean["fragrance_family"].value_counts(dropna=False).head(8).to_string())

    print("\n  ── Era cohort ────────────────────────────────────")
    print(df_clean["era_cohort"].value_counts(dropna=False).to_string())

    feat_cols = [c for c in df_model.columns if any(c.startswith(p)
                 for p in ("top__","heart__","base__","accord__",
                            "dosage_","gender_","family_","era_"))]
    print(f"\n  ── Feature columns in model_ready.csv ────────────")
    print(f"  Note indicators (top/heart/base) : "
          f"{sum(1 for c in feat_cols if c.startswith(('top__','heart__','base__')))}")
    print(f"  Accord indicators                : "
          f"{sum(1 for c in feat_cols if c.startswith('accord__'))}")
    print(f"  Categorical dummies              : "
          f"{sum(1 for c in feat_cols if c.startswith(('dosage_','gender_','family_','era_')))}")
    print(f"  Total encoded feature columns    : {len(feat_cols)}")

    print("\n  ── Top missing (>5%, clean dataset) ──────────────")
    miss = (df_clean.isna().mean() * 100).sort_values(ascending=False)
    print(miss[miss > 5].round(1).to_string())


# ═══════════════════════════════════════════════════════════════
# 7.  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Parse, clean and feature-engineer all fragrance NDJSON parts"
    )
    parser.add_argument("--input",       default="data/raw",
                        help="Folder with fragrances_part_1.ndjson … fragrances_part_29.ndjson")
    parser.add_argument("--output",      default="data/processed",
                        help="Output folder")
    parser.add_argument("--top-notes",   type=int, default=TOP_NOTES_N,
                        help=f"Top-N notes per pyramid level to encode (default {TOP_NOTES_N})")
    parser.add_argument("--top-accords", type=int, default=TOP_ACCORDS_N,
                        help=f"Top-N accords to encode (default {TOP_ACCORDS_N})")
    parser.add_argument("--parts",       type=int, default=PARTS,
                        help=f"Number of part files (default {PARTS})")
    args = parser.parse_args()

    input_dir  = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("═" * 60)
    print("  Fragrance NDJSON → Model-Ready CSV")
    print(f"  Parts  : 1 … {args.parts}")
    print(f"  Input  : {input_dir}")
    print(f"  Output : {output_dir}")
    print(f"  Notes  : top-{args.top_notes} per level  |  Accords: top-{args.top_accords}")
    print("═" * 60 + "\n")

    df_raw   = load_all_parts(input_dir, args.parts)
    df_clean = clean(df_raw.copy())
    df_model = engineer_features(df_clean.copy(), args.top_notes, args.top_accords)
    df_model = reorder_columns(df_model)

    clean_path = output_dir / "fragrantica_clean.csv"
    model_path = output_dir / "model_ready.csv"

    df_clean.to_csv(clean_path, index=False, encoding="utf-8")
    df_model.to_csv(model_path, index=False, encoding="utf-8")

    print("\n── Saved ───────────────────────────────────────────")
    print(f"  {clean_path}  ({len(df_clean):,} rows × {len(df_clean.columns)} cols)")
    print(f"  {model_path}  ({len(df_model):,} rows × {len(df_model.columns)} cols)")

    print_summary(df_clean, df_model)
    print("\n✓  All done.")


if __name__ == "__main__":
    main()
