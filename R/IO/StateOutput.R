#Get State output ratios for commodities and industries using existing data
#Static functions that are currently limited by state and year to one example
#State is state acronymn or 'US'
getStateCommodityOutput = function (state,year) {
  #temp - set state = 'ST' to get hypothetical output, set year to 2013
  state = 'ST'
  year = 2013
  SoI_output_file = paste(USEEIOpath,"State_comm_output_",year,".csv",sep="")
  SoI_output = read.table(SoI_output_file, sep=",", header=T, colClasses = c("character","numeric","numeric") ) [c("BEA_389", "US", state)]
  colnames(SoI_output) = c("BEA_389", "US", "SoI")
  SoI_output$SoI_US_ratio = SoI_output$SoI / SoI_output$US
  SoI_output$ICF_category = 2
  return(SoI_output)
}

getStateIndustryOutput = function (state,year) {
  #temp - set state = 'ST' to get hypothetical output, set year to 2013
  state = 'ST'
  year = 2013
  SoI_output_file = paste(USEEIOpath,"State_ind_output_",year,".csv",sep="")
  SoI_output = read.table(SoI_output_file, sep=",", header=T, colClasses = c("character","numeric","numeric") ) [c("BEA_389", "US", state)]
  colnames(SoI_output) = c("BEA_389", "US", "SoI")
  SoI_output$SoI_US_ratio = SoI_output$SoI / SoI_output$US
  return(SoI_output)
}


