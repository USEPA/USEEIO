# get_alias.py
# !/usr/bin/env python3
# coding=utf-8
"""
Picks a random alias name from a source of names in a yaml file that is not already reserved in the aliases.csv

This file requires the source name be passed like:
    -s migratory_songbirds

The source must be the base name (no extension) of a yaml file with a list of names present in the data directory
"""

import argparse
import random
import yaml
import pandas as pd
from pathlib import Path

verPath = Path(__file__).parent
dataPath = verPath / 'data'

def main(**kwargs):

    parser = argparse.ArgumentParser(argument_default = argparse.SUPPRESS)

    parser.add_argument('-s',
                        help = 'Enter the name of yaml file of names in the data path wout the extension',
                        type = str)
    if len(kwargs) == 0:
        kwargs = vars(parser.parse_args())

    aliases = set(pd.read_csv(verPath / "aliases.csv")["Alias"])
    source = kwargs['s'] +".yaml"

    if not (dataPath / source).exists():
        raise IndexError(f'names file not found: {source}')

    with open(dataPath / source, "r") as file:
        names = yaml.safe_load(file)
        names = names.get("names")

    names = list(set(names) - aliases)
    print("Your next alias is ... "+ random.choice(names))

if __name__ == "__main__":
    main()
