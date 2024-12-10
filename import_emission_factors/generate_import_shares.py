"""
Generates import shares (fractions of imports by commodity and country)
"""

from pathlib import Path
import pandas as pd

from download_imports_data import get_imports_data

conPath = Path(__file__).parent / 'concordances'
out_Path = Path(__file__).parent / 'output'

single_country_regions = ('CA', 'MX', 'JP', 'CN')

def generate_import_shares(year, schema):
    useeio_corr = get_detail_to_summary_useeio_concordance(schema=schema)
    # Country imports by detail sector
    imports = get_imports_data(year=year, schema=schema)
    if len(imports.query('`Import Quantity` <0')) > 0:
        print('WARNING: negative import values...')
        imports = imports.query('`Import Quantity` >= 0').reset_index(drop=True)
    if sum(imports.duplicated(['Country', 'BEA Detail'])) > 0:
        print('Error calculating country coefficients by detail sector')

    elec = get_electricity_imports(year)
    imports = pd.concat([imports, elec],ignore_index=True)
    imports = imports.merge(useeio_corr, how='left', on='BEA Detail')
    imports = map_countries_to_regions(imports)
    imports = calc_contribution_coefficients(imports, schema=schema)
    ## ^^ Country contribution coefficients by sector
    imports.to_csv(out_Path / f'import_shares_{year}.csv', index=False)


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


def map_countries_to_regions(df):
    path = conPath / 'country_to_region_concordance.csv'
    regions = (pd.read_csv(path, dtype=str,
                           usecols=['Country', 'Region'])
               )
    df = df.merge(regions, on='Country', how='left', validate='m:1')
    missing = (set(df[df.isnull().any(axis=1)]['Country'])
               - set(regions['Country']))
    if len(missing) > 0:
        print(f'WARNING: missing countries in correspondence: {missing}')

    return df.dropna(subset='Region').reset_index(drop=True)


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
        (df['Region'].isin(single_country_regions))),
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
        (df['Region'].isin(single_country_regions))),
        'cntry_cntrb_to_region_detail'] = 1
    df.loc[(df['cntry_cntrb_to_region_detail'].isna() &
        (~df['Region'].isin(single_country_regions))),
        'cntry_cntrb_to_region_detail'] = (
            1 / df.groupby(['Region', 'BEA Detail'])
                ['Country'].transform('count'))
    return df

#%%
if __name__ == '__main__':
    generate_import_shares(year = 2019, schema = 2017)
