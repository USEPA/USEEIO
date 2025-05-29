# Import Emission Factors

Code in this folder can be used to produce measures of embodied environmental flows per dollar commodity imported into the U.S. 
This is the active implementation of the methodology described in the USEPA report [Estimating embodied environmental flows in international imports for the USEEIO Model](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=362470). The two primary steps are the creation of import sharesand generation of the import emission factors. The first step is the creation of the import shares. The import shares are the fractions of contributions from countries to a dollar import of a given commodity in a year. Import shares are independent of the MRIO. The second major step is the generation of the import emission factors from a given multi-regional input-output (MRIO) model. Import emissions factors are created by an environmental flow (e.g., Carbon dioxide) in units of that flow per USD (e.g., kg/USD).

## Steps

1. Generate Import Shares

Import shares are generated through running [generate_import_shares.py](generate_import_shares.py). This will generate the import_shares for a given year and write an *import_shares_{year}.csv* to the output folder. 
These import shares are defined at two levels of commodity resolution - BEA detail and BEA summary

2. Generate Import Emission Factors from an MRIO 

To generate import emission factors from an MRIO model, the requisite MRIO data and correspondence files must be in place along with configuration data and then a helper script must be prepared to process the MRIO. Once in place the import emission factors for that MRIO can be generated. The substeps include:

2.1. MRIO data files

MRIO data files are not stored in this report. Code may be provided if they can be called and stored locally; otherwise the files need to be provided separately. Per the methodology the data files that are needed are equaivalent to what is defined [for the USEEIO model as $M$ and $q$](https://github.com/USEPA/useeior/blob/master/format_specs/Model.md), and also a trade matrix showing exports of commodities from MRIO regions into the U.S. These files are then accessed using the MRIO helper script. 

2.2. MRIO-USEEIO concordances and country list

A country concordance and a commodity concordance are needed to relate the MRIO countries to countries in the trade data used to generate the import shares for USEEIO, as well as a concordance to relate the commodities in the MRIO to those in USEEIO. These are both stored as .csv files in the [concordances](concordances) folder.

2.3. Add configuration data 

Configuration data specific to the MRIO need to be added to the [mrio_config.yml](data/mrio_config.yml).

2.4 MRIO helper script

A script with functions to further prepare the MRIO model data for use in the IEF generation. These might included currency conversion functions and functions to filter reshape model data, filter out data that will not be used, etc.

2.5 Run script to generate IEFS for that MRIO 
  
Run the script [generate_import_factors.py](generate_import_factors.py) after changing the basic parameters to specific use of the desired MRIO as the source.

For each year, the following files are generated:

- *US_detail_import_factors_{source}_{year}.csv*: Single set of import factors for the US by detail sector.
- *US_summary_import_factors_{source}_{year}.csv*: Single set of import factors for the US by summary sector.
- *Regional_detail_import_factors_{source}_{year}.csv*: Import factors for each of seven regions, by detail sector, 
- *Regional_summary_import_factors_{source}_{year}.csv*: Import factors for each of seven regions, by summary sector, 
- *multiplier_df_{source}_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

File names are appended with the BEA schema year, e.g., `_17sch`.

The field in the *_import_factors* files are defined as

| Field | Description | Example
| --- | --- | ---
| Sector | USEEIO sector code | `325111`
| Year | Year of data | 2021
| Unit | Numerator unit for Import factor | kg
| ReferenceCurrency | Denominator unit for Import factor | USD
| PriceType | Price type of ReferenceCurrency | Basic
| Flowable | Name of substance | Carbon dioxide
| Context | Environmental compartment to or from | air
| FlowUUID | ID from FEDEFL | b6f010fb-a764-3063-af2d-bcb8309a97b7
| FlowAmount | Import factor value | 0.57
| BaseIOLevel | BEA IO table basis | Detail

The environmental flows fields are the same as those used for USEEIO which are from the [Federal LCA Commons Elementary Flow List](https://github.com/USEPA/fedelemflowlist).

## BEA API Access
To make calls to BEA for service imports data (by BEA service category, country, and year), users must first register at https://apps.bea.gov/api/signup/.
After doing so, users will be provided with an API key to the provided email.
Store this as 'BEA_API_key.yaml' in the API subfolder of the import_emission_factors directory.

## Package requirements
- pandas
- esupy
- fedelemflowlist
- [currencyconverter](https://pypi.org/project/CurrencyConverter/)
- openpyxl
- pymrio

## MRIO Schema
Processed MRIO objects are stored as `.pkl` files, separately for each year.
These files are dictionaries which contain dataframes with the following keys:

- *M*: rows are flows, columns are regions and commodities
- *N* (optional): rows are impacts, columsn are regions and commodities
- *Bilateral Trade*: rows are regions and commodities, columns are regions
- *output*: rows are regions and commodities, single column is output
