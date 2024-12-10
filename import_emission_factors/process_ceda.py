"""
Processes raw CEDA files and stores as a pickle the
relevant matrices for import factors calculation
"""

import pandas as pd

from pathlib import Path
import pickle as pkl


model_Path = Path(__file__).parent / 'mrio_models'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'

PATH_TO_CEDA_M = f"{model_Path}/M_GLOBAL.parquet"
PATH_TO_CEDA_PRICE_INDEX = f"{model_Path}/price_index.parquet"
PATH_TO_CEDA_BACI_HS22 = f"{model_Path}/BACI_HS22.parquet"
PATH_TO_CEDA_Q_USA = f"{model_Path}/q_USA.parquet"

CEDA_BASE_YEAR = 2022

IMPORT_FACTOR_GHG_FLOWS = ["CO2", "CH4", "HFCs", "N2O", "PFCs", "SF6"]

# 100-year Global Warming Potential Values from Box 3.2, Table 1 in IPCC AR5 Synthesis Report:
# https://www.ipcc.ch/site/assets/uploads/2018/02/SYR_AR5_FINAL_full.pdf
GWP100_AR5 = {"CO2": 1, "CH4": 28, "N2O": 265, "SF6": 23500}


def get_path_to_scaled_ceda_uimp_2017(target_year: int):
    return f"{model_Path}/Uimp_2017_scaled_{target_year}.parquet"


def extract_flows_from_ceda_M(target_year: int) -> pd.DataFrame:
    """
    Retrieves CEDA M matrix for flows of interest in import factors
    calculation.

    Rows are country and CEDA sectors, columns are GHG flows.
    """
    M = pd.read_parquet(PATH_TO_CEDA_M).T

    price_index = pd.read_parquet(PATH_TO_CEDA_PRICE_INDEX)
    # units of M are kg/2022 USD
    # Multiply by 2022 USD/target_year USD to get kg/target_year USD
    price_ratio_base_year_to_target_year = (
        (price_index[CEDA_BASE_YEAR] / price_index[target_year])
        .reindex(M.index.get_level_values("sector").unique())
        .fillna(1.0)
    )

    M_target_year = M.mul(price_ratio_base_year_to_target_year, axis=0)

    # Convert CH4, N2O, SF6 to original kg
    gwp_factors = pd.Series(GWP100_AR5).loc[["CH4", "N2O", "SF6"]]
    M_target_year[["CH4", "N2O", "SF6"]] = M_target_year[["CH4", "N2O", "SF6"]].div(
        gwp_factors
    )

    return M_target_year[IMPORT_FACTOR_GHG_FLOWS].reset_index()


def extract_exports_to_usa_from_Uimp_and_baci(
    target_year: int,
) -> pd.DataFrame:
    """
    Extracts exports to USA. Rows are exporting country and sector,
    column is imported values to the US.
    """
    Uimp_target_year = pd.read_parquet(get_path_to_scaled_ceda_uimp_2017(target_year))
    imports_target_year = Uimp_target_year.sum(axis=1)

    baci_usa_imports = pd.DataFrame(pd.read_parquet(PATH_TO_CEDA_BACI_HS22).loc["USA", :])

    exports_to_usa_by_country_sector = baci_usa_imports.mul(
        imports_target_year,
        axis=0,
        # baci does not have all sectors in Uimp
        # fill those with 0's because they correspond to
        # non-globally traded sectors
    ).fillna(0.0)

    # reformat table so its rows have exporting (country, sector)
    # and columns are values of exports to the US
    exports_to_usa_by_country_sector = pd.DataFrame(
        exports_to_usa_by_country_sector.T.stack()
    ).reset_index()
    exports_to_usa_by_country_sector.columns = pd.Index(
        ["country", "sector", "exports_to_usa"],
    )

    return exports_to_usa_by_country_sector


def extract_total_usa_output_from_ceda(target_year: int) -> pd.DataFrame:
    # we only need total output for the USA, even though CEDA
    # has output for all countries
    q_usa = pd.read_parquet(PATH_TO_CEDA_Q_USA)

    price_index = pd.read_parquet(PATH_TO_CEDA_PRICE_INDEX)
    price_ratio_base_year_to_target_year = (
        (price_index[target_year] / price_index[CEDA_BASE_YEAR])
        .reindex(q_usa.index)
        .fillna(1.0)
    )

    q_usa_target_year = q_usa.mul(
        price_ratio_base_year_to_target_year, axis=0
    ).reset_index()
    q_usa_target_year["country"] = "USA"
    q_usa_target_year.columns = pd.Index(
        ["sector", "industry_output", "country"],
    )
    q_usa_target_year = q_usa_target_year.set_index(["country", "sector"])
    return q_usa_target_year


def process_ceda(year_start=2017, year_end=2022):
    years = list(range(year_start, year_end+1))
    resource_Path.mkdir(exist_ok=True)

    for target_year in years:
        print(f"Generating CEDA artifacts for {target_year}")

        M = extract_flows_from_ceda_M(target_year)
        bilateral_trade = extract_exports_to_usa_from_Uimp_and_baci(target_year)  # type: ignore
        output = extract_total_usa_output_from_ceda(target_year)
        mrio_objects = {"M": M, "Bilateral Trade": bilateral_trade, "output": output}

        pkl.dump(mrio_objects, open(f"ceda_all_resources_{target_year}.pkl", "wb"))


if __name__ == '__main__':
    process_ceda(year_start=2019, year_end=2019)
