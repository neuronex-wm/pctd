import glob
import pandas as pd
import json
def main():
    #glob the csvs
    csvs = glob.glob("*.csv")
    for f in csvs:
        filename = f.split('.')[0]
        df = pd.read_csv(f)
        json_df = df.to_json(filename+'.json', orient='records', indent=4)
        #parsed = json.loads(json_df)
        #json_str = json.dumps(parsed, indent=4)  
    return

if __name__=="__main__":
    main()