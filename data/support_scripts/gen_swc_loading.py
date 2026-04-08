# Script to load SWC files and save them as PNG images for use in the web app. 
# This is a one-time script to convert the SWC files to PNG images, which can then be used in the web app without needing to load the SWC files directly.

import glob
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import ngauge
from ngauge import Neuron
swc_dir = r"C:\Users\SMest\Downloads\NXWM NC Paper - Morpho\NXWM NC Paper - Morpho"
out_dir = r"data\morph"

def main():
    swc_files = glob.glob(swc_dir + "/*.swc")
    for swc_file in swc_files:
        print(f"Loading SWC file: {swc_file}")
        morph = Neuron().from_swc(swc_file)
        # Plot 
        fig = morph.plot(fig=None, ax=None, color="k" )

        # Format and save
        ax = fig.get_axes()[0]
        ax.axis('off')
        output_file = os.path.basename(swc_file).replace('.swc', '_morph')
        #also sub out periods in the name
        output_file = output_file.replace('.', '_')
        output_file = output_file + ".png"
        fig.savefig(os.path.join(out_dir, output_file), dpi=300)
        plt.close(fig)

        #make a smalll 48x48 thumbnail version of the image for use in the web app
        thumbnail_file = os.path.basename(swc_file).replace('.swc', '_morph_thumb')
        fig = plt.figure(figsize=(0.48, 0.48), dpi=100)
        ax = fig.add_subplot(111)
        morph.plot(fig=fig, ax=ax, color="k" )
        ax.axis('off')
        #make canvas transparent
        fig.patch.set_alpha(0)
        thumbnail_file = thumbnail_file.replace('.', '_')
        thumbnail_file = thumbnail_file + ".png"
        fig.savefig(os.path.join(out_dir, thumbnail_file), dpi=100)
        plt.close(fig)


    return

if __name__ == "__main__":
    main()