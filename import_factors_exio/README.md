# Generating Import Factors from Exiobase
To generate import factors from exiobase, run the script [useeio_imports_script.py](useeio_imports_script.py) 

For each year, the following files are generated:

- *aggregate_detail_imports_multipliers_exio_{year}.csv*: Single set of import factors for the US by detail sector.
- *aggregate_summary_imports_multipliers_exio_{year}.csv*: Single set of import factors for the US by summary sector.
- *aggregate_detail_imports_multipliers_by_subregion_exio_{year}.csv*: Import factors for the US by TiVA region, by summary sector, 
- *aggregate_summary_imports_multipliers_by_subregion_exio_{year}.csv*: Import factors for the US by TiVA region, by summary sector, 
- *detail_imports_multipliers_contribution_by_nation_exio_{year}.csv*: Import factors for the US, disaggregated by nation, by detail sector,
- *summary_imports_multipliers_contribution_by_nation_exio_{year}.csv*: Import factors for the US , disaggregated by nation, by summary sector, 
- *multiplier_df_exio_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

## Package requirements
- pandas
- esupy
- fedelemflowlist
- [currencyconverter](https://pypi.org/project/CurrencyConverter/)
- pymrio

## API Key
To make calls to USATrade Online (Census) for goods imports data (by country, NAICS sector and year), users must first create an account on https://usatrade.census.gov/. After doing so, they will be provided with an API key. Store this as 'Census_API_key.yaml' in the API subfolder of the import_factors_exio directory.