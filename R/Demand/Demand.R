## Calculate total consumption and production vectors 

source('R/Demand/USDemandFunctions.R')


#Define consumption and production as a series of final demand columns
Ch = c("F01000","F02R00")
Cb = c("F02S00","F02E00","F02N00")
G = c("F06C00","F06S00","F06E00","F06N00","F07C00","F07S00","F07E00","F07N00","F10C00","F10S00","F10E00","F10N00")
E = "F04000"
I = "F05000"
C= "F03000"
TtlCons = c(Ch,Cb,G)
TtlProd = c(TtlCons,E,I,C)

# startyear and endyear set time range of Consumption and Production
# CPIreferenceyear is the unit of currency for the model
#Multiple years can be given if your are imputing demand. 
getUSTotalConsProd = function (startyear,endyear,CPIreferenceyear,imputedemand=FALSE) {
  # Create US total consumption and production for all years
  temp = list()
  if(imputedemand) {
    for (year in startyear:endyear) {
      temp[[year-startyear+1]] = as.data.frame(cbind(rowSums(generateUSDemandforFutureYear(year)[,TtlCons]),
                                                     rowSums(generateUSDemandforFutureYear(year)[,TtlProd])))
      colnames(temp[[year-startyear+1]]) = c(paste(year,"_US_Consumption",sep=""), paste(year,"_US_Production",sep=""))
    }
    USConsProd = do.call(cbind, temp)
  } else {
    temp[[2007]] = as.data.frame(cbind(rowSums(getUSDetailDemandfromUseTable()[,TtlCons]),
                                                   rowSums(getUSDetailDemandfromUseTable()[,TtlProd])))
    colnames(temp[[2007]]) = c("2007_US_Consumption","2007_US_Production")
    USConsProd = temp[[2007]]
  }
  
  
  # read in processed commodity name
  CommName = unique(read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""))[c("BEA_389_Code","USEEIO1_Commodity")])
  # read in processed price index
  CPI = read.table(paste(BEApath,"389_CPI.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F) 
  # create a crosswalk by merging the CommName and CPI
  crosswalk = merge(CommName, CPI, by.x="BEA_389_Code", by.y=0, all=T)
  # merge USConsProd with crosswalk to create an adjusted USConsProd
  USConsProd_adj = merge(USConsProd, crosswalk, by.x=0, by.y="BEA_389_Code", all.x=T)
  # calculate average CPI for the 4 "troublesome" commodities: S00300, S00401, S00401, S00900
  comm = c("S00300", "S00401", "S00402", "S00900")
  for (i in 1:4) {
    startcol = ncol(USConsProd_adj)-18 # 1997 CPI column
    endcol = ncol(USConsProd_adj) # 2015 CPI column
    USConsProd_adj[USConsProd_adj$Row.names == comm[i],startcol:endcol]=apply(USConsProd_adj[!USConsProd_adj$Row.names %in% comm,startcol:endcol],2,mean)
  }
  # adjust consumption and production according to CPI of RefYear
  for (year in startyear:endyear) {
    USConsProd_adj[,paste(year,"_US_Consumption",sep="")] = USConsProd_adj[,paste(year,"_US_Consumption",sep="")]*USConsProd_adj[,as.character(CPIreferenceyear)]/USConsProd_adj[,as.character(year)]
    USConsProd_adj[,paste(year,"_US_Production",sep="")] = USConsProd_adj[,paste(year,"_US_Production",sep="")]*USConsProd_adj[,as.character(CPIreferenceyear)]/USConsProd_adj[,as.character(year)]
  }
  # add Location column, re-order columns (drop useless columns), and modify colnames
  USConsProd_adj$Location = "US"
  USConsProd_adj = USConsProd_adj[c("Row.names","USEEIO1_Commodity","Location",colnames(USConsProd))]
  colnames(USConsProd_adj)[1:2] = c("BEA_389_code", "BEA_389_def")
  # remove the Scrap row
  USConsProd_adj = USConsProd_adj[!USConsProd_adj$BEA_389_code=="S00401",]
  #make code into a factor
  USConsProd_adj$BEA_389_code = as.factor(USConsProd_adj$BEA_389_code)
  
  return(USConsProd_adj)
}

#Takes a subsystem (final demand coefficients must exist) and a formatted demand df and adds on columns for subsystem demand
addDemandforSubsystem = function (subsystem_name,FormattedFinalDemand) {
  
  #Import subsystem coefficients
  subsystemdemandcoefficients = read.table(paste(USEEIOpath,"USEEIO_SubsystemDemandCoefficients.csv",sep=""),sep=",",header=T,row.names=1)
  subsystemdemandcoefficients = subset(subsystemdemandcoefficients,select=subsystem_name)
  
  allcolnames = colnames(FormattedFinalDemand)
  demandcolnames = colnames(FormattedFinalDemand)[-c(1:3)]
  
  #Tack _subsystem_name onto existing column names to build new column names
  subsysdemandcolnames = as.character(sapply(demandcolnames,function(x) paste(x,"_",subsystem_name,sep="")))
  
  #Merge demand and subsystem coeffs to apply to new subsystem cols
  temp  = merge(FormattedFinalDemand,subsystemdemandcoefficients,by.x=1,by.y=0,all.x=T)
  temp[,subsysdemandcolnames] = temp[,demandcolnames]*temp[,subsystem_name]
  
  FormattedFinalDemandwithSubsystemDemand = temp[,c(allcolnames,subsysdemandcolnames)]
  rm(temp)
  return(FormattedFinalDemandwithSubsystemDemand)
  
}
