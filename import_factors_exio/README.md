# Generating Import Factors from Exiobase
To generate import factors from exiobase, run the script [generate_import_factors.py](generate_import_factors.py) 

For each year, the following files are generated:

- *aggregate_detail_imports_multipliers_exio_{year}.csv*: Single set of import factors for the US by detail sector.
- *aggregate_summary_imports_multipliers_exio_{year}.csv*: Single set of import factors for the US by summary sector.
- *aggregate_detail_imports_multipliers_by_subregion_exio_{year}.csv*: Import factors for the US by TiVA region, by summary sector, 
- *aggregate_summary_imports_multipliers_by_subregion_exio_{year}.csv*: Import factors for the US by TiVA region, by summary sector, 
- *detail_imports_multipliers_contribution_by_nation_exio_{year}.csv*: Import factors for the US, disaggregated by nation, by detail sector,
- *summary_imports_multipliers_contribution_by_nation_exio_{year}.csv*: Import factors for the US , disaggregated by nation, by summary sector, 
- *multiplier_df_exio_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

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
