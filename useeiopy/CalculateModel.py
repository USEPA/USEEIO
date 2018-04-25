#Calculates results of a USEEIO form model; writes them to disk

import iomb.demand2dict as dd
import iomb.calc as calc
import os
import logging

#Returns model calculation results for demand vector
def calculate (model,year,location,demandtype,perspective,modelname,modelpath):

    demandfile = modelpath + modelname + "_FinalDemand.csv"
    demandcolumnname = str(year) + '_' + location + "_" + demandtype
    demand = dd.demandtodict(demandcolumnname,demandfile)
    if (perspective=='FINAL'):
        p = calc.FINAL_PERSPECTIVE
    else:
        p = calc.DIRECT_PERSPECTIVE
    result = calc.calculate(model, demand, p)
    lciacontributions = result.lcia_contributions.transpose()
    lciaflowcontributions = result.lcia_flow_contributions.transpose()
    resultsfolder = modelpath + "results/"
    if os.path.exists(resultsfolder) is False:
        os.mkdir(resultsfolder)
    lciacontributions.to_csv(resultsfolder+modelname+"_"+ str(year)+"_"+location+"_"+demandtype+"_"+perspective+"_"+"lciacontributions.csv")
    lciaflowcontributions.to_csv(resultsfolder+modelname+"_"+ str(year)+"_"+location+"_"+demandtype+"_"+perspective+"_"+"lciaflowcontributions.csv")