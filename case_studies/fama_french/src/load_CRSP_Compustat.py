"""
Code to calculate the Fama-French 1993 factors
from: https://www.fredasongdrechsler.com/data-crunching/fama-french
Citation: Drechsler, Qingyi (Freda) S., 2023, Python Programs for Empirical 
Finance, https://www.fredasongdrechsler.com

This file was lightly modified from the original by Tobias Rodriguez
del Pozo for use in the course "Data Science Tools for Finance" by
Jeremy Bejarano.
"""
import pandas as pd
from pandas.tseries.offsets import MonthEnd, YearEnd

import numpy as np
import wrds

import config
from pathlib import Path

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME
START_DATE = config.START_DATE
END_DATE = config.END_DATE

def pull_compustat(wrds_username=WRDS_USERNAME):
    sql_query = """
        SELECT 
            a.gvkey, a.datadate, a.conm, a.fyear, a.tic, a.cusip, a.naicsh, 
            a.sich, a.aco, a.act, a.ajex, a.am, a.ao, a.ap, a.at, a.capx, a.ceq,
            a.ceqt, a.che, a.cogs, a.csho, a.cshrc, a.dcpstk, a.dcvt, a.dlc, 
            a.dlcch, a.dltis, a.dltr, a.dltt, a.dm, a.dp, a.drc, a.drlt, a.dv, 
            a.dvc, a.dvp, a.dvpa, a.dvpd, a.dvpsx_c, a.dvt, a.ebit, a.ebitda,
            a.emp, a.epspi, a.epspx, a.fatb, a.fatl, a.ffo, a.fincf, a.fopt,
            a.gdwl, a.gdwlia, a.gdwlip, a.gwo, a.ib, a.ibcom, a.intan, a.invt,
            a.ivao, a.ivncf, a.ivst, a.lco, a.lct, a.lo, a.lt, a.mib, a.msa,
            a.ni, a.nopi, a.oancf, a.ob, a.oiadp, a.oibdp, a.pi, a.ppenb, 
            a.ppegt, a.ppenls, a.ppent, a.prcc_c, a.prcc_f, a.prstkc, a.prstkcc,
            a.pstk, a.pstkl, a.pstkrv, a.re, a.rect, a.recta, a.revt, a.sale,
            a.scstkc, a.seq, a.spi, a.sstk, a.tstkp, a.txdb, a.txdi, a.txditc,
            a.txfo, a.txfed, a.txp, a.txt, a.wcap, a.wcapch, a.xacc, a.xad, 
            a.xint, a.xrd, a.xpp, a.xsga
        FROM 
            COMP.FUNDA as a
        WHERE 
            a.consol = 'C' AND
            a.popsrc = 'D' AND
            a.datafmt = 'STD' AND
            a.curcd = 'USD' AND
            a.indfmt = 'INDL' AND 
            datadate >= '01/01/1959'
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     comp = db.raw_sql(sql_query, date_cols=["datadate"])
    db = wrds.Connection(wrds_username=wrds_username)
    comp = db.raw_sql(sql_query, date_cols=["datadate"])
    db.close()

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
    return comp


def pull_CRSP_ff_inputs(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    raw_sql = f"""
        SELECT 
            a.permno, a.permco, a.date, b.shrcd, b.exchcd, 
            a.ret, a.retx, a.shrout, a.prc
        FROM 
            crsp.msf AS a
        LEFT JOIN 
            crsp.msenames AS b
        ON
            a.permno=b.permno AND 
            b.namedt<=a.date AND 
            a.date<=b.nameendt
        where 
            a.date BETWEEN '{start_date}' AND '{end_date}' AND 
            b.exchcd BETWEEN 0 AND 3
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     crsp_m = db.raw_sql(
    #         raw_sql,
    #         date_cols=["date"],
    #     )

    #     # add delisting return
    #     dlret = db.raw_sql(
    #         """
    #     SELECT
    #         permno, dlret, dlstdt
    #     FROM
    #         crsp.msedelist
    #     """,
    #         date_cols=["dlstdt"],
    #     )
    db = wrds.Connection(wrds_username=wrds_username)
    crsp_m = db.raw_sql(
        raw_sql,
        date_cols=["date"],
    )

    # add delisting return
    dlret = db.raw_sql(
        """
    SELECT 
        permno, dlret, dlstdt 
    FROM 
        crsp.msedelist
    """,
        date_cols=["dlstdt"],
    )
    db.close()

    # change variable format to int
    crsp_m[["permco", "permno", "shrcd", "exchcd"]] = crsp_m[
        ["permco", "permno", "shrcd", "exchcd"]
    ].astype(int)

    # Line up date to be end of month
    crsp_m["jdate"] = crsp_m["date"] + MonthEnd(0)

    dlret["permno"] = dlret["permno"].astype(int)
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
    return crsp


def pull_CRSP_Comp_Link_Table(data_dir=DATA_DIR, wrds_username=WRDS_USERNAME):
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     ccm = db.raw_sql(
    #         """
    #         SELECT
    #             gvkey, lpermno AS permno, linktype, linkprim,
    #             linkdt, linkenddt
    #         FROM
    #             crsp.ccmxpf_linktable
    #         WHERE
    #             substr(linktype,1,1)='L' AND
    #             (linkprim ='C' OR linkprim='P')
    #         """,
    #         date_cols=["linkdt", "linkenddt"],
    #     )
    db = wrds.Connection(wrds_username=wrds_username)
    ccm = db.raw_sql(
        """
        SELECT 
            gvkey, lpermno AS permno, linktype, linkprim, 
            linkdt, linkenddt
        FROM 
            crsp.ccmxpf_linktable
        WHERE 
            substr(linktype,1,1)='L' AND 
            (linkprim ='C' OR linkprim='P')
        """,
        date_cols=["linkdt", "linkenddt"],
    )
    db.close()

    ccm["linkenddt"] = ccm["linkenddt"].fillna(pd.to_datetime("today"))
    return ccm


def load_compustat(data_dir=DATA_DIR):
    """Load Compustat data from disk"""
    path = Path(data_dir) / "pulled" / "Compustat.parquet"
    df = pd.read_parquet(path)
    return df


def load_CRSP_ff_inputs(data_dir=DATA_DIR):
    """Load CRSP data from disk"""
    path = Path(data_dir) / "pulled" / "CRSP_FF.parquet"
    df = pd.read_parquet(path)
    return df


def load_CRSP_Comp_Link_Table(data_dir=DATA_DIR):
    """Load CRSP/Compustat merged data from disk"""
    path = Path(data_dir) / "pulled" / "CRSP_Comp_Link_Table.parquet"
    df = pd.read_parquet(path)
    return df


def _demo():
    comp = load_compustat(data_dir=DATA_DIR)
    crsp = load_CRSP_ff_inputs(data_dir=DATA_DIR)
    ccm = load_CRSP_Comp_Link_Table(data_dir=DATA_DIR)


if __name__ == "__main__":
    comp = pull_compustat(wrds_username=WRDS_USERNAME)
    comp.to_parquet(DATA_DIR / "pulled" / "Compustat.parquet")

    crsp = pull_CRSP_ff_inputs(wrds_username=WRDS_USERNAME)
    crsp.to_parquet(DATA_DIR / "pulled" / "CRSP_FF.parquet")

    ccm = pull_CRSP_Comp_Link_Table(wrds_username=WRDS_USERNAME)
    ccm.to_parquet(DATA_DIR / "pulled" / "CRSP_Comp_Link_Table.parquet")
