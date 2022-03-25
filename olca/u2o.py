"""useeior to openLCA converter

This script converts the API model output (function `writeModelforAPI`) of
useeior to a JSON-LD package that can be imported into openLCA. It is a
stand-alone script with no other dependencies than NumPy and the Python 3.x
standard library. This script can be executed from the command line like this:

```
$ python3 u2o.py [USEEIO data folder] [openLCA JSON-LD zip file]
```
"""

import csv
import json
import yaml
import datetime
import logging as log
import os.path
import struct
import sys
import uuid
import zipfile

from typing import Dict, List, Optional, Tuple

import numpy

MODEL_VERSION = '2.0.1'
MODEL_NAME = '2.0.1-411'
USEEIOR_VERSION = '1.0.2'
TARGET_YEAR = 2021
NOW = datetime.datetime.now().isoformat(timespec='seconds')
FLOW_STR = 'Flow generated for use in USEEIO models'
indicators_to_write = ['Waste Generated', 'Economic & Social']

useeio_source = {'name': 'Ingwersen et al. 2022, USEEIO 2.0',
                 'description': 'Ingwersen, W.; Li, M.; Young, B.; Vendries, J.; Birney, C. '
                         'USEEIO v2.0, the US Environmentally-Extended Input-Output Model V2.0. '
                         'Scientific Data',
                 'textReference': '',
                 'year': '2022',
                 'url': ''}

class _RefIds:
    LOCATION_US = '0b3b97fa-6688-3c56-88ee-4ae80ec0c3c2'

    UNIT_KG = '20aadc24-a391-41cf-b340-3e4529f44bde'
    UNIT_KBQ = 'e9773595-284e-46dd-9671-5fc9ff406833'
    UNIT_M2A = 'c7266b67-4ea2-457f-b391-9b94e26e195a'
    UNIT_MJ = '52765a6c-3896-43c2-b2f4-c679acf13efe'
    UNIT_ITEMS = '6dabe201-aaac-4509-92f0-d00c26cb72ab'
    UNIT_USD = 'd0d3bdb1-311a-4ea7-8d37-808f11adbc61'

    QUANTITY_KG = '93a60a56-a3c8-11da-a746-0800200b9a66'
    QUANTITY_KBQ = '93a60a56-a3c8-17da-a746-0800200c9a66'
    QUANTITY_M2A = '93a60a56-a3c8-21da-a746-0800200c9a66'
    QUANTITY_MJ = 'f6811440-ee37-11de-8a39-0800200c9a66'
    QUANTITY_ITEMS = '01846770-4cfe-4a25-8ad9-919d8d378345'
    QUANTITY_USD = '3bf53920-157c-4c2f-bddd-7c92c9d35f10'

    IMPACT_METHOD = 'bb205cad-3c8e-49bb-865d-c4f6fb807724'

    @staticmethod
    def of_quantity(unit: str) -> str:
        u = unit.strip()
        if u == 'kg':
            return _RefIds.QUANTITY_KG
        if u == 'kBq':
            return _RefIds.QUANTITY_KBQ
        if u == 'm2*a':
            return _RefIds.QUANTITY_M2A
        if u == 'MJ':
            return _RefIds.QUANTITY_MJ
        if u == 'p':
            return _RefIds.QUANTITY_ITEMS
        if u == 'USD':
            return _RefIds.QUANTITY_USD
        log.error('unknown unit %s', unit)
        sys.exit(1)

    @staticmethod
    def of_unit(unit: str) -> str:
        u = unit.strip()
        if u == 'kg':
            return _RefIds.UNIT_KG
        if u == 'kBq':
            return _RefIds.UNIT_KBQ
        if u == 'm2*a':
            return _RefIds.UNIT_M2A
        if u == 'MJ':
            return _RefIds.UNIT_MJ
        if u == 'p':
            return _RefIds.UNIT_ITEMS
        if u == 'USD':
            return _RefIds.UNIT_USD
        log.error('unknown unit %s', unit)
        sys.exit(1)


class _Sector:

    def __init__(self, csv_row: List[str]):
        self.index = int(csv_row[0])
        self.sector_id = csv_row[1]
        self.uid = _uid(csv_row[1])
        self.name = csv_row[2]
        self.code = csv_row[3]
        self.location_code = csv_row[4]
        self.category = csv_row[5]
        self.description = csv_row[6]


class _Flow:

    def __init__(self, csv_row: List[str]):
        self.index = int(csv_row[0])
        if(csv_row[5] == ''):
            self.uid = _uid(csv_row[1])
        else:
            self.uid = csv_row[5]
        self.name = csv_row[2]
        self.context = csv_row[3]
        self.unit = csv_row[4]


class _Indicator:

    def __init__(self, csv_row: List[str]):
        self.index = int(csv_row[0])
        self.uid = _uid(csv_row[1])
        self.name = csv_row[2]
        self.code = csv_row[3]
        self.unit = csv_row[4]
        self.group = csv_row[5]


class _Demand:

    def __init__(self, csv_row: List[str]):
        self.demand_id = csv_row[0]
        self.uid = _uid(csv_row[0])
        self.year = int(csv_row[1])
        self.demand_type = csv_row[2]
        self.system = csv_row[3]
        self.location_code = csv_row[4]

    @property
    def name(self):
        return f'{self.demand_type}, {self.system}, {self.year}'


class _Source:

    def __init__(self, source_dict):
        source_keys = {'name',
                       'description',
                       'textReference',
                       'year',
                       'url',
                       }
        self.__dict__.update((k, v) for k, v in source_dict.items()
                             if k in source_keys)

    def json_obj(self):
        obj = {
            '@type': 'Source',
            '@id': _uid(self.name),
            'name': self.name,
            'description': self.description,
            'textReference': self.textReference,
            'year': self.year,
            'url': self.url,
        }
        return obj


def convert(folder_path, zip_path, bib_path=None):
    if not _is_valid_useeio_folder(folder_path):
        return

    source_list = []
    if bib_path:
        try:
            SOURCES = _read_metadata('useeio_sources.yml')
            source_list = generate_sources(bib_path, SOURCES)
        except:
            print('error generating source list')
    # read the matrix files
    A = _read_matrix(os.path.join(folder_path, 'A.bin'))
    B = _read_matrix(os.path.join(folder_path, 'B.bin'))
    C = _read_matrix(os.path.join(folder_path, 'C.bin'))

    # read the meta data CSV files
    sector_rows = _read_csv(os.path.join(folder_path, 'sectors.csv'))
    sectors: List[_Sector] = [_Sector(row) for row in sector_rows]
    flow_rows = _read_csv(os.path.join(folder_path, 'flows.csv'))
    flows: List[_Flow] = [_Flow(row) for row in flow_rows]
    env_flows = [flow for flow in flows if not flow.context.startswith('Waste')]
    waste_flows = [flow for flow in flows if flow.context.startswith('Waste')]
    indicator_rows = _read_csv(os.path.join(folder_path, 'indicators.csv'))
    indicators: List[_Indicator] = [_Indicator(row) for row in indicator_rows]
    demand_rows = _read_csv(os.path.join(folder_path, 'demands.csv'))
    demands: List[_Demand] = [_Demand(row) for row in demand_rows]

    with zipfile.ZipFile(zip_path, mode='w',
                         compression=zipfile.ZIP_DEFLATED) as zipf:
        _write_ref_data(zipf)
        _write_sources(zipf, source_list)
        _write_sources(zipf, [_Source(useeio_source)])
        _write_categories(zipf, 'FLOW',
                          ['Elementary flows/' + f.context for f in env_flows])
        _write_categories(zipf, 'FLOW',
                          [f.context for f in waste_flows])
        _write_categories(zipf, 'PROCESS', [s.category for s in sectors])
        _write_categories(zipf, 'FLOW',
                          ['Technosphere Flows/' + s.category for s in sectors])
        _write_tech_flows(zipf, sectors)
        _write_envi_flows(zipf, env_flows, 'ELEMENTARY_FLOW')
        _write_envi_flows(zipf, waste_flows, 'WASTE_FLOW')
        _write_processes(zipf, sectors, flows, A, B, source_list)
        _write_impacts(zipf, [i for i in indicators if i.group in indicators_to_write],
                              flows, C)

        # write the demands
        demand_category = {
            '@type': 'Category',
            '@id': _uid('process', 'demands'),
            'name': 'demands',
            'modelType': 'PROCESS',
        }
        _write_obj(zipf, 'categories', demand_category)
        demand_category['@id'] = _uid('flow', 'demands')
        demand_category['modelType'] = 'FLOW'
        _write_obj(zipf, 'categories', demand_category)
        for demand in demands:
            path = os.path.join(
                folder_path, 'demands', f'{demand.demand_id}.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    demand_data: List[dict] = json.load(f)
                    _write_demand(zipf, demand, demand_data, sectors)


def _write_processes(zip_file: zipfile.ZipFile, sectors: List[_Sector],
                     flows: List[_Flow], A: numpy.ndarray, B: numpy.ndarray,
                     source_list: List[_Source]):
    for sector in sectors:
        process = _init_process(sector, source_list)
        exchanges: List[dict] = process['exchanges']
        iid = 1

        # add tech-flows
        for tech_flow in _create_tech_exchanges(sector, sectors, A):
            iid += 1
            tech_flow['internalId'] = iid
            exchanges.append(tech_flow)

        # add envi-flows
        for envi_flow in _create_envi_exchanges(sector, flows, B):
            iid += 1
            envi_flow['internalId'] = iid
            exchanges.append(envi_flow)

        process['lastInternalId'] = iid
        _write_obj(zip_file, 'processes', process)


def _write_demand(zip_file: zipfile.ZipFile, demand: _Demand,
                  data: List[dict], sectors: List[_Sector]):
    # create the demand flow
    flow = {
        '@type': 'Flow',
        '@id': _uid('flow', demand.uid),
        'name': demand.name,
        'description': FLOW_STR,
        'version': MODEL_VERSION,
        'flowType': 'PRODUCT_FLOW',
        'category': {'@id': _uid('flow', 'demands')},
        'flowProperties': [{
            'referenceFlowProperty': True,
            'conversionFactor': 1.0,
            'flowProperty': {'@id': _RefIds.QUANTITY_USD},
        }]
    }
    _write_obj(zip_file, 'flows', flow)

    process = {
        '@type': 'Process',
        '@id': demand.uid,
        'name': demand.name,
        'category': {'@id': _uid('process', 'demands')},
        'version': MODEL_VERSION,
        'description': demand_metadata['description'],
        'processType': 'UNIT_PROCESS',
        'processDocumentation': _process_doc(demand_metadata),
    }
    if demand.location_code == 'US':
        process['location'] = {'@id': _RefIds.LOCATION_US}

    iid = 0
    total = 0.0
    exchanges = []
    sector_map: Dict[str, _Sector] = {
        sector.sector_id: sector for sector in sectors
    }
    for datum in data:
        sector_id = datum.get('sector')
        if not isinstance(sector_id, str):
            continue
        amount = datum.get('amount')
        if not isinstance(amount, (int, float)):
            continue
        sector = sector_map.get(sector_id)
        if not sector:
            continue
        iid += 1
        total += amount
        exchanges.append({
            'input': True,
            'amount': amount,
            'flow': {'@id': _uid('flow', sector.uid)},
            'unit': {'@id': _RefIds.UNIT_USD},
            'flowProperty': {'@id': _RefIds.QUANTITY_USD},
            'defaultProvider': {'@id': _uid('process', sector.uid)}
        })

    # add the quantitative reference
    iid += 1
    exchanges.append({
        'internalId': iid,
        'input': False,
        'amount': total,
        'quantitativeReference': True,
        'flow': {'@id': _uid('flow', demand.uid)},
        'unit': {'@id': _RefIds.UNIT_USD},
        'flowProperty': {'@id': _RefIds.QUANTITY_USD},
    })

    process['exchanges'] = exchanges
    process['lastInternalId'] = iid
    _write_obj(zip_file, 'processes', process)


def _is_valid_useeio_folder(folder: str) -> bool:
    required_files = [
        'A.bin',
        'B.bin',
        'C.bin',
        'flows.csv',
        'sectors.csv',
        'indicators.csv',
        'demands.csv',
    ]
    for f in required_files:
        full_path = os.path.join(folder, f)
        if not os.path.exists(full_path):
            log.error("required file '%s' is missing in '%s'", f, folder)
            return False
    return True


def _read_csv(file_path: str) -> List[List[str]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip the header row
        return [row for row in reader]


def _read_matrix_shape(file_path: str) -> Tuple[int, int]:
    with open(file_path, 'rb') as f:
        rows: int = struct.unpack('<i', f.read(4))[0]
        cols: int = struct.unpack('<i', f.read(4))[0]
        return rows, cols


def _read_matrix(file_path: str) -> numpy.ndarray:
    shape = _read_matrix_shape(file_path)
    return numpy.memmap(
        file_path, mode='c', dtype='<f8', shape=shape, offset=8, order='F')


def _uid(*xs: str) -> str:
    path: List[str] = []
    for arg in xs:
        if arg is None:
            continue
        path.append(str(arg).strip().lower())
    return str(uuid.uuid3(uuid.NAMESPACE_OID, '/'.join(path)))


def _write_ref_data(zip_file: zipfile.ZipFile):
    _write_obj(zip_file, 'locations', {
        "@type": "Location",
        "@id": _RefIds.LOCATION_US,
        "name": "United States",
        "code": "US",
        "latitude": 52.125,
        "longitude": 39.62
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "93a60a57-a4c8-11da-a746-0800200c9a66",
        "name": "Units of mass",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_KG,
                "name": "kg",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "93a60a57-a3c8-16da-a746-0800200c9a66",
        "name": "Units of radioactivity",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_KBQ,
                "name": "kBq",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "93a60a57-a3c8-20da-a746-0800200c9a66",
        "name": "Units of area*time",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_M2A,
                "name": "m2*a",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "93a60a57-a3c8-11da-a746-0800200c9a66",
        "name": "Units of energy",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_MJ,
                "name": "MJ",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "5beb6eed-33a9-47b8-9ede-1dfe8f679159",
        "name": "Units of items",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_ITEMS,
                "name": "Item(s)",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'unit_groups', {
        "@type": "UnitGroup",
        "@id": "01d54e11-f5a6-43e2-a7d9-ec307ae96c1b",
        "name": "Currencies",
        "units": [
            {
                "@type": "Unit",
                "@id": _RefIds.UNIT_USD,
                "name": "USD",
                "referenceUnit": True,
                "conversionFactor": 1.0
            }
        ]
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_USD,
        "name": "Producer price, USD 2012",
        "flowPropertyType": "ECONOMIC_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "01d54e11-f5a6-43e2-a7d9-ec307ae96c1b"
        }
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_KG,
        "name": "Mass",
        "flowPropertyType": "PHYSICAL_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "93a60a57-a4c8-11da-a746-0800200c9a66"
        }
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_KBQ,
        "name": "Radioactivity",
        "flowPropertyType": "PHYSICAL_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "93a60a57-a3c8-16da-a746-0800200c9a66"
        }
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_M2A,
        "name": "Area*time",
        "flowPropertyType": "PHYSICAL_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "93a60a57-a3c8-20da-a746-0800200c9a66"
        }
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_MJ,
        "name": "Energy",
        "flowPropertyType": "PHYSICAL_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "93a60a57-a3c8-11da-a746-0800200c9a66"
        }
    })

    _write_obj(zip_file, 'flow_properties', {
        "@type": "FlowProperty",
        "@id": _RefIds.QUANTITY_ITEMS,
        "name": "Number of items",
        "flowPropertyType": "PHYSICAL_QUANTITY",
        "unitGroup": {
            "@type": "UnitGroup",
            "@id": "5beb6eed-33a9-47b8-9ede-1dfe8f679159"
        }
    })

    for actor in actor_dict.values():
        if actor['name'] is None:
            continue
        uid = actor['id']
        if actor['id'] == '' or actor['id'] is None:
            uid = _uid(actor['name'])
        _write_obj(zip_file, 'actors', {
            "@type": "Actor",
            "@id": uid,
            "name": actor['name'],
            "description": actor['description'],
            "email": actor['email'],
        })


def _write_sources(zip_file: zipfile.ZipFile, sources: List[_Source]):
    for source in sources:
        _write_obj(zip_file, 'sources', source.json_obj())

def _write_categories(zip_file: zipfile.ZipFile, model_type: str,
                      paths: List[str]):
    handled: Dict[str, dict] = {}

    def w(segments: List[str]) -> Optional[dict]:
        if len(segments) == 0:
            return None
        uid = _uid(model_type.lower(), *segments)
        obj = handled.get(uid)
        if obj:
            return obj
        obj = {
            '@type': 'Category',
            '@id': uid,
            'name': segments[-1],
            'modelType': model_type
        }
        parent = w(segments[0:len(segments) - 1])
        if parent:
            obj['category'] = parent

        _write_obj(zip_file, 'categories', obj)
        handled[uid] = obj
        return obj

    for path in paths:
        p = path.strip().rstrip('/')
        if p == '' or p == '/':
            continue
        w([segment.strip() for segment in p.split('/')])


def _write_tech_flows(zip_file: zipfile.ZipFile, sectors: List[_Sector]):
    for sector in sectors:
        obj = {
            '@type': 'Flow',
            '@id': _uid('flow', sector.uid),
            'name': sector.name,
            'description': FLOW_STR,
            'version': MODEL_VERSION,
            'flowType': 'PRODUCT_FLOW',
            'flowProperties': [{
                'referenceFlowProperty': True,
                'conversionFactor': 1.0,
                'flowProperty': {'@id': _RefIds.QUANTITY_USD},
            }]
        }
        if sector.category not in ('', '/'):
            cat = "Technosphere Flows/" + sector.category.rstrip('/')
            path = [p.strip() for p in cat.split('/')]
            obj['category'] = {'@id': _uid('flow', *path)}
        _write_obj(zip_file, 'flows', obj)


def _write_envi_flows(zip_file: zipfile.ZipFile, flows: List[_Flow],
                      flowType='ELEMENTARY_FLOW'):
    for flow in flows:
        obj = {
            '@type': 'Flow',
            '@id': flow.uid,
            'name': flow.name,
            'flowType': flowType,
            'flowProperties': [{
                'referenceFlowProperty': True,
                'conversionFactor': 1.0,
                'flowProperty': {'@id': _RefIds.of_quantity(flow.unit)},
            }]
        }
        if flow.context not in ('', '/'):
            if flowType == 'ELEMENTARY_FLOW':
                context = "Elementary flows/" + flow.context
            else:
                context = flow.context
            path = [p.strip() for p in context.split('/')]
            obj['category'] = {'@id': _uid('flow', *path)}
        if flowType == 'WASTE_FLOW':
            obj['description'] = FLOW_STR

        _write_obj(zip_file, 'flows', obj)


def _init_process(sector: _Sector, source_list: List[_Source]) -> dict:

    obj = {
        '@type': 'Process',
        '@id': _uid('process', sector.uid),
        'name': sector.name,
        'version': MODEL_VERSION,
        'description': _conc_meta([sector.description, metadata['description']]),
        'processType': 'UNIT_PROCESS',
        'processDocumentation': _process_doc(metadata, source_list),
        'lastInternalId': 1,
        'exchanges': [
            {
                'internalId': 1,
                'input': False,
                'amount': 1.0,
                'quantitativeReference': True,
                'flow': {'@id': _uid('flow', sector.uid)},
                'unit': {'@id': _RefIds.UNIT_USD},
                'flowProperty': {'@id': _RefIds.QUANTITY_USD},
            }
        ]
    }
    if sector.location_code == 'US':
        obj['location'] = {'@id': _RefIds.LOCATION_US}
    if sector.category != '':
        cat = sector.category.rstrip('/')
        path = [p.strip() for p in cat.split('/')]
        obj['category'] = {'@id': _uid('process', *path)}
    return obj


def _create_tech_exchanges(sector: _Sector, sectors: List[_Sector],
                           A: numpy.ndarray) -> List[dict]:
    col = sector.index
    exchanges = []
    for other in sectors:
        row = other.index
        amount = A[row, col]
        if amount == 0:
            continue
        exchanges.append({
            'input': True,
            'amount': amount,
            'flow': {'@id': _uid('flow', other.uid)},
            'unit': {'@id': _RefIds.UNIT_USD},
            'flowProperty': {'@id': _RefIds.QUANTITY_USD},
            'defaultProvider': {'@id': _uid('process', other.uid)}
        })
    return exchanges


def _create_envi_exchanges(sector: _Sector, flows: List[_Flow],
                           B: numpy.ndarray) -> List[dict]:
    col = sector.index
    exchanges = []
    for flow in flows:
        row = flow.index
        amount = B[row, col]
        if amount == 0:
            continue
        exchanges.append({
            'input': flow.context.lower().strip().startswith('resource'),
            'amount': amount,
            'flow': {'@id': flow.uid},
            'unit': {'@id': _RefIds.of_unit(flow.unit)},
            'flowProperty': {'@id': _RefIds.of_quantity(flow.unit)}
        })
    return exchanges


def _write_impacts(zip_file: zipfile.ZipFile, indicators: List[_Indicator],
                   flows: List[_Flow], C: numpy.ndarray):
    # create the categories for the impacts
    categories: Dict[str, dict] = {}
    for indicator in indicators:
        if indicator.group in categories:
            continue
        obj = {
            '@type': 'Category',
            '@id': _uid('impact_categoriy', indicator.group),
            'name': indicator.group,
            'modelType': 'IMPACT_CATEGORY',
        }
        categories[indicator.group] = obj
        _write_obj(zip_file, 'categories', obj)

    # write the impact categories
    for indicator in indicators:
        obj = {
            '@type': 'ImpactCategory',
            '@id': indicator.uid,
            'name': indicator.name,
            'category': categories.get(indicator.group),
            'referenceUnitName': indicator.unit,
        }

        factors: List[dict] = []
        row = indicator.index
        for flow in flows:
            value = C[row, flow.index]
            if value == 0:
                continue
            factors.append({
                'value': value,
                'flow': {'@id': flow.uid},
                'unit': {'@id': _RefIds.of_unit(flow.unit)},
                'flowProperty': {'@id': _RefIds.of_quantity(flow.unit)},
            })

        obj['impactFactors'] = factors
        _write_obj(zip_file, 'lcia_categories', obj)

    # write the LCIA method
    method = {
        '@type': 'ImpactMethod',
        '@id': _RefIds.IMPACT_METHOD,
        'name': 'USEEIO - LCIA Method',
        'description': 'Indicators generated specifically for use in USEEIO models',
        'version': MODEL_VERSION,
        'impactCategories': [
            {'@id': indicator.uid} for indicator in indicators
        ]
    }
    _write_obj(zip_file, 'lcia_methods', method)


def _write_obj(zip_file: zipfile.ZipFile, path: str, obj: dict):
    uid = obj.get('@id')
    obj["@context"] = "http://greendelta.github.io/olca-schema/"
    if uid is None or uid == '':
        log.error('invalid @id for object %s in %s', obj, path)
        return
    zip_file.writestr(f'{path}/{uid}.json', json.dumps(obj))


def _read_metadata(path=None):
    if not path:
        path = os.path.dirname(__file__) + "/useeio_metadata.yml"
    with open(path) as f:
        m = yaml.safe_load(f)
    return m


def _parse_metadata(m, subset=None):
    if not subset:
        metadata = {k: v for k, v in m.items() if not isinstance(v, dict)}
    else:
        metadata = m[subset]
        for k, v in m.items():
            if k not in metadata and not isinstance(v, dict):
                metadata[k] = v
    for key, value in metadata.items():
        if key == 'id' and not value:
            value = _uid(metadata['name'])
        elif not value:
            value = ''
        else:
            value = _conc_meta(value)
        # update key words
        value = value.replace('[model_name]', MODEL_NAME)
        value = value.replace('[model_version]', MODEL_NAME)
        value = value.replace('[useeior_package_version]', USEEIOR_VERSION)
        value = value.replace('[target_year]', str(TARGET_YEAR))
        metadata[key] = value
    return metadata

def _conc_meta(m):
    if isinstance(m, str):
        return m
    if isinstance(m, list):
        return "\n\n".join(m)


def _process_doc(m, source_list=None):
    source_ids = []
    if source_list:
        source_ids = [{'@type': s.json_obj()['@type'],
                       '@id': s.json_obj()['@id'],
                       'name': s.json_obj()['name']} for s in source_list]

    proc_dict = {'validFrom': datetime.datetime(TARGET_YEAR, 1, 1).isoformat(timespec='seconds'),
                 'validUntil': datetime.datetime(TARGET_YEAR, 12, 31).isoformat(timespec='seconds'),
                 'timeDescription': m['time_description'],
                 'geographyDescription': m['geographic_description'],
                 'technologyDescription': m['technology_descripton'],

                 'intendedApplication': m['intended_application'],
                 'dataSetOwner': {'@id': _parse_metadata(actor_dict, 'owner')['id']},
                 'dataGenerator': {'@id': _parse_metadata(actor_dict, 'generator')['id']},
                 'dataDocumentor': {'@id': _parse_metadata(actor_dict, 'generator')['id']},
                 'publication': {'@id': _Source(useeio_source).json_obj()['@id']},
                 'restrictionsDescription': m['access_restrictions'],
                 'projectDescription': m['project'],
                 'creationDate': NOW,
                 'copyright': False,

                 'inventoryMethodDescription': m['lci_method'],
                 'modelingConstantsDescription': m['model_constants'],
                 'completenessDescription': m['data_completeness'],
                 'dataSelectDescription': m['data_selection'],
                 'dataTreatmentDescription': m['data_treatment'],
                 'samplingDescription': m['sampling_procedure'],
                 'dataCollectionDescription': m['data_collection_period'],
                 #'reviewer': ,
                 #'reviewDetails': ,
                 'sources': source_ids,
                 }
    return proc_dict


def generate_sources(bib_path, bibids):
    import bibtexparser
    from bibtexparser.bparser import BibTexParser


    def customizations(record):
        """Use some functions delivered by the library

        :param record: a record
        :returns: -- customized record
        """
        #record = bibtexparser.customization.author(record)
        record = bibtexparser.customization.add_plaintext_fields(record)
        record = bibtexparser.customization.doi(record)

        return record

    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    parser.homogenize_fields = True
    parser.customization = customizations

    def read_bib_file(path: str):
        with open(path) as bibtex_file:
            bib_database = parser.parse_file(bibtex_file)

        return bib_database.entries_dict


    def parse_for_olca(bibids, d):

        key_dict = {'description': ['plain_publisher',
                                    'plain_title',
                                    'year'],
                    'textReference': '',
                    'year': 'plain_year',
                    'url': 'url',
                    }
        s = []
        for bibid, name in bibids.items():
            try:
                record = d[bibid]
            except KeyError:
                print(f'{bibid} not found')
                continue
            source = {}
            source['name'] = bibids[bibid]
            for key, value in key_dict.items():
                try:
                    if isinstance(value, list):
                        source[key] = ', '.join([record[v] for v in value])
                    else:
                        source[key] = record[value]
                except KeyError:
                    source[key] = ''
            s.append(_Source(source))
        return s

    d = read_bib_file(bib_path)
    source_list = parse_for_olca(bibids, d)
    return source_list


# define metadata for entire script
model_yaml = _read_metadata()
metadata = _parse_metadata(model_yaml)
demand_metadata = _parse_metadata(model_yaml, 'demand_processes')
actor_dict = _read_metadata(os.path.dirname(__file__) + "/useeio_actors.yml")



if __name__ == '__main__':
    args = sys.argv
    if len(args) < 3:
        print("""
A simple USEEIO (matrix API export) to openLCA (JSON-LD) converter

Usage:

  $ python3 [USEEIO data folder] [openLCA JSON-LD zip file]
""")
    else:
        bib_path = None
        if len(args) == 4:
            bib_path = args[3]
        convert(args[1], args[2], bib_path)
