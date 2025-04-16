"""
Generates import factors from selected MRIO.
Current options are: EXIOBASE, CEDA, GLORIA
"""

import pickle as pkl
import sys
from pathlib import Path

import fedelemflowlist as fedelem
import numpy as np
import pandas as pd
import yaml
from esupy.dqi import get_weighted_average

# add path to subfolder for importing modules
path_proj = Path(__file__).parents[1]
sys.path.append(str(path_proj / 'import_emission_factors'))  # accepts str, not pathlib obj
from generate_import_shares import get_detail_to_summary_useeio_concordance, \
    generate_import_shares

#%% Set Parameters for import emission factors
years = list(range(2017,2023)) # list
schema = 2017 # int
source = 'gloria' # options are 'exiobase', 'ceda', 'gloria'

dataPath = Path(__file__).parent / 'data'
conPath = Path(__file__).parent / 'concordances'
resource_Path = Path(__file__).parent / 'processed_mrio_resources'
out_Path = Path(__file__).parent / 'output'
out_Path.mkdir(exist_ok=True)

flow_cols = ('Flow', 'Compartment', 'Unit',
             'Year', 'PriceType',
             'Flowable', 'Context', 'FlowUUID', 'ReferenceCurrency')

#%%

with open(dataPath / "mrio_config.yml", "r") as file:
    config = yaml.safe_load(file)
    config = config.get(source)
    if not config:
        raise IndexError(f'MRIO config not found for {source}')
    if config.get('mapping_file'):
        # read in mapping file and recreate flows dict
        flows = pd.read_csv(dataPath / config['mapping_file'])
        config['mapping_file'] = flows
        config['flows'] = dict(zip(flows['SourceFlowName'], flows['TargetFlowName']))


def generate_import_emission_factors(years: list, schema=2012, calc_tiva=False):
    '''
    Runs through script to produce emission factors for U.S. imports from MRIO
    '''
    for year in years:
        useeio_corr = get_detail_to_summary_useeio_concordance(schema=schema)
        if not (out_Path / f'import_shares_{year}.csv').exists():
            generate_import_shares(year, schema)
        imports = pd.read_csv(out_Path / f'import_shares_{year}.csv')
        imports = map_mrio_countires(imports)

        ## Generate country specific emission factors by BEA sector weighted
        ## by exports to US when sector mappings are not clean
        mrio_to_useeio = get_mrio_to_useeio_concordance(schema=schema)
        mrio_df = pull_mrio_multipliers(year)
        bilateral = pull_mrio_data(year, opt = "bilateral")
        output = pull_mrio_data(year, opt = "output")
        export_field = list(config.get('exports').values())[0]

        mrio_df = (
            mrio_df.merge(bilateral, on=['CountryCode','MRIO Sector'], how='left')
                   .merge(output, on=['CountryCode','MRIO Sector'], how='left')
                   .merge(mrio_to_useeio, on='MRIO Sector', how='left')
                   )

        if config.get('calculation_configs')\
            .get('use_industry_output_for_usa_electricity_imports'):
            # Perform adjustment for electricity which is not well characterized by
            # export data
            mrio_df[export_field] = np.where(mrio_df['BEA Detail'].str.startswith('221100'),
                                            mrio_df['Output'], mrio_df[export_field])

        # to maintain US data, use industry output as the export field for US
        mrio_df[export_field] = np.where(mrio_df['CountryCode'] == "US",
                                         mrio_df['Output'], mrio_df[export_field])

        # INSERT HERE TO REVIEW MRIO SECTOR CONTRIBUTIONS WITHIN A COUNTRY
        # Weight MRIO sectors within BEA sectors according to trade
        mrio_df = mrio_df.drop(columns=['MRIO Sector','Year'])
        agg_cols = ['BEA Detail', 'CountryCode', 'BaseIOSchema']
        cols = [c for c in mrio_df.columns if c not in ([export_field] + agg_cols)]
        agg_dict = {col: 'mean' if col in cols else 'sum'
                    for col in cols + [export_field]}
        agg = mrio_df.groupby(agg_cols).agg(agg_dict)
        # Don't lose countries with no US exports in MRIO, as these countries
        # may have exports according to US data, collapse them using straight mean
        agg2 = agg.query(f'`{export_field}` == 0')
        agg = agg.query(f'`{export_field}` > 0')
        for c in cols:
            agg[c] = get_weighted_average(mrio_df.query(f'`{export_field}` > 0'),
                                          c, export_field, agg_cols)
        agg = (pd.concat([agg, agg2], ignore_index=False)
               .reset_index()
               .sort_values(by=['BEA Detail', 'CountryCode'])
               .merge(useeio_corr, how='left', on='BEA Detail')
               )
        ## ^^ MRIO Emission Factors by USEEIO Detail in MRIO currency

        ## Combine EFs with contributions by country
        # Aggregate imports data by MRIO country code
        imports_agg = (
            imports.groupby(
                [c for c in imports if c not in (
                    'Country', 'Import Quantity', 'cntry_cntrb_to_region_summary',
                    'cntry_cntrb_to_region_detail', 'cntry_cntrb_to_national_summary',
                    'cntry_cntrb_to_national_detail')])
                    .agg({'Import Quantity': sum,
                          'cntry_cntrb_to_region_summary': sum,
                          'cntry_cntrb_to_region_detail': sum,
                          'cntry_cntrb_to_national_summary': sum,
                          'cntry_cntrb_to_national_detail': sum})
                    .reset_index()
                    )
        mrio_country_names = pd.read_csv(dataPath / f'{source}_country_names.csv')
        multiplier_df = (agg.reset_index(drop=True).drop(columns=export_field)
                            .merge(imports_agg.drop(columns=['Unit']),
                                   how='left',
                                   on=['CountryCode', 'BEA Detail', 'BEA Summary'])
                            .merge(mrio_country_names, on='CountryCode', validate='m:1')
                            )
        missing = set(imports_agg['CountryCode']) - set(agg['CountryCode'])
        if(len(missing) > 0):
            print(f'WARNING: missing countries in correspondence: {missing}')

        # Check for sectors missing from MRIO mapping file
        check = pd.concat([
            imports_agg.query('cntry_cntrb_to_national_detail > 0')[['BEA Summary', 'BEA Detail']].drop_duplicates().assign(source='imports'),
            agg[['BEA Summary', 'BEA Detail']].drop_duplicates().assign(source='mrio')],
            ignore_index=True)
        duplicates = check.duplicated(keep=False, subset=['BEA Summary', 'BEA Detail'])
        check_unique = check[~duplicates]
        missing = check_unique.query('source == "imports"').sort_values(by='BEA Summary')
        if(len(missing) > 0):
            print(f'WARNING: sectors with imports not found in MRIO: \n',
                  f'{missing.drop(columns="source").to_string(index=False)}')

        ## NOTE: If in future more physical data are brought in, the code 
        ##       is unable to distinguish and sort out mismatches by detail/
        ##       summary sectors.
        multiplier_df = df_prepare(multiplier_df, year)
        check = (multiplier_df
                 .query('Flow == @multiplier_df["Flow"][0]')
                 .groupby(['BEA Summary']).agg({'cntry_cntrb_to_national_summary':'sum'})
                 .rename(columns={'cntry_cntrb_to_national_summary': 'contrib'})
                 .query('contrib > 0 and contrib <= 0.9999')
                 )
        if(len(check) > 0):
            print(f'WARNING: some sectors may have missing data: \n'
                  f'{check.to_string(index=True)}')
        multiplier_df.to_csv(
            out_Path /f'multiplier_df_{source}_{year}_{str(schema)[-2:]}sch.csv', index=False)
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

    if 'mapping_file' in config:
        mapping = config.get('mapping_file')
        df = (df
            .assign(Context = lambda x: x['Flow'].map(
                pd.Series(mapping['TargetFlowContext'].values,
                          index=mapping['TargetFlowName'])
                .to_dict()))
            .assign(Unit = lambda x: x['Flow'].map(
                pd.Series(mapping['TargetUnit'].values,
                          index=mapping['TargetFlowName'])
                .to_dict()))
            .assign(FlowUUID = lambda x: x['Flow'].map(
                pd.Series(mapping['TargetFlowUUID'].values,
                          index=mapping['TargetFlowName'])
                .to_dict()))
            .assign(Flowable = lambda x: x['Flow'])
            )
    else:
        df = (df
            .assign(Compartment='emission/air')
            .assign(Unit='kg')
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

    df = (df
        .assign(ReferenceCurrency=config['reference_currency'])
        .assign(Year=str(year))
        .assign(PriceType=config['price_type'])
        )

    df = adjust_currency_and_rename_flows_units(df, year)

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
    

def adjust_currency_and_rename_flows_units(df, year):
    if 'currency_function' in config:
        fxn = extract_function_from_config('currency_function')
        df = fxn(df, year)

    df.loc[df['Flowable'] == 'HFCs and PFCs, unspecified',
        'Unit'] = 'kg CO2e'
    #^^ update units to kg CO2e for HFCs and PFCs unspecified, consider
    # more dynamic implementation

    return df


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


def get_mrio_to_useeio_concordance(schema=2012):
    '''
    Opens MRIO to USEEIO binary concordance.
    '''
    path = conPath / config.get('useeio_concordance').get('file')
    fields = config.get('useeio_concordance').get('fields')
    fields = {k.replace('__schema__', str(schema)): v for k,v in fields.items()}
    e_u = pd.read_csv(path, dtype=str).rename(columns={**fields})
    e_u = (e_u.filter(['BEA Detail','MRIO Sector'])
              .drop_duplicates()
              .reset_index(drop=True)
              .assign(BaseIOSchema = str(int(schema)))
              )
    return e_u


def map_mrio_countires(df):
    path = conPath / f'{source}_country_concordance.csv'
    codes = pd.read_csv(path, dtype=str, usecols=['Country', 'CountryCode'])
    df = df.merge(codes, on='Country', how='left', validate='m:1')
    missing = (set(df[df.isnull().any(axis=1)]['Country']))
    if len(missing) > 0:
        print(f'WARNING: missing countries in correspondence: {missing}')

    return df.dropna(subset='CountryCode').reset_index(drop=True)


def pull_mrio_multipliers(year):
    '''
    Extracts multiplier matrix from stored MRIO model.
    '''
    file = resource_Path / f'{source}_all_resources_{year}.pkl'
    if not file.exists():
        print(f"{source} data not found for {year}")
        process_mrio_data(year)
    mrio = pkl.load(open(file,'rb'))

    fields_to_rename = {**config['fields'], **config['flows']}
    M_df = clean_mrio_M_matrix(mrio['M'], fields_to_rename, year)
    M_df = M_df.assign(Year=str(year))

    # # for impacts
    # M_df = mrio['N']
    # fields = {**config['fields'], **config['impacts']}
    # M_df = M_df.loc[M_df.index.isin(fields.keys())]

    return M_df


def pull_mrio_data(year, opt):
    '''
    Extracts bilateral trade data (opt = "bilateral") by industry from
    countries to the U.S. or industry output (opt = "output")
    from stored MRIO model.
    '''
    file = resource_Path / f'{source}_all_resources_{year}.pkl'
    if not file.exists():
        print(f"{source} data not found for {year}")
        process_mrio_data(year)
    mrio = pkl.load(open(file,'rb'))
    fields = {**config['fields'], **config['exports'], **config['output']}
    if opt == "bilateral":
        df = mrio['Bilateral Trade']
        df = (clean_mrio_trade_data(df).rename(columns=fields))
    elif opt == "output":
        df = mrio['output']
        df = (df
              .reset_index()
              .rename(columns=fields)
              )
    return df


def process_mrio_data(year):
    '''
    Wrapper function to call correct MRIO processing function
    '''
    fxn = extract_function_from_config('process_function')
    fxn(year_start=year, year_end=year)


def clean_mrio_M_matrix(M, fields_to_rename, year):
    '''
    Wrapper function to call correct M matrix cleaning function for MRIO
    '''
    fxn = extract_function_from_config('clean_M_function')
    return fxn(M, fields_to_rename, mapping=config.get('mapping_file'), year=year)


def clean_mrio_trade_data(df):
    '''
    Wrapper function to correctly clean the MRIO bilateral trade data
    '''
    if 'clean_trade_function' in config:
        fxn = extract_function_from_config('clean_trade_function')
        return fxn(df)
    else:
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
                out_Path / f'US_{v.lower()}_import_factors_{source}_{year}_{schema[-2:]}sch.csv',
                index=False)
        elif r == 'subregion':
            agg_df.to_csv(
                out_Path / f'Regional_{v.lower()}_import_factors_{source}_{year}_{schema[-2:]}sch.csv',
                index=False)


def calculate_and_store_TiVA_approach(multiplier_df,
                                      import_contribution_coeffs, year):
    '''
    Merges import contribution coefficients with weighted MRIO 
    multiplier dataframe. Import coefficients are then multiplied by the 
    weighted MRIO multipliers to produce weighted multipliers that 
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
        out_Path / f'US_summary_import_factors_TiVA_approach_{source}_{year}_{schema[-2:]}sch.csv',
        index=False)
    imports_multipliers_td.to_csv(
        out_Path / f'US_detail_import_factors_TiVA_approach_{source}_{year}_{schema[-2:]}sch.csv',
        index=False)


def extract_function_from_config(fkey):
    source_fxn = config.get(fkey).split('/')
    try:
        module = __import__(source_fxn[0])
    except ModuleNotFoundError:
        raise ModuleNotFoundError(f'No module named "{source_fxn[0]}". '
                                  f'{fkey} must contain the '
                                  'source module for the function. '
                                  'For example: '
                                  '"download_exiobase/process_exiobase"')
    fxn = getattr(module, source_fxn[1])
    if callable(fxn):
        return fxn
    else:
        raise KeyError(f'Error parsing {fkey} key')


#%%
if __name__ == '__main__':
    generate_import_emission_factors(years = years, schema = schema)
    # multiplier_df = (pd.read_csv(out_Path /f'multiplier_df_{source}_2022_{str(schema)[-2:]}sch.csv')
    #                   .query('Flow == "Carbon dioxide"'))
