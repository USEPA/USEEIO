import pandas as pd
import pickle as pkl
import numpy as np
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
e_u = exiobase to detail useeio concordance, condensed long format
u_cc = complete useeio internal concordance
u_c = useeio detail to summary code concordance
r_i = imports, by NAICS category, from countries aggregated in 
      TiVA regions (ROW, EU, APAC)
e_d = Exiobase emission factors per unit currency
'''

#%%
# set list of years to run for factors
# years = [2019]
years = list(range(2017,2023))
# years = list(range(2012,2017))
schema = 2017

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


def generate_exio_factors(years: list, schema=2012):
    '''
    Runs through script to produce emission factors for U.S. imports from exiobase
    '''
    for year in years:
        # Country imports by detail sector
        sr_i = get_subregion_imports(year, schema=schema)
        if len(sr_i.query('`Import Quantity` <0')) > 0:
            print('WARNING: negative import values...')
        if sum(sr_i.duplicated(['CountryCode', 'BEA Detail'])) > 0:
            print('Error calculating country coefficients by detail sector')

        elec = get_electricity_imports(year)
        sr_i = pd.concat([sr_i,elec],ignore_index=True)

        ## Generate country specific emission factors by BEA sector weighted
        ## by exports to US when sector mappings are not clean
        e_u = get_exio_to_useeio_concordance(schema=schema)
        e_d = pull_exiobase_multipliers(year)
        e_bil = pull_exiobase_data(year, opt = "bilateral")
        e_out = pull_exiobase_data(year, opt = "output")
        export_field = list(config.get('exports').values())[0]
        e_d = (e_d.merge(e_bil, on=['CountryCode','Exiobase Sector'], how='left')
                  .merge(e_out, on=['CountryCode','Exiobase Sector'], how='left')
                  .merge(e_u, on='Exiobase Sector', how='left')
                  )
        # Perform adjustment for electricity which is not well characterized by
        # export data
        e_d[export_field] = np.where(e_d['BEA Detail'].str.startswith('221100'),
                                     e_d['Output'], e_d[export_field])

        # to maintain US data, use industry output as the export field for US
        e_d[export_field] = np.where(e_d['CountryCode'] == "US",
                                     e_d['Output'], e_d[export_field])

        # INSERT HERE TO REVIEW SECTOR CONTRIBUTIONS WITHIN A COUNTRY
        # Weight exiobase sectors within BEA sectors according to trade
        e_d = e_d.drop(columns=['Exiobase Sector','Year'])
        agg_cols = ['BEA Detail', 'CountryCode', 'TiVA Region', 'BaseIOSchema']
        cols = [c for c in e_d.columns if c not in ([export_field] + agg_cols)]
        agg_dict = {col: 'mean' if col in cols else 'sum'
                    for col in cols + [export_field]}
        agg = e_d.groupby(agg_cols).agg(agg_dict)
        # Don't lose countries with no US exports in exiobase, as these countries
        # may have exports according to US data, collapse them using straight mean
        agg2 = agg.query(f'`{export_field}` == 0')
        agg = agg.query(f'`{export_field}` > 0')
        for c in cols:
            agg[c] = get_weighted_average(e_d.query(f'`{export_field}` > 0'),
                                          c, export_field, agg_cols)
        agg = (pd.concat([agg, agg2], ignore_index=False)
               .reset_index()
               .sort_values(by=['BEA Detail', 'CountryCode'])
               )
        u_c = get_detail_to_summary_useeio_concordance(schema=schema)
        ## Combine EFs with contributions by country
        multiplier_df = (agg.reset_index(drop=True).drop(columns=export_field)
                            .merge(sr_i.drop(columns=['Unit', 'TiVA Region']),
                                   how='left',
                                   on=['CountryCode', 'BEA Detail'])
                            .merge(u_c, how='left', on='BEA Detail', validate='m:1')
                            )
        ## NOTE: If in future more physical data are brought in, the code 
        ##       is unable to distinguish and sort out mismatches by detail/
        ##       summary sectors.

        ## CONSIDER OUTER MERGE ^^

        # Extract out US data separately
        us_df = multiplier_df.query('CountryCode == "US"')
        us_df = df_prepare(us_df, year)
        us_df.to_csv(
            out_Path /f'us_df_exio_{year}_{str(schema)[-2:]}sch.csv', index=False)

        multiplier_df = calc_contribution_coefficients(multiplier_df, schema=schema)
        multiplier_df = df_prepare(multiplier_df, year)
        multiplier_df.to_csv(
            out_Path /f'multiplier_df_exio_{year}_{str(schema)[-2:]}sch.csv', index=False)
        calculate_and_store_emission_factors(multiplier_df)
        
        # Optional: Recalculate using TiVA regions under original approach
        t_c = calc_tiva_coefficients(year, schema=schema)
        calculate_and_store_TiVA_approach(multiplier_df, t_c, year)


def df_prepare(df, year):
    "melt dataframe, add metadata, convert to fedefl and apply currency exchange"
    df = df.melt(
        id_vars = [c for c in df if c not in 
                   config['flows'].values()],
        var_name = 'Flow',
        value_name = 'EF'
        )

    df = (df
        .assign(Compartment='emission/air')
        .assign(Unit='kg')
        .assign(ReferenceCurrency='Euro')
        .assign(CurrencyYear=str(year))
        .assign(EmissionYear='2019' if year > 2019 else str(year))
        # ^^ GHG data stops at 2019
        .assign(PriceType='Basic')
        )

    fl = (fedelem.get_flows()
          .query('Flowable in @df.Flow')
          .filter(['Flowable', 'Context', 'Flow UUID'])
          )
    df = (df
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
    df = (df
        .assign(EF=lambda x: x['EF']/exch)
        .assign(ReferenceCurrency='USD')
        )
    df.loc[df['Flowable'] == 'HFCs and PFCs, unspecified',
           'Unit'] = 'kg CO2e'
    #^^ update units to kg CO2e for HFCs and PFCs unspecified, consider
    # more dynamic implementation

    return df


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

def get_electricity_imports(year):
    url = 'https://www.eia.gov/electricity/annual/xls/epa_02_14.xlsx'
    sheet = 'epa_02_14'
    c_map = {'Mexico':'MX','Canada':'CA'}
    df = pd.read_excel(url, sheet_name=sheet,usecols=[0,1,3],
                       skiprows=[0,1,2,], skipfooter=1)
    df.columns.values[1] = 'Canada'
    df.columns.values[2] = 'Mexico'
    df['Year'] = df['Year'].astype(int)
    df_y = df.loc[df['Year']==year]
    df_y = pd.melt(df_y, id_vars=['Year'],value_vars=['Mexico','Canada'])
    df_y = df_y.rename(columns={'variable':'Country',
                                'value':'Import Quantity'})
    df_y = (df_y.assign(Unit='MWh')
            .assign(BEADetail='221100')
            .assign(Source='EIA')
            .rename(columns={'BEADetail':'BEA Detail'}))
    df_y['CountryCode'] = df_y['Country'].map(c_map)
    df_y['TiVA Region']=df_y['CountryCode']
    elec = df_y[['BEA Detail','Year','CountryCode','Import Quantity','Unit',
                 'Source','Country','TiVA Region']]
    elec['Year']=elec['Year'].astype(str)
    return(elec)
    
def calc_tiva_coefficients(year, level='Summary', schema=2012):
    '''
    Calculate the fractional contributions, by TiVA region, to total imports
    by BEA-summary sector. Resulting dataframe is long format. 
    '''
    t_df = get_tiva_data(year)
    col = f'USEEIO_Detail_{schema}' if level == "Detail" else "BEA Summary"
    corr = (pd.read_csv(conPath / 'tiva_imports_corr.csv',
                        usecols=['TiVA', col])
            .rename(columns = {col: f'BEA {level}'})
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


def get_exio_to_useeio_concordance(schema=2012):
    '''
    Opens Exiobase to USEEIO binary concordance.
    modified slightly and flattened from:
        https://ntnu.app.box.com/v/EXIOBASEconcordances/file/983477211189
    '''
    path = conPath / "exio_to_useeio2_commodity_concordance.csv"
    e_u = (pd.read_csv(path, dtype=str)
               .rename(columns={f'USEEIO_Detail_{schema}': 'BEA Detail'}))
    e_u = (e_u.filter(['BEA Detail','Exiobase Sector'])
              .drop_duplicates()
              .reset_index(drop=True)
              .assign(BaseIOSchema = str(int(schema)))
              )
    return e_u


def get_detail_to_summary_useeio_concordance(schema=2012):
    '''
    Opens crosswalk between BEA (summary & detail) and USEEIO (with and 
    without waste disaggregation) sectors. USEEIO Detail with Waste Disagg 
    and corresponding summary-level codes. 
    '''
    path = conPath / 'useeio_internal_concordance.csv'
    u_cc = (pd.read_csv(path, dtype=str)
              .rename(columns={f'USEEIO_Detail_{schema}': 'BEA Detail',
                               'BEA_Summary': 'BEA Summary'})
              )
    u_c = u_cc[['BEA Detail','BEA Summary']]
    u_c = u_c.drop_duplicates()
    return u_c


def get_subregion_imports(year, schema=2012):
    '''
    Generates dataset of imports by country by sector from BEA and Census
    '''
    sr_i = get_imports_data(year=year, schema=schema)
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
    M_df = (M_df
            .sort_index(axis=1)
            .drop(columns='stressor', level=0)
            .groupby('flow').agg('sum')
            )
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


def pull_exiobase_data(year, opt):
    '''
    Extracts bilateral trade data (opt = "bilateral") by industry from
    countries to the U.S. or industry output (opt = "output")
    from stored Exiobase model.
    '''
    file = resource_Path / f'exio_all_resources_{year}.pkl'
    if not file.exists():
        print(f"Exiobase data not found for {year}")
        process_exiobase(year_start=year, year_end=year, download=True)
    exio = pkl.load(open(file,'rb'))
    fields = {**config['fields'], **config['exports'], **config['output']}
    if opt == "bilateral":
        df = exio['Bilateral Trade']
        df = (df
              .filter(['US'])
              .reset_index()
              .rename(columns=fields)
              )
    elif opt == "output":
        df = exio['output']
        df = (df
              .reset_index()
              .rename(columns=fields)
              )
    return df


def calc_contribution_coefficients(df, schema=2012):
    '''
    Appends contribution coefficients to prepared dataframe.
    '''
    df['Import Quantity'] = df['Import Quantity'].fillna(0)
    t_c = (calc_tiva_coefficients(year=df['Year'][0], level="Detail", schema=schema)
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
    Calculates and saves import factors by region and aggregated to national
    totals.
    '''
    schema = str(int(multiplier_df['BaseIOSchema'][0]))
    cols = [c for c in multiplier_df if c in flow_cols]
    year = multiplier_df['Year'][0]
    print(f'Saving files for {year}')
    for k, v in {'Subregion Contribution to Detail': 'Detail',
                 'Subregion Contribution to Summary': 'Summary',
                 'National Contribution to Detail': 'Detail',
                 'National Contribution to Summary': 'Summary'}.items():
        r = 'nation' if 'National' in k else 'subregion'
        c =  'CountryCode' if 'National' in k else 'TiVA Region'
        agg_df = (multiplier_df
                  .assign(FlowAmount = (multiplier_df['EF'] * multiplier_df[k])))
        agg_df = (agg_df
                  .rename(columns={f'BEA {v}': 'Sector'})
                  .groupby([c, 'Sector'] + cols)
                  .agg({'FlowAmount': sum}).reset_index()
                  .assign(BaseIOLevel=v)
                  )

        if r == 'nation':
            (agg_df.rename(columns={'FlowAmount': 'Contribution_to_EF'})
                   .to_csv(out_Path / f'{v.lower()}_imports_multipliers_contribution_by_{r}_exio_{year}_{schema[-2:]}sch.csv', index=False))

            agg_df = (agg_df
                      .groupby(['Sector'] + cols)
                      .agg({'FlowAmount': sum})
                      .assign(BaseIOLevel=v)
                      .reset_index())
            agg_df.to_csv(
                out_Path /f'aggregate_{v.lower()}_imports_multipliers_exio_{year}_{schema[-2:]}sch.csv', index=False)
        elif r == 'subregion':
            agg_df.to_csv(
               out_Path / f'aggregate_{v.lower()}_imports_multipliers_by_{r}_exio_{year}_{schema[-2:]}sch.csv', index=False)


def calculate_and_store_TiVA_approach(multiplier_df,
                                      import_contribution_coeffs, year):
    '''
    Merges import contribution coefficients with weighted exiobase 
    multiplier dataframe. Import coefficients are then multiplied by the 
    weighted exiobase multipliers to produce weighted multipliers that 
    incorporate TiVA imports by region.
    '''
    schema = str(int(multiplier_df['BaseIOSchema'][0]))
    weighted_df_imports = (
        multiplier_df
        .merge(import_contribution_coeffs, how='left', validate='m:1',
               on=['TiVA Region','BEA Summary'])
        .assign(region_contributions_imports=lambda x:
                x['region_contributions_imports'].fillna(0))
        .assign(national_summary_by_tiva=lambda x: x['region_contributions_imports'] *
                x['Subregion Contribution to Summary'])
        .assign(FlowAmount_Summary=lambda x: x['EF'] * x['national_summary_by_tiva'])
        .rename(columns={'national_summary_by_tiva':'National Contribution to Summary TiVA'})
        .assign(national_detail_by_tiva=lambda x: x['region_contributions_imports'] *
                x['Subregion Contribution to Detail'])
        .assign(FlowAmount_Detail=lambda x: x['EF'] * x['national_detail_by_tiva'])
        .rename(columns={'national_detail_by_tiva':'National Contribution to Detail TiVA'}))
        
    weighted_df_imports_td = weighted_df_imports.rename(columns={'FlowAmount_Detail':'FlowAmount'})
    weighted_df_imports_ts = weighted_df_imports.rename(columns={'FlowAmount_Summary':'FlowAmount'})

    cols = [c for c in weighted_df_imports_ts if c in flow_cols]

    imports_multipliers_ts = (
        weighted_df_imports_ts
        .rename(columns={f'BEA Summary': 'Sector'})
        .groupby(['Sector'] + cols)
        .agg({'FlowAmount': 'sum'})
        .reset_index()
        )
    imports_multipliers_td = (
        weighted_df_imports_td
        .rename(columns={f'BEA Detail': 'Sector'})
        .groupby(['Sector'] + cols)
        .agg({'FlowAmount': 'sum'})
        .reset_index()
        )

    check = (set(import_contribution_coeffs.query('region_contributions_imports != 0')['BEA Summary']) - 
              set(imports_multipliers_ts.query('FlowAmount != 0')['Sector']))
    if len(check) > 0:
        print(f'In the Summary TiVA approach, there are sectors with imports but no '
              f'emisson factors: {check}')

    imports_multipliers_ts.to_csv(
        out_Path / f'aggregate_summary_imports_multipliers_TiVA_approach_exio_{year}_{schema[-2:]}sch.csv',
        index=False)
    imports_multipliers_td.to_csv(
        out_Path / f'aggregate_detail_imports_multipliers_TiVA_approach_exio_{year}_{schema[-2:]}sch.csv',
        index=False)


#%%
if __name__ == '__main__':
    generate_exio_factors(years = years, schema = schema)
