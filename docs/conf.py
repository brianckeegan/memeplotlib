# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import json

# Make sure the source directory is importable for autodoc
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------

project = "memeplotlib"
copyright = "2025, Brian Keegan"
author = "Brian Keegan"
html_title = "memeplotlib"


def _get_release() -> str:
    """Resolve the docs release string from GitHub release metadata when available."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        with open(event_path, encoding="utf-8") as event_file:
            event_payload = json.load(event_file)

        release_tag = event_payload.get("release", {}).get("tag_name")
        if release_tag:
            return release_tag

    return os.environ.get("GITHUB_REF_NAME", "0.1.0")


release = _get_release()

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_gallery.gen_gallery",
]

# Napoleon settings for NumPy-style docstrings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# -- Sphinx-Gallery configuration -------------------------------------------

sphinx_gallery_conf = {
    "examples_dirs": ["../examples"],
    "gallery_dirs": ["auto_examples"],
    "filename_pattern": r"/plot_",
    "matplotlib_animations": True,
    "image_scrapers": ("matplotlib",),
    "remove_config_comments": True,
    "plot_gallery": "True",
    "abort_on_example_error": False,
    "only_warn_on_example_error": True,
}

# Intersphinx links to external projects
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "description": "Memes with Python's matplotlib",
    "github_user": "brianckeegan",
    "github_repo": "memeplotlib",
    "github_banner": False,
    "fixed_sidebar": True,
}
html_static_path = ["_static"]
