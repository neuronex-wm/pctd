"""
Run the PCTD data pipeline end-to-end, or individual steps.

Usage:
    python run_pipeline.py                           # run all steps
    python run_pipeline.py convert                   # full regeneration from source CSV
    python run_pipeline.py append path/to/new.csv    # append new cells to existing DB
    python run_pipeline.py traces --source-dir ./x/  # copy/rename traces
    python run_pipeline.py morph                     # render morphology PNGs
    python run_pipeline.py dandi                     # prepare NWBs for DANDI
"""
import argparse
import sys
from pathlib import Path

from pipeline_config import BOX2_CSV, BOX2_JSON, TRACES_DIR, MORPH_DIR, SOURCE_CSV


def validate_step(step_name: str):
    """Check that outputs from a prerequisite step exist."""
    checks = {
        "convert": [BOX2_CSV, BOX2_JSON],
        "traces": [TRACES_DIR],
        "morph": [MORPH_DIR],
    }
    if step_name in checks:
        for path in checks[step_name]:
            if not path.exists():
                print(f"WARNING: Expected output from '{step_name}' not found: {path}")
                return False
    return True


def run_convert(args):
    """Full regeneration from source CSV."""
    from convert_dataset import full_convert
    source = Path(args.source) if hasattr(args, "source") and args.source else SOURCE_CSV
    full_convert(source)


def run_append(args):
    """Append new cells to existing database."""
    from convert_dataset import append_cells
    append_cells(Path(args.csv))


def run_traces(args):
    """Copy and rename trace files from a local directory."""
    from pull_traces import rename_traces
    if not validate_step("convert"):
        print("Hint: run 'convert' or 'append' first to generate box2_ephys.csv")
    if not args.source_dir:
        print("Specify --source-dir. See --help.")
        sys.exit(1)
    rename_traces(Path(args.source_dir))


def run_morph(args):
    """Render morphology PNGs from SWC files."""
    from render_morphology import render_all
    from pipeline_config import SWC_DIR
    swc_dir = Path(args.swc_dir) if hasattr(args, "swc_dir") and args.swc_dir else SWC_DIR
    render_all(swc_dir)


def run_dandi(args):
    """Run DANDI preparation steps."""
    if not validate_step("convert"):
        print("Hint: run 'convert' or 'append' first to generate box2_ephys.csv")
    # Import and run the existing dandi prep
    sys.path.insert(0, str(Path(__file__).parent / "dandi_prep"))
    from prep_for_dandi import main as prep_main
    prep_main()


def main():
    parser = argparse.ArgumentParser(
        description="PCTD data pipeline orchestrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  convert   Full regeneration from source CSV (requires PCTD_SOURCE_CSV)
  append    Append/merge new cells into the existing database
  traces    Copy and rename local trace files
  morph     Render SWC morphology files as PNGs
  dandi     Prepare NWBs for DANDI upload

Common workflows:
  # New contributor adding cells to the database:
  python run_pipeline.py append path/to/new_cells.csv

  # Full rebuild from scratch:
  set PCTD_SOURCE_CSV=C:\\path\\to\\full_dataset.csv
  python run_pipeline.py convert traces morph dandi
""",
    )
    subparsers = parser.add_subparsers(dest="step")

    # convert
    p_convert = subparsers.add_parser("convert", help="Full regeneration from source CSV")
    p_convert.add_argument("--source", "-s", type=str, help="Path to source CSV")
    p_convert.set_defaults(func=run_convert)

    # append
    p_append = subparsers.add_parser("append", help="Append new cells to existing DB")
    p_append.add_argument("csv", type=str, help="Path to CSV with new cells")
    p_append.set_defaults(func=run_append)

    # traces
    p_traces = subparsers.add_parser("traces", help="Copy/rename local trace files")
    p_traces.add_argument("--source-dir", required=True, type=str, help="Local dir of traces to copy")
    p_traces.set_defaults(func=run_traces)

    # morph
    p_morph = subparsers.add_parser("morph", help="Render morphology PNGs")
    p_morph.add_argument("--swc-dir", type=str, help="Directory with .swc files")
    p_morph.set_defaults(func=run_morph)

    # dandi
    p_dandi = subparsers.add_parser("dandi", help="Prepare NWBs for DANDI upload")
    p_dandi.set_defaults(func=run_dandi)

    args = parser.parse_args()

    if args.step is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
