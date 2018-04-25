#Run this script to "refresh" and write all BEA data to csv files storeed in SI/BEA path
source('R/Data Import/BEADataFunctions.R')

##Write data files in standard format

#Write summary use to csv files
for (year in 2008:2015) {
  summaryusetable = getSummaryUseTable(year)
  write.csv(summaryusetable,file=paste(BEApath,"Summary_Use_",year,"_PRO_BeforeRedef.csv",sep=""))
}
#Write very basic metadata file for summary use with info on written tables
APIaccesstimestamp = Sys.time()
summaryusemeta = paste("BEA Summary Use Tables (table 46) for Years 2008-2015 accessed via API in JSON format on:",APIaccesstimestamp)  
write(summaryusemeta,file=paste(BEApath,"AboutSummaryUseTables.txt",sep=""))

#write summary import matrixes to csv
for (year in 2008:2015) {
  summaryimport = getBEASummaryImportMatrixbyYear(year)
  write.csv(summaryimport,file=paste(BEApath,"Summary_ImportMatrix_",year,"_BeforeRedef.csv",sep=""))
}
#Write very basic metadata file for summary use with info on written tables
APIaccesstimestamp = Sys.time()
summaryimportmeta = paste("BEA Summary Import Matrices for Years 2008-2015 accessed from https://www.bea.gov/industry/xls/io-annual/ImportMatrices_Before_Redefinitions_SUM_1997-2015.xlsx on",APIaccesstimestamp)  
write(summaryimportmeta,file=paste(BEApath,"AboutSummaryImportTables.txt",sep=""))

#Write detailed gross output
BEA403_GrossOutput = getBEA403GrossOutput()
BEA389_GrossOutput = adjustGrossOutputBEA403toBEA389()
write.csv(BEA389_GrossOutput,paste(BEApath,"389_GrossOutput_CurrentDollars.csv",sep=""))

#Write detailed CPI
BEA389_CPI = getDetailedCPIforGrossOutput()
write.csv(BEA389_CPI,paste(BEApath,"389_CPI.csv",sep=""))


#Write USEEIO gross output to a csv
USEEIOv1_GrossOutput_USD2015 = adjustUSEEIOGrossOutputbyCPIYear(2015)
write.csv(USEEIOv1_GrossOutput_USD2015,file=paste(USEEIOpath,"USEEIOv1_GrossOutput_USD2015.csv",sep=""))

# Write the detailed make
Make_2007_389_PRO_BeforeRef = getBEADetailedMake2007()
write.csv(Make_2007_389_PRO_BeforeRef,paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""))

#Write detailed use
Use_2007_389_PRO_BeforeRedef = getBEADetailedUse2007()
write.csv(Use_2007_389_PRO_BeforeRedef,paste(BEApath,"389_Use_2007_PRO_BeforeRedef.csv",sep=""))
Use_2007_389_PRO_BeforeRedef_NoFinalDemand = getBEADetailedUse2007withoutFinalDemand()
write.csv(Use_2007_389_PRO_BeforeRedef_NoFinalDemand,paste(BEApath,"389_Use_2007_PRO_BeforeRedef_NoFinalDemand.csv",sep=""))

#Write detailed import matrix
ImportMatrix = getBEADetailedImportMatrix2007()
write.csv(ImportMatrix,paste(BEApath,"393_ImportMatrix_2007_BeforeRedef.csv",sep=""))


# use the function
Use_2007_389_PRO_BeforeRedef = getBEADetailedUse2007withoutFinalDemand()
write.csv(Use_2007_389_PRO_BeforeRef,paste(BEApath,"389_Use_2007_PRO_BeforeRedef_NoFinalDemand.csv",sep=""))

