#Maps resource and emissions names from original sources

#import flow mapping file
flowmapping = read.table(paste(Crosswalkpath,"USEEIO_FlowMapping.csv",sep=""),header=T,sep = ",",check.names=F,fill=TRUE,colClasses = c(rep("character", 26),rep("numeric",2)))

listOriginalSources = function () {
  return(unique(flowmapping$Source))
}
  

#Takes a sat table in standard format
mapListbyName = function (sattable) {
  if(originalflowsource=="") {
    stop("Set variable 'originalflowsource' first.")
  }
  #Get subset for mapping
  sourcemapping = subset(flowmapping,Source==originalflowsource)
  fieldstokeep = c("OriginalName","NewName","CAS","NewCategory","NewSubCategory","NewUnit","UUID")
  sourcemapping = sourcemapping[,fieldstokeep]
  
  sattablewithmap = merge(sattable,sourcemapping,by.x="FlowName",by.y="OriginalName",all.x=TRUE)
  #Add old flow name as tag is this changes
  if(!identical(sattablewithmap$FlowName,sattablewithmap$NewName)) {
    sattablewithmap$MetaTags = sattablewithmap$FlowName
  }
  sattablewithmap$FlowName = sattablewithmap$NewName
  sattablewithmap$FlowCategory = sattablewithmap$NewCategory
  sattablewithmap$FlowSubCategory = sattablewithmap$NewSubCategory
  sattablewithmap$CAS = sattablewithmap$CAS.y
  sattablewithmap$FlowUnit = sattablewithmap$NewUnit
  sattablewithmap$FlowUUID = sattablewithmap$UUID
  
  
  source('R/Satellite/SatelliteFunctions.R')
  standardnames = colnames(getStandardSatelliteTableFormat())
  sattable  = sattablewithmap[,standardnames]
  return(sattable)
  
}


#Returns full flow information as a vector of 6 components using original name only
#Must set original source before getting this information
#orginal category is an optional parameter
mapFlowbyNameandCategory = function (originalname,originalcategory="") {
  if(originalflowsource=="") {
    stop("Set variable 'originalflowsource' first.")
  }
  sourcemapping = subset(flowmapping,Source==originalflowsource)
  if (nrow(sourcemapping)==0) {
    stop(paste("No flows found for source",originalflowsource))
  }
  if (originalcategory != "") {
    matchingrow = subset(sourcemapping,OriginalName==originalname&&OriginalCategory==originalcategory) 
  } else {
    matchingrow = subset(sourcemapping,OriginalName==originalname)
  }
  if(nrow(matchingrow)==0) {
    stop(paste("No flow found with original name",originalname,"and category",originalcategory,"for source",originalflowsource))
  } else if (nrow(matchingrow)>1) {
    stop(paste("More than 1 flow with name",originalname,"found for source",originalflowsource,"You must specify a context."))
  }
  name = as.character(matchingrow["NewName"])
  CAS = as.character(matchingrow["CAS"])
  category = as.character(matchingrow["NewCategory"])
  subcategory = as.character(matchingrow["NewSubCategory"])
  UUID = as.character(matchingrow["UUID"])
  unit = as.character(matchingrow["NewUnit"])
  flow = c(name,CAS,category,subcategory,unit)
  return(flow)
}

mapFlowbyCodeandCategory = function (originalcas,originalcategory="") {
  if(originalflowsource=="") {
    stop("Set variable 'originalflowsource' first.")
  }
  sourcemapping = subset(flowmapping,Source==originalflowsource)
  if (nrow(sourcemapping)==0) {
    stop(paste("No flows found for source",originalflowsource))
  }
  if (originalcategory != "") {
    matchingrow = subset(sourcemapping,OriginalCAS==originalcas&&OriginalCategory==originalcategory) 
  } else {
    matchingrow = subset(sourcemapping,OriginalCAS==originalcas)
  }
  if(nrow(matchingrow)==0) {
    stop(paste("No flow found with original CAS",originalcas,"and category",originalcategory,"for source",originalflowsource))
  } else if (nrow(matchingrow)>1) {
    stop(paste("More than 1 flow with CAS",originalcas,"found for source",originalflowsource,"You must specify a context."))
  }
  name = as.character(matchingrow["NewName"])
  CAS = as.character(matchingrow["CAS"])
  category = as.character(matchingrow["NewCategory"])
  subcategory = as.character(matchingrow["NewSubCategory"])
  UUID = as.character(matchingrow["UUID"])
  unit = as.character(matchingrow["NewUnit"])
  flow = c(name,CAS,category,subcategory,UUID,unit)
  return(flow)
}
