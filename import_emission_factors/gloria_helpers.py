import statistics
from datetime import date

from currency_converter import CurrencyConverter

def clean_gloria_M_matrix(M, fields_to_rename):
    # for satellite
    M_df = M.copy().reset_index()

    M_df['flow'] = M_df.stressor
    M_df['flow'] = M_df['flow'].map(fields_to_rename)
    M_df = M_df.loc[M_df.flow.isin(fields_to_rename.values())]
    M_df = (M_df
            .sort_index(axis=1)
            .drop(columns=['stressor', 'category'], level=0)
            .groupby('flow').agg('sum')
            )

    M_df = (M_df.transpose().reset_index()
            .rename(columns=fields_to_rename)
            )
    return M_df

# def gloria_adjust_currency(df, year):
#     c = CurrencyConverter(fallback_on_missing_rate=True)
#     exch = statistics.mean([c.convert(1, 'EUR', 'USD', date=date(year, 1, 1)),
#                             c.convert(1, 'EUR', 'USD', date=date(year, 12, 30))])
#     df = (df
#         .assign(EF=lambda x: x['EF']/exch)
#         .assign(ReferenceCurrency='USD')
#         )
#     return df

def gloria_clean_trade(df):
    return df.filter(['USA']).reset_index()
