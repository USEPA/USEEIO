# Generating Import Factors from Exiobase

To generate import factors from exiobase, run

	python generate_import_factors.py

Or you can create a virtual environment and install python libraries first:

	python3 -m venv env
	source env/bin/activate
	pip install pandas
	pip install pyyaml
	pip install pymrio
	pip install pathlib
	pip install path
	pip install currencyconverter

<!-- Try without: pip install path -->

How do we install `esupy` and `fedelemflowlist`?  NOT these

	npm install git+https://github.com/USEPA/esupy.git#egg=esupy

	npm install git+https://github.com/USEPA/USEEIO.git#egg=fedelemflowlist

## Resulting Data

For each year, the following files are generated:

- *US_detail_import_factors_exio_{year}.csv*: Single set of import factors for the US by detail sector.
- *US_summary_import_factors_exio_{year}.csv*: Single set of import factors for the US by summary sector.
- *Regional_detail_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by detail sector, 
- *Regional_summary_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by summary sector, 
- *country_contributions_by_sector_{year}.csv*: Provides the contribution to sector imports by country
- *multiplier_df_exio_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

File names are appended with the BEA schema year, e.g., `_17sch`.

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
