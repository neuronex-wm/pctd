import pandas
import os
import shutil

id_lookup_csv = r"C:\Users\SMest\Dropbox\pctd-master\pctd-master\data\box2_ephys.csv"
traces_dir = r"C:\Users\SMest\source\pctd\data\traces"
def main():
    #read the csv
    df = pandas.read_csv(id_lookup_csv)
    #create a dictionary from the csv
    id_dict = dict(zip(df['cellID'], df['internalID']))
    #save the dictionary as a json
    #for each file in the traces directory, rename it to the corresponding cellID from the dictionary
    for file in os.listdir(traces_dir):
        if file.endswith(".csv"):
            internal_id = file.split('.')[0]
            if int(internal_id) in id_dict:
                cell_id = id_dict[int(internal_id)]
                new_file_name = cell_id + ".csv"
                shutil.copy(os.path.join(traces_dir, file), os.path.join(traces_dir, new_file_name))
                print(f"Renamed {file} to {new_file_name}")
    return

if __name__ == "__main__":   
    main()