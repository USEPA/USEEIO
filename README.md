# United States Environmentally-Extended Input-Output (USEEIO) Modeling Framework 
A modeling framework for creating versions of the [USEEIO](https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-models) model for estimating
potential impacts of goods and services in the US economy. This framework supports the Sustainable Materials Management program at US EPA (www.epa.gov/smm),
but may also be useful for other purposes. It is built using methods from input-output analysis and life cycle assessment (LCA) that combine industry economic data with data on environmental releases and resources used. A background and description of USEEIO can be found in the original manuscript cited below.

Within this repository are scripts to support:
1. JSON-LD versions of a USEEIO model in [u2o.py](olca/u2o.py)
2. The generation of Import Emission Factors from an MRIO model [here](import_emission_factors/README.md)

## Current platform
[useeior](https://github.com/USEPA/useeior). An R package that reads in economic data, houses model configuration files, generates model components, result matrices and price adjustment matrices, and performs model calculations. useeior is used to generate USEEIO models >= v2.0

### Supporting software
[stateior](https://github.com/USEPA/stateio). An R package that builds Make and Use Input-Output economic model for US states. These support state-specific USEEIO models.

[flowsa](https://github.com/USEPA/flowsa). A Python package that provides the environmental and employment data in the form of regional totals
of flows by North American Industry Classification System (NAICS) industry codes. flowsa in turn gets USEPA facility-based reporting data from [StEWI](https://github.com/usepa/standardizedinventories). useeior either uses flowsa directly or uses datasets output from flowsa for environmental data input. 

[LCIAformatter](https://github.com/USEPA/LCIAformatter). A Python package that provides complete life cycle impact assessment methods or life cycle inventory grouping methods in a standard format. useeior either uses the package directly or uses datasets output from LCIAformatter for indicator data input.

Both flowsa and the LCIAformatter draw on the [fedelemflowlist](https://github.com/USEPA/Federal-LCA-Commons-Elementary-Flow-List) Python package to map elementary flows to use the Federal LCA Commons Elementary Flow List to use a standardized set of elementary flows. 
 
### Serving the model for web applications 
[USEEIO API](https://github.com/USEPA/useeio_api/). A Go lang web server for serving USEEIO models. useeior can write USEEIO models out in a format for use on the USEEIO API.
 
## Former platforms 
[useeiopy](https://github.com/USEPA/useeiopy) and the [IO Model Builder](https://github.com/usepa/IO-model-builder) are Python packages for assembling model components and writing the model out for serving on the USEEIO API or for use in openLCA. These packages were used for created USEEIO v1 models and are not supported for current USEEIO models. The former framework used to generate USEEIO versions <= 1.2 is still accessible under [Releases](https://github.com/USEPA/USEEIO/releases).

## Model Versioning
See the [Versioning Scheme](versioning/VersioningScheme.md) for an explanation of USEEIO model version numbers and names.

## Citation
If you use USEEIO models for your research, please cite the original paper 

Yang Y, Ingwersen WW, Hawkins TR, Srocka M, Meyer DE (2017) 
USEEIO: A New and Transparent United States Environmentally-Extended Input-Output Model. 
Journal of Cleaner Production 158:308-318. DOI:[10.1016/j.jclepro.2017.04.150](https://doi.org/10.1016/j.jclepro.2017.04.150)
[Open access version from PubMed](https://pubmed.ncbi.nlm.nih.gov/30344374/)

If you use a specific software for building or calculating a USEEIO model, please cite that software release. 

If you use a published dataset for a USEEIO model, please cite that dataset. 

## Disclaimer
The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use.  EPA has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information.  Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA.  The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government.
