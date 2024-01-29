"""
This code was adapted from from: 
https://www.fredasongdrechsler.com/data-crunching/fama-french
Citation: Drechsler, Qingyi (Freda) S., 2023, Python Programs for Empirical Finance, 
https://www.fredasongdrechsler.com

Thank you to Tobias Rodriguez del Pozo for his assistance in writing this code.
"""
from matplotlib import pyplot as plt
import pandas as pd
from pandas.tseries.offsets import MonthEnd, YearEnd
import numpy as np

import load_CRSP_Compustat
import load_Fama_French

import config

DATA_DIR = config.DATA_DIR
START_DATE = config.START_DATE
END_DATE = config.END_DATE


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


####################################################################################################


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
        m = (d * w).sum() / w.sum()
    except ZeroDivisionError:
        m = np.nan
    return m


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


def calc_and_pull_ff_factors(data_dir=DATA_DIR):
    comp = load_CRSP_Compustat.load_compustat(data_dir=data_dir)
    crsp = load_CRSP_Compustat.load_CRSP_ff_inputs(data_dir=data_dir)
    ccm = load_CRSP_Compustat.load_CRSP_Comp_Link_Table(data_dir=data_dir)

    crsp_jun, crsp = calc_CRSP_ff_mktcap(crsp)
    ccm_jun = merge_CRSP_CCM_Comp(crsp_jun, ccm, comp)
    ccm4 = calc_ff_percentiles(ccm_jun, crsp)
    ff_factors, ff_nfirms = calc_ff_93_factors(ccm4)
    ff_factors_92, ff_nfirms_92 = calc_ff_92_factors(ccm4)

    # Join the datasets on date, add '_92' suffix to the 1992 factors
    ff_factors = ff_factors.merge(ff_factors_92, on="date", suffixes=("", "_92"))
    ff_nfirms = ff_nfirms.merge(ff_nfirms_92, on="date", suffixes=("", "_92"))

    return ff_factors, ff_nfirms


def plot_all_factors(
    filt_start=START_DATE,
    filt_end=END_DATE,
    factors=["FF_SMB", "FF_HML", "WSMB", "WHML", "WSMB_92", "WHML_92"],
):
    # This re-creates the OAP diagram.
    ff_factors = pd.read_parquet(DATA_DIR / "pulled" / "FF_FACTORS_all.parquet")

    # Load official FF factors
    _ff = load_Fama_French.load_Fama_French_factors(data_dir=DATA_DIR)

    ff_factors = ff_factors.merge(_ff, on="date", how="left")
    ff_factors = ff_factors.set_index("date")

    ff_filt = ff_factors.loc[filt_start:filt_end, factors]
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


def calc_BM_Dec_OAP(
    start_date=START_DATE, end_date=END_DATE, data_dir=DATA_DIR, from_cache=False
):
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


def _main():
    comp = load_CRSP_Compustat.load_compustat(data_dir=DATA_DIR)
    crsp = load_CRSP_Compustat.load_CRSP_ff_inputs(data_dir=DATA_DIR)
    ccm = load_CRSP_Compustat.load_CRSP_Comp_Link_Table(data_dir=DATA_DIR)

    crsp_jun, crsp3 = calc_CRSP_ff_mktcap(crsp)
    # mccm = merge_CRSP_CCM_Comp(crsp, ccm, comp)
    ccm_merged = merge_CRSP_CCM_Comp(crsp_jun, ccm, comp)
    ccm_merged.to_parquet(DATA_DIR / "pulled" / "FF_CRSP_Comp_Merged.parquet")

    ff_factors, ff_nfirms = calc_and_pull_ff_factors(data_dir=DATA_DIR)
    path = DATA_DIR / "pulled" / "FF_FACTORS_all.parquet"
    ff_factors.to_parquet(path)
    path = DATA_DIR / "pulled" / "FF_NFIRMS.parquet"
    ff_nfirms.to_parquet(path)


def _demo():
    _main()

    plot_all_factors()
    if True:
        plot_all_factors(
            filt_start=START_DATE,
            filt_end=END_DATE,
            # factors=["FF_SMB", "FF_HML", "WSMB", "WHML", "WSMB_92", "WHML_92"],)
            factors=["FF_HML", "WHML", "WHML_92"],)
        plt.title("Comparing Value Factors");


if __name__ == "__main__":
    _main()
