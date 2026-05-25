"""
Prune voltage sweeps in trace CSVs.

For each CSV in --input-dir (default: data/traces), keep every Nth sweep
(--keep-stride, default 2 = every other sweep). If the resulting selection
contains no spiking sweep, additionally insert the FIRST spiking sweep,
preserving original row order.

CSV format:
    Line 1 (header):       SweepName,StimAmp,Var3_1,Var3_2,...
    Line 2 (time vector):  time,0.0,0.0,0.0002,0.0004,...
    Lines 3..N (sweeps):   Sweep_<n>,<injected_current_pA>,v0,v1,v2,...

The header and time-vector rows are ALWAYS preserved verbatim; pruning
operates only on the sweep rows.

Spike detection: any voltage sample > --spike-threshold (default 0.0 mV).
Resting potentials sit ~-75 mV; APs peak well above 0 mV.

Output goes to --output-dir (default: data/traces_pruned) UNLESS --in-place
is passed, in which case --input-dir is overwritten.

Usage:
    python prune_sweeps.py --dry-run
    python prune_sweeps.py
    python prune_sweeps.py --in-place --input-dir data/traces
"""
import argparse
from pathlib import Path


def parse_sweep_max_voltage(line: str) -> float:
    """Return the maximum voltage sample (columns 2..N) for one sweep row.

    Returns -inf if the row has too few columns to contain voltage data.
    """
    parts = line.rstrip("\r\n").split(",")
    if len(parts) < 3:
        return float("-inf")
    vmax = float("-inf")
    for tok in parts[2:]:
        tok = tok.strip()
        if not tok:
            continue
        try:
            v = float(tok)
        except ValueError:
            continue
        if v > vmax:
            vmax = v
    return vmax


def select_indices(n_sweeps: int, spiking: list[int], stride: int) -> list[int]:
    """Return sorted list of sweep indices to keep.

    Always includes indices 0, stride, 2*stride, ... If that set contains no
    spiking sweep but at least one spiking sweep exists, the first spiking
    index is added.
    """
    kept = set(range(0, n_sweeps, stride))
    if spiking and not (kept & set(spiking)):
        kept.add(spiking[0])
    return sorted(kept)


def process_file(
    src: Path,
    dest: Path,
    stride: int,
    spike_threshold: float,
    dry_run: bool,
) -> dict:
    with src.open("r", encoding="utf-8", newline="") as fh:
        lines = fh.readlines()

    # Drop trailing blank lines.
    trailing_blank = len(lines) > 0 and lines[-1].strip() == ""
    if trailing_blank:
        lines = lines[:-1]

    # First two lines are reserved: header + time vector. Pruning operates
    # only on the sweep rows that follow.
    if len(lines) < 3:
        # Not enough sweep rows to prune; emit verbatim.
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            out_lines = list(lines)
            if out_lines and not out_lines[-1].endswith("\n"):
                out_lines[-1] = out_lines[-1] + "\n"
            with dest.open("w", encoding="utf-8", newline="") as fh:
                fh.writelines(out_lines)
        return {
            "file": src.name,
            "n_in": max(0, len(lines) - 2),
            "n_out": max(0, len(lines) - 2),
            "n_spiking_in": 0,
            "n_spiking_kept": 0,
            "skipped": True,
        }

    header_line = lines[0]
    time_line = lines[1]
    sweep_lines = lines[2:]

    n_in = len(sweep_lines)
    spiking = [
        i for i, line in enumerate(sweep_lines)
        if parse_sweep_max_voltage(line) > spike_threshold
    ]

    keep = select_indices(n_in, spiking, stride)
    kept_spiking = [i for i in keep if i in set(spiking)]

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        out_lines = [header_line, time_line] + [sweep_lines[i] for i in keep]
        # Ensure last line ends with newline for cleanliness.
        if out_lines and not out_lines[-1].endswith("\n"):
            out_lines[-1] = out_lines[-1] + "\n"
        with dest.open("w", encoding="utf-8", newline="") as fh:
            fh.writelines(out_lines)

    return {
        "file": src.name,
        "n_in": n_in,
        "n_out": len(keep),
        "n_spiking_in": len(spiking),
        "n_spiking_kept": len(kept_spiking),
        "skipped": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input-dir", type=Path, default=Path("data/traces"))
    p.add_argument("--output-dir", type=Path, default=Path("data/traces_pruned"))
    p.add_argument("--in-place", action="store_true",
                   help="Overwrite files in --input-dir. Required to write back to source.")
    p.add_argument("--dry-run", action="store_true", help="Print summary; do not write any files.")
    p.add_argument("--spike-threshold", type=float, default=0.0,
                   help="Voltage (mV) above which a sweep is considered spiking (default: 0.0).")
    p.add_argument("--keep-stride", type=int, default=2,
                   help="Keep every Nth sweep starting from index 0 (default: 2).")
    args = p.parse_args()

    if args.keep_stride < 1:
        p.error("--keep-stride must be >= 1")

    in_dir: Path = args.input_dir
    if not in_dir.is_dir():
        p.error(f"--input-dir does not exist: {in_dir}")

    if args.in_place:
        out_dir = in_dir
    else:
        out_dir = args.output_dir

    csvs = sorted(in_dir.glob("*.csv"))
    if not csvs:
        print(f"No CSVs found in {in_dir}")
        return

    mode = "DRY RUN" if args.dry_run else ("IN-PLACE" if args.in_place else f"-> {out_dir}")
    print(f"Pruning sweeps in {len(csvs)} file(s) from {in_dir}  [{mode}]")
    print(f"  stride={args.keep_stride}  spike_threshold={args.spike_threshold} mV")
    print()
    header = f"{'file':<55} {'in':>5} {'out':>5} {'spk_in':>7} {'spk_kept':>9}"
    print(header)
    print("-" * len(header))

    total_in = total_out = total_spk_in = total_spk_kept = 0
    skipped = 0
    no_spike_files = []

    for src in csvs:
        dest = out_dir / src.name
        info = process_file(src, dest, args.keep_stride, args.spike_threshold, args.dry_run)
        flag = " SKIP" if info["skipped"] else ""
        print(f"{info['file']:<55} {info['n_in']:>5} {info['n_out']:>5} "
              f"{info['n_spiking_in']:>7} {info['n_spiking_kept']:>9}{flag}")
        if info["skipped"]:
            skipped += 1
            continue
        total_in += info["n_in"]
        total_out += info["n_out"]
        total_spk_in += info["n_spiking_in"]
        total_spk_kept += info["n_spiking_kept"]
        if info["n_spiking_in"] == 0:
            no_spike_files.append(info["file"])

    print()
    print(f"Totals: in={total_in}  out={total_out}  "
          f"spk_in={total_spk_in}  spk_kept={total_spk_kept}  skipped={skipped}")
    if no_spike_files:
        print(f"WARNING: {len(no_spike_files)} file(s) had NO sweep above "
              f"{args.spike_threshold} mV (no spiking sweep to preserve):")
        for f in no_spike_files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
