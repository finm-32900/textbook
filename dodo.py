"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""

import shutil
from pathlib import Path

from doit.task import clean_targets
from doit.tools import run_once

import config

OUTPUT_DIR = Path(config.OUTPUT_DIR)
BUILD_DIR = Path(config.BUILD_DIR)
NOTEBOOK_BUILD_DIR = Path(config.NOTEBOOK_BUILD_DIR)
GITHUB_PAGES_REPO_DIR = Path(config.GITHUB_PAGES_REPO_DIR)


# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
def jupyter_execute_notebook(notebook):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace {notebook}.ipynb"
def jupyter_to_html(notebook):
    return f"jupyter nbconvert --to html --output-dir='../output' {notebook}.ipynb"
def jupyter_to_md(notebook):
    """Requires jupytext"""
    return f"jupytext --to markdown {notebook}.ipynb"
def jupyter_to_python(notebook, build_dir):
    """Requires jupytext"""
    return f"jupyter nbconvert --to python {notebook}.ipynb --output {notebook}.py --output-dir {build_dir}"
def jupyter_clear_output(notebook):
    return f"jupyter nbconvert --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace {notebook}.ipynb"
# fmt: on


def copy_notebook_to_folder(notebook_stem, origin_folder, destination_folder):
    origin_path = Path(origin_folder) / f"{notebook_stem}.ipynb"
    destination_path = Path(destination_folder) / f"_{notebook_stem}.ipynb"
    shutil.copy2(origin_path, destination_path)


def remove_build_dir():
    """Recursively remove the build directory and its contents."""

    if BUILD_DIR.exists():
        try:
            shutil.rmtree(BUILD_DIR)
        except Exception as e:
            print(f"Error removing directory: {BUILD_DIR}. {e}")


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


##################################
## Begin rest of PyDoit tasks here
##################################


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
                    (notebook, Path("../case_study_repo_spikes/_output"), OUTPUT_DIR),
                )
                for notebook in stems
            ],
            (
                copy_directory,
                (Path("../case_study_repo_spikes/src/assets"), OUTPUT_DIR / "assets"),
            ),
        ],
        "targets": [OUTPUT_DIR / "_01_repo_spikes.ipynb", OUTPUT_DIR / "assets"],
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
                    (notebook, Path("../case_study_wage_growth/_output"), OUTPUT_DIR),
                )
                for notebook in stems
            ],
        ],
        "targets": [OUTPUT_DIR / "_01_wage_growth_during_the_recession.ipynb"],
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
                    (notebook, "../case_study_wrds_fama_french/_output", OUTPUT_DIR),
                )
                for notebook in stems
            ],
        ],
        "targets": [
            OUTPUT_DIR / "_01_wrds_python_package.ipynb",
            OUTPUT_DIR / "_02_CRSP_market_index.ipynb",
            OUTPUT_DIR / "_03_SP500_constituents_and_index.ipynb",
            OUTPUT_DIR / "_04_Fama_French_1993.ipynb",
            OUTPUT_DIR / "_05_basics_of_SQL.ipynb",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


book_source_files = [
    "intro.md",
    "README.md",
    ##
    "lectures/Week1/case_study_reproducibility_in_finance.md",
    "lectures/Week1/HW0.md",
    "lectures/Week1/HW1.md",
    "lectures/Week1/overview_w1.md",
    "lectures/Week1/reproducible_analytical_pipelines.md",
    "lectures/Week1/what_is_this_course_about.md",
    "lectures/Week1/case_study_atlanta_fed_wage_growth_tracker.md",
    "lectures/Week1/virtual_environments.md",
    ##
    "output/_01_repo_spikes.ipynb",
    ##
    "lectures/Week2/HW2.md",
    "lectures/Week3/what_is_a_task_runner.md",
    "lectures/Week2/env_files.md",
    "lectures/Week2/WRDS_intro_and_web_queries.md",
    "lectures/Week2/project_structure.md",
    "lectures/Week2/overview_w2.md",
    ##
    "output/_01_wage_growth_during_the_recession.ipynb",
    ##
    "lectures/Week3/overview_w3.md",
    "lectures/Week3/HW3.md",
    ##
    "output/_01_wrds_python_package.ipynb",
    ##
    "lectures/Week4/overview_w4.md",
    "lectures/Week4/intro_to_LaTeX.md",
    "lectures/Week4/reports_with_jupyter_notebooks.md",
    "lectures/Week4/latex_essentials.md",
    ##
    "lectures/Week5/overview_w5.md",
    "lectures/Week5/sphinx.md",
    "lectures/Week5/unit_tests.md",
    ##
    "lectures/Week6/overview_w6.md",
    "lectures/Week6/bloomberg_terminal.md",
    "lectures/Week6/GitHub_pull_requests.md",
    ##
    "lectures/Week7/overview_w7.md",
    ##
    "lectures/Week8/overview_w8.md",
    "lectures/Week8/github_actions_interactive_dashboard.md",
    ##
    "lectures/Week8/HW4.md",
    ##
    "lectures/Misc/appendix.md",
    "lectures/Misc/final_project.md",
    "lectures/Misc/potential_final_projects.md",
]

_book_compiled = [page.split(".")[0] + ".html" for page in book_source_files]
book_compiled = [
    "genindex.html",
    "search.html",
    "index.html",
    *_book_compiled,
]


def task_compile_book():
    """Run jupyter-book build to compile the book."""

    file_dep = [
        "_config.yml",
        "_toc.yml",
        *book_source_files,
    ]

    targets = [Path("_build") / "html" / page for page in book_compiled]

    return {
        "actions": [
            "jupyter-book build -W ./",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": [clean_targets, remove_build_dir],
    }


def copy_build_files_to_github_page_repo():
    # shutil.rmtree(GITHUB_PAGES_REPO_DIR, ignore_errors=True)
    # shutil.copytree(BUILD_DIR, GITHUB_PAGES_REPO_DIR)

    for item in (BUILD_DIR / "html").iterdir():
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
    file_dep = [Path("_build") / "html" / page for page in book_compiled]
    pages = book_compiled
    targets = [Path(GITHUB_PAGES_REPO_DIR) / page for page in pages]

    return {
        "actions": [
            copy_build_files_to_github_page_repo,
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }
