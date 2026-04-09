# This script will be used to organize all the nwbs for upload to DANDI
# Here we will pull the NWBs (ID'd by internal name), and rename them according to the cellID mapping in the provided CSV, and copy them to the new directory for upload to DANDI.
import argparse
import glob

import pandas
import os
import shutil
import h5py
import pynwb
from pynwb.icephys import IntracellularElectrode, Device
print(pynwb.__version__)

data_folders = [r"G:\Data4Website" ]

id_lookup_csv = r"C:\Users\SMest\source\pctd\data\box2_ephys.csv"
new_nwb_dir = r"C:\Users\SMest\source\pctd\data\updated_nwbs"


def pynwb_check(nwb_file):
    import pynwb
    try:
        with pynwb.NWBHDF5IO(nwb_file, 'r') as io:
            nwb_data = io.read()
            print(f"Successfully read {nwb_file} with pynwb.")
            return True
    except Exception as e:
        print(f"Error reading {nwb_file} with pynwb: {e}")
        return False

def find_electrode_group(nwb):
    if '/general/intracellular_ephys' in nwb:
        for key in nwb['/general/intracellular_ephys']:
            if 'unknown_electrode' in key.lower() or 'intracellular_electrode' in key.lower() or 'electrode' in key.lower():
                return nwb['/general/intracellular_ephys'][key], key
    return None, None


def main(retain_original_id=False):
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
                if retain_original_id:
                    new_file_name = internal_id + ".nwb"
                else:
                    new_file_name = str(cell_id) + ".nwb"
                shutil.copy(os.path.join(folder, nwb), os.path.join(new_nwb_dir, subj, new_file_name))
                if not pynwb_check(os.path.join(new_nwb_dir, subj, new_file_name)): #if we cant read the NWB file with pynwb, we need to modify it to make it readable.
                    # the nwbs are currently broken due to matnwb issues. 
                    # We need to pack in an intracellular electrode to make them readable by pynwb, but this is a bit of a hack and we should eventually fix the matnwb export to include the intracellular electrode in the correct format. For now, we will just add a dummy intracellular electrode to each nwb file to make them readable by pynwb, and then we can remove the dummy electrode later if we want to.
                    with h5py.File(os.path.join(new_nwb_dir, subj, new_file_name), 'r+') as nwb_file:
                            # the electrode is there, but not linked to the acquisition data, which is what is causing the issue with pynwb. 
                            #get the electrode object
                            #try to find the 
                            IntracellularEl, IEname = find_electrode_group(nwb_file)
                            if IntracellularEl is None:
                                IntracellularEl = IntracellularElectrode(name='unknown_electrode', 
                                                                    description='Dummy electrode added to make the NWB file readable by pynwb. This electrode does not contain any real data and should be removed before analysis.',
                                                                    device=Device(name='unknown_device'), location='unknown')
                                #link the electrode to the electrode group
                                #nwb_file['/general/intracellular_ephys'].copy(IntracellularEl, 'unknown_electrode')
                                print("Added dummy intracellular electrode to NWB file to make it readable by pynwb.")
                            else:
                                #move the existing electrode to the correct location in the NWB file, which is under /general/intracellular_ephys/unknown_electrode, and link it to the acquisition data
                                #IntracellularEl.parent.move(IEname, '/general/intracellular_ephys/nsfa')
                                print("Moved existing electrode to correct location in NWB file and linked it to acquisition data.")
                            electrode_group, _ = find_electrode_group(nwb_file)
                            
                            for key in range(nwb_file['/general/intracellular_ephys/intracellular_recordings/electrodes/electrode'].len()):
                                nwb_file['/general/intracellular_ephys/intracellular_recordings/electrodes/electrode'][key] = electrode_group.ref
                            for key in nwb_file['acquisition']:
                                #link the electrode to the acquisition data
                                #pop the electrode to 'delete' it, then re-add it as an IntracellularElectrode to link it properly
                                try:
                                    del nwb_file['acquisition'][key]['electrode']
                                except:
                                    print(f"No existing electrode reference found in acquisition data for {key}. Adding new reference to electrode group.")
                                nwb_file['acquisition'][key]['electrode'] = h5py.SoftLink(electrode_group.name)
                            for key in nwb_file['/stimulus/presentation/']:
                                #link the electrode to the stimulus presentation data
                                try:
                                    del nwb_file['/stimulus/presentation/'][key]['electrode']
                                except:
                                    print(f"No existing electrode reference found in stimulus presentation data for {key}. Adding new reference to electrode group.")
                                nwb_file['/stimulus/presentation/'][key]['electrode'] = h5py.SoftLink(electrode_group.name)
                            #I think we also need to upda the refs here: /general/intracellular_ephys/intracellular_recordings/electrodes/electrode
                            print("Linked electrode to acquisition and stimulus presentation data in NWB file.")
                            print(electrode_group.ref)


                            #save the modified NWB file
                            nwb_file.flush()
                    #attempt to read the modified NWB file with pynwb to ensure it is now readable
                    with pynwb.NWBHDF5IO(os.path.join(new_nwb_dir, subj, new_file_name), 'r') as io:
                        nwb_data = io.read() #if this works, then the NWB file is now readable by pynwb and we can move on to the next file. If it doesn't work, then we need to investigate further.
                        print(f"Successfully read {os.path.join(new_nwb_dir, subj, new_file_name)} with pynwb.")

            
                #Even if it does open we need to modify to add subject weight
                with h5py.File(os.path.join(new_nwb_dir, subj, new_file_name), 'r+') as nwb_file:
                    if '/general/subject' in nwb_file:
                        if 'weight' not in nwb_file['/general/subject']:
                            nwb_file['/general/subject'].create_dataset('weight', data="0.0 kg")
                            print(f"Added weight dataset to subject in NWB file {new_file_name}.")
                        else:
                            #get the current val and add units if not already there
                            current_weight = nwb_file['/general/subject']['weight'][()]
                            if isinstance(current_weight, bytes):
                                current_weight = current_weight.decode('utf-8')
                            if current_weight is None or current_weight == "" or current_weight == b'' or current_weight == b'NaN' or current_weight == 'NaN':
                                nwb_file['/general/subject']['weight'][()] = "0.0 kg"
                                print(f"Set weight dataset in subject in NWB file {new_file_name} to default value of 0.0 kg.")
                            elif not isinstance(current_weight, str) or not current_weight.endswith("kg"):
                                nwb_file['/general/subject']['weight'][()] = str(current_weight) + " kg"
                                print(f"Updated weight dataset in subject in NWB file {new_file_name} to include units.")
                    
                    nwb_file.flush()
                print(f"Copied {nwb} to {new_file_name}")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare NWB files for DANDI upload.")
    parser.add_argument("--data-folders", nargs='+', default=data_folders,
                        help="List of folders to search for NWB files.")
    parser.add_argument("--id-lookup-csv", default=id_lookup_csv,
                        help="Path to the CSV file containing the internalID to cellID mapping.")
    parser.add_argument("--new-nwb-dir", default=new_nwb_dir,
                        help="Directory to save the renamed NWB files for DANDI upload.")
    parser.add_argument("--retain-original-id", action="store_true", default=True,
                        help="Include the original internal ID in the output file name (e.g. cellID_internalID.nwb)")
    args = parser.parse_args()
    main(retain_original_id=args.retain_original_id)