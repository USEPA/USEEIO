source("R/InterregionalCommodityFlows.R")
source("R/IO/IOFunctions.R")

#Must declare state_acronym to call this script
### Use IOMB output

if(exists("state")) {
  ICF_comm = generate2RegionICFs(state)
  ICF_comm = ICF_comm[!ICF_comm$BEA_389 == "S00401",]
}

# read in IOMB output data
dr = as.matrix(read.table(paste(IOMBpath,"389_2007_PRO_DirectRequirements.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))
ms = as.matrix(read.table(paste(IOMBpath,"389_2007_PRO_MarketShares.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))
transformation = as.matrix(read.table(paste(IOMBpath,"389_2007_PRO_TransformationMatrix.csv",sep=""),header=T,sep = ",",row.names=1,check.names=F))

generateStateRoUSMatrices = function (matrix) {
  ## 2-region matrix (2*389 by 2*389)
  # build an all 0 matrix
  matrix_2r = matrix(0, nrow=2*nrow(matrix), ncol=2*ncol(matrix))
  # assign i based on dimension of matrix
  i = if(nrow(matrix) == nrow(ICF_comm)) 1 else 2
  # first quadrant (SoI to SoI) 
  matrix_2r[1:(nrow(matrix_2r)/2), 1:(ncol(matrix_2r)/2)] = sweep(matrix, i, ICF_comm$SoI2SoI, "*")
  # third quadrant (RoC to SoI)
  matrix_2r[((nrow(matrix_2r)/2)+1):nrow(matrix_2r), 1:(ncol(matrix_2r)/2)] = sweep(matrix, i, ICF_comm$RoC2SoI, "*")
  # second quadrant (SoI to RoC) 
  matrix_2r[1:(nrow(matrix_2r)/2), ((ncol(matrix_2r)/2)+1):ncol(matrix_2r)] = sweep(matrix, i, ICF_comm$SoI2RoC, "*")
  # forth quadrant (SoI to RoC) 
  matrix_2r[((nrow(matrix_2r)/2)+1):nrow(matrix_2r), ((ncol(matrix_2r)/2)+1):ncol(matrix_2r)] = sweep(matrix, i, ICF_comm$RoC2RoC, "*")
  # assign row and column names
  SoIrownames = paste(substr(rownames(matrix), 1, nchar(rownames(matrix))-2),"us-",tolower(state_acronym),sep="")
  RoCrownames = paste(substr(rownames(matrix), 1, nchar(rownames(matrix))-2),"rous",sep="")
  SoIcolnames = paste(substr(colnames(matrix), 1, nchar(colnames(matrix))-2),"us-",tolower(state_acronym),sep="")
  RoCcolnames = paste(substr(colnames(matrix), 1, nchar(colnames(matrix))-2),"rous",sep="")
  rownames(matrix_2r) = c(SoIrownames,RoCrownames)
  colnames(matrix_2r) = c(SoIcolnames,RoCcolnames)
  return(matrix_2r)
}

# create Direct Requirements 2 region coefficients
generateDR2RegionCoeffs = function () {
  DR2R_coeffs = generateStateRoUSMatrices(dr) %*% generateStateRoUSMatrices(transformation)
  return(DR2R_coeffs)
}

generateDR1RegionCoeffs = function () {
  DR_coeffs = dr %*% transformation
  return(DR_coeffs)
}
