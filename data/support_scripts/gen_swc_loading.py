import glob
import pandas as pd
import numpy as np
array = []
def main():
    #glob the csvs
    csvs = glob.glob("swc//*.swc")
    for f in csvs:
        filename = ''.join(f.split('.swc')[:-1]).split('\\')[-1]
        array.append(f"<option value=\"swc\{filename}.swc\">{filename}</option>")
        #parsed = json.loads(json_df)
        #json_str = json.dumps(parsed, indent=4)
    np.savetxt("swc_list.txt", array, delimiter=" ", newline = "\n", fmt="%s")
    return

if __name__=="__main__":
    main()