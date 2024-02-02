#!/usr/bin/env python
# coding: utf-8

# # Example: Connecting to the WRDS Platform With Python
# 
# 
# The `wrds` Python package is a tool designed to facilitate data retrieval from the Wharton Research Data Services (WRDS) database. 
#  
# - It provides direct access to the WRDS database, allowing users to programmatically query and retrieve data. 
# - The package supports a simple Python API as well as the ability to send raw SQL queries.
# - Retrieved data can be easily converted into Pandas DataFrames.
# - Secure access to the WRDS database is managed through user authentication, ensuring data security and compliance with usage policies.
# 
# ## Installation
# 
# The package can be installed via pip:
# 
# ```
# pip install wrds
# ```
# 
# To use the package, one would typically import it in Python, authenticate with WRDS credentials, and then proceed with data queries and analysis. This notebook walks through some of these basic features.
# 
# ## Usage
# 
# Here are some helpful links to learn how to use the `wrds` Python package:
# 
#  - [Video: Using Python on the WRDS Platform](https://wrds-www.wharton.upenn.edu/pages/grid-items/using-python-wrds-platform/)
#  - [PyPI Homepage for WRDS Python Package](https://pypi.org/project/wrds/)
#  - [WRDS Guide: Querying WRDS Data using Python](https://wrds-www.wharton.upenn.edu/pages/support/programming-wrds/programming-python/querying-wrds-data-python/)
#  - [WRDS Python Package Demo Walkthrough](https://wrds-www.wharton.upenn.edu/documents/1443/wrds_connection.html)
# 
# 
# ### Import and Establish Connection
# 
# Establish connection with WRDS server. 
# Log in using your WRDS username and password.
# Set up a `pgpass` file to store the info. This will allow you to access WRDS without supplying your password each time, as long as you supply your username (which we are doing below via environment variables). We want to be able to access WRDS without a password so that we can automate the query.

# In[1]:


import config
from pathlib import Path
OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME

import wrds


# In[2]:


db = wrds.Connection(wrds_username=WRDS_USERNAME)


# In[3]:


# The `obs` keyword argument limits the number of rows returned.
# You can omit it to get all rows.
df = db.get_table(library='crsp', table='msf', columns=['cusip', 'permno', 'date', 'shrout', 'prc', 'ret', 'retx'], obs=10)
df


# ## Exploring the Data
# 
# As described [here](https://wrds-www.wharton.upenn.edu/pages/support/programming-wrds/programming-python/querying-wrds-data-python/), 
# 
# > Data at WRDS is organized in a hierarchical manner by vendor (e.g. crsp), referred to at the top-level as libraries. Each library contains a number of component tables or datasets (e.g. dsf) which contain the actual data in tabular format, with column headers called variables (such as date, askhi, bidlo, etc).
# > 
# > You can analyze the structure of the data through its metadata using the wrds module, as outlined in the following steps:
# >
# > - List all available libraries at WRDS using list_libraries()
# > - Select a library to work with, and list all available datasets within that library using list_tables()
# > - Select a dataset, and list all available variables (column headers) within that dataset using describe_table()
# >
# > **NOTE:** When referencing library and dataset names, you must use all lowercase.
# >
# > Alternatively, a comprehensive list of all WRDS libraries is available at the Dataset List. This resource provides a listing of each library, their component datasets and variables, as well as a tabular database preview feature, and is helpful in establishing the structure of the data you're looking for in an easy manner from a Web browser.
# >
# > 1. Determine the libraries available at WRDS:

# In[4]:


sorted(db.list_libraries())[0:10]


# > This will list all libraries available at WRDS in alphabetical order. Though all libraries will be shown, you must have a valid, current subscription for a library in order to access it via Python, just as with SAS or any other supported programming language at WRDS. You will receive an error message indicating this if you attempt to query a table to which your institution does not have access.
# >
# > 2. To determine the datasets within a given library:

# In[5]:


db.list_tables(library="crsp")[0:10]


# > Where 'library; is a dataset, such as crsp or comp, as returned from step 1 above.
# >
# > 3. To determine the column headers (variables) within a given dataset:

# In[6]:


db.describe_table(library="crsp", table="msf")


# > Where 'library' is a dataset such as crsp as returned from #1 above and 'table' is a component database within that library, such as msf, as returned from query #2 above. Remember that both the library and the dataset are case-sensitive, and must be all-lowercase.
# >
# > Alternatively, a comprehensive list of all WRDS libraries is available via the WRDS Dataset List. This online resource provides a listing of each library, their component datasets and variables, as well as a tabular database preview feature, and is helpful in establishing the structure of the data you're looking for in an easy, web-friendly manner.
# >
# > By examining the metadata available to us -- the structure of the data -- we've determined how to reference the data we're researching, and what variables are available within that data. We can now perform our actual research, creating data queries, which are explored in depth in the next section.

# ## Querying WRDS Data
# 
# Continue the walkthrough provided here: https://wrds-www.wharton.upenn.edu/pages/support/programming-wrds/programming-python/querying-wrds-data-python/

# ### Using `get_table`

# In[7]:


# The `obs` keyword argument limits the number of rows returned.
# You can omit it to get all rows.
df = db.get_table(library='crsp', table='msf', columns=['cusip', 'permno', 'date', 'shrout', 'prc', 'ret', 'retx'], obs=10)
df


# ### Using `raw_sql`

# In[8]:


df = db.raw_sql(
    """
    SELECT
        cusip, permno, date, shrout, prc, ret, retx
    FROM 
        crsp.msf
    LIMIT 10
    """,
    date_cols=['date']
    )
df


# In[9]:


df = db.raw_sql(
    """
    SELECT 
        a.gvkey, a.datadate, a.tic, a.conm, a.at, a.lt, b.prccm, b.cshoq
    FROM 
        comp.funda a
    JOIN 
        comp.secm b ON a.gvkey = b.gvkey AND a.datadate = b.datadate
    WHERE 
        a.tic = 'IBM' AND 
        a.datafmt = 'STD' AND 
        a.consol = 'C' AND 
        a.indfmt = 'INDL'
    LIMIT 10
    """
)
df


# In[10]:


params = {"tickers": ("0015B", "0030B", "0032A", "0033A", "0038A")}
df = db.raw_sql(
    """
    SELECT 
        datadate, gvkey, cusip 
    FROM comp.funda 
    WHERE 
        tic IN %(tickers)s
    LIMIT 10
    """,
    params=params,
)
df


# ### Misc

# In[11]:


data = db.get_row_count('djones', 'djdaily')
data


# In[12]:


db.close()

