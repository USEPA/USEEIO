""" Functions to support the processing of EXIOBASE MRIO models"""

import statistics
from datetime import date

from currency_converter import CurrencyConverter

def clean_exiobase_M_matrix(M, fields_to_rename, **kwargs):
    # for satellite
    M_df = M.copy().reset_index()

    M_df['flow'] = M_df.stressor.str.split(pat=' -', n=1, expand=True)[0]
    M_df['flow'] = M_df['flow'].map(fields_to_rename)
    M_df = M_df.loc[M_df.flow.isin(fields_to_rename.values())]
    M_df = (M_df
            .sort_index(axis=1)
            .drop(columns='stressor', level=0)
            .groupby('flow').agg('sum')
            )
    # Exiobase units are kg / million Euro, convert to kg / Euro
    M_df = M_df / 1000000 

    M_df = (M_df.transpose().reset_index()
            .rename(columns=fields_to_rename)
            )
    return M_df

def exiobase_adjust_currency(df, year):
    c = CurrencyConverter(fallback_on_missing_rate=True)
    exch = statistics.mean([c.convert(1, 'EUR', 'USD', date=date(year, 1, 1)),
                            c.convert(1, 'EUR', 'USD', date=date(year, 12, 30))])
    df = (df
        .assign(EF=lambda x: x['EF']/exch)
        .assign(ReferenceCurrency='USD')
        )
    return df

def exiobase_clean_trade(df):
    return df.filter(['US']).reset_index()
