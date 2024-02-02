"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""
import sys
sys.path.insert(1, './src/')


import config
from pathlib import Path
from doit.tools import run_once


OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)

# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
def jupyter_execute_notebook(notebook):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
def jupyter_to_html(notebook, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_md(notebook, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_python(notebook, build_dir):
    """Convert a notebook to a python script"""
    return f"jupyter nbconvert --to python ./src/{notebook}.ipynb --output _{notebook}.py --output-dir {build_dir}"
def jupyter_clear_output(notebook):
    return f"jupyter nbconvert --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
# fmt: on




# # Check if .env file exists. If not, create it by copying from .env.example
# env_file = ".env"
# env_example_file = "env.example"

# if not os.path.exists(env_file):
#     shutil.copy(env_example_file, env_file)


def task_pull_CRSP_Compustat():
    """Pull CRSP/Compustat data from WRDS and save to disk
    """
    file_dep = [
        "./src/config.py", 
        "./src/load_CRSP_stock.py",
        "./src/load_CRSP_Compustat.py",
        ]
    targets = [
        Path(DATA_DIR) / "pulled" / file for file in 
        [
            ## src/load_CRSP_stock.py
            "CRSP_MSF_INDEX_INPUTS.parquet", 
            "CRSP_MSIX.parquet", 
            ## src/load_CRSP_Compustat.py
            "Compustat.parquet",
            "CRSP_stock_ciz.parquet",
            "CRSP_Comp_Link_Table.parquet",
            "FF_FACTORS.parquet",
        ]
    ]

    return {
        "actions": [
            "ipython src/config.py",
            "ipython src/load_CRSP_stock.py",
            "ipython src/load_CRSP_Compustat.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
        "verbosity": 2, # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_calc_Fama_French_1993_factors():
    """Calculate Factors for Fama-French 1993 model
    """
    file_dep = [
        "./src/calc_Fama_French_1993_factors.py",
        "./src/misc_tools.py",
        ]
    targets = [
        *[Path(DATA_DIR) / "pulled" / file for file in 
        [
            ## src/calc_Fama_French_1993_factors.py
            "FF_1993_vwret.parquet",
            "FF_1993_vwret_n.parquet",
            "FF_1993_factors.parquet",
            "FF_1993_nfirms.parquet",
        ]],
        OUTPUT_DIR / "FF_1993_Comparison.png",
    ]

    return {
        "actions": [
            "ipython src/calc_Fama_French_1993_factors.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }


def task_convert_notebooks_to_scripts():
    """Preps the notebooks for presentation format.
    Execute notebooks with summary stats and plots and remove metadata.
    """
    build_dir = Path(OUTPUT_DIR)
    build_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        "01_wrds_python_package.ipynb",
        "02_CRSP_market_index.ipynb",
        "03_Fama_French_1993.ipynb",
    ]
    file_dep = [Path("./src") / file for file in notebooks]
    stems = [notebook.split(".")[0] for notebook in notebooks]
    targets = [build_dir / f"_{stem}.py" for stem in stems]

    actions = [
        # *[jupyter_execute_notebook(notebook) for notebook in notebooks_to_run],
        # *[jupyter_to_html(notebook) for notebook in notebooks_to_run],
        # *[jupyter_clear_output(notebook) for notebook in stems],
        *[jupyter_to_python(notebook, build_dir) for notebook in stems],
    ]
    return {
        "actions": actions,
        "targets": targets,
        "task_dep": [],
        "file_dep": file_dep,
        "clean": True,
    }


def task_run_notebooks():
    """Preps the notebooks for presentation format.
    Execute notebooks with summary stats and plots and remove metadata.
    """
    notebooks_to_run_as_md = [
        "01_wrds_python_package.ipynb",
        "02_CRSP_market_index.ipynb",
        "03_Fama_French_1993.ipynb",
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks_to_run_as_md]

    file_dep = [
        # 'load_other_data.py',
        *[Path(OUTPUT_DIR) / f"_{stem}.py" for stem in stems],
    ]

    targets = [
        ## Notebooks converted to HTML
        *[OUTPUT_DIR / f"{stem}.html" for stem in stems],
    ]

    actions = [
        *[jupyter_execute_notebook(notebook) for notebook in stems],
        *[jupyter_to_html(notebook) for notebook in stems],
        # *[jupyter_clear_output(notebook) for notebook in stems],
        # *[jupyter_to_python(notebook, build_dir) for notebook in notebooks_to_run],
    ]
    return {
        "actions": actions,
        "targets": targets,
        "task_dep": [],
        "file_dep": file_dep,
        "clean": True,
    }


def task_copy_notebook_assets():
    """Copy all files from ./src/assets to OUTPUT_DIR / 'assets'"""
    assets_dir = Path("./src/assets")
    assets = [file for file in assets_dir.glob("*") if file.is_file()]

    ## if OUTPUT_DIR / "assets" doesn't exist, create it
    (OUTPUT_DIR / "assets").mkdir(parents=True, exist_ok=True)

    targets = [OUTPUT_DIR / "assets" / file.name for file in assets]
    return {
        "actions": [f"cp {asset} {OUTPUT_DIR / 'assets'}" for asset in assets],
        "targets": targets,
        "file_dep": assets,
        "clean": True,
    }