"""
One-time migration: rename morphology assets in MORPH_DIR from internalID-based
names to external cellID-based names.

Renames, for each cell:
    {internalID}.swc              -> {cellID}.swc
    {internalID}_morph.png        -> {cellID}_morph.png
    {internalID}_morph_thumb.png  -> {cellID}_morph_thumb.png

Extended SWC names (e.g. M26_VK_A1_C02_Goettingen_NPI_Cell02) are matched to
their base internalID via fuzzy/base-name matching (see id_utils.resolve_internal_id).

Safety:
    - Dry-run by default: prints the plan and writes a mapping log CSV, but
      changes nothing on disk. Pass --apply to perform the renames.
    - Never overwrites an existing target. When several source files resolve to
      the same target name (base + extended duplicates, or many internalID -> one
      cellID), the first is kept and the rest are logged as SKIPPED-collision.

Usage:
    python rename_morph_to_cellid.py                 # dry-run
    python rename_morph_to_cellid.py --apply         # perform renames
    python rename_morph_to_cellid.py --morph-dir DIR --log plan.csv
"""
import argparse
import csv
from pathlib import Path

from pipeline_config import MORPH_DIR
from id_utils import (
    load_id_mapping,
    resolve_internal_id,
    classify_match,
    check_prerequisite,
)


# Asset suffixes, longest first so "_morph_thumb.png" matches before "_morph.png".
SUFFIXES = ("_morph_thumb.png", "_morph.png", ".swc")


def split_suffix(filename: str):
    """Return (base, suffix) for a known morphology asset, else (None, None)."""
    for suffix in SUFFIXES:
        if filename.endswith(suffix):
            return filename[: -len(suffix)], suffix
    return None, None


def _match_quality(kind: str) -> int:
    """Rank match kinds (lower is better) so exact wins collision arbitration."""
    return {"exact": 0, "prefix": 1, "suffix": 2, "fuzzy": 3}.get(kind, 9)


def plan_renames(morph_dir: Path, mapping: dict, fuzzy_area: bool = True):
    """
    Build the rename plan.

    Returns a list of dict rows with keys:
        old_name, new_name, internalID, cellID, status
    where status is one of: rename, rename-fuzzy, skip-unmapped,
    skip-collision, skip-noop.

    ``rename-fuzzy`` flags area-agnostic matches (the area token differs between
    the morphology filename and the internalID) so they can be audited.

    When several source files resolve to the same target name (base + extended
    duplicates, or many internalID -> one cellID), the best-quality match
    (exact > prefix > suffix > fuzzy-area) is kept and the rest are marked
    skip-collision, so the outcome is independent of filesystem ordering.
    """
    internal_ids = list(mapping.keys())
    files = sorted(p for p in morph_dir.iterdir() if p.is_file())

    rows = []
    candidates = {}  # new_name -> chosen candidate dict

    for path in files:
        base, suffix = split_suffix(path.name)
        if base is None:
            continue  # not a morphology asset we manage

        internal_id = resolve_internal_id(base, internal_ids, fuzzy_area=fuzzy_area)
        if internal_id is None:
            rows.append({
                "old_name": path.name, "new_name": "",
                "internalID": "", "cellID": "", "status": "skip-unmapped",
            })
            continue

        cell_id = mapping[internal_id]
        new_name = f"{cell_id}{suffix}"
        kind = classify_match(base, str(internal_id))

        if new_name == path.name:
            rows.append({
                "old_name": path.name, "new_name": new_name,
                "internalID": internal_id, "cellID": cell_id, "status": "skip-noop",
            })
            continue

        cand = {
            "old_name": path.name, "new_name": new_name,
            "internalID": internal_id, "cellID": cell_id,
            "kind": kind,
            "quality": _match_quality(kind),
            "exists": (morph_dir / new_name).exists(),
        }
        prev = candidates.get(new_name)
        if prev is None:
            candidates[new_name] = cand
        else:
            # Keep the better match; loser becomes a collision.
            winner, loser = (prev, cand) if cand["quality"] >= prev["quality"] else (cand, prev)
            candidates[new_name] = winner
            rows.append({
                "old_name": loser["old_name"], "new_name": new_name,
                "internalID": loser["internalID"], "cellID": loser["cellID"],
                "status": "skip-collision",
            })

    for new_name, cand in candidates.items():
        # A pre-existing on-disk target that isn't itself being renamed is a collision.
        if cand["exists"]:
            status = "skip-collision"
        elif cand["kind"] == "fuzzy":
            status = "rename-fuzzy"
        else:
            status = "rename"
        rows.append({
            "old_name": cand["old_name"], "new_name": new_name,
            "internalID": cand["internalID"], "cellID": cand["cellID"],
            "status": status,
        })

    return rows


def write_log(rows, log_path: Path):
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["old_name", "new_name", "internalID", "cellID", "status"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Rename morphology assets from internalID to cellID names."
    )
    parser.add_argument("--apply", action="store_true",
                        help="Perform the renames (default is a dry-run).")
    parser.add_argument("--morph-dir", type=Path, default=MORPH_DIR,
                        help=f"Morphology asset directory (default: {MORPH_DIR}).")
    parser.add_argument("--log", type=Path, default=None,
                        help="Path for the mapping log CSV "
                             "(default: <morph-dir>/rename_morph_log.csv).")
    parser.add_argument("--no-fuzzy", action="store_true",
                        help="Disable area-agnostic fuzzy matching (treat the "
                             "area token as part of cell identity).")
    args = parser.parse_args()

    morph_dir = args.morph_dir
    check_prerequisite(morph_dir, "morphology directory")
    log_path = args.log if args.log else morph_dir / "rename_morph_log.csv"

    mapping = load_id_mapping()  # {internalID: cellID}
    rows = plan_renames(morph_dir, mapping, fuzzy_area=not args.no_fuzzy)

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] morph-dir: {morph_dir}")
    for r in rows:
        if r["status"] == "rename":
            print(f"  {r['old_name']}  ->  {r['new_name']}")
        elif r["status"] == "rename-fuzzy":
            print(f"  {r['old_name']}  ->  {r['new_name']}  (FUZZY subject+cell: {r['internalID']})")
        elif r["status"] == "skip-unmapped":
            print(f"  SKIP (no internalID match): {r['old_name']}")
        elif r["status"] == "skip-collision":
            print(f"  SKIP (target exists/claimed): {r['old_name']} -> {r['new_name']}")
        # skip-noop is silent

    if args.apply:
        for r in rows:
            if r["status"] in ("rename", "rename-fuzzy"):
                (morph_dir / r["old_name"]).rename(morph_dir / r["new_name"])

    write_log(rows, log_path)

    print("\nSummary:")
    for status in ("rename", "rename-fuzzy", "skip-noop", "skip-unmapped", "skip-collision"):
        if status in counts:
            print(f"  {status}: {counts[status]}")
    print(f"Log written to: {log_path}")
    if not args.apply:
        print("\nDry-run only. Re-run with --apply to perform the renames.")


if __name__ == "__main__":
    main()
