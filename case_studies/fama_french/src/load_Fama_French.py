from pathlib import Path
import pandas as pd
from pandas.tseries.offsets import MonthEnd, YearEnd
import wrds

import config
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME

def pull_Fama_French_factors(wrds_username=WRDS_USERNAME):
    # Pull official FF factors
    db = wrds.Connection(wrds_username=wrds_username)
    _ff = db.get_table(library="ff", table="factors_monthly", date_cols=["date"])
    _ff = _ff[["date", "smb", "hml"]]
    _ff.columns = ["date", "FF_SMB", "FF_HML"]
    _ff[["FF_SMB", "FF_HML"]] = _ff[["FF_SMB", "FF_HML"]].astype(float)
    _ff["date"] = _ff["date"] + MonthEnd(0)
    db.close()
    return _ff

def load_Fama_French_factors(data_dir=DATA_DIR):
    path = Path(data_dir) / "pulled" / "FF_FACTORS.parquet"
    df = pd.read_parquet(path)
    return df

if __name__ == "__main__":
    ff = pull_Fama_French_factors(wrds_username=WRDS_USERNAME)
    path = Path(DATA_DIR) / "pulled" / "FF_FACTORS.parquet"
    ff.to_parquet(path)