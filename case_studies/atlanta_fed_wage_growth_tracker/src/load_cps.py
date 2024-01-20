import pandas as pd
import numpy as np

import config
DATA_DIR = config.DATA_DIR

def load_raw(data_dir=DATA_DIR, start_date='2000-01-01', end_date='2024-01-01'):
    
    ## Read and Prepare the Data

    # When you save the file, it must be named `cps.csv`
    # and saved in the directory `../data/manual`.
    # It is placed in the `manual` directory because it is not
    # automatically downloaded from the internet.
    path = data_dir / 'manual' / 'cps.csv'

    df = pd.read_csv(path)
    df['YEAR'] = pd.to_datetime(df['YEAR'], format='%Y') 

    categorical_cols = ['GQ', 'SEX', 'EDUC', 'LABFORCE']
    for col in categorical_cols:
        df[col] = df[col].astype('category')

    # In case these variables were included in the dataset,
    # Drop the variables that we will not need in this exercise.
    labels = ['MONTH', 'ASECFLAG', 'EMPSTAT', 'FTOTVAL', 'PERNUM', 
            'SERIAL', 'CPSIDP', 'ASECWTH', 'HFLAG', 'CPSID']
    for label in labels:
        try:
            df.drop(labels=label, inplace=True, axis=1)
        except:
            pass

    df = df[(df['YEAR'] >= start_date) & (df['YEAR'] <= end_date)]
    return df

def load_clean(data_dir=DATA_DIR, start_date='2000-01-01', end_date='2024-01-01'):
    df = load_raw(data_dir, start_date, end_date)
    ## Fill in Missing Values or NIU
    
    # UHRSWORKLY: Recode missing values
    df.loc[df['UHRSWORKLY'] == 999, 'UHRSWORKLY'] = np.nan

    # INCWAGE: Missing values
    # 9999999 = N.I.U. (Not in Universe). 
    # 9999998 = Missing.
    df.loc[df['INCWAGE'] == 9999999, 'INCWAGE'] = np.nan
    df.loc[df['INCWAGE'] == 9999998, 'INCWAGE'] = np.nan

    # LABFORCE missing values
    # 0 = NIU
    df.loc[df['LABFORCE'] == 0, 'LABFORCE'] = np.nan

    # EDUC Missing values
    EDUC_missing_list = [999, 1, 0]
    for educ_code in EDUC_missing_list:
        df.loc[df['EDUC'] == educ_code, 'EDUC'] = np.nan

    # GQ Missing values
    df.loc[df['GQ'] == 0, 'GQ'] = np.nan
        
    # SEX Missing values
    df.loc[df['SEX'] == 9, 'SEX'] = np.nan


    # TODO: Alternative way is currently NOT WORKING
    # missing_values = {
    #     'UHRSWORKLY': {999: np.nan},
    #     'INCWAGE': {9999998: np.nan, 9999999: np.nan},
    #     'LABFORCE': {0: np.nan},
    #     'EDUC': {0: np.nan, 1: np.nan, 999: np.nan}
    # }
    # df.replace(to_replace=missing_values, inplace=True)
    return df

def _demo():
    df = load_raw()
    df.info()
    df = load_clean()
    print(df.head())
    print(df.info())


if __name__ == "__main__":
    pass