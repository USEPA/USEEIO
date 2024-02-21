import pandas as pd
from pathlib import Path

out_Path = Path(__file__).parent / 'output'
mrio = 'exio'
year = "2019"
flow_cols = ['BEA Summary', 'Unit',
             'CurrencyYear', 'EmissionYear', 'PriceType',
             'Flowable', 'Context', 'FlowUUID', 'ReferenceCurrency']

tiva_df = f'imports_multipliers_exio_{year}.csv'
tiva_df = (pd.read_csv(out_Path / tiva_df))
api_df = f'nation_summary_imports_multipliers_exio_{year}.csv'
api_df = (pd.read_csv(out_Path / api_df))
tiva_df = tiva_df.rename(columns={'FlowAmount':'Amount_summary_tiva',
                                  'Sector':'BEA Summary'})

ta_df = api_df.merge(tiva_df, how='left',validate='m:1', on=[c for c in flow_cols])

ta_df = (ta_df.assign(Ratio = (ta_df['Amount_summary_tiva'] - ta_df['Amount_summary_nation'])/ta_df['Amount_summary_tiva']))

ta_df.to_csv(out_Path / f'TiVA_API_Comparison_{mrio}_{year}.csv', index=False)