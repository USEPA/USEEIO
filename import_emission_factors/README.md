# Generating Import Emission Factors from Exiobase
To generate import emission factors from exiobase, run the script [generate_import_factors.py](generate_import_factors.py) 

An import factor is created for an environmental flow (e.g., Carbon dioxide) in units of that flow per USD (e.g., kg/USD).

For each year, the following files are generated:

- *US_detail_import_factors_exio_{year}.csv*: Single set of import factors for the US by detail sector.
- *US_summary_import_factors_exio_{year}.csv*: Single set of import factors for the US by summary sector.
- *Regional_detail_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by detail sector, 
- *Regional_summary_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by summary sector, 
- *import_shares_{year}.csv*: Provides the contribution to sector imports by country
- *multiplier_df_exio_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

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
Store this as 'BEA_API_key.yaml' in the API subfolder of the import_factors_exio directory.

## Package requirements
- pandas
- esupy
- fedelemflowlist
- [currencyconverter](https://pypi.org/project/CurrencyConverter/)
- pymrio

## MRIO Schema
Processed MRIO objects are stored as `.pkl` files, separately for each year.
These files are dictionaries which contain dataframes with the following keys:

- *M*: rows are flows, columns are regions and commodities
- *N* (optional): rows are impacts, columsn are regions and commodities
- *Bilateral Trade*: rows are regions and commodities, columns are regions
- *output*: rows are regions and commodities, single column is output
