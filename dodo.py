"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""

import sys
from os import environ
from pathlib import Path

sys.path.insert(1, "./src/")

import shutil

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))
GITHUB_PAGES_REPO_DIR = Path(config("GITHUB_PAGES_REPO_DIR"))

OS_TYPE = config("OS_TYPE")

## Helpers for handling Jupyter Notebook tasks
# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
def jupyter_execute_notebook(notebook):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --log-level WARN --inplace ./src/{notebook}.ipynb"
def jupyter_to_html(notebook, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --log-level WARN --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_md(notebook, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --log-level WARN --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_python(notebook, build_dir):
    """Convert a notebook to a python script"""
    return f"jupyter nbconvert --log-level WARN --to python ./src/{notebook}.ipynb --output _{notebook}.py --output-dir {build_dir}"
def jupyter_clear_output(notebook):
    return f"jupyter nbconvert --log-level WARN --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
# fmt: on


def copy_file(origin_path, destination_path, mkdir=True):
    """Create a Python action for copying a file."""

    def _copy_file():
        origin = Path(origin_path)
        dest = Path(destination_path)
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, dest)

    return _copy_file


def copy_directory(source_dir: Path, dest_dir: Path) -> bool:
    """Copy a directory and its contents to a destination path.

    Args:
        source_dir: Path to the source directory
        dest_dir: Path to the destination directory

    Returns:
        bool: True if copy was successful
    """
    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
    return True


def copy_notebook_to_folder(notebook_stem, origin_folder, destination_folder):
    origin_path = Path(origin_folder) / f"{notebook_stem}.ipynb"
    destination_path = Path(destination_folder) / f"_{notebook_stem}.ipynb"
    shutil.copy2(origin_path, destination_path)


##################################
## Begin rest of PyDoit tasks here
##################################


def task_config():
    """Create empty directories for data and output if they don't exist"""
    return {
        "actions": ["ipython ./src/settings.py"],
        "targets": [
            DATA_DIR,
            OUTPUT_DIR,
            Path("_docs"),
            Path("_docs/notebooks"),
            Path("_docs/notebooks/assets"),
        ],
        "file_dep": ["./src/settings.py"],
    }


def task_doit_repo_spikes():
    """Run repo spikes dodo"""
    notebooks = ["01_repo_spikes.ipynb"]
    stems = [notebook.split(".")[0] for notebook in notebooks]
    return {
        "actions": [
            "doit -f ../case_study_repo_spikes/dodo.py",
            *[
                (
                    copy_notebook_to_folder,
                    (
                        notebook,
                        Path("../case_study_repo_spikes/_output"),
                        Path("_docs/notebooks"),
                    ),
                )
                for notebook in stems
            ],
            (
                copy_directory,
                (
                    Path("../case_study_repo_spikes/src/assets"),
                    Path("_docs/notebooks") / "assets",
                ),
            ),
        ],
        "targets": [Path("_docs/notebooks") / "_01_repo_spikes.ipynb"],
        "verbosity": 2,
    }


def task_doit_atlanta_fed_wage_growth():
    """Run atlanta fed wage growth tracker dodo"""
    notebooks = ["01_wage_growth_during_the_recession.ipynb"]
    stems = [notebook.split(".")[0] for notebook in notebooks]
    return {
        "actions": [
            "doit -f ../case_study_wage_growth/dodo.py",
            *[
                (
                    copy_notebook_to_folder,
                    (
                        notebook,
                        Path("../case_study_wage_growth/_output"),
                        Path("_docs/notebooks"),
                    ),
                )
                for notebook in stems
            ],
            (
                copy_directory,
                (
                    Path("../case_study_wage_growth/src/assets"),
                    Path("_docs/notebooks") / "assets",
                ),
            ),
        ],
        "targets": [
            Path("_docs/notebooks") / "_01_wage_growth_during_the_recession.ipynb"
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_doit_fama_french():
    """Run fama french dodo"""
    notebooks = [
        "01_wrds_python_package.ipynb",
        "02_CRSP_market_index.ipynb",
        "03_SP500_constituents_and_index.ipynb",
        "04_Fama_French_1993.ipynb",
        "05_basics_of_SQL.ipynb",
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks]

    return {
        "actions": [
            "doit -f ../case_study_wrds_fama_french/dodo.py",
            *[
                (
                    copy_notebook_to_folder,
                    (
                        notebook,
                        "../case_study_wrds_fama_french/_output",
                        Path("_docs/notebooks"),
                    ),
                )
                for notebook in stems
            ],
            (
                copy_directory,
                (
                    Path("../case_study_wrds_fama_french/src/assets"),
                    Path("_docs/notebooks") / "assets",
                ),
            ),
        ],
        "targets": [
            Path("_docs/notebooks") / "_01_wrds_python_package.ipynb",
            Path("_docs/notebooks") / "_02_CRSP_market_index.ipynb",
            Path("_docs/notebooks") / "_03_SP500_constituents_and_index.ipynb",
            Path("_docs/notebooks") / "_04_Fama_French_1993.ipynb",
            Path("_docs/notebooks") / "_05_basics_of_SQL.ipynb",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_doit_yield_curve():
    """Run yield curve dodo"""
    notebooks = [
        "01_CRSP_treasury_overview.ipynb",
        "02_replicate_GSW2005.ipynb",
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks]

    return {
        "actions": [
            "doit -f ../case_study_yield_curve/dodo.py",
            *[
                (
                    copy_notebook_to_folder,
                    (
                        notebook,
                        "../case_study_yield_curve/_output",
                        Path("_docs/notebooks"),
                    ),
                )
                for notebook in stems
            ],
            # copy_directory,
            # (
            #     Path("../case_study_yield_curve/src/assets"),
            #     Path("_docs/notebooks") / "assets",
            # ),
        ],
        "targets": [
            Path("_docs/notebooks") / "_01_CRSP_treasury_overview.ipynb",
            Path("_docs/notebooks") / "_02_replicate_GSW2005.ipynb",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_doit_options():
    """Run options case study dodo"""
    notebooks = [
        "corporate_hedging.ipynb",
        "spx_hedging.ipynb",
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks]

    return {
        "actions": [
            "doit -f ../case_study_options/dodo.py",
            *[
                (
                    copy_notebook_to_folder,
                    (
                        notebook,
                        "../case_study_options/_output",
                        Path("_docs/notebooks"),
                    ),
                )
                for notebook in stems
            ],
            (
                copy_directory,
                (
                    Path("../case_study_options/src/assets"),
                    Path("_docs/notebooks") / "assets",
                ),
            ),
        ],
        "targets": [
            Path("_docs/notebooks") / "_corporate_hedging.ipynb",
            Path("_docs/notebooks") / "_spx_hedging.ipynb",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


# ###############################################################
# ## Sphinx documentation
# ###############################################################


book_source_md_files = [
    str(p)
    for p in Path("docs_src").glob("**/*")
    if not p.name == ".DS_Store" and p.is_file()
]
book_source_ipynb_files = [
    str(p)
    for p in Path("_docs/notebooks").glob("**/*")
    if not p.name == ".DS_Store" and p.is_file()
]
book_source_files = book_source_md_files + book_source_ipynb_files

_book_compiled = [
    f.replace("docs_src/", "")
    .replace("_docs/", "")
    .replace(".md", ".html")
    .replace(".ipynb", ".html")
    for f in book_source_files
    if f.endswith((".md", ".ipynb"))
]

book_compiled = [
    "genindex.html",
    "search.html",
    *_book_compiled,
]


def copy_docs_src_to_docs():
    """
    Copy all files and subdirectories from the docs_src directory to the _docs directory,
    and copy src/assets to _docs/notebooks/assets.
    """
    src = Path("docs_src")
    dst = Path("_docs")

    # Ensure the destination directory exists
    dst.mkdir(parents=True, exist_ok=True)

    # Loop through all files and directories in docs_src
    for item in src.rglob("*"):
        relative_path = item.relative_to(src)
        target = dst / relative_path
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(item, target)

    # Copy README.md to _docs
    copy_file(Path("README.md"), dst / "README.md", mkdir=True)()

    # # Copy src/assets to _docs/notebooks/assets
    # src_assets = Path("src/assets")
    # dst_assets = Path("_docs/notebooks/assets")
    # if src_assets.exists():
    #     dst_assets.mkdir(parents=True, exist_ok=True)
    #     for item in src_assets.rglob('*'):
    #         relative_path = item.relative_to(src_assets)
    #         target = dst_assets / relative_path
    #         if item.is_dir():
    #             target.mkdir(parents=True, exist_ok=True)
    #         else:
    #             target.parent.mkdir(parents=True, exist_ok=True)
    #             shutil.copy2(item, target)


def copy_docs_build_to_docs():
    """
    Copy all files and subdirectories from _docs/_build/html to docs.
    This function copies each file individually while preserving the directory structure.
    It does not delete any existing contents in docs.
    After copying, it creates an empty .nojekyll file in the docs directory.
    """
    src = Path("_docs/_build/html")
    dst = Path("docs")
    dst.mkdir(parents=True, exist_ok=True)

    # Loop through all files and directories in src
    for item in src.rglob("*"):
        relative_path = item.relative_to(src)
        target = dst / relative_path
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    # Touch an empty .nojekyll file in the docs directory.
    (dst / ".nojekyll").touch()


def task_compile_book():
    """Compile Sphinx Docs"""

    targets = [Path("_docs/_build/html") / page for page in book_compiled]

    return {
        "actions": [
            copy_docs_src_to_docs,
            "sphinx-build -M html ./_docs/ ./_docs/_build",
            copy_docs_build_to_docs,
        ],
        "targets": targets,
        "file_dep": book_source_files,
        "task_dep": [
            "doit_repo_spikes",
            "doit_atlanta_fed_wage_growth",
            "doit_fama_french",
            "doit_yield_curve",
            "doit_options",
        ],
        "clean": True,
    }


def copy_docs_to_github_pages_repo():
    # shutil.rmtree(GITHUB_PAGES_REPO_DIR, ignore_errors=True)
    # shutil.copytree(BUILD_DIR, GITHUB_PAGES_REPO_DIR)

    for item in Path("docs").iterdir():
        if item.is_file():
            target_file = GITHUB_PAGES_REPO_DIR / item.name
            if target_file.exists():
                target_file.unlink()
            shutil.copy2(item, GITHUB_PAGES_REPO_DIR)
        elif item.is_dir():
            target_dir = GITHUB_PAGES_REPO_DIR / item.name
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(item, target_dir)

    nojekyll_file = GITHUB_PAGES_REPO_DIR / ".nojekyll"
    if not nojekyll_file.exists():
        nojekyll_file.touch()


def task_copy_compiled_book_to_github_pages_repo():
    """copy_compiled_book_to_github_pages_repo"""
    file_dep = [Path("docs") / page for page in book_compiled]
    pages = book_compiled
    targets = [Path(GITHUB_PAGES_REPO_DIR) / page for page in pages]

    return {
        "actions": [
            copy_docs_to_github_pages_repo,
        ],
        "targets": targets,
        "file_dep": file_dep,
        "task_dep": ["compile_book"],
        "clean": True,
    }
