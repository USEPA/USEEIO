'''
Compare national emission factors between appraoch based entirely on BEA/Census
imports data to that where regions are aggregated to national based on TiVA data
'''


import pandas as pd
from pathlib import Path

out_Path = Path(__file__).parent.parent / 'output'
mrio = 'exio'
year = "2019"
schema = "17sch"
flow_cols = ['Sector', 'Unit',
             'Year', 'PriceType',
             'Flowable', 'Context', 'FlowUUID', 'ReferenceCurrency']

tiva_df = f'US_summary_import_factors_TiVA_approach_{mrio}_{year}_{schema}.csv'
tiva_df = (pd.read_csv(out_Path / tiva_df))
api_df = f'US_summary_import_factors_{mrio}_{year}_{schema}.csv'
api_df = (pd.read_csv(out_Path / api_df))
tiva_df = tiva_df.rename(columns={'FlowAmount':'Amount_summary_tiva'})

ta_df = api_df.merge(tiva_df, how='left',validate='m:1', on=[c for c in flow_cols])

ta_df = (ta_df.assign(Ratio = (ta_df['Amount_summary_tiva'] - ta_df['FlowAmount'])/ta_df['FlowAmount']))

ta_df.to_csv(out_Path / f'TiVA_comparison_{mrio}_{year}_{schema}.csv', index=False)
