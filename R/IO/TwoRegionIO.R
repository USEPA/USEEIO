source("R/InterregionalCommodityFlows.R")
source("R/IO/IOFunctions.R")
state = "GA"
ICF_comm = generate2RegionICFs(state)

#Build two-region Direct Requirement Matrix
generate2RegionDRM = function (state) {
  dr_Use_2007_389 = generateDirectRequirementCoefficientfromUse2007()
  #### 2-region direct requirement matrix (2*389 by 2*389)
  # build an all 0 matrix
  dr_2r = matrix(0, nrow=2*nrow(dr_Use_2007_389), ncol=2*ncol(dr_Use_2007_389))
  # first quadrant (SoI to SoI) 
  dr_2r[1:(nrow(dr_2r)/2), 1:(nrow(dr_2r)/2)] = sweep(dr_Use_2007_389, 1, ICF_comm$SoI2SoI, "*")
  # third quadrant (RoC to SoI)
  dr_2r[((nrow(dr_2r)/2)+1):nrow(dr_2r), 1:(nrow(dr_2r)/2)] = sweep(dr_Use_2007_389, 1, ICF_comm$RoC2SoI, "*")
  # second quadrant (SoI to RoC) 
  dr_2r[1:(nrow(dr_2r)/2), ((nrow(dr_2r)/2)+1):nrow(dr_2r)] = sweep(dr_Use_2007_389, 1, ICF_comm$SoI2RoC, "*")
  # forth quadrant (SoI to RoC) 
  dr_2r[((nrow(dr_2r)/2)+1):nrow(dr_2r), ((nrow(dr_2r)/2)+1):nrow(dr_2r)] = sweep(dr_Use_2007_389, 1, ICF_comm$RoC2RoC, "*")
  # assign row and column names
  crosswalk = read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""))
  rownames = unique(merge(dr_Use_2007_389[,1:2], crosswalk[c("BEA_389_Code","USEEIO1_Commodity")], by.x = 0, by.y = "BEA_389_Code")[,-c(2:3)])
  colnames = unique(merge(t(dr_Use_2007_389[1:2,]), crosswalk[c("BEA_389_Code","USEEIO1_Commodity")], by.x = 0, by.y = "BEA_389_Code")[,-c(2:3)])
  rownames(dr_2r) = c(paste(rownames$Row.names,"/",rownames$USEEIO1_Commodity,"/us-ga",sep=""),
                      paste(rownames$Row.names,"/",rownames$USEEIO1_Commodity,"/us",sep=""))
  colnames(dr_2r) = c(paste(colnames$Row.names,"/",colnames$USEEIO1_Commodity,"/us-ga",sep=""),
                      paste(colnames$Row.names,"/",colnames$USEEIO1_Commodity,"/us",sep=""))
  return(dr_2r)
}

#Build two-region Market Share Matrix
generate2RegionMSM = function (state) {
  ms_Make_2007_389 = generateMarketShareCoefficientfromMake2007()
  #### 2-region market share matrix (2*389 by 2*389)
  # build an all 0 matrix
  ms_2r = matrix(0, nrow=2*389, ncol=2*389)
  # first quadrant (SoI to SoI) 
  ms_2r[1:389, 1:389] = sweep(ms_Make_2007_389, 2, t(ICF_comm$SoI2SoI), "*")
  # third quadrant (RoC to SoI)
  ms_2r[390:778, 1:389] = sweep(ms_Make_2007_389, 2, t(ICF_comm$RoC2SoI), "*")
  # second quadrant (SoI to RoC) 
  ms_2r[1:389, 390:778] = sweep(ms_Make_2007_389, 2, t(ICF_comm$SoI2RoC), "*")
  # forth quadrant (SoI to RoC) 
  ms_2r[390:778, 390:778] = sweep(ms_Make_2007_389, 2, t(ICF_comm$RoC2RoC), "*")
  # assign row and column names
  crosswalk = read.csv(paste(Crosswalkpath,"MasterCrosswalk.csv",sep=""))
  rownames = unique(merge(ms_Make_2007_389[,1:2], crosswalk[c("BEA_389_Code","USEEIO1_Commodity")], by.x = 0, by.y = "BEA_389_Code")[,-c(2:3)])
  colnames = unique(merge(t(ms_Make_2007_389[1:2,]), crosswalk[c("BEA_389_Code","USEEIO1_Commodity")], by.x = 0, by.y = "BEA_389_Code")[,-c(2:3)])
  rownames(ms_2r) = c(paste(rownames$Row.names,"/",rownames$USEEIO1_Commodity,"/us-ga",sep=""),
                      paste(rownames$Row.names,"/",rownames$USEEIO1_Commodity,"/us",sep=""))
  colnames(ms_2r) = c(paste(colnames$Row.names,"/",colnames$USEEIO1_Commodity,"/us-ga",sep=""),
                      paste(colnames$Row.names,"/",colnames$USEEIO1_Commodity,"/us",sep=""))
  return(ms_2r)
}
