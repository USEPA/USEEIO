#Generates LCIA Factors
#Generate LCIA table
generateLCIA  = function (version) { # version is numeric value, e.g. 1 or 2
  #import LCIA factors
  lciafact = read.table(paste(LCIApath,"LCIA_factors.csv",sep=""),header=TRUE,sep=",",fill=TRUE,encoding="UTF-8",colClasses = c(rep("character",5)))
  #Melt these so there is one indicator score per line
  lciafactlong = melt(lciafact,id.vars = c(1:5))
  #drop zeroes
  lciafactlong = subset(lciafactlong,value!=0)
  #Change colname for merging later
  names(lciafactlong)[names(lciafactlong) == "variable"] = "Abbreviation"
  
  #Previously lciafactlong$value was converted to numeric here but this was changing the value!
  #https://github.com/USEPA/USEEIO/issues/4
  
  #Import LCIA indicator info 
  lciainfo = read.table(paste(LCIApath,"LCIA_indicators.csv",sep=""),header=TRUE,sep=",",check.names=FALSE,encoding="UTF-8")
  #keep version of interest
  lciainfo = lciainfo[,c(colnames(lciainfo)[1:4],version)]
  
  #Rename colnames
  colnames(lciainfo) = c("Full name","Abbreviation","Category","Units","version")
  
  #Remove indicators not used by that version
  lciainfo = subset(lciainfo,version == 1)
  
  #Drop the version column
  lciainfo = lciainfo[,c("Full name","Abbreviation","Category","Units")]
  
  #merge in info for getting indicator metadata
  lciafactlongwithmeta = merge(lciafactlong,lciainfo, by="Abbreviation")
  
  #import LCIA fields for IOMB
  lciafields = read.table(paste(IOMBpath,"LCIA_fields.csv",sep=""),header=TRUE,sep=",")
  
  #Change col names to match those in final format
  colnames(lciafactlongwithmeta) = c("Code","Flow","Compartment","Sub.Compartment","Unit","Flow.UUID","Amount","Name","Group","Ref.Unit")
  
  #Reformat to meet final format
  finallcia = lciafactlongwithmeta[,colnames(lciafields)]
  
  return(finallcia)
}
