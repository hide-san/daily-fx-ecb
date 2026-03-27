"""
scripts/create_notebook_pipeline.py
====================================
Generate the pipeline overview notebook pushed to Kaggle once per week.

The notebook fetches KAGGLE_README.md and CHANGELOG.md directly from the
GitHub repository at runtime, so Kaggle always shows the latest content
without any double-maintenance of documentation.

Output
------
notebooks/pipeline/
    pipeline_overview.ipynb      nbformat v4 notebook
    kernel-metadata-pipeline.json  Kaggle Kernels API descriptor
"""

import json
import sys
from typing import Any

from common import (
    GITHUB_RAW_BASE_URL,
    PIPELINE_NOTEBOOK_TITLE,
    append_github_summary,
    code,
    dataset_slug,
    load_pairs_file,
    load_public_kernels,
    pipeline_notebook_output_dir,
    pipeline_notebook_slug,
)

_README_URL = f"{GITHUB_RAW_BASE_URL}/main/KAGGLE_README.md"
_CHANGELOG_URL = f"{GITHUB_RAW_BASE_URL}/main/CHANGELOG.md"
_CHANGELOG_PREVIEW_LINES = 30


def build_pipeline_notebook() -> dict[str, Any]:
    """Build the pipeline overview notebook."""
    cells = [
        code(
            "import requests\n"
            "from IPython.display import Markdown, display\n"
            "\n"
            f'response = requests.get("{_README_URL}")\n'
            "response.raise_for_status()\n"
            "display(Markdown(response.text))\n"
        ),
        code(
            f'response = requests.get("{_CHANGELOG_URL}")\n'
            "response.raise_for_status()\n"
            "lines = [line for line in response.text.splitlines() if line.strip()]\n"
            f'display(Markdown("\\n".join(lines[:{_CHANGELOG_PREVIEW_LINES}])))\n'
        ),
    ]

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": cells,
    }


def write_kernel_metadata() -> None:
    """Write kernel-metadata-pipeline.json for the Kaggle Kernels API."""
    output_dir = pipeline_notebook_output_dir()
    metadata = {
        "id": pipeline_notebook_slug(),
        "title": PIPELINE_NOTEBOOK_TITLE,
        "code_file": "pipeline_overview.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "enable_gpu": False,
        "enable_tpu": False,
        "is_private": False,
        "enable_internet": True,  # Required: fetches KAGGLE_README.md from GitHub at runtime
        "dataset_sources": [dataset_slug(p) for p in load_pairs_file()],
        "competition_sources": [],
        "kernel_sources": [],
    }
    with open(output_dir / "kernel-metadata-pipeline.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)


def main() -> None:
    slug = pipeline_notebook_slug()
    if slug not in load_public_kernels():
        print(f"ERROR: '{slug}' is not listed in public_kernels.txt.", file=sys.stderr)
        sys.exit(1)

    output_dir = pipeline_notebook_output_dir()

    nb = build_pipeline_notebook()
    nb_path = output_dir / "pipeline_overview.ipynb"
    with open(nb_path, "w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1)
    print(f"Saved notebook : {nb_path}")

    write_kernel_metadata()
    print("Metadata       : kernel-metadata-pipeline.json written")

    append_github_summary("| pipeline | ok |\n")


if __name__ == "__main__":
    main()
