import pandas as pd
import pickle as pkl
import yaml
import sys
import statistics
from currency_converter import CurrencyConverter
from datetime import date
from pathlib import Path

import fedelemflowlist as fedelem
from esupy.dqi import get_weighted_average

# add path to subfolder for importing modules
path_proj = Path(__file__).parents[1]
sys.path.append(str(path_proj / 'import_factors_exio'))  # accepts str, not pathlib obj
from API_Imports_Data_Script import get_imports_data
from Exiobase_downloads import process_exiobase

''' 
VARIABLES:
path = data path, set to parent directory
t_df = dataframe of tiva region imports data
e = complete exiobase model
e_m = extracts m vector (containing emission factors per unit currency)
i_d = imports data
t_e = region mappings from BEA TiVA to exiobase countries
t_c = BEA TiVA import contributions coefficients, by BEA naics category for 
      available region datasets
e_u_b = exiobase to detail useeio concordance, binary format, from exiobase team
e_u_l = exiobase to detail useeio concordance, converted to long format
e_u = exiobase to detail useeio concordance, condensed long format
u_cc = complete useeio internal concordance
u_c = useeio detail to summary code concordance
r_i = imports, by NAICS category, from countries aggregated in 
      TiVA regions (ROW, EU, APAC)
e_d = Exiobase emission factors per unit currency
'''

#%%
# set list of years to run for factors
years = [2019]
# years = list(range(2012,2021))

dataPath = Path(__file__).parent / 'data'
conPath = Path(__file__).parent / 'concordances'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'
out_Path = Path(__file__).parent / 'output'
out_Path.mkdir(exist_ok=True)

flow_cols = ('Flow', 'Compartment', 'Unit',
             'CurrencyYear', 'EmissionYear', 'PriceType',
             'Flowable', 'Context', 'FlowUUID', 'ReferenceCurrency')

#%%

with open(dataPath / "exio_config.yml", "r") as file:
    config = yaml.safe_load(file)


def generate_exio_factors(years: list):
    '''
    Runs through script to produce emission factors for U.S. imports from exiobase
    '''
    for year in years:
        # Country imports by detail sector
        sr_i = get_subregion_imports(year)
        if len(sr_i.query('`Import Quantity` <0')) > 0:
            print('WARNING: negative import values...')
        if sum(sr_i.duplicated(['CountryCode', 'BEA Detail'])) > 0:
            print('Error calculating country coefficients by detail sector')

        ## Generate country specific emission factors by BEA sector weighted
        ## by exports to US when sector mappings are not clean
        e_u = get_exio_to_useeio_concordance()
        e_d = pull_exiobase_multipliers(year)
        e_bil = pull_exiobase_bilateral_trade(year)
        export_field = list(config.get('exports').values())[0]
        e_d = (e_d.merge(e_bil, on=['CountryCode','Exiobase Sector'], how='left')
                  .merge(e_u, on='Exiobase Sector', how='left')
                  .drop(columns=['Exiobase Sector','Year']))
        e_d = e_d.query(f'`{export_field}` > 0')
        # INSERT HERE TO REVIEW SECTOR CONTRIBUTIONS WITHIN A COUNTRY
        agg = e_d.groupby(['BEA Detail', 'CountryCode', 'TiVA Region']).agg('sum')
        for c in [c for c in agg.columns if c != export_field]:
            agg[c] = get_weighted_average(e_d, c, export_field, 
                                          ['BEA Detail','CountryCode'])
        # ^^ make sure not to drop when all exports to US are 0 but only single sector e.g. "USED"
        u_c = get_detail_to_summary_useeio_concordance()
        ## Combine EFs with contributions by country
        multiplier_df = (agg.reset_index().drop(columns=export_field)
                            .merge(sr_i.drop(columns=['Unit', 'TiVA Region']),
                                   how='left',
                                   on=['CountryCode', 'BEA Detail'])
                            .merge(u_c, how='left', on='BEA Detail', validate='m:1')
                            )
            ## CONSIDER OUTER MERGE ^^
        multiplier_df = calc_contribution_coefficients(multiplier_df)

        multiplier_df = multiplier_df.melt(
            id_vars = [c for c in multiplier_df if c not in 
                       config['flows'].values()],
            var_name = 'Flow',
            value_name = 'EF')
    
        multiplier_df = (
            multiplier_df
            .assign(Compartment='emission/air')
            .assign(Unit='kg')
            .assign(ReferenceCurrency='Euro')
            .assign(CurrencyYear=str(year))
            .assign(EmissionYear='2019' if year > 2019 else str(year))
            # ^^ GHG data stops at 2019
            .assign(PriceType='Basic')
            )
    
        fl = (fedelem.get_flows()
              .query('Flowable in @multiplier_df.Flow')
              .filter(['Flowable', 'Context', 'Flow UUID'])
              )
        multiplier_df = (
            multiplier_df
            .merge(fl, how='left',
                   left_on=['Flow', 'Compartment'],
                   right_on=['Flowable', 'Context'],
                   )
            .assign(Flowable=lambda x: x['Flowable'].fillna(x['Flow']))
            .drop(columns=['Flow', 'Compartment'])
            .rename(columns={'Flow UUID': 'FlowUUID'})
            .assign(FlowUUID=lambda x: x['FlowUUID'].fillna('n.a.'))
            .assign(Context=lambda x: x['Context'].fillna('emission/air'))
            )

        # Currency adjustment
        c = CurrencyConverter(fallback_on_missing_rate=True)
        exch = statistics.mean([c.convert(1, 'EUR', 'USD', date=date(year, 1, 1)),
                                c.convert(1, 'EUR', 'USD', date=date(year, 12, 30))])
        multiplier_df = (
            multiplier_df
            .assign(EF=lambda x: x['EF']/exch)
            .assign(ReferenceCurrency='USD')
            )
        multiplier_df.loc[multiplier_df['Flowable'] == 'HFCs and '
                              'PFCs, unspecified', 'Unit'] = 'kg CO2e'
        #^^ update units to kg CO2e for HFCs and PFCs unspecified, consider
        # more dynamic implementation

        multiplier_df.to_csv(
            out_Path /f'multiplier_df_exio_{year}.csv', index=False)
        calculate_and_store_emission_factors(multiplier_df)
        
        # # Recalculat using TiVA regions
        # t_c = calc_tiva_coefficients(year)
        # imports_multipliers = calculateWeightedEFsImportsData(
        #     # weighted_multipliers_bea_summary, t_c)
        #     weighted_multipliers_bea_summary_tiva.query('Amount_summary_tiva != 0'),
        #     t_c.query('region_contributions_imports != 0'),
        #     year)
        # check = (set(t_c.query('region_contributions_imports != 0')['BEA Summary']) - 
        #          set(weighted_multipliers_bea_summary_tiva.query('Amount_summary_tiva != 0')['BEA Summary']))
        # if len(check) > 0:
        #     print(f'There are sectors with imports but no emisson factors: {check}')



def get_tiva_data(year):
    '''
    Iteratively pulls BEA imports data matricies from stored csv file,
    extracts the Total Imports columns by region, and consolidates 
    into one dataframe. 
    
    https://apps.bea.gov/iTable/?reqid=157&step=1
    '''

    f_n = f'Import Matrix, __region__, After Redefinitions_{year}.csv'
    regions = {'Canada': 'CA',
               'China': 'CN', 
               'Europe': 'EU',
               'Japan': 'JP',
               'Mexico': 'MX', 
               'Rest of Asia and Pacific': 'APAC',
               'Rest of World': 'ROW',
               }
    ri_df = pd.DataFrame()
    for region, abbv in regions.items():
        r_path = f_n.replace('__region__', region)
        df = (pd.read_csv(dataPath / r_path, skiprows=3, index_col=0)
                 .drop(['IOCode'])
                 .drop(['Commodities/Industries'], axis=1)
                 .dropna()
                 .apply(pd.to_numeric)
                 )
        df[abbv] = df[list(df.columns)].sum(axis=1) # row sums
        ri_r = df[[abbv]]
        ri_df = pd.concat([ri_df, ri_r], axis=1)

    return ri_df


def calc_tiva_coefficients(year, level='Summary'):
    '''
    Calculate the fractional contributions, by TiVA region, to total imports
    by BEA-summary sector. Resulting dataframe is long format. 
    '''
    t_df = get_tiva_data(year)
    corr = (pd.read_csv(conPath / 'tiva_imports_corr.csv',
                        usecols=['TiVA', f'BEA {level}'])
            .drop_duplicates())
    # ^^ requires mapping of import codes to summary codes. These codes are 
    # between detail and summary.

    t_c = (t_df
           .reset_index()
           .rename(columns={'IOCode': 'TiVA'})
           .merge(corr, on='TiVA', how='left', validate='one_to_many')
           .drop(columns='TiVA')
           .groupby(f'BEA {level}').agg('sum'))
    count = list(t_c.loc[(t_c.sum(axis=1) != 0),].reset_index()[f'BEA {level}'])
    ## ^^ Sectors with imports
    t_c = (t_c.div(t_c.sum(axis=1), axis=0).fillna(0)
              .reset_index())

    if not round(t_c.drop(columns=f'BEA {level}')
                    .sum(axis=1),5).isin([0,1]).all():
        print('WARNING: error calculating import shares.')

    t_c = t_c.melt(id_vars=[f'BEA {level}'], var_name='TiVA Region',
                   value_name='region_contributions_imports')

    return t_c


def get_exio_to_useeio_concordance():
    '''
    Opens Exiobase to USEEIO binary concordance.
    Transforms wide-form Exiobase to USEEIO concordance into long form, 
    extracts all mappings to create new, two column concordance consisting of 
    USEEIO detail and mappings to Exiobase.
    modified slightly from: https://ntnu.app.box.com/v/EXIOBASEconcordances/file/983477211189
    '''
    path = conPath / "exio_to_bea_commodity_concordance.csv"
    e_u_b = (pd.read_csv(path, dtype=str)
               .rename(columns={'Unnamed: 0':'BEA Detail'}))
    e_u_l = pd.melt(e_u_b, id_vars=['BEA Detail'], var_name='Exiobase Sector')
    e_u = (e_u_l.query('value == "1"')
                .reset_index(drop=True))
    e_u = (e_u[['BEA Detail','Exiobase Sector']])
    return e_u


def get_detail_to_summary_useeio_concordance():
    '''
    Opens crosswalk between BEA (summary & detail) and USEEIO (with and 
    without waste disaggregation) sectors. USEEIO Detail with Waste Disagg 
    and corresponding summary-level codes. 
    '''
    path = conPath / 'useeio_internal_concordance.csv'
    u_cc = (pd.read_csv(path, dtype=str)
              .rename(columns={'BEA_Detail_Waste_Disagg': 'BEA Detail',
                               'BEA_Summary': 'BEA Summary'})
              )
    u_c = u_cc[['BEA Detail','BEA Summary']]
    u_c = u_c.drop_duplicates()
    return u_c


def get_subregion_imports(year):
    '''
    Generates dataset of imports by country by sector from BEA and Census
    '''
    sr_i = get_imports_data(year=year)
    path = conPath / 'exio_tiva_concordance.csv'
    regions = (pd.read_csv(path, dtype=str,
                           usecols=['ISO 3166-alpha-2', 'TiVA Region'])
               .rename(columns={'ISO 3166-alpha-2': 'CountryCode'})
               )
    sr_i = (sr_i.merge(regions, on='CountryCode', how='left', validate='m:1')
                .rename(columns={'BEA Sector':'BEA Detail'}))
    return sr_i


def pull_exiobase_multipliers(year):
    '''
    Extracts multiplier matrix from stored Exiobase model.
    '''
    file = resource_Path / f'exio_all_resources_{year}.pkl'
    if not file.exists():
        print(f"Exiobase data not found for {year}")
        process_exiobase(year_start=year, year_end=year, download=True)
    exio = pkl.load(open(file,'rb'))

    # for satellite
    M_df = exio['M'].copy().reset_index()
    fields = {**config['fields'], **config['flows']}
    M_df['flow'] = M_df.stressor.str.split(pat=' -', n=1, expand=True)[0]
    M_df['flow'] = M_df['flow'].map(fields)
    M_df = M_df.loc[M_df.flow.isin(fields.values())]
    M_df = M_df.drop(columns='stressor', level=0).groupby('flow').agg('sum')
    ##  ^^ TODO fix performance warning
    M_df = M_df / 1000000 # units are kg / million Euro

    # # for impacts
    # M_df = exio['N']
    # fields = {**config['fields'], **config['impacts']}
    # M_df = M_df.loc[M_df.index.isin(fields.keys())]

    M_df = (M_df
            .transpose()
            .reset_index()
            .rename(columns=fields)
            .assign(Year=str(year))
            )
    path = conPath / 'exio_tiva_concordance.csv'
    regions = (pd.read_csv(path, dtype=str,
                           usecols=['ISO 3166-alpha-2', 'TiVA Region'])
               .rename(columns={'ISO 3166-alpha-2': 'CountryCode'})
               )
    M_df = M_df.merge(regions, how='left', on='CountryCode')
    return M_df


def pull_exiobase_bilateral_trade(year):
    '''
    Extracts bilateral trade data by industry from countries to the U.S.
    from stored Exiobase model.
    '''
    file = resource_Path / f'exio_all_resources_{year}.pkl'
    if not file.exists():
        print(f"Exiobase data not found for {year}")
        process_exiobase(year_start=year, year_end=year, download=True)
    exio = pkl.load(open(file,'rb'))
    fields = {**config['fields'], **config['exports']}
    t_df = exio['Bilateral Trade']
    t_df = (t_df
            .filter(['US'])
            .reset_index()
            .rename(columns=fields)
            )
    return t_df


def calc_contribution_coefficients(df):
    '''
    Appends contribution coefficients to prepared dataframe.
    '''
    df['Import Quantity'] = df['Import Quantity'].fillna(0)
    t_c = (calc_tiva_coefficients(year=df['Year'][0], level="Detail")
           .rename(columns={'region_contributions_imports': 'TiVA_coefficients'})
           )
    df = df.merge(t_c, on=['BEA Detail', 'TiVA Region'])
    df = calc_coefficients_bea_summary(df)
    df = calc_coefficients_bea_detail(df)

    if not(df['Subregion Contribution to Summary'].fillna(0).between(0,1).all() &
           df['Subregion Contribution to Detail'].fillna(0).between(0,1).all() &
           df['National Contribution to Summary'].fillna(0).between(0,1).all() &
           df['National Contribution to Detail'].fillna(0).between(0,1).all()):
        print('ERROR: Check contribution values outside of [0-1]')
    return df.drop(columns=['TiVA_coefficients'])


def calc_coefficients_bea_summary(df):
    '''
    Calculate the fractional contributions, by sector, of each Exiobase 
    country to the TiVA region they are assigned. This creates 2 new columns:
    1) 'TiVA_indout_subtotal, where industry outputs are summed according to
    TiVA-sector pairings; 2) 'region_contributions_TiVA, where each 
    Exiobase country's industry outputs are divided by their corresponding
    TiVA_indout_subtotals to create the fractional contribution coefficients.
    '''
    
    df['Subregion Contribution to Summary'] = (df['Import Quantity']/
                                               df.groupby(['TiVA Region',
                                                           'BEA Summary'])
                                               ['Import Quantity']
                                               .transform('sum'))

    ## If no imports identified for summary code,
    ## where the country == region, set contribution to 1
    ## where country != region, set contribution to detail equal for all countries
    ## then multiply by the TiVA contributions
    df.loc[(df['Subregion Contribution to Summary'].isna() &
        (df['CountryCode'] == df['TiVA Region'])),
        'detail_contrib'] = 1
    df.loc[(df['Subregion Contribution to Summary'].isna() &
        (df['CountryCode'] != df['TiVA Region'])),
        'detail_contrib'] = (
            1 / df.groupby(['TiVA Region', 'BEA Detail'])
                ['CountryCode'].transform('count'))

    df['National Contribution to Summary'] =(df['Import Quantity']/
                                              df.groupby(['BEA Summary'])
                                              ['Import Quantity']
                                              .transform('sum'))
    df['Subregion Contribution to Summary'] = (
        df['Subregion Contribution to Summary'].fillna(
            df['TiVA_coefficients'] / df.groupby(['TiVA Region', 'BEA Summary'])
            ['TiVA_coefficients'].transform('sum')))
    df['National Contribution to Summary'] = (
        df['National Contribution to Summary'].fillna(
            df['TiVA_coefficients'] * df['detail_contrib']))
    return df.drop(columns='detail_contrib')


def calc_coefficients_bea_detail(df):
    '''
    Calculate the fractional contributions, by sector, of each Exiobase 
    country to their corresponding USEEIO summary-level sector(s). These
    concordances were based on Exiobase sector --> USEEIO Detail-level 
    sector, and USEEIO detail-level sector --> USEEIO summary-level sector
    mappins. The function creates 2 new columns: 1) 'USEEIO_indout_subtotal, 
    where industry outputs are summed according to
    TiVA-Exiobase sector-USEEIO summary sector combinations; 
    2) 'regional_contributions_USEEIO, where each 
    Exiobase country's industry outputs are divided by their corresponding
    USEEIO_indout_subtotals to create the fractional contribution 
    coefficients to each USEEIO category. 
    '''
    
    df['Subregion Contribution to Detail'] = (df['Import Quantity']/
                                              df.groupby(['TiVA Region',
                                                          'BEA Detail'])
                                              ['Import Quantity']
                                              .transform('sum'))
    ## If no imports identified for detail code,
    ## where the country == region, set contribution to 1
    ## where country != region, set contribution to detail equal for all countries
    df.loc[(df['Subregion Contribution to Detail'].isna() &
        (df['CountryCode'] == df['TiVA Region'])),
        'Subregion Contribution to Detail'] = 1
    df.loc[(df['Subregion Contribution to Detail'].isna() &
        (df['CountryCode'] != df['TiVA Region'])),
        'Subregion Contribution to Detail'] = (
            1 / df.groupby(['TiVA Region', 'BEA Detail'])
                ['CountryCode'].transform('count'))
    df['National Contribution to Detail'] =(df['Import Quantity']/
                                              df.groupby(['BEA Detail'])
                                              ['Import Quantity']
                                              .transform('sum'))
    df['National Contribution to Detail'] = (
        df['National Contribution to Detail'].fillna(
            df['TiVA_coefficients'] * df['Subregion Contribution to Detail']))
    return df


def calculate_and_store_emission_factors(multiplier_df):
    '''
    Calculates TiVA-exiobase sector and TiVA-bea summary sector emission
    multipliers.
    '''
    cols = [c for c in multiplier_df if c in flow_cols]
    year = multiplier_df['Year'][0]
    for k, v in {'Subregion Contribution to Detail': 'Detail',
                 'Subregion Contribution to Summary': 'Summary',
                 'National Contribution to Detail': 'Detail',
                 'National Contribution to Summary': 'Summary'}.items():
        r = 'nation' if 'National' in k else 'subregion'
        c =  'CountryCode' if 'National' in k else 'TiVA Region'
        agg_df = (multiplier_df
                  .assign(Amount = (multiplier_df['EF'] * multiplier_df[k])))
        agg_df = (agg_df
                  .groupby([c, f'BEA {v}'] + cols)
                  .agg({'Amount': sum}).reset_index()
                  .rename(columns={f'BEA {v}': 'Sector'})
                  .assign(BaseIOLevel='Summary')
                  )

        agg_df.to_csv(
           out_Path / f'weighted_multipliers_{v}_{r}_exio_{year}.csv', index=False)

        if r == 'nation':
            agg_df = (agg_df
                      .groupby(['Sector'] + cols)
                      .agg({'Amount': sum})
                      .reset_index())
            agg_df.to_csv(
                out_Path /f'nation_{v}_imports_multipliers_exio_{year}.csv', index=False)


def calculateWeightedEFsImportsData(weighted_multipliers,
                                    import_contribution_coeffs, year):
    '''
    Merges import contribution coefficients with weighted exiobase 
    multiplier dataframe. Import coefficients are then multiplied by the 
    weighted exiobase multipliers to produce weighted multipliers that 
    incorporate imports data. These are stored in new 'Weighted-Imports 
    (insert multiplier category)' columns. Subsequently, unnecessary columns, 
    such as unweighted Exiobase multipliers and used contribution factors, 
    are dropped from the dataframe. Other than weighted burden columns, the 
    output dataframe only continues to include 'USEEIO Summary' codes.
    '''
    weighted_df_imports = (
        weighted_multipliers
        .merge(import_contribution_coeffs, how='right', validate='m:1',
               on=['TiVA Region','BEA Summary'])
        .assign(region_contributions_imports=lambda x:
                x['region_contributions_imports'].fillna(0))
        .rename(columns={'Amount_summary_tiva':'EF'})
            )

    weighted_df_imports = (
        weighted_df_imports.assign(Amount=lambda x:
                                   x['EF'] *
                                   x['region_contributions_imports'])
        )
    # INSERT HERE TO GET DATA BY TIVA REGION
    tiva_summary = (weighted_df_imports
                    .groupby(['Flowable', 'TiVA Region', 'BEA Summary'])
                    .agg({'Amount': sum,
                          'region_contributions_imports': sum})
                    .rename(columns={'region_contributions_imports':
                                     'contribution_imports'})
                    )
    tiva_summary['contribution_ef'] = (tiva_summary['Amount'] / 
                                       tiva_summary.groupby(['BEA Summary', 'Flowable'])
                                       ['Amount'].transform('sum'))

    tiva_summary.drop(columns='Amount').to_csv(out_Path /
        f'import_multipliers_by_TiVA_{year}.csv')

    col = [c for c in weighted_df_imports if c in flow_cols]

    imports_multipliers = (
        weighted_df_imports
        .groupby(['BEA Summary'] + col)
        .agg({'Amount': 'sum'})
        .reset_index()
        )
    return imports_multipliers


#%%
if __name__ == '__main__':
    generate_exio_factors(years = years)
