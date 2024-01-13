#!/usr/bin/env python
# coding: utf-8

# # Rate Spikes in the Market for Repurchase Agreements
# 
# 
# ## What is the role of the repo market and why is it important?
# 
# The market for repurchase agreements, commonly known as the repo market,
# serves as a cornerstone for short-term financing among financial institutions.
# This market enables entities, including banks, dealers, money market funds,
# insurance companies, pension funds, and other entities, to obtain liquidity on
# an overnight basis or for other short tenures, thereby ensuring operational
# continuity.  Its collateralized nature minimizes credit risk, making it a
# preferred avenue for secure, short-term lending and borrowing. 
# 
# Moreover, the repo market is critical in implementing monetary policy, especially considering the diminished role of the unsecured interbank market compared to the secured market following the 2007-2008 financial crisis. Its central role in providing liquidity and facilitating monetary policy execution underscores the necessity of the repo market's efficient functioning for financial stability and the broader economy. Disruptions within this market can have widespread impacts, affecting various financial participants, including banks, money market funds, hedge funds, and corporations.
# 

# ## What is a repurchase agreement?
# 
# A repurchase agreement, often referred to as a repo, is a form of short-term borrowing mainly used in the money markets.
# A repurchase agreement can be visualized as follows. The following Figure is from *Fixed Income Securities*, by Veronsi.
# This demonstrates a trader purchasing a bond in the market and financing the purchase via a repurchase agreement.
# 
# ![](./assets/hw01_repo_diagram_veronesi.png)
# 
# ### At Time $t$
# 
# 1. **Choosing Bond to Finance**:
#    - The **TRADER** initiates the transaction by purchasing a bond from the **MARKET** at a price $P_t$.
#    - The **TRADER** then agrees to sell this bond to the **REPO DEALER** while simultaneously agreeing to repurchase it at a future date for a predetermined price.
# 
# 2. **Exchange of Bond for Cash**:
#    - The **TRADER** delivers the bond to the **REPO DEALER**.
#    - In return, the **REPO DEALER** pays the **TRADER** an amount equal to $P_t$ minus a "haircut." The haircut is a discount on the bond's value, which serves as a protection for the dealer against the risk of the bond's price decline.
# 
# ### At Time $T = t + n \text{ days}$
# 
# 3. **Repurchase of the Bond**:
#    - At the end of the repo term, the **TRADER** repurchases the bond from the **REPO DEALER**.
#    - The repurchase price is calculated as $(P_t - \text{haircut}) \times \left(1 + \frac{\text{repo rate} \times n}{360}\right)$, where the repo rate is the interest rate agreed upon for the repo, and $n$ is the number of days the repo agreement lasts.
# 
# 4. **Unwinding Bond Financing**:
#    - The **TRADER** pays the calculated repurchase price to the **REPO DEALER** and receives the bond back.
#    - If the **TRADER** does not refinance the bond, the **TRADER** sells the bond back to the **MARKET** for a price of $P_T$.
# 
# The repo transaction allows the **TRADER** to obtain short-term financing by temporarily transferring a security to a **REPO DEALER** in exchange for cash, with the agreement to buy back the security at a later date for a slightly higher price, the difference being equivalent to the interest on the loan. The repo rate effectively acts as the interest rate on the cash borrowed by the **TRADER**.
# 
# In quantitative finance, repos are commonly used to raise short-term capital. They are also used for leveraged trades and managing liquidity. Repos are secured loans because they involve the transfer of securities; they are usually seen as low-risk instruments because the terms of the transaction are secured by the collateral, which is the bond in this case. That said, they can be used to create highly levered positions which are not low risk.

# 
# The haircut on the repo pins down the maximum amount of leverage that can be obtained with the repo. Such a position is highly risky.
# 
# $$
# \text{Repo interest} = \frac{n}{360} \times \text{Repo rate} \times (P_t - \text{haircut})
# $$
# and
# $$
# \text{Return on capital for TRADER} = \frac{P_T - P_t - \text{Repo interest}}{\text{Haircut}}
# $$
# 
# Consider some back-of-the-envelop calculations within a highly simplified 2-period model to demonstrate this:
# 
# **Example 1:**
# No leverage, interest rates go down from 4\% to 3\%
# 
# $$Ret = (97 – 92 – 4)/92 = 1.1\%$$
# 
# **Example 2:**
# Full leverage, interest rates go down from 4\% to 3\%
# 
# $$Ret = (97 – 92 – 4)/(92*0.02) = 54\%$$
# 
# **Example 3:**
# Full leverage, interest rates go up from 4\% to 5\%
# 
# $$Ret = (95 – 92 – 4)/(92*0.02) = -54\%$$
# 

# ## Money market dislocations and the repo rate spikes of 2018-2019
# 
# Repo rates are the interest rates at which financial institutions borrow or lend funds via repurchase agreements (repos). In recent years, there have been several notable spikes in these rates. The most significant spike occurred in September 2019, although smaller spikes also occurred throughout 2018 and 2019. A repo spike refers to a sudden, substantial increase in repo rates within the financial market. These spikes indicate an abrupt imbalance in the supply and demand for funds in the repo market, leading to an increase in borrowing costs. Such spikes can disrupt the financial system and may signal deeper issues related to liquidity and funding stress.
# 
# Additionally, these rate spikes can be seen as dislocations in the money markets. Specifically, these repo spikes represented significant deviations between repo rates and the interest on reserve balances or the Federal Reserve's Overnight Reverse Repo Facility rate (ON/RRP rate). These dislocations imply potential arbitrage opportunities, suggesting that institutions capable of earning interest on reserves or with access to the Fed's ON/RRP facility should theoretically show no preference between using these facilities and lending in the repo markets. Since lending in repo markets typically involves overcollateralization with Treasury securities and occurs overnight, repo market rates should align closely with other near risk-free rates. Understanding the causes of these deviations is crucial for grasping their implications for the financial sector.
# 
# ## Relationship to Quantitative Investors
# 
# See here: https://www.bloomberg.com/news/articles/2023-12-20/inside-the-basis-trade-hedge-fund-traders-dominate-gigantic-bond-bet
# 
# ![The Hedge Fund Traders Dominating a Massive Bet on Bonds](./assets/hw01_basis_hf.png)
# 
# And here: https://www.bloomberg.com/opinion/articles/2024-01-08/the-fed-won-t-do-slow-and-steady-if-the-labor-market-wobbles
# 
# ![Year-End Money-Markets Angst on Fed Exit Echoes 2018 Crunch](./assets/hw01_repo_vol.png)
# 
# What is a basis trade. From this [Reuters article](https://www.reuters.com/markets/us/fed-economists-sound-alarm-hedge-funds-gaming-us-treasuries-2023-09-13/), they say:
# 
# > Hedge funds' short positions in some Treasuries futures - contracts for the purchase and sale of bonds for future delivery - have recently hit record highs as part of so-called basis trades, which take advantage of the premium of futures contracts over the price of the underlying bonds, analysts have said.
# >
# > The trades - typically the domain of macro hedge funds with relative value strategies - consist of selling a futures contract, buying Treasuries deliverable into that contract with repurchase agreement (repo) funding, and delivering them at contract expiry.
# 
# The involvement of hedge funds and other asset management companies in this space have receive a lot of attention recently. Some examples:
# 
#  - [Citadel’s Ken Griffin warns against hedge fund clampdown to curb basis trade risk](https://www.ft.com/content/927aba63-eff3-44c4-a5df-a5872e988720)
#  - [Taming the Treasury basis trade](https://www.ft.com/content/6a752818-3f05-45da-a6f9-c752710d0a9f)
#  - [Citadel and Its Peers Are Piling Into the Same Trades. Regulators Are Taking Notice](https://www.bloomberg.com/news/articles/2023-11-30/ken-griffin-s-citadel-hedge-fund-rivals-draw-scrutiny-over-crowding-leverage)
#  - [Fed's reverse repo facility drawdown looms large in balance sheet debate](https://www.reuters.com/markets/us/feds-reverse-repo-facility-drawdown-looms-large-balance-sheet-debate-2023-10-31/)
#  - [Fed economists sound alarm on hedge funds gaming US Treasuries](https://www.reuters.com/markets/us/fed-economists-sound-alarm-hedge-funds-gaming-us-treasuries-2023-09-13/)
# 
# ## Understanding Repo Markets Are Important to Understanding the Risks involved in this Trade 
# 
# In this homework assignment, we'll create some charts to better understand this market. I also recommend reading this paper, [Kahn et al (2023). "Anatomy of the Repo Rate Spikes in September 2019." Journal of Financial Crises 5, no. 4 (2023): 1-25.](https://elischolar.library.yale.edu/journal-of-financial-crises/vol5/iss4/1/)
# 
# We'll replicate Figure 1 from this paper. 

# In[1]:


import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

import load_repo_data


# In[2]:


from pathlib import Path
import config

OUTPUT_DIR = Path(config.output_dir)
DATA_DIR = Path(config.data_dir)


# ## Repo Rates and Fed Funds Rates
# Replicate Figure 1 from "Anatomy of the Repo Rate Spikes"

# In[3]:


load_repo_data.series_descriptions


# In[4]:


new_labels = {
    'REPO-TRI_AR_OO-P':'Tri-Party Overnight Average Rate',
    'RRPONTSYAWARD': 'ON-RRP facility rate',
    'Gen_IORB': 'Interest on Reserves', # This series uses FRED's Interest on 
    # Reserve Balances series. However, this doesn't go back very far, so it is
    # backfilled with interest on excess reserves when necessary.
}


# In[5]:


df = load_repo_data.load_all(data_dir = DATA_DIR)


# The following plot show the effective fed funds rate (from FRED), the tri-party overnight average rate (from the OFR series `REPO-TRI_AR_OO-P`), and the shaded region shows the lower and upper limit of the federal funds target range (`DFEDTARL` and `DFEDTARU`).

# In[6]:


fig, ax = plt.subplots()
ax.fill_between(df.index, df['DFEDTARU'], df['DFEDTARL'], alpha=0.5)
df[['REPO-TRI_AR_OO-P', 'EFFR']].rename(columns=new_labels).plot(ax=ax)


# In the following plot, we zoom in a little to see just how large these spikes were.

# In[7]:


fig, ax = plt.subplots()
date_start = '2014-Aug'
date_end = '2019-Dec'
_df = df.loc[date_start:date_end, :]
ax.fill_between(_df.index, _df['DFEDTARU'], _df['DFEDTARL'], alpha=0.5)
_df[['REPO-TRI_AR_OO-P', 'EFFR']].rename(columns=new_labels).plot(ax=ax)
# plt.ylim(-0.2, 1.0)


# Normalize rates to be centered at the fed funds target window midpoint.

# In[8]:


df_norm = df.copy()
df['target_midpoint'] = (df['DFEDTARU'] + df['DFEDTARL'])/2
for s in ['DFEDTARU', 'DFEDTARL', 'REPO-TRI_AR_OO-P', 
          'EFFR', 'target_midpoint', 
          'Gen_IORB', 'RRPONTSYAWARD', 'SOFR']:
    df_norm[s] = df[s] - df['target_midpoint']


# Now, plot the series that is normalized by the fed funds target midpoint.

# In[9]:


fig, ax = plt.subplots()
date_start = '2014-Aug'
date_end = '2019-Dec'
_df = df_norm.loc[date_start:date_end, :]
ax.fill_between(_df.index, _df['DFEDTARU'], _df['DFEDTARL'], alpha=0.2)
_df[['REPO-TRI_AR_OO-P', 'EFFR']].rename(columns=new_labels).plot(ax=ax)
plt.ylim(-0.4, 1.0)
plt.ylabel("Spread of federal feds target midpoint (percent)")
arrowprops = dict( 
    arrowstyle = "->"
)
ax.annotate('Sep. 17, 2019: 3.06%', 
            xy=('2019-Sep-17', 0.95), 
            xytext=('2017-Oct-27', 0.9),
            arrowprops = arrowprops);


# Now, let's consider interest on reserves as well as the ON-RRP rate, as these in theory put bounds on the repo rate.

# In[10]:


fig, ax = plt.subplots()
date_start = '2014-Aug'
date_end = '2019-Dec'
_df = df_norm.loc[date_start:date_end, :].copy()

ax.fill_between(_df.index, _df['DFEDTARU'], _df['DFEDTARL'], alpha=0.2)
_df[['REPO-TRI_AR_OO-P', 'EFFR', 'Gen_IORB', 'RRPONTSYAWARD']].rename(columns=new_labels).plot(ax=ax)
plt.ylim(-0.4, 1.0)
plt.ylabel("Spread of federal feds target midpoint (percent)")
arrowprops = dict( 
    arrowstyle = "->"
)
ax.annotate('Sep. 17, 2019: 3.06%', 
            xy=('2019-Sep-17', 0.95), 
            xytext=('2017-Oct-27', 0.9),
            arrowprops = arrowprops);


# In[11]:


fig, ax = plt.subplots()
date_start = '2018-Apr'
date_end = None
_df = df_norm.loc[date_start:date_end, :].copy()

ax.fill_between(_df.index, _df['DFEDTARU'], _df['DFEDTARL'], alpha=0.1)
_df[['SOFR', 'EFFR', 'Gen_IORB', 'RRPONTSYAWARD']].rename(columns=new_labels).plot(ax=ax)
plt.ylim(-0.4, 1.0)
plt.ylabel("Spread of federal feds target midpoint (percent)")
arrowprops = dict( 
    arrowstyle = "->"
)
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
# ax.annotate('Sep. 17, 2019: 3.06%', 
#             xy=('2019-Sep-17', 0.95), 
#             xytext=('2015-Oct-27', 0.9),
#             arrowprops = arrowprops);


# In[12]:


fig, ax = plt.subplots()
date_start = '2023-Jul'
date_end = None
_df = df_norm.loc[date_start:date_end, :].copy()

ax.fill_between(_df.index, _df['DFEDTARU'], _df['DFEDTARL'], alpha=0.1)
_df[['SOFR', 'EFFR', 'Gen_IORB', 'RRPONTSYAWARD']].rename(columns=new_labels).plot(ax=ax)
plt.ylim(-0.4, 1.0)
plt.ylabel("Spread of federal feds target midpoint (percent)")
arrowprops = dict( 
    arrowstyle = "->"
)
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
# ax.annotate('Sep. 17, 2019: 3.06%', 
#             xy=('2019-Sep-17', 0.95), 
#             xytext=('2015-Oct-27', 0.9),
#             arrowprops = arrowprops);


# In[13]:


df['SOFR-IORB'] = df['SOFR'] - df['Gen_IORB']
df.loc['2018':'2020', ['SOFR-IORB']].plot()


# In[14]:


df.loc['2018':, ['SOFR-IORB']].plot()


# # Understanding this plot
# 
# Now, let's spend some time trying to understand this plot. 
# 
# ## Reserve Levels vs Spikes
# First of all, depository intitutions have a choice between keeping their reserves at the Fed and earning interest on reserve balances or lending the money into repo. When the repo rates were spiking in 2018 and 2019, I would imagine that total reserve levels would be low.

# In[15]:


df['net_fed_repo'] = (df['RPONTSYD'] - df['RRPONTSYD']) / 1000
df['triparty_less_fed_onrrp_rate'] = (df['REPO-TRI_AR_OO-P'] - df['RRPONTSYAWARD']) * 100
df['total reserves / currency'] = df['TOTRESNS'] / df['CURRCIR']


# In[16]:


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
df[['TOTRESNS']].rename(
    columns=load_repo_data.series_descriptions
).plot(ax=ax1,color='g')
ax1.set_ylabel('$ Billions')
ax2.set_ylabel('Basis Points')
ax1.legend(loc='center left', bbox_to_anchor=(1, 1.1))
df[['triparty_less_fed_onrrp_rate']].rename(
    columns={'triparty_less_fed_onrrp_rate':'Tri-Party - Fed ON/RRP Rate'}
).plot(ax=ax2)
ax2.legend(loc='center left', bbox_to_anchor=(1, 1));


# Now, let's normalize by currency in circulation, so as to account for the normal growth in the economy or the financial system. This is done because total reserves is not stationary.

# In[17]:


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
df[['total reserves / currency']].plot(ax=ax1,color='g')
df[['triparty_less_fed_onrrp_rate']].rename(
    columns={'triparty_less_fed_onrrp_rate':'Tri-Party - Fed ON/RRP Rate'}
).plot(ax=ax2)
ax1.set_ylabel('Ratio')
ax2.set_ylabel('Basis Points')
ax1.legend(loc='center left', bbox_to_anchor=(1, 1.1))
ax2.legend(loc='center left', bbox_to_anchor=(1, 1));
# Total Reserves held by depository institutions, divided by currency in circulation


# ## Fed Repo and Reverse Repo Facility Takeup

# In[18]:


df[['RPONTSYD','RRPONTSYD']].rename(
    columns=load_repo_data.series_descriptions
).plot(alpha=0.5)


# In[19]:


# Net Fed Repo Lending (positive is net lending by the Fed.
# Negative is the use of the reverse repo facility.)
df[['net_fed_repo']].plot()
plt.ylabel('$ Trillions');


# In[20]:


# TODO
# # Net Fed Repo Lending (positive is net lending by the Fed.
# # Negative is the use of the reverse repo facility.)
# df.loc['2023',['net_fed_repo']].plot()
# plt.ylabel('$ Trillions');


# In[21]:


df[['net_fed_repo', 'triparty_less_fed_onrrp_rate']].plot()
plt.ylim([-50,100])


# The Fed is lending money when the repo rate is spiking. When the repo rate is low relative to the ON/RRP rate, usage of the ON/RRP facility goes up, as can be seen here.

# In[22]:


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
df[['net_fed_repo']].plot(ax=ax1,color='g')
df[['triparty_less_fed_onrrp_rate']].plot(ax=ax2)


# # How should we define a repo spike?
# 
# Now, I turn to the question of how to define a repo rate spike. 
# 
# ## Fed Fund's Target Range
# 
# The first way to approach this is to just look at when the triparty rate exceeded the upper bound of the fed's federal funds rate target range.

# **Tri-Party Ave vs Fed Upper Limit**

# In[23]:


df['is_tri_above_fed_upper'] = df['REPO-TRI_AR_OO-P'] > df['DFEDTARU']


# In[24]:


df.index[df['is_tri_above_fed_upper']]


# In[25]:


len(df.index[df['is_tri_above_fed_upper']])


# **SOFR vs Fed Upper Limit**

# In[26]:


df['is_SOFR_above_fed_upper'] = df['SOFR'] > df['DFEDTARU']
len(df.index[df['is_SOFR_above_fed_upper']])


# In[27]:


df.index[df['is_SOFR_above_fed_upper']]


# **SOFR vs Interest of Reserves**
# 
# This measure is good because it represents a kind of arbitrage opportunity. Either leave money at Fed to earn interest, or put money into repo market. This is what the paper, "Reserves were not so amply after all" uses.

# In[28]:


df[['SOFR-IORB']].dropna(how='all').plot()


# In[29]:


df['is_SOFR_above_IORB'] =df['SOFR-IORB'] > 0
len(df.index[df['is_SOFR_above_IORB']])


# In[30]:


df.index[df['is_SOFR_above_IORB']]


# Now, let's ask if it's 2 standard deviations above IORB

# In[31]:


df['SOFR-IORB'].std()


# In[32]:


df['is_SOFR_2std_above_IORB'] = df['SOFR-IORB'] > 2 * df['SOFR-IORB'].std()
len(df.index[df['is_SOFR_2std_above_IORB']])


# In[33]:


df.index[df['is_SOFR_2std_above_IORB']]


# In[34]:


df['SOFR-IORB'].mean()


# In[35]:


df.index[df['is_SOFR_2std_above_IORB']].intersection(df.index[df['is_SOFR_above_fed_upper']])


# In[36]:


len(df.index[df['is_SOFR_2std_above_IORB']].intersection(df.index[df['is_SOFR_above_fed_upper']]))


# In[37]:


# filedir = Path(OUTPUT_DIR)
# df[
#     ['is_SOFR_above_fed_upper', 'is_SOFR_2std_above_IORB', 
#     'is_SOFR_above_IORB', 'is_tri_above_fed_upper']
#   ].to_csv(filedir / 'is_spike.csv')


# # Summary Stats about Various Repo Rates

# In[38]:


df.info()


# I don't include GCF in this first comparison, because it has a lot of missing values. I want to only compare values for which all rates are non-null. That's why I drop the whole row when any rate is missing.
# 
# Here, we see that DVP average is lower than Triparty average. SOFR is closer to triparty, but is still lower. This is because SOFR tries to remove specials.
# 
# Notice, however, that this is different when comparing the 75% percentiles. SOFR is higher than triparty and DVP is even higher.

# In[39]:


df[['SOFR', 'REPO-TRI_AR_OO-P', 'REPO-DVP_AR_OO-P']].dropna().describe()


# Now, I include GCF. It appears that GCF is the highest. Borrow low at tri-party, lend higher into SOFR (but lower to specials) and lend highest to GCF.

# In[40]:


df[['SOFR', 'REPO-TRI_AR_OO-P', 'REPO-DVP_AR_OO-P', 'REPO-GCF_AR_OO-P']].dropna().describe()

