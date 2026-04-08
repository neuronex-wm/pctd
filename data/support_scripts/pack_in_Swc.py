# Here we will attemp to load pack the SWC files into the nwbs, but this is not a priority

import glob
import pandas
import pynwb
import os
from pynwb import NWBHDF5IO
from hdmf.common import DynamicTable, VectorData
import shutil

NWB_DIR = r"C:\Users\SMest\source\pctd\data\updated_nwbs"
NWB_OUT_DIR = r"C:\Users\SMest\source\pctd\data\nwbs_with_morph"

CSV_FILE = r"C:\Users\SMest\source\pctd\data\box2_ephys.csv"

SWC_DIR = r"C:\Users\SMest\Downloads\NXWM NC Paper - Morpho\NXWM NC Paper - Morpho"

ORGIN_IDS = True

def main():
    df = pandas.read_csv(CSV_FILE)
    nwbs = glob.glob(os.path.join(NWB_DIR, "**/*.nwb"), recursive=True)
    swcs = glob.glob(os.path.join(SWC_DIR, "*.swc"))
    for nwb in nwbs: #reverse the list of nwbs so we start with the most recent ones first, since those are more likely to have swc files. 
        swc_file = None #reset so we don't accidentally use the same swc file for multiple nwbs if there is an error in the code and we don't find a swc file for a particular nwb. This way we won't accidentally add the same swc file to multiple nwbs.
        #nwbs are labeled by cellID, swcs are by internalID, so we need to get the internalID from the cellID using the provided CSV
        cell_id = os.path.basename(nwb).split('.')[0]
        internal_id = df[df['cellID'] == int(cell_id)]['internalID'].values[0] if not ORGIN_IDS else cell_id #if the original ids are in the nwbs, then we can just use the cell_id as the internal_id, since they are the same. Otherwise, we need to look up the internal_id using the cell_id from the CSV.
        #find the corresponding swc file    
        swc_file = [swc for swc in swcs if os.path.basename(swc).split('.')[0] == internal_id] #not all cells have swc files, so this will throw an error if there is no swc file for the cell. We can catch this error and just skip the cell if there is no swc file.
        if swc_file or len(swc_file) > 0: #if there is a swc file for the cell
            swc_file = swc_file[0]
            #load the nwb file
            nwb_file = pynwb.NWBHDF5IO(nwb, 'a')
            nwb_data = nwb_file.read()
            # Just keeps the PI's happy
            subj = internal_id[:3]
            if not os.path.exists(os.path.join(NWB_OUT_DIR, subj)):
                os.makedirs(os.path.join(NWB_OUT_DIR, subj))
                out_path = os.path.join(NWB_OUT_DIR, subj, os.path.basename(nwb))
            else:
                out_path = os.path.join(NWB_OUT_DIR, subj, os.path.basename(nwb))
            #load the swc file, its actually just a space delimited text file, so we can use pandas to read it in
            #sometimes it has comments at the top, so we need to skip those. We can do this by specifying the comment character in pandas read_csv, which is '#'
            swc_data = pandas.read_csv(swc_file, sep=' ', header=None, names=['Index', 'Type', 'X', 'Y', 'Z', 'Radius', 'Parent'], comment='#')
            #make a new DynamicTable to hold the swc data
            index_col = VectorData(name='Index', description='Index of the SWC point', data=swc_data['Index'].values)
            type_col = VectorData(name='Type', description='Type of the SWC point', data=swc_data['Type'].values)
            x_col = VectorData(name='X', description='X coordinate of the SWC point, in microns', data=swc_data['X'].values)
            y_col = VectorData(name='Y', description='Y coordinate of the SWC point, in microns', data=swc_data['Y'].values)
            z_col = VectorData(name='Z', description='Z coordinate of the SWC point, in microns', data=swc_data['Z'].values)
            radius_col = VectorData(name='Radius', description='Radius of the SWC point, in microns', data=swc_data['Radius'].values)
            parent_col = VectorData(name='Parent', description='Index of the parent SWC point, -1 if there is no parent', data=swc_data['Parent'].values)
            swc_table = DynamicTable(name='SWC', description='SWC data from '+ os.path.basename(swc_file), columns=[index_col, type_col, x_col, y_col, z_col, radius_col, parent_col])

            nwb_data.create_processing_module(name='morphology', description='Module to hold morphology data')
            #add to the processing subdir
            nwb_data.processing['morphology'].add(swc_table)
            #save the new nwb file for recording keeping, we will save it in a new directory so we don't accidentally overwrite the original nwbs

            with NWBHDF5IO(out_path, mode="w") as export_io:
                export_io.export(src_io=nwb_file, nwbfile=nwb_data)


            nwb_file.close()
            #test read
            with pynwb.NWBHDF5IO(out_path, 'r') as io:
                nwb_data = io.read()
                print(nwb_data.processing['morphology']['SWC'])
                print(f"X col:{nwb_data.processing['morphology']['SWC']['X'].data[:10]}")

        else:
            #otherwise just copy the nwb file to the new directory without adding the swc data, since we want to keep all the nwbs in the new directory even if they don't have swc files, for consistency and record keeping. We can just use shutil.copy for this.
            subj = internal_id[:3]
            if not os.path.exists(os.path.join(NWB_OUT_DIR, subj)):
                os.makedirs(os.path.join(NWB_OUT_DIR, subj))
                out_path = os.path.join(NWB_OUT_DIR, subj, os.path.basename(nwb))
            else:
                out_path = os.path.join(NWB_OUT_DIR, subj, os.path.basename(nwb))
            shutil.copy(nwb, out_path)





if __name__ == "__main__":
    main()