#Generate Demand
source('R/Demand/Demand.R')

#Get US demand for 2007 in USD 2013
#StartYear,EndYear,CPIRefYear
USEEIODemand = getUSTotalConsProd(2007,2007,2013)


# Reverse rank the sectors, so highest demand is number 1
USEEIODemandRank = USEEIODemand
for (i in 4:ncol(USEEIODemand)) {
  USEEIODemandRank[,i] = rank(-USEEIODemand[,i])
}
View(USEEIODemandRank)


#Test to see how the results from (I-A)-1*f compare to total commodity output
#Import code to get A matrix and calculate L
source('R/IO/IOfunctions.R')
A = generateDR1RegionCoeffs()
I= diag(nrow(A))
L = solve(I-A)

#verify row and cols identical for L
all.equal(colnames(L),row.names(L)) #TRUE

#Get 2007 Demand from 2007 Use table in millions of dollars
UseDetail07 = read.table(paste(BEApath,"389_Use_2007_PRO_BeforeRedef.csv",sep=""),sep = ",",header=T,row.names=1,check.names=F,nrows=389)
# Replace NAs with 0
UseDetail07[is.na(UseDetail07)]=0
# Import (F05000) of 2122A0 was 1439, corrected it to -2561,a value from the import matrixes for this cell  
UseDetail07["2122A0", "F05000"] = -2561
#Remove scrap
UseDetail07 = UseDetail07[-which(rownames(UseDetail07) %in% c("S00401")),]
#Use total final demand from use detail
FinalDemand2007 = subset(UseDetail07, select="T004")*100000
CommodityOutput2007 = subset(UseDetail07, select="T007")*100000
Usetablecodes = row.names(UseDetail07)

#Check 2007 use table codes in same order as A matrix
Lcodes = colnames(L)
all.equal(Usetablecodes,Lcodes) #all TRUE
#Must merge to get order correct
#Lcodes_df = data.frame('Code'=Lcodes)
#Lwithdemand = merge(Lcodes_df,FinalDemand2007,by.x="Code",by.y=0)
#Lwithdemandandoutput = merge(Lwithdemand,CommodityOutput2007,by.x="Code",by.y=0)

finaldemand = as.matrix(FinalDemand2007)
TotalUse2007 = L %*% finaldemand
colnames(TotalUse2007) = "ComputedOutput"
CompareDemandwithoutput2007 = data.frame(TotalUse2007,CommodityOutput2007)
CompareDemandwithoutput2007$PercentDiff = format((CompareDemandwithoutput2007$ComputedOutput- CompareDemandwithoutput2007$T007)/ CompareDemandwithoutput2007$T007,digits = 4)
row.names(CompareDemandwithoutput2007) = Lcodes
View(CompareDemandwithoutput2007)

#Optionally write-out to csv
#write.csv(CompareDemandwithoutput2007,'../CompareDemandwithoutput2007.csv')


