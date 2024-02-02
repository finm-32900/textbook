#!/usr/bin/env python
# coding: utf-8

# # HW Guide Part A: CRSP Market Returns Indices
# 
# The CRSP (Center for Research in Security Prices) dataset provides two indices
# for market returns: an equal-weighted index and a value-weighted index (both provided
# in terms of returns with and without dividends). The equal-weighted index
# computes the simple average of returns across stocks. This series is available as `EWRETD` and `EWRETX`, (with and without dividends, respectively).
# The value-Weighted Returns index represents a stock market index that calculates the return on investment by considering both the price changes and dividends of each component security, weighted by its market capitalization. This means that larger companies have a greater impact on the index's performance compared to smaller companies. The value-weighting approach aims to reflect the actual investment returns that an investor would achieve by holding a market portfolio, mirroring the performance of the overall market or specific market segments more accurately than equal-weighted indices. The CRSP indices are widely used in academic research and financial analysis to study market trends, evaluate investment strategies, and benchmark the performance of portfolios against the broader market. This series is available in the CRSP tables under the mnemonic `VWRETD` and `VWRETX` (with and without dividends, respectively).
# 
# In this guide, we'll discuss the construction of the equal- and value-weighted market return indices. To construct these indices, we'll follow the suggestions here: https://wrds-www.wharton.upenn.edu/pages/support/support-articles/crsp/index-and-deciles/constructing-value-weighted-return-series-matches-vwretd-crsp-monthly-value-weighted-returns-includes-distributions/
# 
# These suggestions boil down to the most important part: we must select the correct universe of stocks that comprise "the market".

# In[1]:


import pandas as pd

import config
import load_CRSP_stock
import calc_CRSP_indices
import misc_tools

DATA_DIR = config.DATA_DIR


# In[2]:


df_msf = load_CRSP_stock.load_CRSP_monthly_file(data_dir=DATA_DIR)
df_msix = load_CRSP_stock.load_CRSP_index_files(data_dir=DATA_DIR)


# In[3]:


df_msix.info()


# In[4]:


df_msix[[
    "caldt",
    "vwretd",
    "vwretx",
    "vwindx",
    "ewretd",
    "ewretx",]].tail()


# ## Inclusion into the CRSP Market Index:
# 
# From  https://wrds-www.wharton.upenn.edu/pages/support/support-articles/crsp/index-and-deciles/constructing-value-weighted-return-series-matches-vwretd-crsp-monthly-value-weighted-returns-includes-distributions/ ,
# 
# 
# > Our experiments with different VWRETD replication methods show that it is relatively easy to come close to this data series using PERMNO-based returns in the CRSP datasets, but exact matches to every data month is not possible because we do not know the exact sample set of PERMNOs used by CRSP.  Their criteria is listed in the CRSP manual and is roughly:
# > 
# > **CRSP CAP-BASED PORTFOLIOS** -- The following types of securities, listed on NYSE, AMEX, and Nasdaq National Market, are eligible for inclusion in the Cap-Based Indices:
# >
# > - Common Stocks
# > - Certificates
# > - Shares of Beneficial Interest
# > - Units (Depository Units, Units of Beneficial Interest, Units of Limited Partnership Interest, Depository Receipts, etc.)
# > 
# > The following types of securities are NOT eligible for inclusion in the Cap-Based Indices:
# >
# > - ADRs
# > - Closed-End Mutual Funds, WEBS Index Funds, Unit Investment Trusts
# > - All Common Stocks with non-US Incorporation
# > - Americus Trust Components
# > - HOLDRs Trusts
# > - REITs (Real Estate Investment Trusts)
# > - Rights and Warrants
# > - Preferred stock
# > - "Packaged" Units (Common Stocks Bundled with Rights or Warrants)
# > - Over-the-Counter Bulletin Board Issues
# > - N.B. The Cap-Based Indices do include returns from time ranges during which eligible securities trade on "leading prices" or "reorganization" when-issued status. The Cap-Based Indices do NOT include returns from time ranges during which eligible securities trade on "ex-distribution" or "additional" when-issued status.
# > 
# > Note that VWRETD is not computed by WRDS but provided directly by CRSP along with the PERMNO based returns. For general SAS coding help for this problem see the WRDS Research Application: Portfolios by Size and Book-to-Market. This WRDS Support document provides examples of cap-based decile breakdowns, but the same general principles apply to the total market index.
# 
# I've provided code for you that will take care of this subsetting in the function `pull_CRSP_monthly_file`:
# ```
#     SELECT 
#         date,
#         msf.permno, msf.permco, shrcd, exchcd, comnam, shrcls, 
#         ret, retx, dlret, dlretx, dlstcd,
#         prc, altprc, vol, shrout, cfacshr, cfacpr,
#         naics, siccd
#     FROM crsp.msf AS msf
#     LEFT JOIN 
#         crsp.msenames as msenames
#     ON 
#         msf.permno = msenames.permno AND
#         msenames.namedt <= msf.date AND
#         msf.date <= msenames.nameendt
#     LEFT JOIN 
#         crsp.msedelist as msedelist
#     ON 
#         msf.permno = msedelist.permno AND
#         date_trunc('month', msf.date)::date =
#         date_trunc('month', msedelist.dlstdt)::date
#     WHERE 
#         msf.date BETWEEN '{start_date}' AND '{end_date}' AND 
#         msenames.shrcd IN (10, 11, 20, 21, 40, 41, 70, 71, 73)
# ```
# To best understand this, please look up `shrcd` in the Data Manual here: https://wrds-www.wharton.upenn.edu/documents/396/CRSP_US_Stock_Indices_Data_Descriptions.pdf . You'll find the information on p. 81.

# ## Calculation of Equal-Weighted Returns and Value-Weighted Returns
# 
# With the proper universe of stocks in hand, all that is left is to group the returns by `permno` (the identifier of choice here) and average. However, the equal weighted average is a mere simple average. To calculate the value-weighted average, we need to calculate the *lagged* market cap of each stock $i$ at time $t$.
# 
# That is, the value-weighted return is given by the following formula:
# 
# $$
# r_t = \frac{\sum_{i=1}^{N_t} w_{i,t-1} \, r_{i,t}}{\sum_{i=1}^{N_t} w_{i,t-1}}
# $$
# 
# where $w_{i,t-1}$ is the market capitalization of stock $i$ at time $t-1$ and
# $r_t$ can be the returns with dividends `ret` or the returns without dividends `retx`.
# The market capitalization of a stock is its price times the shares outstanding,
# $$
# w_{it} = \text{SHROUT}_{it} \times \text{PRC}_{it}.
# $$

# In[5]:


df_eq_idx = calc_CRSP_indices.calc_equal_weighted_index(df_msf)
df_vw_idx = calc_CRSP_indices.calc_CRSP_value_weighted_index(df_msf)
df_idxs = calc_CRSP_indices.calc_CRSP_indices_merge(df_msf, df_msix)
df_idxs[[ 
    'vwretd', 'vwretx', 'ewretd', 'ewretx',
    'vwretd_manual', 'vwretx_manual', 'ewretd_manual', 'ewretx_manual',]].head()


# In[6]:


df_idxs[[ 
    'vwretd', 'vwretx', 'ewretd', 'ewretx',
    'vwretd_manual', 'vwretx_manual', 'ewretd_manual', 'ewretx_manual',]].corr()


# As you can see above, our manually-created return index doesn't match the CRSP index perfectly but is still very close. In this HW, you'll be required to construct this index only approximately. A loose match, as seen here, will be fine.
# 
# Note, a helpful tool to create the lagged time series for market capitalization is provided in `misc_tools`.
# Use the function `with_lagged_column`, which will create a lagged column that accounts for the fact that multiple stocks show up in a flat file. See the following example:

# In[7]:


a=[
    [1,'1990/1/1',1],
    [1,'1990/2/1',2],
    [1,'1990/3/1',3],
    [2,'1989/12/1',3],
    [2,'1990/1/1',3],
    [2,'1990/2/1',4],
    [2,'1990/3/1',5.5],
    [2,'1990/4/1',5],
    [2,'1990/6/1',6]
    ]
data=pd.DataFrame(a,columns=['id','date','value'])
data['date']=pd.to_datetime(data['date'])
data


# In[8]:


data_lag = misc_tools.with_lagged_columns(data=data, columns_to_lag=['value'], id_columns=['id'], lags=1)
data_lag


# As you can see, naively using `shift` to create our lag would miss the fact that observation `1989-12-01` for stock `id=2` should have a missing lagged `value`. For example, the following would be incorrect:
# 

# In[9]:


data['value'].shift(1)

