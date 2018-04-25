#Detail level codes
demandcodes_detail = c("F01000","F02S00","F02E00","F02N00","F02R00","F03000", "F04000",
                       "F05000","F06C00","F06S00","F06E00","F06N00","F07C00","F07S00",
                       "F07E00","F07N00","F10C00","F10S00","F10E00","F10N00")


getUSDetailDemandfromUseTable = function () {
  
  UseDetail07 = read.table(paste(BEApath,"389_Use_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F,nrows=389)
  # Replace NAs with 0
  UseDetail07[is.na(UseDetail07)]=0
  # Import (F05000) of 2122A0 was 1439, corrected it to -2561,a value from the import matrixes for this cell  
  UseDetail07["2122A0", "F05000"] = -2561
  #Convert from million to USD
  FinalDemand_Detail_07 = UseDetail07[,demandcodes_detail]*1E6
  return(FinalDemand_Detail_07)
}

