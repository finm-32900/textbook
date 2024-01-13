"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""
from doit.tools import run_once
from os import getcwd

import config
from pathlib import Path

# import shutil

OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)
NOTEBOOK_BUILD_DIR = Path(config.OUTPUT_DIR)
# NOTEBOOK_BUILD_DIR = Path("./")


# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
def jupyter_execute_notebook(notebook):
    return f"""jupyter nbconvert --execute --to notebook --inplace {notebook}.ipynb --ClearMetadataPreprocessor.enabled=True --ClearMetadataPreprocessor.preserve_cell_metadata_mask='[("tags")]' --log-level WARN"""
def jupyter_to_html(notebook, output_dir):
    return f"jupyter nbconvert --to html --output-dir='{output_dir}' {notebook}.ipynb --log-level WARN"
def jupyter_to_md(notebook):
    """Requires jupytext"""
    return f"jupytext --to markdown {notebook}.ipynb"
def jupyter_to_python(notebook, notebook_build_dir):
    return f"jupyter nbconvert --to python {notebook}.ipynb --output _{notebook}.py --output-dir {notebook_build_dir} --log-level WARN"
def jupyter_clear_input(notebook, output_dir):
    """Doesn't work right now. I think this only works for other file output types besides .ipynb.
    """
    return f"jupyter nbconvert --to notebook {notebook}.ipynb --output _{notebook}.ipynb --no-input --no-prompt  --output-dir='{output_dir}' --log-level WARN"
def jupyter_clear_output(notebook):
    return f"""jupyter nbconvert --inplace {notebook}.ipynb --ClearMetadataPreprocessor.enabled=True --ClearMetadataPreprocessor.preserve_cell_metadata_mask='[("tags")]' --log-level WARN"""
def copy_notebook_to_folder(notebook, destination_folder):
    destination_path = Path(destination_folder) / f"_{notebook}.ipynb"
    return f"cp  {notebook}.ipynb {destination_path}"
# def copy_notebook_to_folder(notebook_html, destination_folder):
#     notebook = notebook_html.split('.')[0]
#     shutil.copy(Path(f"{notebook}.ipynb"), destination_folder)
#     return True
# fmt: on


def task_pull_data():
    """ """
    file_dep = ["load_fred.py", "load_ofr_api_data.py"]
    file_output = [
        "fred_repo_related_data.parquet",
        "fred_repo_related_data_all.parquet",
        "ofr_public_repo_data.parquet",
    ]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    return {
        "actions": [
            "ipython ./load_fred.py",
            "ipython ./load_ofr_api_data.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }


def task_convert_notebooks_to_scripts():
    """Converts notebooks to .py scripts. This is used for
    version control. Changes to these files trigger execution.
    """

    notebooks = [
        "01_repo_spikes.ipynb",
    ]
    file_dep = notebooks
    stems = [notebook.split(".")[0] for notebook in notebooks]
    targets = [NOTEBOOK_BUILD_DIR / f"_{stem}.py" for stem in stems]

    actions = [
        # *[jupyter_execute_notebook(notebook) for notebook in notebooks_to_run],
        # *[jupyter_to_html(notebook, output_dir) for notebook in notebooks_to_run],
        # *[jupyter_clear_output(notebook) for notebook in stems],
        *[jupyter_to_python(notebook, NOTEBOOK_BUILD_DIR) for notebook in stems],
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
    notebooks_to_run = [
        "01_repo_spikes.ipynb",
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks_to_run]

    file_dep = [
        # Dependers:
        ## 01_repo_spikes.ipynb
        "load_repo_data.py",
        "load_fred.py",
        "load_ofr_api_data.py",
        *[NOTEBOOK_BUILD_DIR / f"_{stem}.py" for stem in stems],
    ]

    targets = [
        ## 01_repo_spikes.ipynb output
        # OUTPUT_DIR / 'is_spike.csv',
        ## Notebooks converted to HTML
        *[OUTPUT_DIR / f"{stem}.html" for stem in stems],
    ]

    actions = [
        *[jupyter_execute_notebook(notebook) for notebook in stems],
        *[copy_notebook_to_folder(notebook, NOTEBOOK_BUILD_DIR) for notebook in stems],
        *[jupyter_to_html(notebook, OUTPUT_DIR) for notebook in stems],
        # *[jupyter_clear_input(notebook, NOTEBOOK_BUILD_DIR) for notebook in stems],
        *[jupyter_clear_output(notebook) for notebook in stems],
        # *[jupyter_to_python(notebook, NOTEBOOK_BUILD_DIR) for notebook in notebooks_to_run],
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
    assets_dir = Path("./assets")
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
