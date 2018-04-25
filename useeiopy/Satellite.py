# Functions for downloading, extracting, modifying the satellite tables so they are prepped for creating the
# combined satellite for a model

import pandas as pd
import os.path
import zipfile
import requests
import io
import csv
import logging

def listRequiredSatelliteFilesBeforeRenaming(modelname, modelpath):
    satfiles = pd.read_csv(modelpath + modelname + "_satellitefiles.csv")
    # Store the file paths in a list, for items in list append 'satellite_tables/'
    satcsvfiles = [f for f in satfiles['NewFile']]
    return (satcsvfiles)

#Gets names of satellite files after renaming sectors
def listRequiredSatelliteFilesAfterRenaming(modelname, modelpath):
    satfiles = pd.read_csv(modelpath + modelname + "_satellitefiles.csv")
    # Store the file paths in a list, for items in list append 'satellite_tables/'
    satcsvfiles = [f for f in satfiles['NewFilewithnewG&S']]
    return (satcsvfiles)

def checkforSatelliteExcelFilePath(excelfilepath):
    if os.path.exists(excelfilepath):
        return True
    else:
        return False

#Downloads and unzips the USEEIO v1.1 Satellite file to a new directory
def downloadandunzipSatellite(excelfilepath):
    USEEIOv11satellitetableurl = "https://pasteur.epa.gov/uploads/A-sj4g/667/USEEIOv1.1SatelliteTables.zip"
    USEEIOv11satellitetablerequest = requests.get(USEEIOv11satellitetableurl)
    zip_file = zipfile.ZipFile(io.BytesIO(USEEIOv11satellitetablerequest.content))
    #excelfilepath = '/USEEIOv1.1 Satellite Excel Files/'
    os.mkdir(excelfilepath)
    zip_file.extractall(path=excelfilepath)

#Extracts satellite tables from Excel file
def extract_sat_tables(modelname, modelpath, excelfilepath, exportsheetname):
    # Specific file paths and csv names are stored in a csv file. Get that info
    satfiles = pd.read_csv(modelpath + modelname + "_satellitefiles.csv")
    # Store the file paths in a list, for items in list append 'satellite_tables/'
    satcsvfiles = [modelpath + 'satellite_tables/' + f for f in satfiles['NewFile']]
    # for each item in list, extract to csv
    for row in satfiles.itertuples():
        if (os.path.isfile(modelpath + 'satellite_tables/' + row[3])):
            logging.debug(row[3] + " already exists.")
        else:
            path = excelfilepath + row[2]
            table = pd.read_excel(path, sheetname=exportsheetname, header=0)
            table.to_csv(modelpath + 'satellite_tables/' + row[3], index=False)
            logging.info("Wrote " + row[1] + " satellite file to csv.")
    return satcsvfiles

#Gives sectors a USEEIO commodity name instead of the BEA name
def renameSatelliteSectors(satcsvfiles, sattablepath):
    Crosswalkrelpath = '../SI/Crosswalk'
    if os.path.isfile(Crosswalkrelpath + '/MasterCrosswalk.csv'):
        names = read_names(Crosswalkrelpath + '/MasterCrosswalk.csv')
    else:
        logging.error('Crosswalk file not found at: ' + Crosswalkrelpath + '/MasterCrosswalk.csv' )
    files = satcsvfiles
    for file_name in files:
        replace_names(file_name, names, sattablepath)

#Gets mapping file with USEEIO names to use in replacement
def read_names(mapping_file):
    """ Reading the name mappings: code -> new name """
    names = {}
    with open(mapping_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            # 8 colum: USEEIO1_Code
            # 10 column: USEEIO1_Commodity
            names[row[6].strip()] = row[8].strip()
    return names

#Replace old names with new nanmes
def replace_names(file_name, names, sattablepath):
    endofname = len(file_name)-4
    out_file = sattablepath + file_name[0:endofname] + "_newG&Snames.csv"
    handled = {}
    in_file = sattablepath + file_name
    with open(in_file, 'r', encoding='utf-8', newline='\n') as f:
        reader = csv.reader(f)
        with open(out_file, 'w', encoding='utf-8', newline='\n') as out:
            writer = csv.writer(out)
            writer.writerow(next(reader))  # header
            for row in reader:
                row = rounddataqualityscores(row)
                code = row[6]
                new_name = names.get(code)
                if new_name is None:
                    if code not in handled:
                        logging.warning('WARNING: unknown sector code' + code +
                              'did nothing')
                        handled[code] = True
                else:
                    if code not in handled:
                        # print('  INFO: rename sector', code, 'with', new_name)
                        handled[code] = True
                    row[5] = new_name
                writer.writerow(row)


#Rounds data quality scores to interage
def rounddataqualityscores(row):
    # data quality starts in col 15 to 19
    for i in range(15, 19):
        logging.debug("INFO: DQ score="+ row[i])
        if row[i] is not "":
            row[i] = round(float(row[i]), 0)
        else:
            row[i] = 0
    return row
