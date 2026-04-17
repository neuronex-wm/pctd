"""
Central configuration for the PCTD data pipeline.
All paths resolve relative to the repo root by default.
Override any path via environment variable (PCTD_*).
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # data/support_scripts/../../

# --- Core data files --- These are the main outputs of the conversion step, and inputs to downstream steps. Generally should not be overridden.
BOX2_CSV = Path(os.environ.get("PCTD_BOX2_CSV", REPO_ROOT / "data" / "box2_ephys.csv"))
BOX2_JSON = Path(os.environ.get("PCTD_BOX2_JSON", REPO_ROOT / "data" / "box2_ephys.json"))
DANDI_MAPPING = Path(os.environ.get("PCTD_DANDI_MAPPING", REPO_ROOT / "data" / "dandi_mapping.csv"))

# --- Asset directories --- # These can be overridden to point to different locations, but defaults are set to subdirectories of data/ for convenience.
TRACES_DIR = Path(os.environ.get("PCTD_TRACES_DIR", REPO_ROOT / "data" / "traces"))
MORPH_DIR = Path(os.environ.get("PCTD_MORPH_DIR", REPO_ROOT / "data" / "morph"))
UPDATED_NWBS = Path(os.environ.get("PCTD_UPDATED_NWBS", REPO_ROOT / "data" / "updated_nwbs"))
NWBS_WITH_MORPH = Path(os.environ.get("PCTD_NWBS_MORPH", REPO_ROOT / "data" / "nwbs_with_morph"))
DANDI_DIR = Path(os.environ.get("PCTD_DANDI_DIR", REPO_ROOT / "001776"))

# --- External inputs (no defaults — user MUST set these for full regeneration) --- # These are the raw source files that the conversion step depends on. Must be set via environment variable or passed as argument to conversion functions.
SOURCE_CSV = Path(os.environ.get("PCTD_SOURCE_CSV", ""))
SWC_DIR = Path(os.environ.get("PCTD_SWC_DIR", ""))
RAW_NWB_DIR = Path(os.environ.get("PCTD_RAW_NWB_DIR", ""))

# --- Column mappings (single source of truth for Python <-> JS sync) ---
# Keys: raw source CSV column names
# Values: display names used in box2_ephys.csv/.json and ephysConfig.js
COLUMN_MAPPINGS = {
    "RinHD": "Resistance",
    "widTP_LP": "AP halfwidth",
    "heightTP_SP": "Amplitude",
    "Vrest": "Resting potential",
    "Rheo": "Rheobase",
    "brainOrigin": "Cortical area",
    "tau": "Time Constant",
    "maxRt": "Max Firing Rate",
    "medInstaRt": "Median instantanous frequency",
    "dendriticType": "Dendrite type",
    "SomaLayerLoc": "Cortical layer",
}

# Raw source column name mappings for core ID/metadata columns
RAW_ID_MAPPINGS = {
    "Row": "internalID",
    "Identifier": "cellID",
}

DENDRITE_MAP = {"A": "Aspiny", "S": "Spiny"}
DENDRITE_DEFAULT = "Unk."

SUBJECT_ID_LENGTH = 3  # first N chars of internalID used as subject folder name

# Whether to auto-generate cellID by hashing row contents (when source has no Identifier column)
HASH_CELL_ID = False
