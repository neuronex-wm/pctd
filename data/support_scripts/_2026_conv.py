# ==============================================================
# 2026_conv.py
# ==============================================================
# This script converts the 2026 dataset into a format suitable compat with the old naming convetions. It reads the original dataset, processes it, and saves the converted data in a new directory.
# expect a lot of weird names and hardcoded stuff, but it should work for the specific dataset structure.
import glob
import pandas as pd
import json

#set the column names which will converted back to the old naming conventions. This is just an example, you will need to adjust it based on the actual column names in your dataset.
ROW_ID_COL = 'Row'
SPECIES_COL = 'Species'
SEX_COL = 'Sex'
AGE_COL = 'Age'

# here we want a unique identifier for each cell, which is required for the old naming conventions. You can either create this by hashing the individual columns together, or just use the row number as the id. If you want to use the row number, set HASH_indiv to False and make sure to rename the column to 'cellID'. If you want to hash the individual columns together, set HASH_indiv to True and make sure to provide a column name for the new id column in CELL_ID_COL. If CELL_ID_COL is None, it will default to 'id'.
#whether to make a id column by hashing the individual columns together, or just use the row number as the id. This is just an example, you will need to adjust it based on the actual structure of your dataset.
CELL_ID_COL = 'Identifier'
HASH_indiv = False 

#other mappings; while we are here you can rename some columns if you want. Make 'em more user friendly or something. This is just an example, you will need to adjust it based on the actual column names in your dataset.
OTHER_MAPPINGS = {
    'RinHD': 'Resistance',
    'widTP_LP': 'AP halfwidth',
    'heightTP_SP': 'Amplitude',
    'Vrest': 'Resting potential',
    'Rheo': 'Rheobase',
    'brainOrigin': 'Cortical area',
    'tau': 'Time Constant',
    'maxRt': 'Max Firing Rate',
    'medInstaRt': 'Median instantanous frequency',
    'dendriticType': "Dendrite type",
    "SomaLayerLoc": "Cortical layer"
}


def convert_conventions(df):
    # This function will convert the dataframe to the new naming conventions.
    # For example, if the original dataset has a column named 'old_name', we will rename it to 'new_name'.
    # This is just an example, you will need to adjust it based on the actual column names in your dataset.
    
    # Hardcoded renaming of columns to match the old naming conventions
    df = df.rename(columns={
        ROW_ID_COL: 'internalID',
        SPECIES_COL: 'Species',
        SEX_COL: 'Sex',
        AGE_COL: 'Age' 
    })
    

    if HASH_indiv and CELL_ID_COL is not None:
        # Create a new column 'id' by hashing the individual columns together
        df[CELL_ID_COL] = df.apply(lambda row: hash(tuple(row)), axis=1)
    elif not HASH_indiv and CELL_ID_COL is not None:
        #the user may have provided
        df = df.rename(columns={
            CELL_ID_COL: 'cellID'
            })

    if OTHER_MAPPINGS:
        df = df.rename(columns=OTHER_MAPPINGS)

    return df


def main():
    #glob the csvs
    new_df = pd.read_csv(r"C:\Users\SMest\Downloads\marmData_wUMAP.csv")
    #convert the conventions
    new_df = convert_conventions(new_df)
    #save the new dataframe to a new directory
    new_df.to_csv(r"./data/box2_ephys.csv", index=False)
    new_df.to_json(r"./data/box2_ephys.json", orient='records', indent=4)
    return

if __name__ == "__main__":
    main()