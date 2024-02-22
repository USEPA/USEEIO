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

## Census API Access
In order to...

## Package requirements
- pandas
- esupy
- fedelemflowlist
- [currencyconverter](https://pypi.org/project/CurrencyConverter/)
- pymrio
