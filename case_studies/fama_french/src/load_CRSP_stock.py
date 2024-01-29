"""
Functions to pull and calculate the value and equal weighted CRSP indices.

 - Data for indices: https://wrds-www.wharton.upenn.edu/data-dictionary/crsp_a_indexes/
 - Data for raw stock data: https://wrds-www.wharton.upenn.edu/pages/get-data/center-research-security-prices-crsp/annual-update/stock-security-files/monthly-stock-file/
 - Why we can't perfectly replicate them: https://wrds-www.wharton.upenn.edu/pages/support/support-articles/crsp/index-and-deciles/constructing-value-weighted-return-series-matches-vwretd-crsp-monthly-value-weighted-returns-includes-distributions/
 - Methodology used: https://wrds-www.wharton.upenn.edu/documents/396/CRSP_US_Stock_Indices_Data_Descriptions.pdf
 - Useful link: https://www.tidy-finance.org/python/wrds-crsp-and-compustat.html

Thank you to Tobias Rodriguez del Pozo for his assistance in writing this
code.

"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

import config

DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME
START_DATE = config.START_DATE
END_DATE = config.END_DATE

def fix_crsp_dtypes(df):
    # cast the following columns as integers
    cols = [
        "issuno",
        "permno",
        "permco",
        "hexcd",
        "hsiccd",
        # "shrcd", # Some share codes are missing
        "exchcd",
        "primexch",
        "trdstat",
        "secstat",
    ]
    for col in cols:
        try:
            df[col] = df[col].astype(int)
        except KeyError:
            pass

    # cast the following columns as strings
    cols = [
        "issuno",
        "permno",
        "cusip",
        "permco",
        "hexcd",
        "hsiccd",
        "shrcd",
        "exchcd",
        "siccd",
        "ncusip",
        "ticker",
        "comnam",
        "shrcls",
        "tsymbol",
        "naics",
        "primexch",
        "trdstat",
        "secstat",
    ]
    for col in cols:
        try:
            df[col] = df[col].astype(str)
        except KeyError:
            pass

    return df


def pull_CRSP_monthly_file(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    """
    Pulls monthly CRSP stock data from a specified start date to end date.

    SQL query to pull data, controls for delisting, and importantly
    follows the guidelines that CRSP uses for inclusion, with the exception
    of code 73, which is foreign companies -- without including this, the universe
    of securities is roughly half of what it should be.
    """
    # Not a perfect solution, but since value requires t-1 period market cap,
    # we need to pull one extra month of data. This is hidden from the user.
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    start_date = start_date - relativedelta(months=1)
    start_date = start_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT 
        date,
        msf.permno, msf.permco, shrcd, exchcd, comnam, shrcls, 
        ret, retx, dlret, dlretx, dlstcd,
        prc, altprc, vol, shrout, cfacshr, cfacpr,
        naics, siccd,
        date_trunc('month', msf.date)::date as month_start
    FROM crsp.msf AS msf
    LEFT JOIN 
        crsp.msenames as msenames
    ON 
        msf.permno = msenames.permno AND
        msenames.namedt <= msf.date AND
        msf.date <= msenames.nameendt
    LEFT JOIN 
        crsp.msedelist as msedelist
    ON 
        msf.permno = msedelist.permno AND
        date_trunc('month', msf.date)::date =
        date_trunc('month', msedelist.dlstdt)::date
    WHERE 
        msf.date BETWEEN '{start_date}' AND '{end_date}' AND 
        msenames.shrcd IN (10, 11, 20, 21, 40, 41, 70, 71, 73)
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     df = db.raw_sql(
    #         query, date_cols=["month_start", "date", "namedt", "nameendt", "dlstdt"]
    #     )
    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(
        query, date_cols=["month_start", "date", "namedt", "nameendt", "dlstdt"]
    )
    db.close()

    df = df.loc[:, ~df.columns.duplicated()]
    # df = fix_crsp_dtypes(df)
    df["shrout"] = df["shrout"] * 1000
    # Deal with delisting returns
    df = apply_delisting_returns(df)

    return df


def pull_fama_french_data(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    query = f"""
    SELECT 
        a.permno, a.permco, a.date, a.ret, a.retx, a.vol, a.shrout, 
        a.prc, a.cfacshr, a.bidlo, a.askhi,
        b.shrcd, b.exchcd, b.siccd, b.ticker, b.shrcls,  -- from identifying info table
        c.dlstcd, c.dlret                                -- from delistings table
    FROM 
        crsp.msf AS a
    LEFT JOIN 
        crsp.msenames AS b
    ON 
        a.permno = b.permno AND 
        b.namedt <= a.date AND 
        a.date <= b.nameendt
    LEFT JOIN 
        crsp.msedelist AS c
    ON 
        a.permno = c.permno AND 
        date_trunc('month', a.date) = date_trunc('month', c.dlstdt)
    WHERE 
        a.date BETWEEN '{start_date}' AND '{end_date}';
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     df = db.raw_sql(query, date_cols=["date"])
    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(query, date_cols=["date"])
    db.close()

    df = df.loc[:, ~df.columns.duplicated()]
    # df = fix_crsp_dtypes(df)
    df["shrout"] = df["shrout"] * 1000

    return df


def apply_delisting_returns(df):
    # First change dlret column. If dlret is NA and dlstcd is not NA, then:
    # if dlstcd is 500, 520, 551-574, 580, or 584, then dlret = -0.3
    # if dlret is NA but dlstcd is not one of the above, then dlret = -1
    # From: Chapter 7 of: Bali, Engle, Murray --
    # Empirical asset pricing-the cross section of stock returns (2016)

    df["dlret"] = np.select(
        [
            df["dlstcd"].isin([500, 520, 580, 584] + list(range(551, 575)))
            & df["dlret"].isna(),
            df["dlret"].isna() & df["dlstcd"].notna() & df["dlstcd"] >= 200,
            True,
        ],
        [-0.3, -1, df["dlret"]],
        default=df["dlret"],
    )

    df["dlretx"] = np.select(
        [
            df["dlstcd"].isin([500, 520, 580, 584] + list(range(551, 575)))
            & df["dlretx"].isna(),
            df["dlretx"].isna() & df["dlstcd"].notna() & df["dlstcd"] >= 200,
            True,
        ],
        [-0.3, -1, df["dlretx"]],
        default=df["dlretx"],
    )

    df.loc[df["dlret"].notna(), "ret"] = df["dlret"]
    df.loc[df["dlretx"].notna(), "retx"] = df["dlretx"]
    return df


def apply_delisting_returns_alt(df):
    df["dlret"] = df["dlret"].fillna(0)
    df["ret"] = df["ret"] + df["dlret"]
    df["ret"] = np.where(
        (df["ret"].isna()) & (df["dlret"] != 0), df["dlret"], df["ret"]
    )
    return df


def pull_CRSP_index_files(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    # Pull index files
    query = f"""
        SELECT date_trunc('month', msix.caldt)::date as month_start, * 
        FROM crsp_a_indexes.msix as msix
        WHERE msix.caldt BETWEEN '{start_date}' AND '{end_date}'
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     df = db.raw_sql(query, date_cols=["month", "caldt"])
    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(query, date_cols=["month", "caldt"])
    db.close()
    return df


def load_CRSP_monthly_file(data_dir=DATA_DIR):
    path = Path(data_dir) / "pulled" / "CRSP_MSF_INDEX_INPUTS.parquet"
    df = pd.read_parquet(path)
    return df


def load_CRSP_index_files(data_dir=DATA_DIR):
    path = Path(data_dir) / "pulled" / f"CRSP_MSIX.parquet"
    df = pd.read_parquet(path)
    return df


def load_fama_french_data(data_dir=DATA_DIR):
    path = Path(data_dir) / "pulled" / f"CRSP_FF_93_INPUTS.parquet"
    df = pd.read_parquet(path)
    return df


def _demo():
    df_msf = load_CRSP_monthly_file(data_dir=DATA_DIR)
    df_msix = load_CRSP_index_files(data_dir=DATA_DIR)
    df_ff = load_fama_french_data(data_dir=DATA_DIR)


if __name__ == "__main__":
    start_date = "2019-01-01"
    end_date = "2022-12-31"
    df_msf = pull_CRSP_monthly_file(start_date=start_date, end_date=end_date)
    path = Path(DATA_DIR) / "pulled" / "CRSP_MSF_INDEX_INPUTS.parquet"
    df_msf.to_parquet(path)

    df_msix = pull_CRSP_index_files(start_date=start_date, end_date=end_date)
    path = Path(DATA_DIR) / "pulled" / f"CRSP_MSIX.parquet"
    df_msix.to_parquet(path)

    df_ff = pull_fama_french_data(start_date=start_date, end_date=end_date)
    path = Path(DATA_DIR) / "pulled" / f"CRSP_FF_93_INPUTS.parquet"
    df_ff.to_parquet(path)
