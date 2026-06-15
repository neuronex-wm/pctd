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


def resolve_internal_id(name: str, internal_ids, fuzzy_area: bool = False) -> str | None:
    """
    Resolve a morphology asset name to its base internalID.

    Strips the morphology suffixes (``_morph``, ``_thumb``) and matches the
    remaining stem against ``internal_ids`` using, in priority order:

      1. Exact match (``stem == internalID``).
      2. Disk name extends an internalID, e.g. an extended SWC name
         ``M26_VK_A1_C02_Goettingen_NPI_Cell02`` for internalID
         ``M26_VK_A1_C02`` — the longest such internalID wins.
      3. An internalID extends the disk name, e.g. a short file
         ``M18_SP_A1_C05`` for internalID
         ``M18_SP_A1_C05_Goettingen_HEKA_Cell05`` — used only when exactly
         one internalID matches (ambiguous prefixes are left unmatched).
      4. (only if ``fuzzy_area``) Identity-token match: for a 4-token name
         ``{subject}_{initials}_{area}_{cell}`` the ``initials`` token (the
         tracing experimentalist) and the ``area`` token (a reconstruction
         label) are treated as morphology-side metadata, not part of cell
         identity. Matches an internalID with the same subject and cell number
         but a different initials and/or area token — used only when exactly
         one such candidate exists. E.g. ``A11_SA_A1_C02`` -> ``A11_MM_A1_C02``
         or ``A19_MM_A5_C05`` -> ``A19_MM_A1_C05``.

    Returns None if no internalID matches (or a match is ambiguous).
    """
    s = str(name)
    for suffix in ("_thumb", "_morph"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    ids = [str(i) for i in internal_ids]

    # 1. Exact match.
    if s in ids:
        return s
    # 2. Disk name extends an internalID (disk longer): longest internalID wins.
    prefix_matches = [iid for iid in ids if s.startswith(iid + "_")]
    if prefix_matches:
        return max(prefix_matches, key=len)
    # 3. An internalID extends the disk name (CSV longer): only if unambiguous.
    suffix_matches = [iid for iid in ids if iid.startswith(s + "_")]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    # 4. Identity-token match (opt-in): subject + cell number, ignoring the
    #    initials (experimentalist) and area (reconstruction) tokens.
    if fuzzy_area:
        return _resolve_fuzzy_identity(s, ids)
    return None


def _resolve_fuzzy_identity(stem_name: str, ids) -> str | None:
    """
    Match a 4-token ``{subject}_{initials}_{area}_{cell}`` name to an internalID
    that shares the subject and cell number but differs in the initials and/or
    area token. Returns the match only when exactly one candidate exists, else
    None. The initials token is the tracing experimentalist and the area token
    is a reconstruction label — neither is part of cell identity.
    """
    toks = stem_name.split("_")
    if len(toks) != 4:
        return None
    subject, initials, area, cell = toks
    candidates = []
    for iid in ids:
        it = str(iid).split("_")
        if len(it) != 4:
            continue
        if it[0] == subject and it[3] == cell and (it[1] != initials or it[2] != area):
            candidates.append(iid)
    return candidates[0] if len(candidates) == 1 else None


def classify_match(stem_name: str, internal_id: str) -> str:
    """
    Describe how ``stem_name`` (already suffix-stripped) relates to its resolved
    ``internal_id``: 'exact', 'prefix' (disk extends id), 'suffix' (id extends
    disk), or 'fuzzy' (same subject/cell, different initials and/or area token).
    """
    s, iid = str(stem_name), str(internal_id)
    if s == iid:
        return "exact"
    if s.startswith(iid + "_"):
        return "prefix"
    if iid.startswith(s + "_"):
        return "suffix"
    return "fuzzy"


def resolve_cell_id(name: str, mapping: dict, fuzzy_area: bool = False):
    """
    Resolve a morphology asset name to its external cellID.

    ``mapping`` is a ``{internalID: cellID}`` dict (see ``load_id_mapping``).
    Returns None if the name cannot be matched to a known internalID.
    """
    internal_id = resolve_internal_id(name, mapping.keys(), fuzzy_area=fuzzy_area)
    if internal_id is None:
        return None
    return mapping[internal_id]


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
