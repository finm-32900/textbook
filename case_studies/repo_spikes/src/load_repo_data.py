import pandas as pd

import load_fred
import load_ofr_api_data

import os
from pathlib import Path

import config
OUTPUT_DIR = Path(config.output_dir)
DATA_DIR = Path(config.data_dir)

def load_all(data_dir = DATA_DIR, normalize_timing=True):
    data_dir = Path(data_dir)
    filedir = data_dir / 'pulled'
    # df_bloomberg = pd.read_parquet(filedir / 'bloomberg_repo_rates.parquet')
    df_fred = pd.read_parquet(filedir / 'fred_repo_related_data_all.parquet')
    df_ofr_api = pd.read_parquet(filedir / 'ofr_public_repo_data.parquet')
    # df_bloomberg.index.name = 'DATE'
    df_ofr_api.index.name = 'DATE'
    
    df = pd.concat([df_fred, df_ofr_api], axis=1)
    if normalize_timing:
        # Normalize end-of-day vs start-of-day difference
        df.loc['2016-12-14', ['DFEDTARU', 'DFEDTARL']] = df.loc['2016-12-13', ['DFEDTARU', 'DFEDTARL']]
        df.loc['2015-12-16', ['DFEDTARU', 'DFEDTARL']] = df.loc['2015-12-15', ['DFEDTARU', 'DFEDTARL']]
    return df

_descriptions_1 = load_fred.series_descriptions
_descriptions = load_ofr_api_data.series_descriptions
series_descriptions = {
    **_descriptions_1, 
    **_descriptions,
    }

if __name__ == "__main__":
    df = load_all()
    df[['DFEDTARU', 'DFEDTARL']].rename(columns=series_descriptions).plot()
    # df['BGCR'].plot()
    # df.loc['2019', :]