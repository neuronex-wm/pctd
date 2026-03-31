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
    return

if __name__ == "__main__":
    main()