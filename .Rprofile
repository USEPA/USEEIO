# ipak function: install and load multiple R packages.
# check to see if packages are installed. Install them if they are not, then load them into the R session.
## adopted from https://gist.github.com/stevenworthington/3178163
.First = function(){
  require(utils) #"data.table"
  pkg = c("bit64","gdata","readxl","plyr","dplyr","datasets","jsonlite","curl","tibble","ggplot2","gridExtra","reshape","reshape2")
  new.pkg = pkg[!(pkg %in% installed.packages()[, "Package"])]
  if (length(new.pkg)){install.packages(new.pkg, dependencies = TRUE, repos="https://cloud.r-project.org")}
  lapply(pkg, require, character.only = TRUE)
}

# define global pathways
# Windows paths uses backslashes
BEApath	= "SI/BEA/"
BLSpath =	"SI/BLS/"
Censuspath = "SI/Census/"
Crosswalkpath =	"SI/Crosswalk/"
IOMBpath = "SI/IOMB/"
LCIApath = "SI/USEEIO/"
MSWpath	= "SI/MSW/"
USEEIOpath = "SI/USEEIO/"
USEEIOIOpath = "SI/USEEIO/IO/"
ModelBuildspath = "useeiopy/Model Builds/"

