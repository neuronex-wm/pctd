"""Shared utilities for cell ID mapping, filename handling, and format detection."""
import pandas as pd
from pathlib import Path

from pipeline_config import BOX2_CSV, SUBJECT_ID_LENGTH


def load_id_mapping(csv_path: Path = BOX2_CSV) -> dict:
    """Return {internalID: cellID} dict. Raises FileNotFoundError if CSV missing."""
    check_prerequisite(csv_path, "box2_ephys.csv")
    df = pd.read_csv(csv_path)
    return dict(zip(df["internalID"], df["cellID"]))


def load_reverse_id_mapping(csv_path: Path = BOX2_CSV) -> dict:
    """Return {cellID: internalID} dict."""
    check_prerequisite(csv_path, "box2_ephys.csv")
    df = pd.read_csv(csv_path)
    return dict(zip(df["cellID"], df["internalID"]))


def stem(filepath) -> str:
    """Extract filename without extension, cross-platform."""
    return Path(filepath).stem


def subject_folder(internal_id: str) -> str:
    """Derive subject folder name from an internal ID (first N chars)."""
    return str(internal_id)[:SUBJECT_ID_LENGTH]


def check_prerequisite(path: Path, label: str):
    """Raise if a required file/directory doesn't exist."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Prerequisite missing: {label} ({path}). "
            f"Run the upstream step first -- see README 'Updating the Data'."
        )


def detect_csv_format(df: pd.DataFrame) -> str:
    """
    Detect whether a DataFrame is in 'raw' source format or 'formatted' box2_ephys format.

    Returns:
        'raw'       — has raw column names (Row, Identifier, RinHD, etc.)
        'formatted' — has display column names (internalID, cellID, Resistance, etc.)

    Raises ValueError if format cannot be determined.
    """
    raw_indicators = {"Row", "Identifier", "RinHD", "widTP_LP", "heightTP_SP", "Vrest"}
    formatted_indicators = {"internalID", "cellID", "Resistance", "AP halfwidth", "Amplitude", "Resting potential"}

    cols = set(df.columns)
    raw_hits = len(cols & raw_indicators)
    formatted_hits = len(cols & formatted_indicators)

    if raw_hits >= 3 and raw_hits > formatted_hits:
        return "raw"
    elif formatted_hits >= 3 and formatted_hits > raw_hits:
        return "formatted"
    else:
        raise ValueError(
            f"Cannot auto-detect CSV format. "
            f"Found {raw_hits} raw indicators and {formatted_hits} formatted indicators. "
            f"Expected columns like {sorted(raw_indicators)[:3]} (raw) or "
            f"{sorted(formatted_indicators)[:3]} (formatted). "
            f"Check your input CSV columns: {sorted(df.columns)[:10]}..."
        )
