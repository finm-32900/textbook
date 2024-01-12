"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""
from pathlib import Path

from doit.tools import run_once
from doit.task import clean_targets

import config
import shutil

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


def remove_build_dir():
    """Recursively remove the build directory and its contents."""

    if BUILD_DIR.exists():
        try:
            shutil.rmtree(BUILD_DIR)
        except Exception as e:
            print(f"Error removing directory: {BUILD_DIR}. {e}")

book_files = [
    "_config.yml",
    "_toc.yml",
    "intro.md",
    "README.md",
    "lectures/Week1/HW0.md",
    "lectures/Week1/HW1.md",
    "lectures/Week1/README.md",
    "lectures/Week1/what_is_this_course_about.md",
    "lectures/Week2/what_is_a_build_system.md",
    "lectures/Week2/what_is_a_build_system.md",
    "lectures/Week2/HW2.md",
]

def task_compile_book():
    """Run jupyter-book build to compile the book."""
    file_dep = book_files
    pages = ["index.html", "intro.html"]
    targets = [Path("_build") / "html" / page for page in pages]

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
    file_dep = [
        BUILD_DIR / "html/index.html",
        *book_files,
    ]
    pages = ["index.html", "intro.html"]
    targets = [GITHUB_PAGES_REPO_DIR / page for page in pages]

    return {
        "actions": [
            copy_build_files_to_github_page_repo,
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }
