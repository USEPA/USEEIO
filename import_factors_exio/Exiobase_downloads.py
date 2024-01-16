import pymrio
from pathlib import Path
import pickle as pkl


model_Path = Path(__file__).parent / 'mrio_models'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'
model_type = 'pxp' #model type

def process_exiobase(year_start=2012, year_end=2022, download=False):
    years = list(range(year_start, year_end+1))
    if download == True:
        print('Downloading exiobase files')
        pymrio.download_exiobase3(storage_folder=model_Path,
                                  system=model_type,
                                  years=years)
    resource_Path.mkdir(exist_ok=True)
    for y in years:
        print(f'Processing exiobase files for {y}')
        file = model_Path / f'IOT_{y}_{model_type}.zip'
        e = pymrio.parse_exiobase3(file)
        trade = pymrio.IOSystem.get_gross_trade(e)
        d = {}
        d['M'] = e.impacts.M
        d['Trade Total'] = trade[1]
        # ^^ df with gross total imports and exports per sector and region
        d['Bilateral Trade'] = trade[0]
        # ^^ df with rows: exporting country and sector, columns: importing countries
        pkl.dump(d, open(resource_Path / f'exio_all_resources_{y}.pkl', 'wb'))

if __name__ == '__main__':
    process_exiobase(year_start = 2019, year_end=2019, download=False)
