# Converts all csv files in the current directory and subdirectories to json files with the same name. The json files are saved in the same directory as the csv files.
# DEPRECATED: This script is no longer needed, as the csv files are now saved in the correct format to begin with. This script was used to convert the csv files from the old naming conventions to the new naming conventions,
#  but now that the csv files are saved in the new naming conventions, this script is no longer needed.


import glob
import pandas as pd
import json
def main():
    #glob the csvs
    csvs = glob.glob(".//**//*.csv", recursive=True)
    for f in csvs:
        filename = f.split('.')[0]
        df = pd.read_csv(f)
        json_df = df.to_json(filename+'.json', orient='records', indent=4)
        #parsed = json.loads(json_df)
        #json_str = json.dumps(parsed, indent=4)  
    return

if __name__=="__main__":
    main()