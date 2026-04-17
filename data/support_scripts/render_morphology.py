"""
Render SWC morphology files as PNG images for the web app.

Usage:
    python render_morphology.py                    # Use SWC_DIR from config/env
    python render_morphology.py --swc-dir ./swcs/  # Override SWC source directory
"""
import argparse
from pathlib import Path

from pipeline_config import SWC_DIR, MORPH_DIR
from id_utils import stem, check_prerequisite


def render_all(swc_dir: Path):
    """Convert all SWC files in swc_dir to full-size + thumbnail PNGs."""
    import matplotlib.pyplot as plt
    import ngauge
    from ngauge import Neuron

    check_prerequisite(swc_dir, "SWC directory (set PCTD_SWC_DIR env var)")
    MORPH_DIR.mkdir(parents=True, exist_ok=True)

    swc_files = list(Path(swc_dir).glob("*.swc"))
    print(f"Found {len(swc_files)} SWC files in {swc_dir}")

    for swc_file in swc_files:
        print(f"  Rendering: {swc_file.name}")
        morph = Neuron().from_swc(str(swc_file))
        morph.fix_parents()

        # Full-size render
        fig = morph.plot(fig=None, ax=None, color="k")
        ax = fig.get_axes()[0]
        ax.axis("off")

        output_name = stem(swc_file).replace(".", "_") + "_morph.png"
        fig.savefig(MORPH_DIR / output_name, dpi=300)
        plt.close(fig)

        # Thumbnail (48x48)
        fig = plt.figure(figsize=(0.48, 0.48), dpi=100)
        ax = fig.add_subplot(111)
        morph.plot(fig=fig, ax=ax, color="k")
        ax.axis("off")
        fig.patch.set_alpha(0)

        thumb_name = stem(swc_file).replace(".", "_") + "_morph_thumb.png"
        fig.savefig(MORPH_DIR / thumb_name, dpi=100)
        plt.close(fig)

    print(f"Rendered {len(swc_files)} morphologies -> {MORPH_DIR}")


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
