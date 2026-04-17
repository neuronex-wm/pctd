"""
Copy trace files from a local directory into data/traces/, renaming by internalID.

Usage:
    python pull_traces.py --source-dir /path/to/traces/
"""
import argparse
import shutil
from pathlib import Path

from pipeline_config import BOX2_CSV, TRACES_DIR
from id_utils import load_id_mapping


def rename_traces(source_dir: Path):
    """Copy traces from *source_dir* into TRACES_DIR, keeping internalID names.

    Source files may be named by cellID (numeric) or internalID (string).
    Files already named by internalID are copied as-is; files named by
    cellID are renamed to the corresponding internalID.
    """
    id_map = load_id_mapping()                       # {internalID: cellID}
    cellid_to_internal = {v: k for k, v in id_map.items()}

    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0

    for src in sorted(source_dir.glob("*.csv")):
        stem = src.stem
        # Already an internalID?
        if stem in id_map:
            dest = TRACES_DIR / src.name
        else:
            # Try interpreting as cellID (numeric)
            try:
                cid = int(stem)
            except ValueError:
                print(f"  SKIP {src.name} (unrecognised name)")
                continue
            internal = cellid_to_internal.get(cid)
            if internal is None:
                print(f"  SKIP {src.name} (cellID {cid} not in mapping)")
                continue
            dest = TRACES_DIR / f"{internal}.csv"

        shutil.copy2(src, dest)
        copied += 1

    print(f"Copied {copied} trace(s) from {source_dir} -> {TRACES_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Copy and rename trace files.")
    parser.add_argument(
        "--source-dir", required=True, type=str,
        help="Local directory containing trace CSV files",
    )
    args = parser.parse_args()
    rename_traces(Path(args.source_dir))


if __name__ == "__main__":
    main()
