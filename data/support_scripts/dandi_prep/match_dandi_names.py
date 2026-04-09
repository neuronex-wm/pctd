"""
Match updated_nwbs filenames (cellID.nwb) to DANDI-renamed filenames
in ./001776/ using file-size matching (Tier 1), with h5py session
timestamp matching as fallback (Tier 2).

Output: data/dandi_mapping.csv
"""
import os
import glob
import csv
import re
from collections import defaultdict

# ── paths (relative to repo root) ───────────────────────────────────
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPDATED_NWBS = os.path.join(REPO_ROOT, "data", "updated_nwbs")
DANDI_DIR = os.path.join(REPO_ROOT, "001776")
OUTPUT_CSV = os.path.join(REPO_ROOT, "data", "dandi_mapping.csv")

# ── subject-folder mapping ──────────────────────────────────────────
# updated_nwbs uses short names (A09, M16); DANDI uses sub-A9W, sub-M16G, etc.
# We build the mapping dynamically by listing what exists.

def _dandi_subject_folders():
    """Return dict: folder_name -> full_path for all sub-* dirs in DANDI."""
    folders = {}
    for entry in os.listdir(DANDI_DIR):
        full = os.path.join(DANDI_DIR, entry)
        if os.path.isdir(full) and entry.startswith("sub-"):
            folders[entry] = full
    return folders


def _build_subject_mapping():
    """
    Return dict: updated_nwbs_subdir -> [list of DANDI sub-* dirs].
    Most subjects map 1:1; M16 and M17 map to both G and W variants.
    """
    dandi_folders = _dandi_subject_folders()
    mapping = {}

    for src_subdir in sorted(os.listdir(UPDATED_NWBS)):
        src_path = os.path.join(UPDATED_NWBS, src_subdir)
        if not os.path.isdir(src_path):
            continue

        # Extract the numeric part: A09->9, A10->10, M16->16, etc.
        letter = src_subdir[0]      # A or M
        number = src_subdir[1:]     # "09", "16", etc.
        num_stripped = str(int(number))  # strip leading zero: "09" -> "9"

        candidates = []
        if letter == "A":
            # A subjects -> sub-A{num}W  (DANDI strips leading zeros: A09->A9W)
            key = f"sub-A{num_stripped}W"
            if key in dandi_folders:
                candidates.append(dandi_folders[key])
        elif letter == "M":
            # M subjects -> sub-M{num}G and possibly sub-M{num}W
            # DANDI keeps the original number (M02->M02G, not M2G)
            for suffix in ("G", "W"):
                # Try original number first, then stripped
                for num_variant in (number, num_stripped):
                    key = f"sub-M{num_variant}{suffix}"
                    if key in dandi_folders and dandi_folders[key] not in candidates:
                        candidates.append(dandi_folders[key])

        if not candidates:
            print(f"WARNING: No DANDI folder found for {src_subdir}")
        mapping[src_path] = candidates

    return mapping


def _nwb_files(directory):
    """Return list of (filename, full_path, file_size) for .nwb files."""
    results = []
    for f in os.listdir(directory):
        if f.endswith(".nwb"):
            fp = os.path.join(directory, f)
            results.append((f, fp, os.path.getsize(fp)))
    return results


# ── Tier 1: file-size matching ──────────────────────────────────────

def match_by_size(src_files, dandi_files):
    """
    Attempt 1:1 matching by unique file size.
    Returns (matched_pairs, unmatched_src, unmatched_dandi).
    matched_pairs: list of (src_name, src_path, dandi_name, dandi_path)
    """
    # Group DANDI files by size
    dandi_by_size = defaultdict(list)
    for name, path, size in dandi_files:
        dandi_by_size[size].append((name, path))

    matched = []
    unmatched_src = []

    for src_name, src_path, src_size in src_files:
        candidates = dandi_by_size.get(src_size, [])
        if len(candidates) == 1:
            dandi_name, dandi_path = candidates[0]
            matched.append((src_name, src_path, dandi_name, dandi_path))
            # Remove from pool to prevent double-matching
            del dandi_by_size[src_size]
        elif len(candidates) == 0:
            unmatched_src.append((src_name, src_path, src_size))
        else:
            # Ambiguous — multiple DANDI files with same size
            unmatched_src.append((src_name, src_path, src_size))

    # Remaining DANDI files
    unmatched_dandi = []
    for size, items in dandi_by_size.items():
        for name, path in items:
            unmatched_dandi.append((name, path, size))

    return matched, unmatched_src, unmatched_dandi


# ── Tier 2: h5py session_start_time matching ────────────────────────

def _read_session_start_time(nwb_path):
    """Read session_start_time from NWB file using h5py (fast, single attr)."""
    try:
        import h5py
    except ImportError:
        return None
    try:
        with h5py.File(nwb_path, "r") as f:
            ts = f.get("session_start_time")
            if ts is not None:
                val = ts[()]
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                return str(val)
            # Also try as an attribute on the root
            if "session_start_time" in f.attrs:
                val = f.attrs["session_start_time"]
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                return str(val)
    except Exception as e:
        print(f"  h5py read error for {nwb_path}: {e}")
    return None


def _parse_dandi_timestamp(dandi_filename):
    """Extract session timestamp from DANDI filename like
    sub-A10W_ses-20210602T162346_icephys.nwb -> '20210602T162346'"""
    m = re.search(r"ses-(\d{8}T\d{6})", dandi_filename)
    return m.group(1) if m else None


def match_by_timestamp(unmatched_src, unmatched_dandi):
    """
    Fallback: match remaining files by reading session_start_time from NWB.
    Returns (matched_pairs, still_unmatched_src, still_unmatched_dandi).
    """
    try:
        import h5py  # noqa: F401
    except ImportError:
        print("  h5py not available — cannot run Tier 2 matching.")
        print("  Install with: pip install h5py")
        return [], unmatched_src, unmatched_dandi

    # Build index of DANDI files by their filename-embedded timestamp
    dandi_by_ts = defaultdict(list)
    for name, path, size in unmatched_dandi:
        ts = _parse_dandi_timestamp(name)
        if ts:
            dandi_by_ts[ts].append((name, path, size))

    matched = []
    still_unmatched_src = []

    for src_name, src_path, src_size in unmatched_src:
        src_ts_raw = _read_session_start_time(src_path)
        if src_ts_raw is None:
            still_unmatched_src.append((src_name, src_path, src_size))
            continue

        # Normalize to YYYYMMDDTHHMMSS format
        ts_clean = re.sub(r"[^0-9T]", "", src_ts_raw.replace("-", "").replace(":", "").split("+")[0].split(".")[0])
        candidates = dandi_by_ts.get(ts_clean, [])

        if len(candidates) == 1:
            dandi_name, dandi_path, _ = candidates[0]
            matched.append((src_name, src_path, dandi_name, dandi_path))
            del dandi_by_ts[ts_clean]
        elif len(candidates) > 1:
            # Try narrowing by file size
            size_match = [c for c in candidates if c[2] == src_size]
            if len(size_match) == 1:
                dandi_name, dandi_path, _ = size_match[0]
                matched.append((src_name, src_path, dandi_name, dandi_path))
                candidates.remove(size_match[0])
                # Update the index
                dandi_by_ts[ts_clean] = candidates
            else:
                still_unmatched_src.append((src_name, src_path, src_size))
        else:
            still_unmatched_src.append((src_name, src_path, src_size))

    still_unmatched_dandi = []
    for ts, items in dandi_by_ts.items():
        for name, path, size in items:
            still_unmatched_dandi.append((name, path, size))

    return matched, still_unmatched_src, still_unmatched_dandi


# ── main ────────────────────────────────────────────────────────────

def main():
    subject_map = _build_subject_mapping()

    all_matched = []
    all_unmatched_src = []
    all_unmatched_dandi = []
    total_src = 0
    total_dandi = 0

    print("=" * 70)
    print("Phase 1: Subject folder mapping")
    print("=" * 70)
    for src_dir, dandi_dirs in sorted(subject_map.items()):
        src_subdir = os.path.basename(src_dir)
        dandi_names = [os.path.basename(d) for d in dandi_dirs]
        src_files = _nwb_files(src_dir)
        dandi_files = []
        for dd in dandi_dirs:
            dandi_files.extend(_nwb_files(dd))
        total_src += len(src_files)
        total_dandi += len(dandi_files)
        status = "OK" if len(src_files) == len(dandi_files) else "MISMATCH"
        print(f"  {src_subdir:6s} -> {', '.join(dandi_names):30s}  "
              f"src={len(src_files):3d}  dandi={len(dandi_files):3d}  [{status}]")

    print(f"\nTotal: src={total_src}, dandi={total_dandi}")

    print("\n" + "=" * 70)
    print("Phase 2: File-size matching (Tier 1)")
    print("=" * 70)

    for src_dir, dandi_dirs in sorted(subject_map.items()):
        src_subdir = os.path.basename(src_dir)
        src_files = _nwb_files(src_dir)
        dandi_files = []
        for dd in dandi_dirs:
            dandi_files.extend(_nwb_files(dd))

        matched, unmatched_s, unmatched_d = match_by_size(src_files, dandi_files)

        for s_name, s_path, d_name, d_path in matched:
            all_matched.append((s_name, s_path, d_name, d_path, "size"))

        if unmatched_s:
            print(f"  {src_subdir}: {len(unmatched_s)} src files unmatched by size")
            all_unmatched_src.extend(unmatched_s)
        if unmatched_d:
            all_unmatched_dandi.extend(unmatched_d)

    print(f"\nTier 1 results: {len(all_matched)} matched, "
          f"{len(all_unmatched_src)} src unmatched, "
          f"{len(all_unmatched_dandi)} dandi unmatched")

    # ── Tier 2 fallback ─────────────────────────────────────────────
    if all_unmatched_src:
        print("\n" + "=" * 70)
        print("Phase 3: h5py timestamp matching (Tier 2)")
        print("=" * 70)

        t2_matched, still_src, still_dandi = match_by_timestamp(
            all_unmatched_src, all_unmatched_dandi
        )
        for s_name, s_path, d_name, d_path in t2_matched:
            all_matched.append((s_name, s_path, d_name, d_path, "timestamp"))

        all_unmatched_src = still_src
        all_unmatched_dandi = still_dandi

        print(f"  Tier 2 matched: {len(t2_matched)}")
        print(f"  Still unmatched src: {len(all_unmatched_src)}")
        print(f"  Still unmatched dandi: {len(all_unmatched_dandi)}")

    # ── Report unmatched ────────────────────────────────────────────
    if all_unmatched_src:
        print("\n--- UNMATCHED SOURCE FILES ---")
        for name, path, size in all_unmatched_src:
            print(f"  {name}  ({size:,} bytes)")

    if all_unmatched_dandi:
        print(f"\n--- UNMATCHED DANDI FILES ({len(all_unmatched_dandi)}) ---")
        for name, path, size in all_unmatched_dandi:
            print(f"  {name}  ({size:,} bytes)")

    # ── Write output CSV ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"Writing {len(all_matched)} matches to {OUTPUT_CSV}")
    print("=" * 70)

    # Extract cellID from source filename (strip .nwb)
    rows = []
    for s_name, s_path, d_name, d_path, method in sorted(all_matched):
        cell_id = os.path.splitext(s_name)[0]
        # Relative paths from repo root
        src_rel = os.path.relpath(s_path, REPO_ROOT)
        dandi_rel = os.path.relpath(d_path, REPO_ROOT)
        rows.append({
            "cellID": cell_id,
            "updated_nwbs_path": src_rel,
            "dandi_path": dandi_rel,
            "dandi_filename": d_name,
            "match_method": method,
        })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cellID", "updated_nwbs_path", "dandi_path", "dandi_filename", "match_method"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. {len(rows)} rows written.")

    # ── Summary ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  Source files (updated_nwbs):  {total_src}")
    print(f"  DANDI files (001776):         {total_dandi}")
    print(f"  Matched:                      {len(all_matched)}")
    print(f"  Unmatched source:             {len(all_unmatched_src)}")
    print(f"  Unmatched DANDI:              {len(all_unmatched_dandi)}")
    methods = defaultdict(int)
    for *_, m in all_matched:
        methods[m] += 1
    for m, count in sorted(methods.items()):
        print(f"    via {m}: {count}")


if __name__ == "__main__":
    main()
