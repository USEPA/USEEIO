"""
Format compare country contribution coefficients table
"""

import pandas as pd
from pathlib import Path

out_Path = Path(__file__).parent.parent / 'output'
mrio = 'exio'
years = range(2017, 2023)

df_list = []
for y in years:
    df = pd.read_csv(out_Path / f'import_shares_comparison_{y}.csv',
                     skiprows=2)
    df.columns = ['BEA Summary', 'Year', 'mean', 'min', 'max']
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)
df['difference'] = (df['mean'].map('{:.1%}'.format) +
                  ' [' + df['min'].map('{:.1%}'.format) + ', ' +
                  df['max'].map('{:.1%}'.format) + ']')
df = df.drop(columns=['mean','min', 'max'])
df = df.pivot(columns='Year', index='BEA Summary', values='difference')

for y in years:
    df[y] = df[y].str.replace('0.0', '0', regex=False)
    df[y] = df[y].str.replace('0% [0%, 0%]', '-', regex=False)
df.to_csv(out_Path / 'import_shares_comparison.csv')
