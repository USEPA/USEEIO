#Define functions for getting BEA data via web services or text files if data are not provided via webservices.
#Return data in JSON format.
#Store data to standard csv files
#For web services See https://www.bea.gov/API/bea_web_service_api_user_guide.htm
#User must register for their own API key for use with this script

##For BEA API
#Store personal key in a file
pathtoBEAkey = "../../"
personalkeyfile = paste(pathtoBEAkey,"BEA_API_KEY.txt", sep="")
personalkey = read.table(personalkeyfile)
personalkey = as.character(personalkey[,"V1"])

#User guide at https://www.bea.gov/API/bea_web_service_api_user_guide.htm
#To set dataset list
#/api/data?&UserID=Your-36Character-Key&method=GETDATASETLIST&ResultFormat=XML&

#base URL
basebeaurlgetdata = paste("https://www.bea.gov/api/data/?&UserID=",personalkey,"&method=GetData&datasetname=", sep="")
basebeaurlgetparametervalues = paste("https://www.bea.gov/api/data/?&UserID=",personalkey,"&method=GetParameterValues&ResultFormat=json&DatasetName=", sep="")


#for IO data, parameter values are TableID and year 
#Current IO tables of interest. Use summary, beforeref=46, makesummarybeforeredef=51
IOdatasetname = "InputOutput&TableID="

#for GDP by industry. Not in use because detailed sectors not available via API
#GDPdatasetname = "underlyingGDPbyIndustry"
#See all GDP tables
#tables = "&ParameterName=TableID"
#url = paste(basebeaurlgetparametervalues,GDPdatasetname,tables,sep="")
#GDPtablesjson = fromJSON(url, flatten=T)
#GDPtablesdf = as.data.frame(GDPtablesjson$BEAAPI$Results$ParamValue)
#15 = Gross Output by industry
#Year=2015
#url = paste(basebeaurlgetdata,GDPdatasetname,"&TableID=15&Frequency=Q&Industry=ALL&Year=",Year,sep="")
#grossoutputbyindustry_json = fromJSON(url, flatten=T)

#Returns a summary use table for the year request as a data frame in a standard use table format (rows are commodities)
getSummaryUseTable = function (year) {
  use_beforeredef_summarylevel_id = paste("46&Year=",year,"&ResultFormat=JSON",sep="")
  url = paste(basebeaurlgetdata,IOdatasetname,use_beforeredef_summarylevel_id,sep="")
  summaryinputoutput = fromJSON(url, flatten=T)
  sudf = as.data.frame(summaryinputoutput$BEAAPI$Results$Data)
  #Remove unneeded cols
  sudf2 = sudf[,c("RowCode","ColCode","DataValue")]
  sudf2$DataValue = as.numeric(sudf2$DataValue)
  #Reshape sudf2 from long to wide (making RowCode row.names, ColCode col.names)
  sudf3 = dcast(sudf2, RowCode ~ ColCode, value.var = "DataValue")
  names(sudf3)[1] = "CommodityCode"
  #Make Commodity codes the row names
  row.names(sudf3) = sudf3$CommodityCode
  #Remove the previous data columns of commodity names
  sudf4 = subset(sudf3,select = -CommodityCode)
  #Clean up
  rm(sudf,sudf2,sudf3)
  return(sudf4)
}


#Get BEA detailed sectors from the Make File
getDetailedSectors = function () {
  #Check to see if file exists. Download it if not
  if(!file.exists("IOMake_Before_Redefinitions_2007_Detail.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/IOMake_Before_Redefinitions_2007_Detail.xlsx", "IOMake_Before_Redefinitions_2007_Detail.xlsx",mode="wb")
  }
  BEA_389 = as.data.frame(read_excel("IOMake_Before_Redefinitions_2007_Detail.xlsx", sheet='2007', col_names = F))[6:394,1]
  return (BEA_389)
}

#Import detailed output from BEA Excel file
getBEA403GrossOutput = function () {
  if(!file.exists("GDPbyInd_GO_NAICS_1997_2015.xlsx")) {
  download.file("https://bea.gov/industry/xls/io-annual/GDPbyInd_GO_NAICS_1997-2015.xlsx", "GDPbyInd_GO_NAICS_1997_2015.xlsx",mode="wb")
  }
  GrossOutput = as.data.frame(read_excel("GDPbyInd_GO_NAICS_1997_2015.xlsx", sheet='07NAICS_GO_A_Gross Output', col_names = F))
  output = GrossOutput[6:408, 4:22]
  rownames(output) = GrossOutput[6:408,2]
  colnames(output) = GrossOutput[4, 4:22]
  # transform from BEA 403 to BEA 389
   # aggregate 221112, 221113, 22111A, 221120 into 221100
  return(output) #Return table with row.names the BEA codes and the columns names the year
}

adjustGrossOutputBEA403toBEA389 = function () {
  output = getBEA403GrossOutput()
  
  output["221100",] = colSums(GrossOutput[c(221112, 221113, "22111A", 221120),])
  # aggregate 423000, 424000, 425000, 42XXXX into 420000
  output["420000",] = colSums(GrossOutput[c(423000, 424000, 425000, "42XXXX"),])
  # aggregate 442000, 443000, 444000, 446000, 447000, 448000, 451000, 453000, 454000 into 4A0000
  output["4A0000",] = colSums(GrossOutput[c("442000", 443000, 444000, 446000, 447000, 448000, 451000, 453000, 454000),])
  # keep the BEA 389 sectors
  if (!exists("BEA_389")) {
    BEA_389 = getDetailedSectors()
  }
  output = output[BEA_389,]
  return(output)
}

# Return Price Indexes (CPI) of BEA 389  sectors for year 1997-2015
getDetailedCPIforGrossOutput = function () {
  if(!file.exists("GDPbyInd_GO_NAICS_1997_2015.xlsx")) {
    download.file("https://bea.gov/industry/xls/io-annual/GDPbyInd_GO_NAICS_1997-2015.xlsx", "GDPbyInd_GO_NAICS_1997_2015.xlsx",mode="wb")
  }
  PriceIndexes = as.data.frame(read_excel("GDPbyInd_GO_NAICS_1997_2015.xlsx", sheet='07NAICS_GO_C_Price_Indexes', col_names = F))
  index = PriceIndexes[6:408, 4:22]
  rownames(index) = PriceIndexes[6:408,2]
  colnames(index) = PriceIndexes[4, 4:22]
  # transform from BEA 403 to BEA 389 by weighting price indexes base on output's weight
  if (!exists("BEA403_GrossOutput")) {
    BEA403_GrossOutput = getBEA403GrossOutput()
  }
  for (i in 1:ncol(index)) {
    # aggregate 221112, 221113, 22111A, 221120 into 221100
    index["221100",i] = weighted.mean(index[c(221112, 221113, "22111A", 221120),i], BEA403_GrossOutput[c(221112, 221113, "22111A", 221120),i])
    # aggregate 423000, 424000, 425000, 42XXXX into 420000
    index["420000",i] = weighted.mean(index[c(423000, 424000, 425000, "42XXXX"),i], BEA403_GrossOutput[c(423000, 424000, 425000, "42XXXX"),i])
    # aggregate 442000, 443000, 444000, 446000, 447000, 448000, 451000, 453000, 454000 into 4A0000
    index["4A0000",i] = weighted.mean(index[c("442000", 443000, 444000, 446000, 447000, 448000, 451000, 453000, 454000),i],
                                      BEA403_GrossOutput[c("442000", 443000, 444000, 446000, 447000, 448000, 451000, 453000, 454000),i])
  }
  if (!exists("BEA_389")) {
    BEA_389 = getDetailedSectors()
  }
  index = index[BEA_389,]
  return(index) #Return table with row.names the BEA codes and the columns names the year
}

# Transform Gross Output from BEA to USEEIO sectors
adjustBEAGrossOutputtoUSEEIO = function () {
  if (!exists("BEA389_GrossOutput")) {
    BEA389_GrossOutput = adjustGrossOutputBEA403toBEA389()  
  }
  temp = BEA389_GrossOutput
  temp$BEA_389_Code = rownames(temp)
  # crosswalk
  Crosswalk = read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""))
  GrossOutput_USEEIO = merge(temp, unique(Crosswalk[c("BEA_389_Code", "USEEIO1_Code", "USEEIO2_Code")]), by = "BEA_389_Code", all.x = T)
  # equally allocate USEEIO1 221300 to USEEIO2 221310 & 221320
  GrossOutput_USEEIO[GrossOutput_USEEIO$USEEIO2_Code %in% c("221310", "221320"), 2:20] = GrossOutput_USEEIO[GrossOutput_USEEIO$USEEIO1_Code == "221300", 2:20]/2
  # equally allocate USEEIO1 562000 to USEEIO "562920", "562910", "562OTH", "562111", "562213", "562HAZ", "562212I", "562212O"
  GrossOutput_USEEIO[GrossOutput_USEEIO$USEEIO2_Code %in% c("562920", "562910", "562OTH", "562111", "562213", "562HAZ", "562212I", "562212O"), 2:20] = GrossOutput_USEEIO[GrossOutput_USEEIO$USEEIO1_Code == "562000", 2:20]/8
  GrossOutput_USEEIO = GrossOutput_USEEIO[! is.na(GrossOutput_USEEIO$USEEIO2_Code),]
  return(GrossOutput_USEEIO)
}

#This is a function to adjust the USEEIO sector gross output by a specified dollar year
adjustUSEEIOGrossOutputbyCPIYear = function (year) {
  if (!exists("BEA389_GrossOutput")) {
    BEA389_GrossOutput = adjustGrossOutputBEA403toBEA389()  
  }
  output = BEA389_GrossOutput
  if (!exists("BEA389_CPI")) {
    BEA389_CPI = getDetailedCPIforGrossOutput()  
  }
  outputyears  = colnames(BEA389_GrossOutput)
  for (y in outputyears) {
    output[,y] = BEA389_GrossOutput[,y]*(BEA389_CPI[,as.character(year)]/BEA389_CPI[,y])
  }
  return(output)
}


# Get BEA Detailed Make 2007 from static Excel
# with output
getBEADetailedMake2007 = function () {
  if(!file.exists("IOMake_Before_Redefinitions_2007_Detail.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/IOMake_Before_Redefinitions_2007_Detail.xlsx", "IOMake_Before_Redefinitions_2007_Detail.xlsx",mode="wb")
  }
  IO_Make_2007_389 = as.data.frame(read_excel("IOMake_Before_Redefinitions_2007_Detail.xlsx", sheet='2007', col_names = F))[6:395, 3:392]
  rownames(IO_Make_2007_389) = as.data.frame(read_excel("IOMake_Before_Redefinitions_2007_Detail.xlsx", sheet='2007', col_names = F))[6:395, 1]
  colnames(IO_Make_2007_389) = as.data.frame(read_excel("IOMake_Before_Redefinitions_2007_Detail.xlsx", sheet='2007', col_names = F))[5, 3:392]
  return(IO_Make_2007_389)
}

# Get BEA Detailed Use 2007 from static Excel
# with demand
getBEADetailedUse2007 = function () {
  if(!file.exists("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", "IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", mode="wb")
  }
  IO_Use_2007_389 = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[6:400, 3:414]
  rownames(IO_Use_2007_389) = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[6:400, 1]
  colnames(IO_Use_2007_389) = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[5, 3:414]
  return(IO_Use_2007_389)
}
# without demand
getBEADetailedUse2007withoutFinalDemand = function () {
  if(!file.exists("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", "IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", mode="wb")
  }
  IO_Use_2007_389 = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[6:400, 3:391]
  rownames(IO_Use_2007_389) = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[6:400, 1]
  colnames(IO_Use_2007_389) = as.data.frame(read_excel("IOUse_Before_Redefinitions_PRO_2007_Detail.xlsx", sheet='2007', col_names = F))[5, 3:391]
  return(IO_Use_2007_389)
}

# Get BEA Detailed Import 2007 from static Excel
getBEADetailedImportMatrix2007 = function () {
  if(!file.exists("ImportMatrices_Before_Redefinitions_DET_2007.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/ImportMatrices_Before_Redefinitions_DET_2007.xlsx","ImportMatrices_Before_Redefinitions_DET_2007.xlsx", mode="wb")
  }
  ImportMatrix = as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_DET_2007.xlsx", sheet='2007', col_names = F))[6:398, 3:414]
  rownames(ImportMatrix) = as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_DET_2007.xlsx", sheet='2007', col_names = F))[6:398, 1]
  colnames(ImportMatrix) = as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_DET_2007.xlsx", sheet='2007', col_names = F))[5, 3:414]
  return(ImportMatrix)
}

# Get BEA Detailed Import for specific year from static Excel
getBEASummaryImportMatrixbyYear = function (year) {
  ## read excel sheet
  if(!file.exists("ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx")) {
    download.file("https://www.bea.gov/industry/xls/io-annual/ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx","ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx", mode="wb")
  }
  ISyr=as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx",sheet=as.character(year), col_names=F))[6:78,3:96]
  ## extract useful columns and rows
  rownames(ISyr) = as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx",sheet=as.character(year), col_names=F))[6:78,1]
  colnames(ISyr)= as.data.frame(read_excel("ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx",sheet=as.character(year), col_names=F))[5,3:96]
  return(ISyr)
}
