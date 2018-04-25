getNAICStoUSEEIOAllocation = function (USEEIO,year) { # USEEIO as USEEIO1 or USEEIO2, year in numeric format
  USEEIO_Code = paste(USEEIO,"_Code",sep="")
  # load in USEEIO_BEA_NAICS crosswalk master table
  USEEIO_BEA_NAICS_crosswalk = read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""),header=T,check.names=F,stringsAsFactors=FALSE)
  # select columns of USEEIO and 2012 NAICS
  USEEIO_BEA_NAICS_table = USEEIO_BEA_NAICS_crosswalk[,c(USEEIO_Code,"2012_NAICS_Code")] #,"BEA_71_Code","BEA_71_Industry"
  # drop 2-digit NAICS code
  USEEIO_BEA_NAICS_table = USEEIO_BEA_NAICS_table[USEEIO_BEA_NAICS_table$`2012_NAICS_Code`>100,]
  # drop duplicate "USEEIO v2 code ~ 2012 NAICS code" records, because there are 1 v. N cases for 2012 ~ 2007 NAICS code in the master crosswalk table
  subset_alloc = unique(USEEIO_BEA_NAICS_table)
  # subset repeated NAICS code (the ones that need allocation, excluding 230000 and S00000)
  subset_alloc = subset_alloc[duplicated(subset_alloc$`2012_NAICS_Code`)|duplicated(subset_alloc$`2012_NAICS_Code`,fromLast=TRUE),]
  subset_alloc = subset_alloc[!subset_alloc[,USEEIO_Code] == "230000",]
  
  # read in BEA output data
  Output = read.table(paste(BEApath,"389_GrossOutput_CurrentDollars.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
  Output_year = as.data.frame(rownames(Output))
  colnames(Output_year) = "BEA_389"
  Output_year$BEA_389 = as.character(Output_year$BEA_389)
  Output_year$Output = as.numeric(Output[,as.character(year)])
  
  # merge the code relationship table with the economic output data to determine allocation factors
  USEEIO_BEA_NAICS_allocation = merge(subset_alloc,Output_year,by.x=USEEIO_Code,by.y="BEA_389",all.x=TRUE)
  # insert output value for 221310 & 221320
  USEEIO_BEA_NAICS_allocation[USEEIO_BEA_NAICS_allocation[,USEEIO_Code]%in%c("221310","221320"),"Output"] = 0.5*Output_year[Output_year$BEA_389=="221300","Output"]
  # insert placeholder for NAs in "output" column
  USEEIO_BEA_NAICS_allocation[is.na(USEEIO_BEA_NAICS_allocation)] = 1
  # aggregate output for the same NAICS code
  sum_temp = ddply(USEEIO_BEA_NAICS_allocation,.(`2012_NAICS_Code`),summarise,SumOutput=sum(Output))
  USEEIO_BEA_NAICS_allocation = merge(USEEIO_BEA_NAICS_allocation,sum_temp,by="2012_NAICS_Code",all.x=TRUE)
  # compute allocation factor
  USEEIO_BEA_NAICS_allocation$allocation_factor = USEEIO_BEA_NAICS_allocation$Output/USEEIO_BEA_NAICS_allocation$SumOutput
  
  USEEIO_BEA_NAICS_allocation = USEEIO_BEA_NAICS_allocation[c("2012_NAICS_Code",USEEIO_Code,"allocation_factor")]
  
  return(USEEIO_BEA_NAICS_allocation)
}
