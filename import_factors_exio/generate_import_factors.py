"""
Generates import factors from EXIOBASE
"""

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
from download_imports_data import get_imports_data
from download_exiobase import process_exiobase


#%%
# set list of years to run for factors
years = list(range(2017,2023))
schema = 2017

dataPath = Path(__file__).parent / 'data'
conPath = Path(__file__).parent / 'concordances'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'
out_Path = Path(__file__).parent / 'output'
out_Path.mkdir(exist_ok=True)

flow_cols = ('Flow', 'Compartment', 'Unit',
             'Year', 'PriceType',
             'Flowable', 'Context', 'FlowUUID', 'ReferenceCurrency')

#%%

with open(dataPath / "exio_config.yml", "r") as file:
    config = yaml.safe_load(file)


def generate_exio_factors(years: list, schema=2012, calc_tiva=False):
    '''
    Runs through script to produce emission factors for U.S. imports from exiobase
    '''
    for year in years:
        u_c = get_detail_to_summary_useeio_concordance(schema=schema)
        # Country imports by detail sector
        sr_i = get_imports_data(year=year, schema=schema)
        if len(sr_i.query('`Import Quantity` <0')) > 0:
            print('WARNING: negative import values...')
            sr_i = sr_i.query('`Import Quantity` >= 0').reset_index(drop=True)
        if sum(sr_i.duplicated(['Country', 'BEA Detail'])) > 0:
            print('Error calculating country coefficients by detail sector')

        elec = get_electricity_imports(year)
        sr_i = pd.concat([sr_i,elec],ignore_index=True)
        sr_i = sr_i.merge(u_c, how='left', on='BEA Detail')
        sr_i = map_imports_to_regions(sr_i)
        sr_i = calc_contribution_coefficients(sr_i, schema=schema)
        ## ^^ Country contribution coefficients by sector
        sr_i.to_csv(out_Path / f'import_shares_{year}.csv',
                    index=False)

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

        # INSERT HERE TO REVIEW MRIO SECTOR CONTRIBUTIONS WITHIN A COUNTRY
        # Weight exiobase sectors within BEA sectors according to trade
        e_d = e_d.drop(columns=['Exiobase Sector','Year'])
        agg_cols = ['BEA Detail', 'CountryCode', 'Region', 'BaseIOSchema']
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
               .merge(u_c, how='left', on='BEA Detail')
               )
        ## ^^ MRIO Emission Factors by USEEIO Detail in MRIO currency

        ## Combine EFs with contributions by country
        # Aggregate imports data by MRIO country code
        sr_i_agg = (sr_i.groupby([c for c in sr_i if c
                                  not in ('Country', 'Import Quantity',
                                          'cntry_cntrb_to_region_summary',
                                          'cntry_cntrb_to_region_detail',
                                          'cntry_cntrb_to_national_summary',
                                          'cntry_cntrb_to_national_detail')])
                    .agg({'Import Quantity': sum,
                          'cntry_cntrb_to_region_summary': sum,
                          'cntry_cntrb_to_region_detail': sum,
                          'cntry_cntrb_to_national_summary': sum,
                          'cntry_cntrb_to_national_detail': sum})
                    .reset_index()
                    )
        exio_country_names = pd.read_csv(dataPath / 'exio_country_names.csv')
        multiplier_df = (agg.reset_index(drop=True).drop(columns=export_field)
                            .merge(sr_i_agg.drop(columns=['Unit', 'Region']),
                                   how='left',
                                   on=['CountryCode', 'BEA Detail', 'BEA Summary'])
                            .merge(exio_country_names, on='CountryCode', validate='m:1')
                            )
        ## NOTE: If in future more physical data are brought in, the code 
        ##       is unable to distinguish and sort out mismatches by detail/
        ##       summary sectors.

        multiplier_df = df_prepare(multiplier_df, year)
        multiplier_df.to_csv(
            out_Path /f'multiplier_df_exio_{year}_{str(schema)[-2:]}sch.csv', index=False)
        calculate_and_store_emission_factors(multiplier_df)
        
        # Optional: Recalculate using TiVA regions under original approach
        if(calc_tiva):
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
        .assign(Year=str(year))
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
    elec = df_y.filter(['BEA Detail', 'Year', 'Import Quantity', 'Unit',
                        'Source', 'Country'])
    elec['Year']=elec['Year'].astype(str)
    return elec
    
def calc_tiva_coefficients(year, level='Summary', schema=2012):
    '''
    Calculate the fractional contributions, by TiVA region, to total imports
    by BEA-summary sector. Resulting dataframe is long format. 
    '''
    t_df = get_tiva_data(year)
    col = f'USEEIO_Detail_{schema}' if level == "Detail" else "BEA Summary"
    corr = (pd.read_csv(conPath / 'tiva_to_useeio2_sector_concordance.csv',
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

    t_c = t_c.melt(id_vars=[f'BEA {level}'], var_name='Region',
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


def map_imports_to_regions(sr_i):
    path = conPath / 'exio_country_concordance.csv'
    regions = (pd.read_csv(path, dtype=str,
                           usecols=['Country', 'CountryCode', 'Region'])
               )
    sr_i = sr_i.merge(regions, on='Country', how='left', validate='m:1')
    missing = (set(sr_i[sr_i.isnull().any(axis=1)]['Country'])
               - set(regions['Country']))
    if len(missing) > 0:
        print(f'WARNING: missing countries in correspondence: {missing}')

    return sr_i.dropna(subset='CountryCode').reset_index(drop=True)


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
    path = conPath / 'exio_country_concordance.csv'
    regions = (pd.read_csv(path, dtype=str,
                           usecols=['CountryCode', 'Region'])
               .dropna()
               .drop_duplicates()
               )
    # merge in regions
    M_df = M_df.merge(regions, how='left', on='CountryCode', validate='m:1')
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
    df = calc_coefficients_bea_detail(df)
    df = calc_coefficients_bea_summary(df)

    if not(df['cntry_cntrb_to_region_summary'].between(0,1).all() &
           df['cntry_cntrb_to_region_detail'].between(0,1).all() &
           df['cntry_cntrb_to_national_summary'].between(0,1).all() &
           df['cntry_cntrb_to_national_detail'].between(0,1).all()):
        print('ERROR: Check contribution values outside of [0-1]')
    return df


def calc_coefficients_bea_summary(df):
    '''
    Calculate the fractional contributions of each country
    to total imports by summary sector
    '''
    df['cntry_cntrb_to_national_summary'] =(df['Import Quantity']/
                                              df.groupby(['BEA Summary'])
                                              ['Import Quantity']
                                              .transform('sum'))

    df['cntry_cntrb_to_region_summary'] = (df['Import Quantity']/
                                               df.groupby(['Region',
                                                           'BEA Summary'])
                                               ['Import Quantity']
                                               .transform('sum'))

    ## If no imports identified for summary code,
    ## where the country == region, set contribution to 1
    df.loc[(df['cntry_cntrb_to_region_summary'].isna() &
        (df['CountryCode'] == df['Region'])),
        'cntry_cntrb_to_region_summary'] = 1

    if (df['cntry_cntrb_to_region_summary'].isnull().sum()) > 0:
        print('WARNING: some summary sectors missing contributions')

    return df


def calc_coefficients_bea_detail(df):
    '''
    Calculate the fractional contributions of each country
    to total imports by detail sector
    '''
    df['cntry_cntrb_to_national_detail'] = (df['Import Quantity']/
                                              df.groupby(['BEA Detail'])
                                              ['Import Quantity']
                                              .transform('sum'))
    
    df['cntry_cntrb_to_region_detail'] = (df['Import Quantity']/
                                              df.groupby(['Region',
                                                          'BEA Detail'])
                                              ['Import Quantity']
                                              .transform('sum'))
    ## If no imports identified for detail code,
    ## where the country == region, set contribution to 1
    ## where country != region, set contribution to detail equal for all countries
    df.loc[(df['cntry_cntrb_to_region_detail'].isna() &
        (df['CountryCode'] == df['Region'])),
        'cntry_cntrb_to_region_detail'] = 1
    df.loc[(df['cntry_cntrb_to_region_detail'].isna() &
        (df['CountryCode'] != df['Region'])),
        'cntry_cntrb_to_region_detail'] = (
            1 / df.groupby(['Region', 'BEA Detail'])
                ['CountryCode'].transform('count'))
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
    for k, v in {'cntry_cntrb_to_region_detail': 'Detail',
                 'cntry_cntrb_to_region_summary': 'Summary',
                 'cntry_cntrb_to_national_detail': 'Detail',
                 'cntry_cntrb_to_national_summary': 'Summary'}.items():
        r = 'nation' if 'national' in k else 'subregion'
        c =  'CountryCode' if 'national' in k else 'Region'
        agg_df = (multiplier_df
                  .dropna(subset='Import Quantity')
                  .assign(FlowAmount = (multiplier_df['EF'] * multiplier_df[k])))
        agg_df = (agg_df
                  .rename(columns={f'BEA {v}': 'Sector'})
                  .groupby([c, 'Sector'] + cols)
                  .agg({'FlowAmount': sum}).reset_index()
                  .assign(BaseIOLevel=v)
                  )

        if r == 'nation':
            agg_df = (agg_df
                      .groupby(['Sector'] + cols)
                      .agg({'FlowAmount': sum})
                      .assign(BaseIOLevel=v)
                      .reset_index())
            agg_df.to_csv(
                out_Path / f'US_{v.lower()}_import_factors_exio_{year}_{schema[-2:]}sch.csv',
                index=False)
        elif r == 'subregion':
            agg_df.to_csv(
                out_Path / f'Regional_{v.lower()}_import_factors_exio_{year}_{schema[-2:]}sch.csv',
                index=False)


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
               on=['Region','BEA Summary'])
        .assign(region_contributions_imports=lambda x:
                x['region_contributions_imports'].fillna(0))
        .assign(national_summary_by_tiva=lambda x: x['region_contributions_imports'] *
                x['cntry_cntrb_to_region_summary'])
        .assign(FlowAmount_Summary=lambda x: x['EF'] * x['national_summary_by_tiva'])
        .rename(columns={'national_summary_by_tiva':'cntry_cntrb_to_national_summary TiVA'})
        .assign(national_detail_by_tiva=lambda x: x['region_contributions_imports'] *
                x['cntry_cntrb_to_region_detail'])
        .assign(FlowAmount_Detail=lambda x: x['EF'] * x['national_detail_by_tiva'])
        .rename(columns={'national_detail_by_tiva':'cntry_cntrb_to_national_detail TiVA'}))

    contribution_comparison = (
        weighted_df_imports
        .filter(['BEA Detail', 'BEA Summary', 'Region', 'Year', 'Country',
                 'cntry_cntrb_to_national_summary',
                 'cntry_cntrb_to_national_summary TiVA'])
        .drop_duplicates()
        .drop(columns=['BEA Detail', 'Country'])
        .groupby(['BEA Summary', 'Region', 'Year']).agg(sum)
        .reset_index()
        .assign(Tiva_over_SID = lambda x: 
                x['cntry_cntrb_to_national_summary TiVA'] /
                x['cntry_cntrb_to_national_summary'])
        .assign(Tiva_minus_SID = lambda x: abs(
                x['cntry_cntrb_to_national_summary TiVA'] -
                x['cntry_cntrb_to_national_summary']))
        )
    contribution_comparison = (
        contribution_comparison
        .query('~(cntry_cntrb_to_national_summary == 0 and '
               '`cntry_cntrb_to_national_summary TiVA` == 0)'))
    contribution_comparison.to_csv(
        out_Path / f'import_shares_comparison_detail_{year}.csv')

    summary = (contribution_comparison
               .groupby(['BEA Summary', 'Year'])
               .agg({'Tiva_minus_SID': ['mean', 'min', 'max']})
               )
    summary.to_csv(out_Path / f'import_shares_comparison_{year}.csv')
        
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
        out_Path / f'US_summary_import_factors_TiVA_approach_exio_{year}_{schema[-2:]}sch.csv',
        index=False)
    imports_multipliers_td.to_csv(
        out_Path / f'US_detail_import_factors_TiVA_approach_exio_{year}_{schema[-2:]}sch.csv',
        index=False)


#%%
if __name__ == '__main__':
    generate_exio_factors(years = years, schema = schema)