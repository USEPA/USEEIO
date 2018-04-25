library(reshape2)
source('R/Data Import/BEADataFunctions.R')
USEEIOIOpath = "SI/USEEIO/IO/"

# creata a function to generate the 3-column waste Make/Use table
generate3ColumnDisaggTablefromIOTable = function(iotabletype,originalsectorcode,newsectorcodes) { # iotabletype should be either "Make" or "Use"
  # read in the complete disaggregated table
  DisaggTable = read.table(paste(USEEIOIOpath,originalsectorcode,"DisaggregationFor389_",iotabletype,"_2007_PRO_BeforeRedef.csv",sep=""),
                           sep = ",",header=T,row.names=1,check.names=F) 
  DisaggTable$Index1 = rownames(DisaggTable)
  # transform the table from wide to long
  DisaggTable_long = melt(DisaggTable,id.vars="Index1")
  colnames(DisaggTable_long)[2] = "Index2"
  # create the 3-column waste Use table
  DisaggTable3Column = unique(rbind(DisaggTable_long[DisaggTable_long$Index1%in%newsectorcodes,],
                                    DisaggTable_long[DisaggTable_long$Index2%in%newsectorcodes,]))
  # fill NA with 0
  DisaggTable3Column[is.na(DisaggTable3Column$value),"value"] = 0
  # rename Index1 and Index2 according to iotabletype
  if (iotabletype == "Make") {
    colnames(DisaggTable3Column)[1:2] = c("Industry","Commodity")
    } else {colnames(DisaggTable3Column)[1:2] = c("Commodity","Industry")}
  
  return(DisaggTable3Column)
}


# creata a function to generate the complete disaggregation Make/Use table
generateDisaggTable = function(iotabletype,originalsectorcode) {
  # read in the pre-saved 389 IO Make/Use table
  if (iotabletype == "Make") {
    IO389Table = read.table(paste(BEApath,"389_",iotabletype,"_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
  } else {IO389Table = read.table(paste(BEApath,"389_",iotabletype,"_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)}
  IO389Table$Index1 = rownames(IO389Table)
  # transform the table from wide to long
  IO389Table_long = melt(IO389Table,id.vars="Index1")
  colnames(IO389Table_long)[2] = "Index2"
  # combine with the 3-column waste Use table
  DisaggTable3Column = read.table(paste(USEEIOIOpath,originalsectorcode,"Disaggregation3ColumnFor389_",iotabletype,"_2007_PRO_BeforeRedef.csv",sep=""),
                                  sep=",",header=T,check.names=F)
  colnames(DisaggTable3Column)[1:2] = c("Index1","Index2")
  DisaggTable_long = rbind(IO389Table_long,DisaggTable3Column)
  # drop oldvar
  DisaggTable_long = DisaggTable_long[!DisaggTable_long$Index1==originalsectorcode&!DisaggTable_long$Index2==originalsectorcode,]
  # transform the table from long to wide
  DisaggTable = dcast(DisaggTable_long, Index1 ~ Index2)
  # format
  rownames(DisaggTable) = DisaggTable$Index1
  DisaggTable$Index1 = NULL
  
  return(DisaggTable)
}
