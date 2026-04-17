"""
Pulls pregenerated GOE traces from the provided directory, renames them according to the internalID to cellID mapping in the provided CSV, and copies them to the new directory.
"""
import pandas
import os
import shutil
import glob

id_lookup_csv = r"C:\Users\SMest\source\pctd\data\box2_ephys.csv"
traces_dir = r"C:\Users\SMest\Downloads\DATA_NXWM_GOE_2025\traces"
new_traces_dir = r"C:\Users\SMest\source\pctd\data\traces"
def main():
    #read the csv
    df = pandas.read_csv(id_lookup_csv)
    #create a dictionary from the csv
    id_dict = dict(zip(df['internalID'], df['cellID']))
    #glob them csvs
    traces = glob.glob(os.path.join(traces_dir, "*.csv"))
    #for each file in the traces directory
    for file in traces:
        if file.endswith(".csv"):
            internal_id = os.path.basename(file).split('.')[0]
            if internal_id in id_dict:
                cell_id = internal_id
                new_file_name = cell_id + ".csv"
                shutil.copy(os.path.join(traces_dir, file), os.path.join(new_traces_dir, new_file_name))
                print(f"Copied {file} to {new_file_name}")
    return

if __name__ == "__main__":   
    main()