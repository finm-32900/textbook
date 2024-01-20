import pandas as pd
import numpy as np
import weightedstats


def s04_subsample(df):
    ## Select desired subsample
    # GQ = 0 for vacant units, 1 for Households, 2 for group quarters
    df = df[df["GQ"] == 1]
    #  df['SEX'] = 1 for male
    df = df[df["SEX"] == 1]
    df = df[(df["AGE"] >= 25) & (df["AGE"] <= 54)]
    df = df[df["INCWAGE"] > 0]
    return df


def s05_new_vars(df):
    df["real_incwage"] = df["CPI99"] * df["INCWAGE"]
    df["annual_hours"] = df["WKSWORK1"] * df["UHRSWORKLY"]
    df["real_wage"] = df["real_incwage"] / df["annual_hours"]
    # To prevent infinite wages
    df.loc[df["annual_hours"] <= 0, "real_wage"] = 0

    # Create
    df["in_labor_force"] = df["LABFORCE"] == 2
    return df


def s06_drop(df):
    # Drop the variables that don't need anymore.
    labels = [
        "GQ",
        "SEX",
        "LABFORCE",
        "CPI99",
        "INCTOT",
        "WKSWORK1",
    ]
    for label in labels:
        try:
            df.drop(labels=label, inplace=True, axis=1)
        except:
            pass
    df = df.dropna()
    return df


def s10_drop_by_percentiles(df):
    q99 = df["real_wage"].quantile(q=0.99)
    q01 = df["real_wage"].quantile(q=0.01)
    df = df.query("@q01 < real_wage < @q99")
    return df


def s11_median_wages(df):
    col = "real_wage"
    weights = "ASECWT"
    median_wages = (
        df.dropna(subset=[col], how="any")
        .groupby("YEAR")
        .apply(
            lambda row: weightedstats.weighted_median(row[col], weights=row[weights])
        )
        # Shift time back since the series represents wages from the previous year
        .shift(-1)
    )
    return median_wages


def s11_ave_wages(df):
    col = "real_wage"
    weights = "ASECWT"
    ave_wages = (
        df.dropna(subset=[col], how="any")
        .groupby("YEAR")
        .apply(lambda row: np.average(row[col], weights=row[weights]))
        .shift(-1)
    )
    return ave_wages


def s11_employment(df):
    col = "in_labor_force"
    weights = "ASECWT"
    employment = (
        df.dropna(subset=[col], how="any")
        .groupby("YEAR")
        .apply(lambda row: np.average(row[col], weights=row[weights]))
    )
    return employment


def s12_time_series(df):
    median_wages = s11_median_wages(df)
    ave_wages = s11_ave_wages(df)
    employment = s11_employment(df)
    tdf = pd.concat(
        {
            "ave_wages": ave_wages,
            "median_wages": median_wages,
            "employment": employment,
        },
        axis=1,
    )
    tdf = tdf[["ave_wages", "median_wages", "employment"]]
    return tdf


def s20_bin_vars(df):
    # Add bins to `df` for the AGE and EDUC variables as described in
    # Question 1.B of the HW.
    bins = [25, 30, 35, 40, 45, 50, 55]
    df["age_binned"] = pd.cut(df["AGE"], bins=bins, include_lowest=True, right=False)

    educ_bins = [0, 72, 73, 110, 111, 900]
    educ_bin_labels = [
        "Some_High_School",
        "High_School_Diploma",
        "Some_College",
        "Bachelors_Degree",
        "Beyond_Bachelors",
    ]
    df["educ_binned"] = pd.cut(
        df["EDUC"], bins=educ_bins, labels=educ_bin_labels, include_lowest=True
    )
    return df


def s21_within_group_averages(df):
    # Note that the averages are created using the appropriate weights
    group_means = (
        df.dropna()
        .groupby(by=["age_binned", "educ_binned"], observed=False)
        .apply(lambda x: np.average(x.real_wage, weights=x.ASECWT))
    )
    group_means.name = "average_wage"
    return group_means


def s24_demographically_adj_series(df, tdf):
    shift = -1
    inner_means = (df
                .groupby(by=['YEAR', 'age_binned', 'educ_binned'], observed=False)
                .apply(lambda x: np.average(x['real_wage'], weights=x['ASECWT']))
                )


    # Create Bin Weight Sums
    weights_2000 = (df[df.YEAR == '2000']
                    .dropna()
                    .groupby(by=['age_binned', 'educ_binned'], observed=False)
                    ['ASECWT']
                    .sum()
                )

    adj_series = (inner_means
                .groupby(level='YEAR')
                .apply(lambda x: np.average(x, weights=weights_2000)))
    # Lag, since the we use "last years weeks worked", etc.
    adj_series = adj_series.shift(shift)
    tdf['adj_ave_wages'] = adj_series
    tdf['adj_ave_wage_growth'] = adj_series.pct_change(fill_method=None)

    return tdf

if __name__ == "__main__":
    pass
