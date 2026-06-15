"""
Render SWC morphology files as PNG images for the web app.

Usage:
    python render_morphology.py                    # Use SWC_DIR from config/env
    python render_morphology.py --swc-dir ./swcs/  # Override SWC source directory
"""
import argparse
import shutil
from pathlib import Path

from pipeline_config import SWC_DIR, MORPH_DIR
from id_utils import stem, check_prerequisite, load_id_mapping, resolve_cell_id


def render_all(swc_dir: Path):
    """Convert all SWC files in swc_dir to full-size + thumbnail PNGs.

    Output assets are named by the external cellID (resolved from the SWC's
    internalID via box2_ephys.csv). The source SWC is also copied into MORPH_DIR
    under its cellID name so the website's morphology download link works.
    SWC files that cannot be matched to a known internalID are skipped.
    """
    import matplotlib.pyplot as plt
    import ngauge
    from ngauge import Neuron

    check_prerequisite(swc_dir, "SWC directory (set PCTD_SWC_DIR env var)")
    MORPH_DIR.mkdir(parents=True, exist_ok=True)

    mapping = load_id_mapping()  # {internalID: cellID}

    swc_files = list(Path(swc_dir).glob("*.swc"))
    print(f"Found {len(swc_files)} SWC files in {swc_dir}")

    rendered = 0
    skipped = 0
    for swc_file in swc_files:
        cell_id = resolve_cell_id(stem(swc_file), mapping)
        if cell_id is None:
            print(f"  SKIP (no internalID match): {swc_file.name}")
            skipped += 1
            continue

        print(f"  Rendering: {swc_file.name}  ->  cellID {cell_id}")
        morph = Neuron().from_swc(str(swc_file))
        morph.fix_parents()

        # Full-size render
        fig = morph.plot(fig=None, ax=None, color="k")
        ax = fig.get_axes()[0]
        ax.axis("off")

        output_name = f"{cell_id}_morph.png"
        fig.savefig(MORPH_DIR / output_name, dpi=300)
        plt.close(fig)

        # Thumbnail (48x48)
        fig = plt.figure(figsize=(0.48, 0.48), dpi=100)
        ax = fig.add_subplot(111)
        morph.plot(fig=fig, ax=ax, color="k")
        ax.axis("off")
        fig.patch.set_alpha(0)

        thumb_name = f"{cell_id}_morph_thumb.png"
        fig.savefig(MORPH_DIR / thumb_name, dpi=100)
        plt.close(fig)

        # Copy source SWC under its cellID name for the website download link.
        shutil.copyfile(swc_file, MORPH_DIR / f"{cell_id}.swc")
        rendered += 1

    print(f"Rendered {rendered} morphologies ({skipped} skipped) -> {MORPH_DIR}")


def main():
    parser = argparse.ArgumentParser(
        description="Render SWC morphology files as PNG images for the web app."
    )
    parser.add_argument("--swc-dir", type=Path, metavar="DIR",
                        help="Directory containing .swc files (overrides PCTD_SWC_DIR)")
    args = parser.parse_args()

    swc_dir = args.swc_dir if args.swc_dir else SWC_DIR
    render_all(swc_dir)


if __name__ == "__main__":
    main()
