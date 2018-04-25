import useeiopy

#Assemble USEEIOv1.1
#See README.md in useeiopy/Model Builds folder to see what files and folder need to be present before you can build a model
#The assembly step for v.1.1 will download and unzip the USEEIOv1.1 satellite excel files from an EPA server the first
#time its run; this may be slow.
#This creates an iomb.model object

useeio1pt1 = useeiopy.assemble("USEEIOv1.1")

#Print a validation file for the model
useeiopy.validate(useeio1pt1)

#Calculate a model
useeiopy.calculate(useeio1pt1)

