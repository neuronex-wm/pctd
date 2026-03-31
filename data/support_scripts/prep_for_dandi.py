# This script will be used to organize all the nwbs for upload to DANDI
# Here we will pull the NWBs (ID'd by internal name), and rename them according to the cellID mapping in the provided CSV, and copy them to the new directory for upload to DANDI.
import glob

import pandas
import os
import shutil

data_folders = [r"C:\Users\SMest\Downloads\DATA_NXWM_GOE_2025\DATA_NXWM_GOE_2025", r"G:\Data4Website" ]

id_lookup_csv = r"C:\Users\SMest\source\pctd\data\box2_ephys.csv"
new_nwb_dir = r"C:\Users\SMest\source\pctd\data\nwbs"

def main():
    #read the csv
    df = pandas.read_csv(id_lookup_csv)
    #create a dictionary from the csv
    id_dict = dict(zip(df['internalID'], df['cellID']))
    #for each folder in the data folders
    for folder in data_folders:
        #glob the nwbs
        nwbs = glob.glob(os.path.join(folder, "*.nwb"))
        #for each nwb file in the folder
        for nwb in nwbs:
            internal_id = os.path.basename(nwb).split('.')[0]
            if internal_id in id_dict:
                #org by subject in internalID, (should be first 3 characters)
                # Just keeps the PI's happy
                subj = internal_id[:3]
                if not os.path.exists(os.path.join(new_nwb_dir, subj)):
                    os.makedirs(os.path.join(new_nwb_dir, subj))

                cell_id = id_dict[internal_id]
                new_file_name = str(cell_id) + ".nwb"
                shutil.copy(os.path.join(folder, nwb), os.path.join(new_nwb_dir, subj, new_file_name))
                print(f"Copied {nwb} to {new_file_name}")
    return

if __name__ == "__main__":
    main()