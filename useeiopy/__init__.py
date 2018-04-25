import useeiopy.Satellite as Satellite
import useeiopy.AssembleModel as AssembleModel
import useeiopy.CalculateModel as CalculateModel
import useeiopy.ValidateModel as ValidateModel

import os
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
#, format='%(levelname)s %(message)s')

requiredModelFileEndings = ['_DRC.csv','_MarketShares.csv','_sat_c.csv','_LCIA.csv','_sector_meta_data.csv',
                            '_FinalDemand.csv','_satellitefiles.csv']

modulepath = os.path.dirname(__file__)
print("Current module path" + modulepath)

#Set working directory to module directory
os.chdir(modulepath)

modelbuildpath = modulepath + '/Model Builds/'

#Determines status of current builds as a case, finds or create missing files to proeeed to the next step
def assemble(inputmodelname):
    #modelassembler = modelname + '_Assemble.py'
    #exec(modelassembler)
    global modelname
    global modelpath
    global excelfilepath
    modelname = inputmodelname
    modelpath = modelbuildpath + modelname + '/'
    excelfilepath = modulepath + '/USEEIOv1.1 Satellite Excel Files/'
    sattablepath = modelpath + 'satellite_tables/'
    #status code
    #0  = all files present .. proceed with assembly
    #-1 = missing sat_c .. to check for satellite csv files
    #-2 = missing other files ...abort
    #-3 = missing sat_c but satellite csv files present
    #-4 = missing renamed satellite files but originals present
    #-5 = missing original satellite csv files so find them or download them

    case = checkforModelFiles(modelname,modelpath)

    #If not ready for assembly, loop through until ready
    while case != 0:
        if case == -1:
            #Reset case after trying
            case = checkforSatelliteCSVFiles(sattablepath)
            continue
        elif case == -2:
            log.info("Try again after adding required model files.")
            break
        elif case == -3:
            #proceed to try to build satellite csv
            log.info("Trying to build combined satellite table")
            AssembleModel.buildandwritesatellite(modelname, modelpath)
            case = 0
            continue
        elif case == -4:
            #Proceed to try to rename the sectors and create the renamed csv files
            log.info("Renaming sectors to USEEIO names in satellite tables...")
            Satellite.renameSatelliteSectors(satcsvfiles, sattablepath)
            case = -3
            continue
        elif case == -5:
            #prompt user to download
            if Satellite.checkforSatelliteExcelFilePath(excelfilepath):
                log.info("Extracting satellite tables from excel files...")
                Satellite.extract_sat_tables(modelname, modelpath, excelfilepath, 'Export')
                case = checkforSatelliteCSVFiles(sattablepath)
                continue
            else:
                response = input("One or more required satellite csv files are missing. Would you like to me to download "
                                 "and extract the USEEIOv1.1 satellite table files for you? (y/n)")
                if response.lower() == 'y':
                    log.info("Downloading satellite files...")
                    Satellite.downloadandunzipSatellite(excelfilepath)
                    log.info("Extracting satellite tables from excel files...")
                    Satellite.extract_sat_tables(modelname,modelpath,excelfilepath,'Export')
                    case = checkforSatelliteCSVFiles(sattablepath)
                    continue
                else:
                    log.error("You must add all the csv files specified in the " + modelname + "_satellitefiles.csv file"
                              " to the satellite_tables folder to build a model, or modify the list of satellite tables in"
                              " that file.")
                    break

    if case == 0:
        log.info("Assembling model...")
        model = AssembleModel.make(modelname, modelpath)
        return(model)

def validate(model):
    ValidateModel.validate(model,modelname=modelname,modelpath=modelpath)


def calculate(model,year=2007,location='US',demandtype='Consumption',perspective='DIRECT'):
    CalculateModel.calculate(model,year,location,demandtype,perspective,modelname=modelname,modelpath=modelpath)
    log.info("Wrote results files to model's results folder.")

def checkforModelFiles(modelname,modelpath):
    log.info("Checking for presence of all required model files...")

    requiredModelFiles = []
    requiredSatCfile = modelname+'_sat_c.csv'
    for f in requiredModelFileEndings:
        requiredFile = modelname + f
        requiredModelFiles.append(requiredFile)
    requiredModelFiles.append('USEEIO_compartment_meta_data.csv')
    modelFolderContents = []
    if os.path.exists(modelpath):
        modelFolderContents = os.listdir(modelpath)
        missingFiles= []
        for f in requiredModelFiles:
            if f not in modelFolderContents:
                log.info("Missing " + f)
                missingFiles.append(f)

        PygeneratedFile =  requiredSatCfile
        requiredPreAssemblyFiles = [f for f in requiredModelFiles if f!=PygeneratedFile]

        if len(missingFiles)>0:
            if len(missingFiles) > 1:
                log.error("If not already present, you must manually add or add with a model build script in the USEEIOr package the following files to the Model Builds/" + modelname + " folder before proceeding:" +  str(requiredPreAssemblyFiles))
                return -2
            elif missingFiles[0] == requiredSatCfile:
                return -1
        else:
            return 0
    else:
        log.error("Required model folder is missing:" + modelpath)
        return -2

def checkforSatelliteCSVFiles(sattablepath):
    if os.path.exists(sattablepath) is False:
        os.mkdir(sattablepath)
    fileList = os.listdir(sattablepath)
    #first check for files after renaming
    requiredSatelliteCSVFilesAfterRenaming = Satellite.listRequiredSatelliteFilesAfterRenaming(modelname,modelpath)
    missingRenamedFiles = []
    for f in requiredSatelliteCSVFilesAfterRenaming:
        if f not in fileList:
            missingRenamedFiles.append(f)
    if len(missingRenamedFiles) > 0:
        log.info("CSV files with _newG&Snames missing: " + str(missingRenamedFiles) + ". Proceeding to check for original files")
        requiredSatelliteCSVFilesBeforeRenaming = Satellite.listRequiredSatelliteFilesBeforeRenaming(modelname,modelpath)
        global satcsvfiles
        satcsvfiles = requiredSatelliteCSVFilesBeforeRenaming
        missingOriginalFiles = []
        for f in requiredSatelliteCSVFilesBeforeRenaming:
            if f not in fileList:
                missingOriginalFiles.append(f)
        if len(missingOriginalFiles) > 0:
                log.error("Missing original csv files " + str(missingOriginalFiles))
                return -5
        else:
            log.debug("Returning -4")
            return -4
    else:
        return -3

