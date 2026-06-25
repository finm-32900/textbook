# Week 2: Virtual Environments, WRDS, and CRSP

```{toctree}
:maxdepth: 1
Week2/WRDS_intro_and_web_queries.md
notebooks/_01_wrds_python_package_ipynb.ipynb
notebooks/_05_basics_of_SQL_ipynb.ipynb
Week2/env_files.md
```


## Announcements

- **Final Project Partners**: Start thinking about who you'd like to partner with for the final project. I will post the project options later this week. Projects will be completed in pairs.


## Catch-up from Week 1

We didn't get to everything last week, so we'll start by closing those gaps.

- **In-class examples repo**: Clone <https://github.com/finm-32900/inclass_examples> and take a quick tour. This holds the small, self-contained demos we'll draw on all quarter (virtual environments, env vars, PyDoit, Sphinx, polars, WRDS/Datastream, SQL, LaTeX).
- **Virtual Environments**: See [Virtual Environments](./Week1/virtual_environments.md).
  - *Why we care:* I'm going to hand you a series of repositories this quarter, each with its own `requirements.txt` / `environment.yml`. The whole point of pinning dependencies is **reproducibility**---so that you can install the same software versions I used and reproduce my results exactly. Differences in package versions (and in how data gets pulled) are a common, hard-to-debug source of mismatched results.
  - We'll work through `software_environments/` in the in-class repo, which builds the same small app four ways: `conda`, `conda` + `pip`, `uv`, and `pixi`.


## Objectives

The main event this week: get you pulling data from **WRDS**---specifically **CRSP** (Center for Research in Security Prices)---and use it to **reconstruct the S&P 500 index** from its constituents. That exercise *is* HW 1.

- Motivate the platform we'll use for data all quarter: **WRDS**.
  - [Introduction to WRDS and WRDS Web Queries](./Week2/WRDS_intro_and_web_queries.md). Web queries are a good way to explore the data before we automate.
- **`.env` files and secrets**: Where your WRDS credentials live, and how to keep them out of your code and out of Git. See [Env Files](./Week2/env_files.md). (See also `env_vars/` in the in-class repo.)
- **Automating the data pull**: [Demo of the WRDS Python package](./notebooks/_01_wrds_python_package_ipynb.ipynb).
  - In the past, the first HW had students manually download data, and differences in those manual steps were a common source of error. This week we learn to automate the download so everyone starts from the same data.
- **Basics of SQL**: Enough SQL to query CRSP and make simple joins in our queries. See [Basics of SQL](./notebooks/_05_basics_of_SQL_ipynb.ipynb).
- Discuss [HW 1](./HW1.md):
  - Part 1: GitHub Skills---[review pull requests](https://github.com/skills/review-pull-requests) and [resolve merge conflicts](https://github.com/skills/resolve-merge-conflicts).
  - Part 2: Replicate the CRSP market index, then **reconstruct the S&P 500 index** from its constituents.
    - [HW Guide Part A: CRSP Market Returns Indices](./notebooks/_02_CRSP_market_index_ipynb.ipynb)
    - [HW Guide Part B: Reconstructing the S&P 500 Index](./notebooks/_03_SP500_constituents_and_index_ipynb.ipynb)
  - Workflow reminder: run `doit` first to pull the data, then run `pytest` and fill in the missing code to make the tests pass.


## Looking ahead to Week 3

Next week we extend this to the **Fama-French 1993** replication ([HW 2](./HW2.md)): merging **CRSP with Compustat**, constructing the factors, and then publishing results---tearsheets and **GitHub Pages**---once we have factor loadings worth reporting.
