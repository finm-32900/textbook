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
from pandas.tseries.offsets import MonthEnd, YearEnd
import wrds

import config
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME


def pull_CRSP_monthly_file(start_date='2019-01-01', end_date='2022-12-31'):
    """
    Pulls monthly CRSP stock data from a specified start date to end date.

    SQL query to pull data, controls for delisting, and importantly
    follows the guidelines that CRSP uses for inclusion, with the exception
    of code 73, which is foreign companies -- without including this, the universe
    of securities is roughly half of what it should be.
    """
    # Not a perfect solution, but since value requires t-1 period market cap,
    # we need to pull one extra month of data. This is hidden from the user.
    start_date_og = start_date
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    start_date = start_date - relativedelta(months=1)
    start_date = start_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT 
        date_trunc('month', msf.date)::date as month, * 
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
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        df = db.raw_sql(
            query, date_cols=["month", "date", "namedt", "nameendt", "dlstdt"]
        )
        df = df.loc[:, ~df.columns.duplicated()]
        df["shrout"] = df["shrout"] * 1000
        # Deal with delisting returns
        df = calc_delisting_returns(df)
        
        return df


def calc_delisting_returns(df):
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
        [
            -0.3, 
            -1, 
            df["dlret"]
        ],
        default=df["dlret"],
    )

    df["dlretx"] = np.select(
        [
            df["dlstcd"].isin([500, 520, 580, 584] + list(range(551, 575)))
            & df["dlretx"].isna(),
            df["dlretx"].isna() & df["dlstcd"].notna() & df["dlstcd"] >= 200,
            True,
        ],
        [
            -0.3, 
            -1, 
            df["dlretx"]
        ],
        default=df["dlretx"],
    )

    df.loc[df["dlret"].notna(), "ret"] = df["dlret"]
    df.loc[df["dlretx"].notna(), "retx"] = df["dlretx"]
    return df


def pull_CRSP_index_files(start_date='2019-01-01', end_date='2022-12-31'):
    # Pull index files
    query = f"""
        SELECT date_trunc('month', msix.caldt)::date as month, * 
        FROM crsp_a_indexes.msix as msix
        WHERE msix.caldt BETWEEN '{start_date}' AND '{end_date}'
    """
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        df = db.raw_sql(query, date_cols=["month", "caldt"])
    return df


###################################################

def calc_CRSP_equal_weighted_index(df_inputs):
    # Calculate equal weighted index (just the average of all stocks)
    # Note that ret is raw and retx is adjusted for dividends.
    df_eq_idx = {
        "ewretd": df_inputs.groupby("month")[["ret"]].mean().values[:, 0],
        "ewretx": df_inputs.groupby("month")[["retx"]].mean().values[:, 0],
        "totcnt": df_inputs.groupby("month")[["permno"]].count().values[:, 0],
    }

    df_eq_idx = pd.DataFrame(df_eq_idx, index=df_inputs["month"].unique())
    return df_eq_idx


def calc_CRSP_value_weighted_index(df_inputs):
    # The formula is:
    # r_t = \frac{\sum_{i=1}^{N_t} w_{i,t-1} r_{i,t}}{\sum_{i=1}^{N_t} w_{i,t-1}}
    # That is, the return of the index is the weighted average of the returns, where
    # the weights are the market cap of the stock at the end of the previous month.
    df_inputs["mktcap"] = df_inputs["shrout"] * df_inputs["altprc"]
    df_inputs["weight"] = df_inputs.groupby("permno")["mktcap"].shift(1)
    df_inputs["weight_ret"] = df_inputs["weight"] * df_inputs["ret"]
    df_inputs["weight_retx"] = df_inputs["weight"] * df_inputs["retx"]
    df_inputs["weight_sum"] = df_inputs.groupby("month")["weight"].transform("sum")
    df_inputs["weight_sum_ret"] = df_inputs.groupby("month")["weight_ret"].transform(
        "sum"
    )
    df_inputs["weight_sum_retx"] = df_inputs.groupby("month")["weight_retx"].transform(
        "sum"
    )

    df_vw_idx = {
        "vwretd": df_inputs["weight_sum_ret"].unique()[1:]
        / df_inputs["weight_sum"].unique()[1:],
        "vwretx": df_inputs["weight_sum_retx"].unique()[1:]
        / df_inputs["weight_sum"].unique()[1:],
        "totcnt": df_inputs.groupby("month")[["permno"]].count().values[1:, 0],
    }

    df_vw_idx = pd.DataFrame(df_vw_idx, index=df_inputs["month"].unique()[1:])
    return df_vw_idx


def calc_CRSP_indices_merge(df_msf, df_msix):
    # Merge everything with appropriate suffixes
    df_vw_idx = calc_CRSP_value_weighted_index(df_msf)
    df_eq_idx = calc_CRSP_equal_weighted_index(df_msf)
    df = df_msix.merge(
        df_vw_idx,
        left_index=True,
        right_index=True,
        how="inner",
        suffixes=("", "_manual"),
    )
    df = df.merge(
        df_eq_idx, left_index=True, right_index=True, suffixes=("", "_manual")
    )
    df = df.loc[:, ~df.columns.duplicated()]
    # Drop 'Unnamed: 0' if it exists
    if "Unnamed: 0" in df.columns:
        df = df.drop("Unnamed: 0", axis=1)
    return df


def pull_and_calc_CRSP_indices(
    start_date, end_date, data_dir=DATA_DIR, from_cache=True
):
    # Function to automatically calculate and merge the data.
    path_msf = (
        Path(data_dir) / "pulled" / "CRSP_MSF_INDEX_INPUTS.csv"
    )
    path_msix = Path(data_dir) / "pulled" / f"CRSP_MSIX_.csv"
    if not path_msf.exists() or not from_cache:
        pull_CRSP_monthly_file(start_date, end_date)
    if not path_msix.exists() or not from_cache:
        pull_CRSP_index_files(start_date, end_date)
    df_msf = pd.read_csv(
        path_msf, parse_dates=["month", "date", "namedt", "nameendt", "dlstdt"]
    )
    df_msix = pd.read_csv(path_msix, parse_dates=["month", "caldt"], index_col="month")
    df = calc_CRSP_indices_merge(df_msf, df_msix)
    return df


def pull_fama_french_data(start_date='2019-01-01', end_date='2022-12-31', data_dir=DATA_DIR):
    path_ff_input = (
        Path(data_dir) / "pulled" / f"FF_93_INPUTS_{start_date}_{end_date}.csv"
    )
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        query = f"""SELECT a.permno, a.permco, a.date, a.ret, a.retx, a.vol, a.shrout, a.prc, a.cfacshr, a.bidlo, a.askhi,
                        b.shrcd, b.exchcd, b.siccd, b.ticker, b.shrcls,  -- from identifying info table
                        c.dlstcd, c.dlret                                -- from delistings table
                    FROM crsp.msf AS a
                    LEFT JOIN crsp.msenames AS b
                        ON a.permno = b.permno
                        AND b.namedt <= a.date
                        AND a.date <= b.nameendt
                    LEFT JOIN crsp.msedelist AS c
                        ON a.permno = c.permno
                        AND date_trunc('month', a.date) = date_trunc('month', c.dlstdt)
                    WHERE a.date BETWEEN '{start_date}' AND '{end_date}';
                    """

        df = db.raw_sql(query, date_cols=["date"])
        df = df.loc[:, ~df.columns.duplicated()]
        df["shrout"] = df["shrout"] * 1000
        df.to_csv(path_ff_input)


def calc_delisting_returns_alt(df):
    df["dlret"] = df["dlret"].fillna(0)
    df["ret"] = df["ret"] + df["dlret"]
    df["ret"] = np.where(
        (df["ret"].isna()) & (df["dlret"] != 0), df["dlret"], df["ret"]
    )


# Code to calculate the Fama-French 1993 factors
# Comes from: https://www.fredasongdrechsler.com/data-crunching/fama-french
# Citation: Drechsler, Qingyi (Freda) S., 2023, Python Programs for Empirical Finance, https://www.fredasongdrechsler.com


def pull_compustat(data_dir=DATA_DIR):
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        comp = db.raw_sql(
            """
            SELECT a.gvkey, a.datadate, a.conm, a.fyear, a.tic, a.cusip, a.naicsh, a.sich, 
                    a.aco,a.act,a.ajex,a.am,a.ao,a.ap,a.at,a.capx,a.ceq,a.ceqt,a.che,a.cogs,
                    a.csho,a.cshrc,a.dcpstk,a.dcvt,a.dlc,a.dlcch,a.dltis,a.dltr,
                    a.dltt,a.dm,a.dp,a.drc,a.drlt,a.dv,a.dvc,a.dvp,a.dvpa,a.dvpd,
                    a.dvpsx_c,a.dvt,a.ebit,a.ebitda,a.emp,a.epspi,a.epspx,a.fatb,a.fatl,
                    a.ffo,a.fincf,a.fopt,a.gdwl,a.gdwlia,a.gdwlip,a.gwo,a.ib,a.ibcom,
                    a.intan,a.invt,a.ivao,a.ivncf,a.ivst,a.lco,a.lct,a.lo,a.lt,a.mib,
                    a.msa,a.ni,a.nopi,a.oancf,a.ob,a.oiadp,a.oibdp,a.pi,a.ppenb,a.ppegt,
                    a.ppenls,
                    a.ppent,a.prcc_c,a.prcc_f,a.prstkc,a.prstkcc,a.pstk,a.pstkl,a.pstkrv,
                    a.re,a.rect,a.recta,a.revt,a.sale,a.scstkc,a.seq,a.spi,a.sstk,
                    a.tstkp,a.txdb,a.txdi,a.txditc,a.txfo,a.txfed,a.txp,a.txt,
                    a.wcap,a.wcapch,a.xacc,a.xad,a.xint,a.xrd,a.xpp,a.xsga
                    FROM COMP.FUNDA as a
                    WHERE a.consol = 'C'
                    AND a.popsrc = 'D'
                    AND a.datafmt = 'STD'
                    AND a.curcd = 'USD'
                    AND a.indfmt = 'INDL'
                    and datadate >= '01/01/1959'
            """,
            date_cols=["datadate"],
        )
    comp["year"] = comp["datadate"].dt.year

    # create preferrerd stock
    comp["ps"] = np.where(comp["pstkrv"].isnull(), comp["pstkl"], comp["pstkrv"])
    comp["ps"] = np.where(comp["ps"].isnull(), comp["pstk"], comp["ps"])
    comp["ps"] = np.where(comp["ps"].isnull(), 0, comp["ps"])
    comp["txditc"] = comp["txditc"].fillna(0)

    # create book equity
    comp["be"] = comp["seq"] + comp["txditc"] - comp["ps"]
    comp["be"] = np.where(comp["be"] > 0, comp["be"], np.nan)

    # number of years in Compustat
    comp = comp.sort_values(by=["gvkey", "datadate"])
    comp["count"] = comp.groupby(["gvkey"]).cumcount()

    # comp=comp[['gvkey','datadate','year','be','count']]

    comp.to_csv(Path(data_dir) / "pulled" / "compustat.csv", index=False)


def pull_CRSP_ff_inputs(start_date='2019-01-01', end_date='2022-12-31', data_dir=DATA_DIR):
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        crsp_m = db.raw_sql(
            f"""
                        select a.permno, a.permco, a.date, b.shrcd, b.exchcd,
                        a.ret, a.retx, a.shrout, a.prc
                        from crsp.msf as a
                        left join crsp.msenames as b
                        on a.permno=b.permno
                        and b.namedt<=a.date
                        and a.date<=b.nameendt
                        where a.date between '{start_date}' and '{end_date}'
                        and b.exchcd between 0 and 3
                        """,
            date_cols=["date"],
        )

        # add delisting return
        dlret = db.raw_sql(
            """
                            select permno, dlret, dlstdt 
                            from crsp.msedelist
                            """,
            date_cols=["dlstdt"],
        )
    # change variable format to int
    crsp_m[["permco", "permno", "shrcd", "exchcd"]] = crsp_m[
        ["permco", "permno", "shrcd", "exchcd"]
    ].astype(int)

    # Line up date to be end of month
    crsp_m["jdate"] = crsp_m["date"] + MonthEnd(0)

    dlret.permno = dlret.permno.astype(int)
    # dlret['dlstdt']=pd.to_datetime(dlret['dlstdt'])
    dlret["jdate"] = dlret["dlstdt"] + MonthEnd(0)

    crsp = pd.merge(crsp_m, dlret, how="left", on=["permno", "jdate"])
    crsp["dlret"] = crsp["dlret"].fillna(0)
    crsp["ret"] = crsp["ret"].fillna(0)

    # retadj factors in the delisting returns
    # NOTE: this is different from the asset pricing book.
    crsp["retadj"] = (1 + crsp["ret"]) * (1 + crsp["dlret"]) - 1

    # calculate market equity
    crsp["me"] = crsp["prc"].abs() * crsp["shrout"]
    crsp = crsp.drop(["dlret", "dlstdt", "prc", "shrout"], axis=1)
    crsp = crsp.sort_values(by=["jdate", "permco", "me"])
    crsp.to_csv(
        Path(data_dir) / "pulled" / f"CRSP_FF_{start_date}_{end_date}.csv", index=False
    )


def calc_CRSP_ff_mktcap(crsp):
    # sum of me across different permno belonging to same permco a given date
    crsp_summe = crsp.groupby(["jdate", "permco"])["me"].sum().reset_index()

    # largest mktcap within a permco/date
    crsp_maxme = crsp.groupby(["jdate", "permco"])["me"].max().reset_index()

    # join by jdate/maxme to find the permno
    crsp1 = pd.merge(crsp, crsp_maxme, how="inner", on=["jdate", "permco", "me"])

    # drop me column and replace with the sum me
    crsp1 = crsp1.drop(["me"], axis=1)

    # join with sum of me to get the correct market cap info
    crsp2 = pd.merge(crsp1, crsp_summe, how="inner", on=["jdate", "permco"])

    # sort by permno and date and also drop duplicates
    crsp2 = crsp2.sort_values(by=["permno", "jdate"]).drop_duplicates()

    # keep December market cap
    crsp2["year"] = crsp2["jdate"].dt.year
    crsp2["month"] = crsp2["jdate"].dt.month
    decme = crsp2[crsp2["month"] == 12]
    decme = decme[["permno", "date", "jdate", "me", "year"]].rename(
        columns={"me": "dec_me"}
    )

    ### July to June dates
    crsp2["ffdate"] = crsp2["jdate"] + MonthEnd(-6)
    crsp2["ffyear"] = crsp2["ffdate"].dt.year
    crsp2["ffmonth"] = crsp2["ffdate"].dt.month
    crsp2["1+retx"] = 1 + crsp2["retx"]
    crsp2 = crsp2.sort_values(by=["permno", "date"])

    # cumret by stock
    crsp2["cumretx"] = crsp2.groupby(["permno", "ffyear"])["1+retx"].cumprod()

    # lag cumret
    crsp2["lcumretx"] = crsp2.groupby(["permno"])["cumretx"].shift(1)

    # lag market cap
    crsp2["lme"] = crsp2.groupby(["permno"])["me"].shift(1)

    # if first permno then use me/(1+retx) to replace the missing value
    crsp2["count"] = crsp2.groupby(["permno"]).cumcount()
    crsp2["lme"] = np.where(
        crsp2["count"] == 0, crsp2["me"] / crsp2["1+retx"], crsp2["lme"]
    )

    # baseline me
    mebase = crsp2[crsp2["ffmonth"] == 1][["permno", "ffyear", "lme"]].rename(
        columns={"lme": "mebase"}
    )

    # merge result back together
    crsp3 = pd.merge(crsp2, mebase, how="left", on=["permno", "ffyear"])
    crsp3["wt"] = np.where(
        crsp3["ffmonth"] == 1, crsp3["lme"], crsp3["mebase"] * crsp3["lcumretx"]
    )

    decme["year"] = decme["year"] + 1
    decme = decme[["permno", "year", "dec_me"]]

    # Info as of June
    crsp3_jun = crsp3[crsp3["month"] == 6]

    crsp_jun = pd.merge(crsp3_jun, decme, how="inner", on=["permno", "year"])
    crsp_jun = crsp_jun[
        [
            "permno",
            "date",
            "jdate",
            "shrcd",
            "exchcd",
            "retadj",
            "me",
            "wt",
            "cumretx",
            "mebase",
            "lme",
            "dec_me",
        ]
    ]
    crsp_jun = crsp_jun.sort_values(by=["permno", "jdate"]).drop_duplicates()
    return crsp_jun, crsp3


def pull_CCM(data_dir=DATA_DIR):
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        ccm = db.raw_sql(
            """
                    select gvkey, lpermno as permno, linktype, linkprim, 
                    linkdt, linkenddt
                    from crsp.ccmxpf_linktable
                    where substr(linktype,1,1)='L'
                    and (linkprim ='C' or linkprim='P')
                    """,
            date_cols=["linkdt", "linkenddt"],
        )
        ccm["linkenddt"] = ccm["linkenddt"].fillna(pd.to_datetime("today"))
        ccm.to_csv(Path(data_dir) / "pulled" / "CCM.csv", index=False)


def merge_CRSP_CCM_Comp(crsp_jun, ccm, comp):
    ccm1 = pd.merge(
        comp[["gvkey", "datadate", "be", "count"]], ccm, how="left", on=["gvkey"]
    )
    ccm1["yearend"] = ccm1["datadate"] + YearEnd(0)
    ccm1["jdate"] = ccm1["yearend"] + MonthEnd(6)

    # set link date bounds
    ccm2 = ccm1[
        (ccm1["jdate"] >= ccm1["linkdt"]) & (ccm1["jdate"] <= ccm1["linkenddt"])
    ]
    ccm2 = ccm2[["gvkey", "permno", "datadate", "yearend", "jdate", "be", "count"]]

    # link comp and crsp
    ccm_jun = pd.merge(crsp_jun, ccm2, how="inner", on=["permno", "jdate"])
    ccm_jun["beme"] = ccm_jun["be"] * 1000 / ccm_jun["dec_me"]
    return ccm_jun


# function to assign sz and bm bucket
def sz_bucket(row):
    if row["me"] == np.nan:
        value = ""
    elif row["me"] <= row["sizemedn"]:
        value = "S"
    else:
        value = "B"
    return value


def bm_bucket(row):
    if 0 <= row["beme"] <= row["bm30"]:
        value = "L"
    elif row["beme"] <= row["bm70"]:
        value = "M"
    elif row["beme"] > row["bm70"]:
        value = "H"
    else:
        value = ""
    return value


# function to calculate value weighted return
def wavg(group, avg_name, weight_name):
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan


def calc_ff_percentiles(ccm_jun, crsp):
    # NOTE: This only uses NYSE. It could be changed to include more exchanges.

    # select NYSE stocks for bucket breakdown
    # exchcd = 1 and positive beme and positive me and shrcd in (10,11) and at least 2 years in comp
    nyse = ccm_jun[
        (ccm_jun["exchcd"] == 1)
        & (ccm_jun["beme"] > 0)
        & (ccm_jun["me"] > 0)
        & (ccm_jun["count"] >= 1)
        & ((ccm_jun["shrcd"] == 10) | (ccm_jun["shrcd"] == 11))
    ]

    # size breakdown
    nyse_sz = (
        nyse.groupby(["jdate"])["me"]
        .median()
        .to_frame()
        .reset_index()
        .rename(columns={"me": "sizemedn"})
    )

    # beme breakdown
    nyse_bm = (
        nyse.groupby(["jdate"])["beme"].describe(percentiles=[0.3, 0.7]).reset_index()
    )
    nyse_bm = nyse_bm[["jdate", "30%", "70%"]].rename(
        columns={"30%": "bm30", "70%": "bm70"}
    )

    nyse_breaks = pd.merge(nyse_sz, nyse_bm, how="inner", on=["jdate"])

    # join back size and beme breakdown
    ccm1_jun = pd.merge(ccm_jun, nyse_breaks, how="left", on=["jdate"])

    # assign size portfolio
    ccm1_jun["szport"] = np.where(
        (ccm1_jun["beme"] > 0) & (ccm1_jun["me"] > 0) & (ccm1_jun["count"] >= 1),
        ccm1_jun.apply(sz_bucket, axis=1),
        "",
    )

    # assign book-to-market portfolio
    ccm1_jun["bmport"] = np.where(
        (ccm1_jun["beme"] > 0) & (ccm1_jun["me"] > 0) & (ccm1_jun["count"] >= 1),
        ccm1_jun.apply(bm_bucket, axis=1),
        "",
    )

    # create positivebmeme and nonmissport variable
    ccm1_jun["posbm"] = np.where(
        (ccm1_jun["beme"] > 0) & (ccm1_jun["me"] > 0) & (ccm1_jun["count"] >= 1), 1, 0
    )
    ccm1_jun["nonmissport"] = np.where((ccm1_jun["bmport"] != ""), 1, 0)

    # And update portfolio as of June
    # store portfolio assignment as of June
    june = ccm1_jun[
        ["permno", "date", "jdate", "bmport", "szport", "posbm", "nonmissport"]
    ].copy()
    june["ffyear"] = june["jdate"].dt.year

    # merge back with monthly records
    crsp3 = crsp[
        [
            "date",
            "permno",
            "shrcd",
            "exchcd",
            "retadj",
            "me",
            "wt",
            "cumretx",
            "ffyear",
            "jdate",
        ]
    ]
    ccm3 = pd.merge(
        crsp3,
        june[["permno", "ffyear", "szport", "bmport", "posbm", "nonmissport"]],
        how="left",
        on=["permno", "ffyear"],
    )

    # keeping only records that meet the criteria
    # NOTE: again, this could be changed.
    ccm4 = ccm3[
        (ccm3["wt"] > 0)
        & (ccm3["posbm"] == 1)
        & (ccm3["nonmissport"] == 1)
        & ((ccm3["shrcd"] == 10) | (ccm3["shrcd"] == 11))
    ]

    return ccm4


# Functions to calculate the Fama-French 1992 and 1993 factors.
# The difference between the two is that the '92 factors use univariate
# sorts rather than 2x3. Specifically:
# For HML:
# - 30% of stocks with the highest BM are in the H bucket, 30% of stocks with the lowest BM are in the L bucket.
# - Calculate value-weighted returns for H and L, and then HML = H - L.
# - For '93:
# - Calculate the value-weighted return for big + high, big + low, small + high, small + low.
# - Take a simple average of big + high and big + low, and small + high and small + low.
# - SMB = small + high + small + low
# For SMB:
# - Split the stocks down the median of market cap.
# - Calculate value-weighted returns for small and big, and then SMB = small - big.
# - For '93:
# - Take the average of small + high, small + medium, and small + low, and then SMB = small - big.
# The key difference is that '92 has two portfolios per factors (either H or L, and either small or big),
# whereas '93 calculates 6 portfolios (small + high, small + medium, small + low, big + high, big + medium, big + low),
# and then calculates the factors via different averages of the portfolios.


def calc_ff_92_factors(ccm4):
    # Univariate sorts on size and book-to-market.
    vwret_bm = (
        ccm4.groupby(["jdate", "bmport"])
        .apply(wavg, "retadj", "wt")
        .to_frame()
        .reset_index()
        .rename(columns={0: "vwret"})
    )
    vwret_sz = (
        ccm4.groupby(["jdate", "szport"])
        .apply(wavg, "retadj", "wt")
        .to_frame()
        .reset_index()
        .rename(columns={0: "vwret"})
    )
    vw_ret_bm_n = (
        ccm4.groupby(["jdate", "bmport"])["retadj"]
        .count()
        .reset_index()
        .rename(columns={"retadj": "n_firms"})
    )
    vw_ret_sz_n = (
        ccm4.groupby(["jdate", "szport"])["retadj"]
        .count()
        .reset_index()
        .rename(columns={"retadj": "n_firms"})
    )

    ff_bm = vwret_bm.pivot(
        index="jdate", columns="bmport", values="vwret"
    ).reset_index()
    ff_bm_n = vw_ret_bm_n.pivot(
        index="jdate", columns="bmport", values="n_firms"
    ).reset_index()

    # Create SMB and HML factors
    ff_factors = vwret_sz.pivot(
        index="jdate", columns="szport", values="vwret"
    ).reset_index()
    ff_nfirms = vw_ret_sz_n.pivot(
        index="jdate", columns="szport", values="n_firms"
    ).reset_index()

    ff_factors["WB"] = ff_factors["B"]
    ff_factors["WS"] = ff_factors["S"]
    ff_factors["WSMB"] = ff_factors["WS"] - ff_factors["WB"]

    ff_factors["WH"] = ff_bm["H"]
    ff_factors["WL"] = ff_bm["L"]
    ff_factors["WHML"] = ff_factors["WH"] - ff_factors["WL"]

    ff_nfirms["B"] = ff_nfirms["B"]
    ff_nfirms["S"] = ff_nfirms["S"]
    ff_nfirms["SMB"] = ff_nfirms["B"] + ff_nfirms["S"]

    ff_nfirms["H"] = ff_bm_n["H"]
    ff_nfirms["L"] = ff_bm_n["L"]
    ff_nfirms["HML"] = ff_nfirms["H"] + ff_nfirms["L"]

    ff_factors = ff_factors.rename(columns={"jdate": "date"})
    ff_nfirms = ff_nfirms.rename(columns={"jdate": "date"})
    return ff_factors, ff_nfirms


def calc_ff_93_factors(ccm4):
    # value-weigthed return
    vwret = (
        ccm4.groupby(["jdate", "szport", "bmport"])
        .apply(wavg, "retadj", "wt")
        .to_frame()
        .reset_index()
        .rename(columns={0: "vwret"})
    )
    vwret["sbport"] = vwret["szport"] + vwret["bmport"]

    # firm count
    vwret_n = (
        ccm4.groupby(["jdate", "szport", "bmport"])["retadj"]
        .count()
        .reset_index()
        .rename(columns={"retadj": "n_firms"})
    )
    vwret_n["sbport"] = vwret_n["szport"] + vwret_n["bmport"]

    # transpose
    ff_factors = vwret.pivot(
        index="jdate", columns="sbport", values="vwret"
    ).reset_index()
    ff_nfirms = vwret_n.pivot(
        index="jdate", columns="sbport", values="n_firms"
    ).reset_index()

    # create SMB and HML factors
    ff_factors["WH"] = (ff_factors["BH"] + ff_factors["SH"]) / 2
    ff_factors["WL"] = (ff_factors["BL"] + ff_factors["SL"]) / 2
    ff_factors["WHML"] = ff_factors["WH"] - ff_factors["WL"]

    ff_factors["WB"] = (ff_factors["BL"] + ff_factors["BM"] + ff_factors["BH"]) / 3
    ff_factors["WS"] = (ff_factors["SL"] + ff_factors["SM"] + ff_factors["SH"]) / 3
    ff_factors["WSMB"] = ff_factors["WS"] - ff_factors["WB"]

    ff_factors = ff_factors.rename(columns={"jdate": "date"})

    # n firm count
    ff_nfirms["H"] = ff_nfirms["SH"] + ff_nfirms["BH"]
    ff_nfirms["L"] = ff_nfirms["SL"] + ff_nfirms["BL"]
    ff_nfirms["HML"] = ff_nfirms["H"] + ff_nfirms["L"]

    ff_nfirms["B"] = ff_nfirms["BL"] + ff_nfirms["BM"] + ff_nfirms["BH"]
    ff_nfirms["S"] = ff_nfirms["SL"] + ff_nfirms["SM"] + ff_nfirms["SH"]
    ff_nfirms["SMB"] = ff_nfirms["B"] + ff_nfirms["S"]
    ff_nfirms["TOTAL"] = ff_nfirms["SMB"]
    ff_nfirms = ff_nfirms.rename(columns={"jdate": "date"})
    return ff_factors, ff_nfirms


def calc_and_pull_ff_factors(
    start_date, end_date, data_dir=DATA_DIR, from_cache=False, save=True
):
    # Check if exists in file path or not cache
    path_ff_input = Path(data_dir) / "pulled" / f"CRSP_FF_{start_date}_{end_date}.csv"
    path_ccm = Path(data_dir) / "pulled" / "CCM.csv"
    path_comp = Path(data_dir) / "pulled" / "compustat.csv"
    if not path_ff_input.exists() or not from_cache:
        pull_CRSP_ff_inputs(start_date, end_date, data_dir)
    if not path_ccm.exists() or not from_cache:
        pull_CCM(data_dir)
    if not path_comp.exists() or not from_cache:
        pull_compustat(data_dir)

    # Load data
    crsp = pd.read_csv(path_ff_input, parse_dates=["date", "jdate"])
    ccm = pd.read_csv(path_ccm, parse_dates=["linkdt", "linkenddt"])
    comp = pd.read_csv(path_comp, parse_dates=["datadate"])

    crsp_jun, crsp = calc_CRSP_ff_mktcap(crsp)
    ccm_jun = merge_CRSP_CCM_Comp(crsp_jun, ccm, comp)
    ccm4 = calc_ff_percentiles(ccm_jun, crsp)
    ff_factors, ff_nfirms = calc_ff_93_factors(ccm4)
    ff_factors_92, ff_nfirms_92 = calc_ff_92_factors(ccm4)

    # Join the datasets on date, add '_92' suffix to the 1992 factors
    ff_factors = ff_factors.merge(ff_factors_92, on="date", suffixes=("", "_92"))
    ff_nfirms = ff_nfirms.merge(ff_nfirms_92, on="date", suffixes=("", "_92"))

    if save:
        ff_factors.to_csv(
            Path(data_dir) / "pulled" / f"FF_FACTORS_{start_date}_{end_date}.csv"
        )
        ff_nfirms.to_csv(
            Path(data_dir) / "pulled" / f"FF_NFIRMS_{start_date}_{end_date}.csv"
        )
    return ff_factors, ff_nfirms


def plot_all_factors(start_date='2019-01-01', end_date='2022-12-31', filt_start, filt_end):
    # This re-creates the OAP diagram.
    ff_factors = pd.read_csv(
        f"../data/pulled/CRSP/FF_FACTORS_{start_date}_{end_date}.csv",
        index_col=0,
        parse_dates=["date"],
    )

    # Pull official FF factors
    with wrds.Connection(wrds_username=WRDS_USERNAME) as db:
        _ff = db.get_table(library="ff", table="factors_monthly", date_cols=["date"])
        _ff = _ff[["date", "smb", "hml"]]
        _ff.columns = ["date", "FF_SMB", "FF_HML"]
        _ff[["FF_SMB", "FF_HML"]] = _ff[["FF_SMB", "FF_HML"]].astype(float)
        _ff["date"] = _ff["date"] + MonthEnd(0)

    ff_factors = ff_factors.merge(_ff, on="date", how="left")
    ff_factors = ff_factors.set_index("date")

    ff_filt = ff_factors.loc[
        filt_start:filt_end, ["FF_SMB", "FF_HML", "WSMB", "WHML", "WSMB_92", "WHML_92"]
    ]
    ff_filt.iloc[0] = 0

    # Calculate cum returns
    ff_filt = (ff_filt + 1).cumprod() - 1

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(ff_filt)
    ax.legend(ff_filt.columns)
    ax.set_title("Fama-French Factors")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return")
    fig.tight_layout()


# This is some of the translated OAP code.
# The BMdec calculation is what Freda Song does (above),
# so I merged her code with the univariate sorts for FF92
# factor construction, ie. these functions don't need to be
# used.


def calc_BM_Dec_OAP(start_date='2019-01-01', end_date='2022-12-31', data_dir=DATA_DIR, from_cache=False):
    if not from_cache:
        pull_compustat(data_dir)
        pull_CRSP_ff_inputs(start_date, end_date, data_dir)

    # DATA LOAD
    compustat_data = pd.read_csv(
        Path(data_dir) / "pulled" / "compustat.csv", parse_dates=["datadate"]
    )
    crsp_data = pd.read_csv(
        Path(data_dir) / "pulled" / f"CRSP_FF_93_{start_date}_{end_date}.csv",
        parse_dates=["date", "jdate"],
    )
    ccm_data = pd.read_csv(
        Path(data_dir) / "pulled" / "CCM.csv", parse_dates=["linkdt", "linkenddt"]
    )

    # Join compustat and ccm
    compustat_data = pd.merge(
        compustat_data,
        ccm_data[["gvkey", "permno", "linkdt", "linkenddt"]],
        on="gvkey",
        how="left",
    )
    compustat_data["datadate"] = compustat_data["datadate"] + MonthEnd(0)

    # Keep only the first observation per group
    compustat_data = (
        compustat_data.groupby(["permno", "datadate"]).first().reset_index()
    )

    # Rename datadate to date
    compustat_data = compustat_data.rename(columns={"datadate": "date"})

    # Merge datasets
    merged_data = pd.merge(
        compustat_data,
        crsp_data[["permno", "date", "me", "ret", "retadj", "retx", "jdate"]],
        on=["permno", "date"],
        how="inner",
    )

    # SIGNAL CONSTRUCTION
    merged_data = merged_data.set_index(["permno", "date"]).sort_index()
    idx = merged_data.index.get_level_values("date")

    # Compute tempME
    merged_data["tempME"] = merged_data["me"]
    merged_data["tempYear"] = merged_data.index.get_level_values("date").year

    # Compute tempDecME
    tempDecME = (
        merged_data.groupby(["permno", "tempYear"])["tempME"].min().reset_index()
    )
    merged_data = pd.merge(
        merged_data, tempDecME, on=["permno", "tempYear"], how="left"
    )
    merged_data.index = idx
    # Compute book equity
    merged_data["tempPS"] = merged_data["pstk"]
    merged_data["tempPS"].fillna(merged_data["pstkrv"], inplace=True)
    merged_data["tempPS"].fillna(merged_data["pstkl"], inplace=True)

    merged_data["tempSE"] = merged_data["seq"]
    merged_data["tempSE"].fillna(
        merged_data["ceq"] + merged_data["tempPS"], inplace=True
    )
    merged_data["tempSE"].fillna(merged_data["at"] - merged_data["lt"], inplace=True)

    merged_data["tempBE"] = (
        merged_data["tempSE"] + merged_data["txditc"] - merged_data["tempPS"]
    )

    merged_data["BMdec"] = merged_data["tempBE"] / merged_data.groupby("permno")[
        "tempME_y"
    ].shift(1)
    merged_data["BMdec"].where(
        merged_data.index.get_level_values("date").month >= 6,
        merged_data["tempBE"] / merged_data.groupby("permno")["tempME_y"].shift(2),
        inplace=True,
    )

    return merged_data


def calc_FF_92_OAP(data):
    # Calculate percentiles of BMdec for each month, long/short top and bottom 30%.
    # Calculate the return of the long/short portfolio.

    # Calculate percentiles
    # data['BMdecPercentile'] = data.groupby('date')['BMdec'].transform(lambda x: pd.qcut(x, 10, labels=False))

    nyse_bm = (
        data.groupby(["date"])["BMdec"].describe(percentiles=[0.3, 0.7]).reset_index()
    )
    nyse_bm = nyse_bm[["date", "30%", "70%"]].rename(
        columns={"30%": "bm30", "70%": "bm70"}
    )

    # join back size and beme breakdown
    data_1 = pd.merge(data, nyse_bm, how="left", on=["date"])

    # Calculate long/short portfolio
    data["BMdecPortfolio"] = np.nanw

    # Long
    data["BMdecPortfolio"].where(data["BMdecPercentile"] >= 7, 1, inplace=True)
    # Short
    data["BMdecPortfolio"].where(data["BMdecPercentile"] <= 3, 0, inplace=True)

    # Calculate value weighted returns of long/short portfolio by month
    data["BMdecPortfolioLongWeight"] = data["BMdecPortfolio"] * data["tempME_y"]
    data["BMdecPortfolioShortWeight"] = (1 - data["BMdecPortfolio"]) * data["tempME_y"]
    data["BMdecPortfolioLongReturn"] = data.groupby("date")[
        "BMdecPortfolioLongWeight"
    ].transform(lambda x: x.sum() / x.count())
    data["BMdecPortfolioShortReturn"] = data.groupby("date")[
        "BMdecPortfolioShortWeight"
    ].transform(lambda x: x.sum() / x.count())

    # Calculate long/short portfolio return
    data["BMdecPortfolioReturn"] = (
        data["BMdecPortfolioLongReturn"] - data["BMdecPortfolioShortReturn"]
    ) / 2

    return data


def _debug():
    df = load_whole_monthly_us_equity(data_dir=path_to_data_root)
    df_index = load_NYSE_AMEX_NASDAQ_index(data_dir=path_to_data_root)


if __name__ == "__main__":
    start_date = '2019-01-01'
    end_date = '2022-12-31'
    df = pull_CRSP_monthly_file(start_date=start_date, end_date=end_date)
    df.info()
    path = Path(data_dir) / "pulled" / "CRSP_MSF_INDEX_INPUTS.csv"
    df.to_csv(path)

    df = pull_CRSP_index_files(start_date=start_date, end_date=end_date)    
    path = Path(data_dir) / "pulled" / f"CRSP_MSIX_.csv"
    df.to_csv(path)
