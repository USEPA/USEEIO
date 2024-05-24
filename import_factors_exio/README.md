# Generating Import Factors from Exiobase

"generate_import_factors.py" will pulls the Exiobase data and merges with BEA.
You do not need to run “Exiobase_downloads.py”.

## BEA API Access

To pull data on service imports from the US Bureau of Economic Analysis (BEA) by service category, country, and year, register for the BEA API at https://apps.bea.gov/api/signup/.

After doing so, you'll be provided with an API key via email.

Create the file "../import_factors_exio/API/BEA_API_key.yaml" and add your API key.

## Pull Data from Exiobase and BEA

To generate import factors from exiobase using BEA, run the following. Generating 6 years takes about 70 minutes. The resulting 2017-2022 year files reside in the output subfolder, so you can avoid rerunning if those serve your needs. (Total output: 168.9 MB for 37 items)

	python generate_import_factors.py

You can optionally create a virtual environment first and install the following python libraries:
<!-- Let us know if you also need to add `pip install path` --->

	python3 -m venv env
	source env/bin/activate
	pip install pandas
	pip install pyyaml
	pip install pymrio
	pip install pathlib
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

If you get the error `git-lfs: command not found` you may need to run the following once. [Source](https://stackoverflow.com/questions/67395259/git-clone-git-lfs-filter-process-git-lfs-command-not-found)

	brew install git-lfs
	git lfs install
	git lfs install --system

On a Windows PC, if you get an error installing fedelemflowlist, try deleting the file wiki/Resources/FEDEFLContexts.xlsx to install v1.0.2. (FEDEFLContexts.xlsx does not exist in v1.0.2 and after.) Also, avoid putting a version number in the esupy and fedelemflowlist commands above so you are getting the latest. [See issue](https://github.com/USEPA/fedelemflowlist/issues/162)

<!--
If git-lfs not found next time, run the above outsite virtual env.
Was able to ignore the following the first time:
warning: current user is not root/admin, system install is likely to fail.
warning: error running /Applications/Xcode.app/Contents/Developer/usr/libexec/git-core/git 'config' '--includes' '--system' '--replace-all' 'filter.lfs.clean' 'git-lfs clean -- %f': 'error: could not lock config file /etc/gitconfig: Permission denied' 'exit status 255'


[The wiki](https://github.com/USEPA/fedelemflowlist/wiki/Install#installation-of-python-module-and-dependencies) includes installation instructions for fedelemflowlist. Make sure to use the latest release and not v1.0.8, or just put nothing at all.
-->

[Available models](https://dmap-data-commons-ord.s3.amazonaws.com/index.html?prefix=#USEEIO-State/) - All states 2012-2020.

Now run the app. Before running, you can change the year range at the top of generate_import_factors.py. If the year is not yet available, the other years will still be generated. (2023 was not yet available on May 19, 2024.)

	python generate_import_factors.py

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
