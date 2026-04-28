"""Sphinx configuration for memeplotlib documentation."""

from __future__ import annotations

import json
import os
import sys

# Make sure the source directory is importable for autodoc
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------

project = "memeplotlib"
copyright = "2025, Brian Keegan"
author = "Brian Keegan"
html_title = "memeplotlib"
html_logo = "_static/logo.png"


def _get_release() -> str:
    """Resolve the docs release string from GitHub release metadata when available."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        with open(event_path, encoding="utf-8") as event_file:
            event_payload = json.load(event_file)

        release_tag = event_payload.get("release", {}).get("tag_name")
        if release_tag:
            return release_tag

    return os.environ.get("GITHUB_REF_NAME", "0.2.0")


release = _get_release()

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "numpydoc",
    "sphinx_gallery.gen_gallery",
]

# numpydoc handles NumPy-format docstrings and renders typed signatures;
# we don't combine it with napoleon or sphinx-autodoc-typehints.
numpydoc_show_class_members = False
numpydoc_class_members_toctree = False
numpydoc_xref_param_type = True

# Autodoc + autosummary settings
autodoc_member_order = "bysource"
autodoc_typehints = "none"  # numpydoc renders types from the docstring
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autosummary_generate = True
autosummary_imported_members = False

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

# Sphinx-gallery emits a non-fatal warning when an example exits non-zero
# (for example, a network blip during the live memegen API fetch). The
# build still succeeds; suppress just the gallery's own warning category
# so `-W` doesn't elevate transient network issues into fatal errors.
suppress_warnings = ["sphinx_gallery"]

# Intersphinx links to external projects
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "_internal", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/brianckeegan/memeplotlib",
            "icon": "fa-brands fa-github",
        },
    ],
    "show_nav_level": 2,
    "show_toc_level": 2,
}
html_static_path = ["_static"]
