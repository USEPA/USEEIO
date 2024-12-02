"""
Downloads and stores as pickle the relevant GLORIA matrices
"""

import pandas as pd

from pathlib import Path
import pickle as pkl

# https://drive.google.com/drive/folders/1tm1Cs5ABVRuE3fDkT80TfE5fPmnWPrA7

model_Path = Path(__file__).parent / 'mrio_models'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'
#%%
## install pymrio from https://github.com/francis-barre/pymrio/tree/master
# which matches with https://github.com/IndEcol/pymrio/pull/139
import pymrio

urls = pymrio.tools.iodownloader.GLORIA_CONFIG["datafiles"]
urls = {k: [i for i in lst if 'GLORIA_STDDEV' not in i] for k, lst in urls.items()}
## remove STDDEV files to reduce file size and improve runtime

def process_gloria(year_start=2012, year_end=2022, download=False):
    years = list(range(year_start, year_end+1))
    if download == True:
        print('Downloading GLORIA files')
        pymrio.download_gloria(storage_folder=model_Path, year=years,
                               urls=urls,
                               version='59a')
    
    for y in years:
        gloria = pymrio.parse_gloria(path=model_Path, version='59a',
                                     year=y)
        # temporary storage
        # pkl.dump(gloria, open(resource_Path / f'gloria_parsed_{y}.pkl', 'wb'))
        # gloria = pkl.load(open(resource_Path / f'gloria_parsed_{y}.pkl','rb'))
        gloria.calc_all()
        # pkl.dump(gloria, open(resource_Path / f'gloria_calc_{y}.pkl', 'wb'))
        # gloria = pkl.load(open(resource_Path / f'gloria_calc_{y}.pkl','rb'))
        d = {}
        d['M'] = gloria.Q.M # raw satellite multipliers
        d['output'] = gloria.x
        trade = pymrio.IOSystem.get_gross_trade(gloria)
        d['Trade Total'] = trade[1]
        # ^^ df with gross total imports and exports per sector and region
        d['Bilateral Trade'] = trade[0]
        # ^^ df with rows: exporting country and sector, columns: importing countries
        pkl.dump(d, open(resource_Path / f'gloria_all_resources_{y}.pkl', 'wb'))

if __name__ == '__main__':
    process_gloria(year_start = 2022, year_end = 2022, download=True)
