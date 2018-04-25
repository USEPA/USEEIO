#Load detailed Use and Make table
UseDetail07 = read.table(paste(BEApath,"389_Use_2007_PRO_BeforeRedef_NoFinalDemand.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
MakeDetail07 = read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)

source('R/IO/IOfunctions.R')
#Reformat use to use USEEIO new good and service names
use = formatIOTableforIOMB(UseDetail07,"BEA_389_Code","USEEIO1_Commodity")
make = formatIOTableforIOMB(MakeDetail07,"BEA_389_Code","USEEIO1_Commodity")

write.csv(use, paste(USEEIOIOpath,"USEEIOv1_Use_forIOMB.csv",sep=""))
write.csv(make, paste(USEEIOIOpath,"USEEIOv1_Make_forIOMB.csv",sep=""))
