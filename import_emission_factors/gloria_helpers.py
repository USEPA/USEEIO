import pandas as pd
import statistics
from datetime import date

from currency_converter import CurrencyConverter

def clean_gloria_M_matrix(M, fields_to_rename, **kwargs):
    M_df = M.copy().reset_index()
    mapping = kwargs.get('mapping')
    year = kwargs.get('year')

    M_df['flow'] = M_df['stressor'].map(fields_to_rename)
    missing = [k for k in fields_to_rename.keys() if k not in M_df['stressor'].values]
    M_df['ConversionFactor'] = M_df['stressor'].map(
        pd.Series(mapping['ConversionFactor'].values,
                  index=mapping['SourceFlowName'])
        .to_dict())

    M_df = M_df.loc[M_df.flow.isin(fields_to_rename.values())]

    cols = M_df.select_dtypes(include='number').columns.drop('ConversionFactor', level=0)
    M_df[cols] = M_df[cols].mul(M_df['ConversionFactor'], axis=0)

    M_df = (M_df
            .sort_index(axis=1)
            .drop(columns=['stressor', 'category', 'ConversionFactor'], level=0)
            .groupby('flow').agg('sum')
            )

    M_df = (M_df.transpose().reset_index()
            .rename(columns=fields_to_rename)
            )

    from generate_import_factors import pull_mrio_data
    # filter dataset with sectors that have reasonable output to avoid outliers
    output = pull_mrio_data(year, 'output')
    M_df = (M_df.merge(output, how = 'left')
            .query('Output > 1000')
            .reset_index(drop=True)
            .drop(columns='Output')
            )
    ## ^^ Note that dropping rows can impact the trade contributions later

    drop_list = [
        # ('CHL', 'Motor vehicles, trailers and semi-trailers'),
        # ('BEL', 'Hard Coal'),
        # ('HKG', 'Rubber products'),
        # ('HKG', 'Plastic products'),
        # ('HKG', 'Quarrying of stone, sand and clay'),
        # ('HKG', 'Chemical and fertilizer minerals'),
        # ('SGP', 'Mining and quarrying n.e.c.; services to mining')
        ]
    for i in drop_list:
        print(f'Dropping outliers for {": ".join(i)}')
        M_df = (M_df.query('~(CountryCode == @i[0] and `MRIO Sector` == @i[1])')
                .reset_index(drop=True))
    return M_df

def gloria_adjust_currency(df, year):
    df = (df
        .assign(EF=lambda x: x['EF']/1000)
        .assign(ReferenceCurrency='USD')
        )
    return df

def gloria_clean_trade(df):
    df = df.filter(['USA']).reset_index()
    df.loc[df['USA'] < 0.01, 'USA'] = 0 # round down very small values
    return df
