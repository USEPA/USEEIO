#establish path to satellite table folder
setModelsubpath = function(model,subpath) { 
  modelsubpath = paste(ModelBuildspath,model,subpath,sep="")
  return(modelsubpath)
}

# Satellite tables visualization
VisualizeSatTables = function(model) {
  SatTablepath = setModelsubpath(model,'/satellite_tables/')
  # read in all satellite tables
  files = list.files(path=SatTablepath,pattern="*_newG&Snames.csv")
  sattables = list()
  sattables = lapply(paste(SatTablepath,files,sep=""),function(x) read.table(x,sep = ",",header=T,check.names=F))
  names(sattables) = gsub(paste(model,"_Satellite_",sep=""),"",files)
  # aggregate FlowAmount by ProcessCode and FlowName in each satellite table
  sattables = lapply(sattables,function(x) aggregate(x[,"FlowAmount"],by=list(x[,"FlowName"],x[,"ProcessCode"],x[,"FlowUnit"]),sum))
  sattables = lapply(sattables,setNames,c("FlowName","ProcessCode","FlowUnit","FlowAmount"))
  # plot
  library(ggplot2)
  library(gridExtra)
  for(i in 1:length(sattables)) {
    N = ifelse(nlevels(unique(sattables[[i]]$FlowName))>=10,10,nlevels(unique(sattables[[i]]$FlowName)))
    sattables[[i]] = sattables[[i]][sattables[[i]]$FlowName%in%unique(sattables[[i]]$FlowName)[1:N],]
    p = list()
    for (j in unique(sattables[[i]]$FlowName)[1:N]) {
      p[[j]] = ggplot(data=sattables[[i]][sattables[[i]]$FlowName==j,], aes(x=ProcessCode, y=FlowAmount))+
        #ylim(min(sattables[[i]]$FlowAmount),max(sattables[[i]]$FlowAmount))+ # ylim keeps all plots in one graph having the same y-axis scale
        geom_bar(stat="identity",fill="steelblue")+
        ylab(paste("FlowAmount (",unique(sattables[[i]]$FlowUnit),")",sep=""))+
        ggtitle(paste(gsub("_newG&Snames.csv","",names(sattables)[[i]])," (flow: ",j,")",sep=""))+
        #coord_flip()
        theme(text=element_text(size=8),axis.text.x=element_text(angle=90,hjust=1))
    }
    plot = do.call(grid.arrange,p)
  }
  return(plot)
}


visualizeSectorbyCoefficientsinSatTable = function (model, sattablename) {
  
  firstv = regexpr("[v]",model)
  modelfirst = substr(model,start=0,stop=firstv-1)
  
  SatTablepath = setModelsubpath(model,'/satellite_tables/')
  file = paste(SatTablepath,modelfirst,"_Satellite_",sattablename,"_newG&Snames.csv",sep="")
  sattable = read.table(file,sep = ",",header=T,check.names=F)
  
  #aggregate FlowAmount by ProcessCode and Location and FlowName in each satellite table
  sattableagg = aggregate(sattable[,"FlowAmount"],by=list(sattable[,"FlowName"],sattable[,"ProcessCode"],sattable[,"ProcessLocation"]), sum)
  colnames(sattableagg) = c("FlowName","ProcessCode","Location","Amount")
  
  #Merge in categories, Agg1 level
  categories = read.table(paste(USEEIOpath,"SectorCategories.csv",sep=""),sep = ",",header=T,check.names=F)[,c(1:2)]
  colnames(categories) = c("ProcessCode","Agg1")
  sattableagg = merge(sattableagg,categories,by="ProcessCode")
  
  materiallist = c("Aluminum Cans","Food")
  sattableagg2 = sattableagg[sattableagg$FlowName %in% materiallist,]
  
  # plot
  library(ggplot2)
  ggplot(sattableagg2,aes(x=ProcessCode,y=Amount,color=Location,shape=FlowName)) + geom_point()
    guides(fill=FALSE)
  
  library(gridExtra)
  
  #Make plot with sectors on x and kg/$ on y, grouped by categories, with unique symbols for coefficients
  
  
} 


# Demand vs. Use: column totals
DemandUseColTtlDiff = function(startyear,endyear) {
  source('R/Demand/Demand.R')
  temp = list()
  for (year in startyear:endyear) {
    # create US Demand
    USDemand = getUSDemandbyYear(year)
    USDemand = USDemand[!rownames(USDemand)=="S00401",]
    # create Use table
    summaryUse = UseSummaryDemandbyYear(year)
    summaryUse[is.na(summaryUse)] = 0
    # adjust F050 in summaryUse
    ImportSummaryTotalIntermediate = ImportSummaryTotalIntermediatebyYear(year)
    ImportSummaryTotalIntermediate[is.na(ImportSummaryTotalIntermediate)] = 0
    summaryUse$F050 = summaryUse$F050 + ImportSummaryTotalIntermediate
    # calculate diff.
    temp[[year-startyear+1]] = (colSums(USDemand)-colSums(summaryUse)*10^6)/(colSums(summaryUse)*10^6)
  }
  comparison = do.call(rbind, temp)
  rownames(comparison) = c(startyear:endyear)
  # set a threshold value for pass/fail
  
  return(comparison)
}


getModelResult = function (model,demand,result) {
  resultspath = setModelsubpath(model,'/results/')
  modelfile = paste(resultspath,model,"_",demand,"_",result,".csv",sep="")
  modelresult = read.table(modelfile,sep = ",",header=T, check.name=F)
  return (modelresult)
}


# full model comparison

adjustSectorCodesAsRownames = function(modelresult) {
  rnames = modelresult[,1]
  modelresult = modelresult[,-1]
  sectorcodes = lapply(rnames,function (x) substr(x,1,6))
  row.names(modelresult) = sectorcodes
  return(modelresult)
}


mergeModelResults = function (model1,model2,demand,result) {
  
  model1result = getModelResult(model1,demand,result)
  model1result = adjustSectorCodesAsRownames(model1result)
  model1impactcategories = colnames(model1result)
  model2result = getModelResult(model2,demand,result)
  model2result = adjustSectorCodesAsRownames(model2result)
  mergedresults = merge(model1result,model2result,by=0)
  row.names(mergedresults) = mergedresults[,1]
  mergedresultswithimpactcategories = list(mergedresults,model1impactcategories)
  return(mergedresultswithimpactcategories)
}

#rank by one impact category
rankSectorbyCategory = function(model,demand,perspective="FINAL",categoryname) {
  
  result = paste(perspective,"_lciacontributions",sep="")
  
  modelresult = getModelResult(model,demand,result)
  #sectors = as.character(modelresult[,1])
  colnames(modelresult)[1] = "sector"
  # remove us-ga and rous from sectors
  modelresult$sector = gsub("/[^/]*$", "", as.character(modelresult$sector))
  
  modelresultforrankings = subset(modelresult,select=c("sector",categoryname))
  # aggregate by sector
  modelresultforrankings = aggregate(modelresultforrankings[categoryname],by=list(modelresultforrankings$sector),sum)
  row.names(modelresultforrankings) = modelresultforrankings[,1]
  modelresultforrankings[,1] = NULL
  
  #Use prop.table which is a special case of sweep
  normalizedresults = prop.table(as.matrix(modelresultforrankings),2)
  sumofnormalizedscores = data.frame(rowSums(normalizedresults))
  rankedresults = sumofnormalizedscores
  rankedresults[,"ranking"] = rank(-sumofnormalizedscores[,1])
  rankedresults = rankedresults[order(rankedresults$ranking),]
  return(rankedresults)
}



#Performs an SMM national/state tool style ranking of sectors
rankSectors = function(model,demand,perspective="FINAL") {

  result = paste(perspective,"_lciacontributions",sep="")
  
  modelresult = getModelResult(model,demand,result)
  #sectors = as.character(modelresult[,1])
  colnames(modelresult)[1] = "sector"
  # remove us-ga and rous from sectors
  modelresult$sector = gsub("/[^/]*$", "", as.character(modelresult$sector))
  # keep columns for rankings
  SMMtoolindicatorfile = "SI/SMMTool/indicators.csv"
  SMMtoolindicators = read.table(SMMtoolindicatorfile,header=T,row.names = 1,sep=",")
  indicatorsforranking = row.names(subset(SMMtoolindicators,InRanking == 1))
  modelresultforrankings = subset(modelresult,select=c("sector",indicatorsforranking))
  # aggregate by sector
  modelresultforrankings = aggregate(modelresultforrankings[indicatorsforranking],by=list(modelresultforrankings$sector),sum)
  row.names(modelresultforrankings) = modelresultforrankings[,1]
  modelresultforrankings[,1] = NULL
  
  #Use prop.table which is a special case of sweep
  normalizedresults = prop.table(as.matrix(modelresultforrankings),2)
  sumofnormalizedscores = data.frame(rowSums(normalizedresults))
  rankedresults = sumofnormalizedscores
  rankedresults[,"ranking"] = rank(-sumofnormalizedscores[,1])
  rankedresults = rankedresults[order(rankedresults$ranking),]
  return(rankedresults)
}

# compare ranking of two models
CompareModelsSectorRanking = function (model1,model2,demand1,demand2,perspective="FINAL") {
  rank1 = rankSectors(model1,demand1)
  rank1$sector = rownames(rank1)
  rank1$sectorcode = substr(rownames(rank1),1,6)
  rank2 = rankSectors(model2,demand2)
  rank2$sector = rownames(rank2)
  rank2$sectorcode = substr(rownames(rank2),1,6)
  rank12 = merge(rank1,rank2,by="sectorcode",all=T)
  
  colnames(rank12) = c("sectorcode",paste(model1,"rowSums.normalizedresults"),paste(model1,"ranking"),paste(model1,"sector"),
                       paste(model2,"rowSums.normalizedresults"),paste(model2,"ranking"),paste(model2,"sector"))
  rank12[,paste(model1,"-",model2," relative diff.",sep="")] = (rank12[,paste(model2,"rowSums.normalizedresults")] - rank12[,paste(model1,"rowSums.normalizedresults")])/rank12[,paste(model1,"rowSums.normalizedresults")]
  rank12[,paste(model1,"-",model2," ranking diff.",sep="")] = rank12[,paste(model2,"ranking")] - rank12[,paste(model1,"ranking")]
  return(rank12)
}


CompareModelsCellWisebyImpactCategory = function (model1,model2,demand,result) {
  
  mergedresultslist = mergeModelResults(model1,model2,demand,result)
  mergedresults = mergedresultslist[[1]]
  model1impactcategories = mergedresultslist[[2]]
  
  for (c in model1impactcategories) {
    model1colname = paste(c,".x",sep="")
    model2colname = paste(c,".y",sep="")
    mergedresults[,c]  = (mergedresults[,model2colname]-mergedresults[,model1colname])/mergedresults[,model1colname]
  }
  relativedifference = mergedresults[,model1impactcategories]
  return(relativedifference)
}


