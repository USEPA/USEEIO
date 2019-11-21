# United States Environmentally-Extended Input-Output (USEEIO) Modeling Framework 
A modeling framework for creating versions of the USEEIO model for estimating
potential impacts of goods and services in the US economy in approximately 400 categories.
This framework supports the Sustainable Materials Management program at US EPA (www.epa.gov/smm),
but may also be useful for other purposes. It is built using a technique from life cycle assessment (LCA)
that combines industry economic data with data on environmental releases and resources used.
A background and description of USEEIO can be found in the following publication:

Yang Y, Ingwersen WW, Hawkins TR, Srocka M, Meyer DE (2017) 
USEEIO: A New and Transparent United States Environmentally-Extended Input-Output Model. 
Journal of Cleaner Production 158:308-318. DOI:[10.1016/j.jclepro.2017.04.150](https://doi.org/10.1016/j.jclepro.2017.04.150)

The current modeling framework is now split into two repositories:
1. [useeior](https://github.com/USEPA/useeior) An R package that generates and provides USEEIO model components
 and performs model calculations.

2. [useeiopy](https://github.com/USEPA/useeiopy) A Python package for assembling model components and writing the
model out for serving on the [USEEIO API](https://github.com/USEPA/useeio_api/) or for use in openLCA. Dependent on useeior.

The former framework used to generate USEEIO versions <= 1.2 is still accessible under [Releases](https://github.com/USEPA/USEEIO/releases).

## Citation
If you use this framework to develop models that are then published, please cite the use of
the framework in the following manner. For general uses and referring the concept of this framework, cite:

Ingwersen, WW, Li, M, Yang, Y. United States Environmentally-Extended Input-Output (USEEIO) Modeling Framework. 
DOI: [10.5281/zenodo.1248954](https://doi.org/10.5281/zenodo.1248954)

For uses to build models for research, it's best to cite a specific release version. For example:

Ingwersen, WW, Li, M, Yang, Y. United States Environmentally-Extended Input-Output (USEEIO) Modeling Framework. 
(Version 0.1).DOI: [10.5281/zenodo.1248955](https://doi.org/10.5281/zenodo.1248955)

## Disclaimer
The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use.  EPA has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information.  Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA.  The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government.
