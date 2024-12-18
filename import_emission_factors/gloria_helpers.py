import pandas as pd
import statistics
from datetime import date

from currency_converter import CurrencyConverter

def clean_gloria_M_matrix(M, fields_to_rename, **kwargs):
    M_df = M.copy().reset_index()
    mapping = kwargs.get('mapping')

    M_df['flow'] = M_df['stressor'].map(fields_to_rename)
    M_df['ConversionFactor'] = M_df['stressor'].map(
        pd.Series(mapping['ConversionFactor'].values,
                  index=mapping['SourceFlowName'])
        .to_dict())

    M_df = M_df.loc[M_df.flow.isin(fields_to_rename.values())]

    cols = M_df.select_dtypes(include='number').columns.drop('ConversionFactor', level=0)
    M_df[cols] = M_df[cols].mul(M_df['ConversionFactor'], axis=0)

    M_df = (M_df
            .sort_index(axis=1)
            .drop(columns=['stressor', 'category'], level=0)
            .groupby('flow').agg('sum')
            )

    M_df = (M_df.transpose().reset_index()
            .rename(columns=fields_to_rename)
            )
    return M_df

def gloria_adjust_currency(df, year):
    df = (df
        .assign(EF=lambda x: x['EF']/1000)
        .assign(ReferenceCurrency='USD')
        )
    return df

def gloria_clean_trade(df):
    return df.filter(['USA']).reset_index()
