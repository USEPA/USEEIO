# Generating Import Factors from Exiobase

## BEA API Access

To make calls to US Bureau of Economic Analysis (BEA) API for service imports data (by BEA service category, country, and year), first register at https://apps.bea.gov/api/signup/.

After doing so, users will be provided with an API key to the provided email.

Create the file "../import_factors_exio/API/BEA_API_key.yaml" and add your API key.

## Pull Data from Exiobase

To generate import factors from exiobase, run

	python generate_import_factors.py

Or you can create a virtual environment and install python libraries first:
Try without: `pip install path` - might not be needed.

	python3 -m venv env
	source env/bin/activate
	pip install pandas
	pip install pyyaml
	pip install pymrio
	pip install pathlib
	pip install path
	pip install currencyconverter
	pip install pyarrow

pyarrow is for 64-bit python, whereas fastparquet can be used for 32-bit (but may require additional dependencies).
<!--
    ## Checking python bits for USEEIO install
    #import platform
    ## Either
    #st.write(platform.architecture())
    #print(platform.architecture())
-->

Install esupy and fedelemflowlist

	pip install git+https://github.com/USEPA/esupy.git#egg=esupy

	pip install git+https://github.com/USEPA/fedelemflowlist.git#egg=fedelemflowlist

If you get the error `git-lfs: command not found` you may need to run the following. [Source](https://stackoverflow.com/questions/67395259/git-clone-git-lfs-filter-process-git-lfs-command-not-found)

	brew install git-lfs
	git lfs install
	git lfs install --system

<!--
If git-lfs not found next time, run the above outsite virtual env.
Was able to ignore the following the first time:
warning: current user is not root/admin, system install is likely to fail.
warning: error running /Applications/Xcode.app/Contents/Developer/usr/libexec/git-core/git 'config' '--includes' '--system' '--replace-all' 'filter.lfs.clean' 'git-lfs clean -- %f': 'error: could not lock config file /etc/gitconfig: Permission denied' 'exit status 255'


[The wiki](https://github.com/USEPA/fedelemflowlist/wiki/Install#installation-of-python-module-and-dependencies) includes installation instructions for fedelemflowlist. Make sure to use the latest release and not v1.0.8, or just put nothing at all.
-->

[Available models](https://dmap-data-commons-ord.s3.amazonaws.com/index.html?prefix=#USEEIO-State/) - All states 2012-2020.


## Resulting Data

For each year, the following files are generated:

- *US_detail_import_factors_exio_{year}.csv*: Single set of import factors for the US by detail sector.
- *US_summary_import_factors_exio_{year}.csv*: Single set of import factors for the US by summary sector.
- *Regional_detail_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by detail sector, 
- *Regional_summary_import_factors_exio_{year}.csv*: Import factors for each of seven regions, by summary sector, 
- *country_contributions_by_sector_{year}.csv*: Provides the contribution to sector imports by country
- *multiplier_df_exio_{year}.csv*: Full dataframe with emission factors and contributions by region and sector.

File names are appended with the BEA schema year, e.g., `_17sch`.

## Package requirements
- pandas
- esupy
- fedelemflowlist
- [currencyconverter](https://pypi.org/project/CurrencyConverter/)
- pymrio
