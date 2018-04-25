#Generate components of USEEIOv1.1 model
#currently produces:
# Final demand - total consumption and production vectors for 2007
# Direct requirements coefficients
# Market shares
# LCIA factors
#See the README in the model folder for info on preparation of other model components

#Set output to where you want 
#must create output folder in advance
outputfolder = paste(ModelBuildspath,"USEEIOv1.1/",sep="")
model = "USEEIOv1.1"
modelversion = "v1.1"
majormodelversion=1

#Generate Demand
source('R/Demand/Demand.R')
#StartYear,EndYear,CPIRefYear
USEEIO_Demand = getUSTotalConsProd(2007,2007,2013)

#Generate IO tables 
source("R/IO/IOFunctions.R")
US_marketshares = generateMarketShareCoefficientfromMake2007()
USEEIO_MarketShares =  formatIOTableforIOMB(US_marketshares)
CommodityByCommodityDirectRequirementsCoefficients = generateDR1RegionCoeffs()
USEEIO_DRC = formatIOTableforIOMB(CommodityByCommodityDirectRequirementsCoefficients)

#Generate the LCIA factor table
source('R/General Functions/LCIAFunctions.R')
USEEIO_LCIA = generateLCIA(modelversion)

#Write all files to the apprpriate directory for the model build
write.csv(USEEIO_Demand,paste(outputfolder,model,"_FinalDemand.csv",sep=""),row.names = FALSE)
write.csv(USEEIO_MarketShares,paste(outputfolder,model,'_MarketShares.csv',sep=""),row.names = TRUE)
write.csv(USEEIO_DRC,paste(outputfolder,model,"_DRC.csv",sep=""),row.names = TRUE)
write.csv(USEEIO_LCIA,paste(outputfolder,model,"_LCIA.csv",sep=""),row.names = FALSE)

