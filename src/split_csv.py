"""
src/split_csv.py
================
Splits fragrantica_clean.csv and model_ready.csv into parts
small enough for GitHub (default: 20 MB each).

Usage
-----
    python src/split_csv.py                         # splits both files
    python src/split_csv.py --mb 20                 # 20 MB per part (default)
    python src/split_csv.py --file data/processed/model_ready.csv

To reassemble later (for modelling):
    python src/split_csv.py --reassemble
"""

import argparse
import os
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path("data/processed")
MB = 1024 * 1024   # bytes per MB
DEFAULT_MB = 20    # target max size per part

FILES_TO_SPLIT = [
    "fragrantica_clean.csv",
    "model_ready.csv",
]


# ── Split one CSV ─────────────────────────────────────────────

def split_csv(filepath: Path, max_mb: float) -> None:
    max_bytes = int(max_mb * MB)
    print(f"\n── Splitting {filepath.name}  ({filepath.stat().st_size / MB:.1f} MB)")

    df = pd.read_csv(filepath, low_memory=False)
    total_rows = len(df)
    print(f"   Rows: {total_rows:,}  |  Cols: {df.shape[1]}")

    # Estimate rows per chunk from a small sample
    sample_bytes = df.head(500).to_csv(index=False).encode("utf-8").__len__()
    bytes_per_row = sample_bytes / 500
    rows_per_chunk = max(1, int(max_bytes / bytes_per_row))
    print(f"   ~{rows_per_chunk:,} rows per chunk  (target ≤ {max_mb} MB each)")

    stem    = filepath.stem          # e.g. "model_ready"
    out_dir = filepath.parent
    part    = 1
    parts_written = []

    for start in range(0, total_rows, rows_per_chunk):
        chunk    = df.iloc[start : start + rows_per_chunk]
        out_name = f"{stem}_part_{part}.csv"
        out_path = out_dir / out_name

        chunk.to_csv(out_path, index=False, encoding="utf-8")
        size_mb  = out_path.stat().st_size / MB
        print(f"   ✓ {out_name}  ({len(chunk):,} rows, {size_mb:.1f} MB)")
        parts_written.append(out_name)
        part += 1

    print(f"\n   Done — {part - 1} parts written to {out_dir}/")
    print(f"   Original file kept at {filepath}  (add to .gitignore if needed)")

    # Write a small manifest so reassemble knows the order
    manifest = out_dir / f"{stem}_parts_manifest.txt"
    manifest.write_text("\n".join(parts_written))
    print(f"   Manifest: {manifest.name}")


# ── Reassemble ────────────────────────────────────────────────

def reassemble(out_dir: Path) -> None:
    manifests = list(out_dir.glob("*_parts_manifest.txt"))
    if not manifests:
        print("No manifest files found. Nothing to reassemble.")
        return

    for mf in manifests:
        stem = mf.stem.replace("_parts_manifest", "")
        parts = [p.strip() for p in mf.read_text().splitlines() if p.strip()]
        print(f"\n── Reassembling {stem}.csv from {len(parts)} parts ...")

        dfs = []
        for part_name in parts:
            p = out_dir / part_name
            if not p.exists():
                print(f"   [MISSING] {part_name} — skipping")
                continue
            dfs.append(pd.read_csv(p, low_memory=False))
            print(f"   Read {part_name}  ({len(dfs[-1]):,} rows)")

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            out_path = out_dir / f"{stem}.csv"
            combined.to_csv(out_path, index=False, encoding="utf-8")
            print(f"   ✓ Saved {out_path}  ({len(combined):,} rows × {combined.shape[1]} cols)")


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Split large CSVs for GitHub upload")
    parser.add_argument("--mb",          type=float, default=DEFAULT_MB,
                        help=f"Max MB per part file (default {DEFAULT_MB})")
    parser.add_argument("--file",        type=str,   default=None,
                        help="Split a specific file instead of both defaults")
    parser.add_argument("--reassemble",  action="store_true",
                        help="Reassemble all split parts back into original CSVs")
    parser.add_argument("--dir",         type=str,   default=str(PROCESSED_DIR),
                        help=f"Folder to look in (default: {PROCESSED_DIR})")
    args = parser.parse_args()

    out_dir = Path(args.dir)

    if args.reassemble:
        reassemble(out_dir)
        return

    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"File not found: {p}")
            return
        split_csv(p, args.mb)
    else:
        for fname in FILES_TO_SPLIT:
            p = out_dir / fname
            if not p.exists():
                print(f"[SKIP] {p} not found")
                continue
            split_csv(p, args.mb)

    print("\n── What to do next ──────────────────────────────────")
    print("1. Add the *_part_*.csv files to git:")
    print("     git add data/processed/*_part_*.csv")
    print("     git add data/processed/*_manifest.txt")
    print("2. Add the full CSVs to .gitignore so they are not re-uploaded:")
    print("     echo 'data/processed/model_ready.csv' >> .gitignore")
    print("     echo 'data/processed/fragrantica_clean.csv' >> .gitignore")
    print("3. Commit and push:")
    print("     git commit -m \"Add processed CSV parts for GitHub\"")
    print("     git push origin main")
    print("\nTo reassemble after cloning:")
    print("     python src/split_csv.py --reassemble")


if __name__ == "__main__":
    main()
