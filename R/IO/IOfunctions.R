#Input-output functions 
#Primary source for direct requirements related functions is BEA's Concepts and Methods of the U.S. Input-Output Accounts (2009), Ch.12 

# create function for adjusting output amount based on CPI
getAdjustedOutput = function (outputyear,referenceyear,location,IsRoUS) {
  if (location == "US") {
    Output = read.table(paste(BEApath,"389_GrossOutput_CurrentDollars.csv",sep=""),sep=",",header=T,row.names=1,check.names=F)
  } else {
    #Output = getStateOutput(location)  #for automated state output
    #Temp solution for static GA output
    source('R/State Model Functions/StateOutput.R')
    Output = getStateIndustryOutput(location,outputyear)
    row.names(Output)  = Output[,'BEA_389']
    if(IsRoUS == TRUE) {
      Output$RoUS = Output$US - Output$SoI
      Output = subset(Output,select=RoUS)
    } else {  
      Output = subset(Output,select=SoI)
    }
    #State output only for 2013 for now
    outputyear = 2013
    colnames(Output) = c('2013')
  }
  CPI = read.table(paste(BEApath,"389_CPI.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
  # adjust Output based on CPI
  # Output is in million dollars so multiply by 1E6
  Output_adj = as.data.frame(Output[,as.character(outputyear)]*1E6*(CPI[,as.character(referenceyear)]/CPI[,as.character(outputyear)]))
  colnames(Output_adj) = "output"
  rownames(Output_adj) = rownames(Output)
  
  return(Output_adj)
}

generatePriceAdjustedCommodityOuputforYear = function(outputyear,referenceyear,location="US",IsRoUS=FALSE) {
  Output = read.table(paste(BEApath,"389_GrossOutput_CurrentDollars.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
  MakeDetail07 = read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F)
  CommodityMixDetail07 = getCommodityMixMatrix(MakeDetail07,"detailed")
  
  industryoutputforyear = as.matrix(getAdjustedOutput(outputyear,referenceyear,location,IsRoUS))
  indoutputvectorforyear = as.matrix(Output[,as.character(year)])
  comoutputforyear = as.data.frame(CommodityMixDetail07%*%indoutputvectorforyear)
  colnames(comoutputforyear) = as.character(year)
  
  #Adjust from millions of dollars to dollars
  comoutputforyear[,1] =  comoutputforyear[,1] * 1E6
  return(comoutputforyear)
}

#Returns a commodity x industry commodity mix matrix
#See Miller and Blair
getCommodityMixMatrix = function (standardMaketable,level) {
  #if (level=="detailed") {
  industry_output_code = "T008"
  no_commodities = 389
  no_industries = 389
  #} 
  #replace NAs with zeros if they exist
  standardMaketable[is.na(standardMaketable)] = 0
  #Make into a matrix
  make = as.matrix(standardMaketable)
  #drop commodity totals
  make = make[1:no_commodities,]
  
  #Divide output by total output to get industryoutputraction
  mix = make[,1:no_industries]/make[,industry_output_code]
  
  #Transpose to commodity by industry
  commoditymix = t(mix)
  
  #check that columns sum to 1
  industryoutputfractions = colSums(commoditymix)
  for (s in industryoutputfractions) {
    if (abs(1-s)>0.01) {
      print("Error in commoditymix")
    }
    
  }
  return(commoditymix)
}


## Derive IO coefficients
# MarketShare from Make 2007
generateMarketShareCoefficientfromMake2007 = function(remove_scrap=TRUE) {
  IO_Make_2007_389 = read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F)[,-390]
  IO_Make_2007_389 = apply(IO_Make_2007_389, 2, as.numeric)
  IO_Make_2007_389[is.na(IO_Make_2007_389)] = 0
  ms = sweep(IO_Make_2007_389, 2, tail(IO_Make_2007_389, 1), '/')
  rownames(ms) = rownames(read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))
  if(remove_scrap==TRUE) {
    ms =  ms[,-which(colnames(ms) %in% c("S00401"))]
  } 
  #Columns for two commodities, 'used and secondhand good' and 'imports' have NAs because colSum was zero.Set to zero here.
  ms[is.na(ms)] = 0
  ms = ms[1:389, ]
  return(ms)
}

generateNonScrapRatiosfromMake2007 = function() {
  
  IO_Make_2007_389 = read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F)[-390,]
  IO_Make_2007_389 = apply(IO_Make_2007_389, 2, as.numeric)
  IO_Make_2007_389[is.na(IO_Make_2007_389)] = 0
  ratios = data.frame((IO_Make_2007_389[,"T008"]-IO_Make_2007_389[,"S00401"])/IO_Make_2007_389[,"T008"])
  rownames(ratios) = rownames(read.table(paste(BEApath,"389_Make_2007_PRO_BeforeRedef.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))[1:389]
  return(ratios)
}

generateTransformationMatrixfromMake2007 = function() {
  ms = data.frame(generateMarketShareCoefficientfromMake2007(),check.names = FALSE)
  nonscrapratios = as.matrix(generateNonScrapRatiosfromMake2007())
  if(all(row.names(ms)==row.names(nonscrapratios))) {
    tm = ms[,1:388]/nonscrapratios[,1]
  } else {
    print("Error rows for industries in market shares do not match rows for non scrap ratios")
  }
  tm = as.matrix(tm)
  return(tm)
}


# DirectRequirement from Use 2007
generateDirectRequirementCoefficientfromUse2007 = function (remove_scrap=TRUE) {
  IO_Use_2007_389 = read.table(paste(BEApath,"389_Use_2007_PRO_BeforeRedef_NoFinalDemand.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F)
  IO_Use_2007_389 = apply(IO_Use_2007_389, 2, as.numeric) # convert data.frame to matrix and data class to numeric
  IO_Use_2007_389[is.na(IO_Use_2007_389)] = 0
  dr = sweep(IO_Use_2007_389, 2, tail(IO_Use_2007_389, 1), '/')
  rownames(dr) = rownames(read.table(paste(BEApath,"389_Use_2007_PRO_BeforeRedef_NoFinalDemand.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))
  if(remove_scrap==TRUE) {
    dr =  dr[-which(rownames(dr) %in% c("S00401")),]
    dr = dr[1:388, ]
  } else {
    dr = dr[1:389, ]
  }
  
  return(dr)
}

#takes an IO table with just sector code and changes row and column names to  'code/names/locationcode'
formatIOTableforIOMB = function (IOtable,state_model=FALSE) {
  
  crosswalk = read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""),stringsAsFactors=FALSE)
  #drop Total rows/columns in IOtable, keeps V00100, V00200, and V00300 in UseTable
  IOtable = IOtable[!rownames(IOtable)%in%c("T005","T006","T007","T008"),!colnames(IOtable)=="T008"]
  #modify rownames for IOtable
  IOtablerownamesdf = as.data.frame(rownames(IOtable))
  colnames(IOtablerownamesdf)="rownames"
  IOtablerownamesdf$rownames = as.character(IOtablerownamesdf$rownames)
  #Use left join to preserve order, but haveto make row names a column
  #https://stackoverflow.com/questions/34528297/dplyr-left-join-by-rownames
  codecolumn = paste("USEEIO",majormodelversion,"_Code",sep="")
  namecolumn = paste("USEEIO",majormodelversion,"_Commodity",sep="")
  
  IOtablenewrownames = unique(left_join(IOtablerownamesdf, crosswalk[c(codecolumn,namecolumn)], by=c("rownames"=codecolumn)))
  colnames(IOtablenewrownames)[1] = codecolumn
  #put in lower case
  IOtablenewrownames[,1] = tolower(IOtablenewrownames[,1])
  IOtablenewrownames[,2] = tolower(IOtablenewrownames[,2])
  
  
  #modify colnames for IOtable
  IOtablecolnamesdf = as.data.frame(colnames(IOtable))
  colnames(IOtablecolnamesdf)="colnames"
  IOtablecolnamesdf$colnames = as.character(IOtablecolnamesdf$colnames)
  IOtablenewcolnames = unique(left_join(IOtablecolnamesdf, crosswalk[c(codecolumn,namecolumn)], by=c("colnames"=codecolumn)))
  colnames(IOtablenewcolnames)[1] = codecolumn
  #put in lower case
  IOtablenewcolnames[,1] = tolower(IOtablenewcolnames[,1])
  IOtablenewcolnames[,2] = tolower(IOtablenewcolnames[,2])
  
  if(state_model==TRUE) {
    #double rownames and colnames
    IOtablenewrownames = rbind(IOtablenewrownames,IOtablenewrownames)
    IOtablenewcolnames = rbind(IOtablenewcolnames,IOtablenewcolnames)
    #add locations
    IOtablenewrownames$location = 'NA'
    staterowmax = nrow(IOtable)/2
    rousrowmin = staterowmax + 1
    IOtablenewrownames[1:staterowmax,"location"] = paste("us-",tolower(state_acronym),sep="")
    IOtablenewrownames[rousrowmin:nrow(IOtablenewrownames),"location"] = "rous"
    
    IOtablenewcolnames$location = 'NA'
    statecolmax = ncol(IOtable)/2
    rouscolmin = statecolmax + 1
    IOtablenewcolnames[1:statecolmax,"location"] = paste("us-",tolower(state_acronym),sep="")
    IOtablenewcolnames[rouscolmin:nrow(IOtablenewcolnames),"location"] = "rous"
  } else {
    #add locations
    IOtablenewrownames$location = "us"
    IOtablenewcolnames$location = "us"
  }
  
  
  #assign new row and column names to IOtable
  row.names(IOtable) = paste(IOtablenewrownames[,1],"/",IOtablenewrownames[,2],"/",IOtablenewrownames[,"location"],sep="")
  colnames(IOtable) = paste(IOtablenewcolnames[,1],"/",IOtablenewcolnames[,2],"/",IOtablenewcolnames[,"location"],sep="")
  
  #Set NAs to 0
  IOtable[is.na(IOtable)]=0
  return(IOtable)
}

#Generates output-based allocation factors for a dataframe of BEA codes and a grouping variable
#Input must be dataframe with "Code" and "Group" columns
#Returns codes, groups, and allocation factors
generateOutputBasedAllocationFactorsByGroup = function(codeswithgroups) {
  
  #Get output in desired year and that same currency year
  output = getAdjustedOutput(year,year,location)
  #merge with output
  codeswithgroupswithoutput = merge(codeswithgroups,output,by.x="Code",by.y=0)
  
  #aggregate based on group to get sums of output by group
  outputbygroup =  aggregate(codeswithgroupswithoutput$output,by=list(codeswithgroupswithoutput$Group),sum)
  colnames(outputbygroup) = c("Group","Groupoutput")
  #merge in output totals by group
  codeswithgroupswithoutputandgroupoutput = merge(codeswithgroupswithoutput,outputbygroup,by="Group")
  codeswithgroupswithoutputandgroupoutput$allocationfactor = codeswithgroupswithoutputandgroupoutput$output/codeswithgroupswithoutputandgroupoutput$Groupoutput
  codeswithgroupsandallocation = codeswithgroupswithoutputandgroupoutput[,c("Code","Group","allocationfactor")]
  return(codeswithgroupsandallocation)
}

#Generates the commodity-by-commodity direct requirements table
generateDR1RegionCoeffs = function () {
  dr = generateDirectRequirementCoefficientfromUse2007()
  tm = generateTransformationMatrixfromMake2007()
  #Only generate result if the col names of the direct requirements table match the row names of the transformation matrix
  if (all(colnames(dr)==rownames(tm))) {
    DR_coeffs = dr %*% tm    
  } else {
    print("Error:column names of the direct requirements do not match the rows of the transformation matrix")
  }
  
  return(DR_coeffs)
}
