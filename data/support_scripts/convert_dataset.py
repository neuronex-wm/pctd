"""
Convert a source dataset CSV into the website's box2_ephys.csv/.json.

Modes:
    Full regeneration:  python convert_dataset.py
    Append new cells:   python convert_dataset.py --append path/to/new_cells.csv

The append mode auto-detects whether the input is in raw source format
(e.g. marmData_wUMAP.csv columns) or pre-formatted (box2_ephys column names),
merges new cells into the existing database, and overwrites duplicates by cellID.
"""
import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline_config import (
    SOURCE_CSV,
    BOX2_CSV,
    BOX2_JSON,
    TRACES_DIR,
    MORPH_DIR,
    COLUMN_MAPPINGS,
    RAW_ID_MAPPINGS,
    DENDRITE_MAP,
    DENDRITE_DEFAULT,
    HASH_CELL_ID,
)
from id_utils import check_prerequisite, detect_csv_format, stem


# ─── Transform helpers ──────────────────────────────────────────────────────

def _map_dendritic_type(value):
    return DENDRITE_MAP.get(value, DENDRITE_DEFAULT)


def _compute_has_plot(df: pd.DataFrame) -> pd.Series:
    """Check which internalIDs have a trace CSV in TRACES_DIR."""
    if not TRACES_DIR.exists():
        return pd.Series(False, index=df.index)
    plot_ids = {stem(f) for f in TRACES_DIR.glob("*.csv")}
    return df["internalID"].apply(lambda x: str(x) in plot_ids)


def _compute_has_morph(df: pd.DataFrame) -> pd.Series:
    """Check which internalIDs have a morphology PNG in MORPH_DIR."""
    if not MORPH_DIR.exists():
        return pd.Series(False, index=df.index)
    morph_ids = {stem(f).replace("_morph", "").replace("_thumb", "") for f in MORPH_DIR.glob("*.png")}
    return df["internalID"].apply(lambda x: str(x) in morph_ids)


def _sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sort using sequential sorts matching original _2026_conv.py behavior.
    
    Uses pandas default sort (quicksort) to match original output exactly.
    """
    if "Amplitude" in df.columns:
        df = df.sort_values(by="Amplitude", ascending=False)
    if "hasPlot" in df.columns:
        df = df.sort_values(by="hasPlot", ascending=False)
    if "hasMorph" in df.columns:
        df = df.sort_values(by="hasMorph", ascending=False)
    return df


def transform_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Apply full column renaming and value transforms to a raw-format DataFrame."""
    # Rename ID columns
    df = df.rename(columns=RAW_ID_MAPPINGS)

    # Generate cellID by hash if not present
    if "cellID" not in df.columns:
        if HASH_CELL_ID:
            df["cellID"] = df.apply(lambda row: abs(hash(tuple(row))), axis=1)
        else:
            raise ValueError(
                "Raw CSV has no 'Identifier' or 'cellID' column and HASH_CELL_ID is disabled. "
                "Either add an Identifier column or set PCTD_HASH_CELL_ID=1."
            )

    # Rename feature columns
    df = df.rename(columns=COLUMN_MAPPINGS)

    # Map dendrite type
    if "Dendrite type" in df.columns:
        df["Dendrite type"] = df["Dendrite type"].apply(_map_dendritic_type)

    return df


def enrich_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Compute hasPlot and hasMorph columns."""
    df["hasPlot"] = _compute_has_plot(df)
    df["hasMorph"] = _compute_has_morph(df)
    return df


def write_db(df: pd.DataFrame):
    """Write the database to CSV and JSON."""
    BOX2_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(BOX2_CSV, index=False)
    df.to_json(BOX2_JSON, orient="records", indent=4)
    print(f"Wrote {len(df)} cells -> {BOX2_CSV.name}, {BOX2_JSON.name}")


# ─── Full regeneration mode ─────────────────────────────────────────────────

def full_convert(source_csv: Path = SOURCE_CSV):
    """Full regeneration: read source CSV, transform, write box2_ephys."""
    check_prerequisite(source_csv, "Source dataset CSV (set PCTD_SOURCE_CSV env var)")

    df = pd.read_csv(source_csv)
    df = transform_raw(df)
    df = enrich_flags(df)
    df = _sort_dataframe(df)

    write_db(df)


# ─── Append mode ────────────────────────────────────────────────────────────

def append_cells(csv_path: Path):
    """
    Append new cells from csv_path into the existing box2_ephys database.

    - Auto-detects whether input is raw or pre-formatted
    - Overwrites existing records on cellID collision
    - Creates a .bak backup before modifying
    """
    check_prerequisite(BOX2_CSV, "Existing box2_ephys.csv database")
    check_prerequisite(csv_path, f"Input CSV for append ({csv_path})")

    # Load existing database
    existing = pd.read_csv(BOX2_CSV)
    existing_count = len(existing)

    # Load new data
    new_df = pd.read_csv(csv_path)
    fmt = detect_csv_format(new_df)
    print(f"Detected input format: {fmt} ({len(new_df)} rows)")

    if fmt == "raw":
        new_df = transform_raw(new_df)

    # Compute asset flags for new rows
    new_df = enrich_flags(new_df)

    # Ensure cellID column is compatible type
    existing["cellID"] = existing["cellID"].astype(str)
    new_df["cellID"] = new_df["cellID"].astype(str)

    # Backup existing database
    backup_path = BOX2_CSV.with_suffix(".csv.bak")
    shutil.copy2(BOX2_CSV, backup_path)
    print(f"Backup saved: {backup_path.name}")

    # Merge: concat then drop duplicates keeping last (new data wins)
    merged = pd.concat([existing, new_df], ignore_index=True)
    merged = merged.drop_duplicates(subset="cellID", keep="last")

    # Restore cellID type (numeric if possible)
    try:
        merged["cellID"] = pd.to_numeric(merged["cellID"])
    except (ValueError, TypeError):
        pass  # keep as string if mixed

    # Sort
    merged = _sort_dataframe(merged)

    # Summary
    final_count = len(merged)
    added = final_count - existing_count
    updated = len(new_df) - added if added < len(new_df) else 0
    print(f"Summary: {added} new cells added, {updated} existing cells updated")
    print(f"Total cells: {existing_count} -> {final_count}")

    write_db(merged)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert/append data into the PCTD website database (box2_ephys.csv/.json).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full regeneration from source CSV (requires PCTD_SOURCE_CSV env var)
  python convert_dataset.py

  # Append new cells (auto-detects raw vs formatted input)
  python convert_dataset.py --append path/to/new_cells.csv

  # Append with explicit source CSV for full regen
  python convert_dataset.py --source path/to/full_dataset.csv
""",
    )
    parser.add_argument(
        "--append", "-a",
        type=Path,
        metavar="CSV",
        help="Append/merge cells from this CSV into the existing database. "
             "Input format (raw or formatted) is auto-detected.",
    )
    parser.add_argument(
        "--source", "-s",
        type=Path,
        metavar="CSV",
        help="Source CSV for full regeneration (overrides PCTD_SOURCE_CSV env var).",
    )
    args = parser.parse_args()

    if args.append:
        append_cells(args.append)
    else:
        source = args.source if args.source else SOURCE_CSV
        full_convert(source)


if __name__ == "__main__":
    main()
