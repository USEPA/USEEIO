#Assembles USEEIO-form model

import iomb as iomb
import pandas as pd
import logging

def make(modelname, modelpath):
        #Identify all files
        drcfile = modelpath + modelname +"_DRC.csv"
        satcfile = modelpath+modelname+"_sat_c.csv"
        sectormetafile = modelpath+modelname+'_sector_meta_data.csv'
        compartmentmetadatafile = modelpath + "USEEIO_compartment_meta_data.csv"
        lciafile = modelpath + modelname + "_LCIA.csv"
        #Build model
        model = iomb.make_model(drcfile,[satcfile],sectormetafile,compartments_csv=compartmentmetadatafile,ia_tables=[lciafile])
        return(model)

def buildandwritesatellite(modelname, modelpath, print_sat_i=False):
        satfiles = pd.read_csv(modelpath+modelname+"_satellitefiles.csv")
        csv_files = [modelpath+'satellite_tables/'+f for f in satfiles['NewFilewithnewG&S']]
        sat_i = iomb.make_sat_table(*csv_files)
        if(print_sat_i):
                satifile = modelpath+modelname+"_sat_i.csv"
                sat_i.to_csv(satifile)
        marketshares = pd.read_csv(modelpath+modelname+"_MarketShares.csv",header=0,index_col=0)
        sectormetafile = modelpath+modelname+'_sector_meta_data.csv'
        sat_c = sat_i.apply_market_shares(marketshares,sectormetafile)
        satcfile = modelpath+modelname+"_sat_c.csv"
        sat_c.to_csv(satcfile)
