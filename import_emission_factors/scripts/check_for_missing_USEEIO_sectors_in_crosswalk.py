'''
Can check for USEEIO model sectors that do not have mappings in crosswalk
CAUTION: DOES NOT YET DYNAMICALLY CHANGE IEF Source; its grabbing source that is set in generate_import_factors.py
'''

import pandas as pd
from import_emission_factors.generate_import_factors import get_mrio_to_useeio_concordance

schema = 2017


cw = get_mrio_to_useeio_concordance(schema)
useeio_sectors_in_cw = set(pd.unique(cw.get('BEA Detail').values))

useeio_sectors = pd.read_csv("import_emission_factors/concordances/useeio_internal_concordance.csv")
useeio_sectors = set(pd.unique(useeio_sectors.get('USEEIO_Detail_2017')))

sector_missing_in_cw = useeio_sectors - useeio_sectors_in_cw

print(sector_missing_in_cw)


