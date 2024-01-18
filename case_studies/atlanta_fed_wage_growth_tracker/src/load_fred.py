import pandas_datareader.data as web
import pandas as pd
import numpy as np

import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)

series_to_pull = {
    'LES1252881600Q': 'Employed full time: Median usual weekly real earnings: Wage and salary workers: 16 years and over',
    'LES1252881900Q': 'Employed full time: Median usual weekly real earnings: Wage and salary workers: 16 years and over: Men',
}
series_descriptions = series_to_pull.copy()

def pull_all(start_date='2000-01-01', end_date='2024-01-01'):
    """
    Lookup series code, e.g., like this:
    https://fred.stlouisfed.org/series/RPONTSYD
    """
    df = web.DataReader(list(series_to_pull.keys()), 'fred', start_date, end_date)

    return df


if __name__ == "__main__":

    start_date = '2000-01-01'
    # today = pd.Timestamp.today().strftime('%Y-%m-%d')
    # end_date = today
    end_date = '2024-01-01'
    df = pull_all(start_date, end_date)
    filedir = Path(DATA_DIR) / 'pulled'
    filedir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(filedir / 'fred_wages.parquet')

