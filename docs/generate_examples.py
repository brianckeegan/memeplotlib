#!/usr/bin/env python3
"""Generate static example images for the README and documentation.

This script produces PNG images for every code example in the README,
tutorial, user guide, and API reference.  It tries to fetch templates from
the memegen API first and falls back to synthetic placeholder backgrounds
when the API is unreachable.

Usage
-----
Run from the repository root::

    python docs/generate_examples.py

Images are written to ``docs/_static/examples/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Ensure the local source tree is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from memeplotlib._config import config  # noqa: E402
from memeplotlib._rendering import render_meme, render_memify  # noqa: E402
from memeplotlib._template import (  # noqa: E402
    DEFAULT_TEXT_POSITIONS,
    Template,
    TextPosition,
    _resolve_template,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "_static" / "examples"

# --------------------------------------------------------------------------- #
#  Template helpers
# --------------------------------------------------------------------------- #

# Palette used for synthetic backgrounds when the API is unavailable.
_COLORS = {
    "buzz":       ((50, 80, 180), (100, 160, 220)),
    "doge":       ((200, 170, 80), (240, 210, 130)),
    "drake":      ((120, 60, 40), (200, 140, 100)),
    "distracted": ((60, 130, 80), (140, 200, 140)),
    "expanding-brain": ((80, 60, 120), (160, 130, 200)),
    "default":    ((70, 70, 90), (140, 140, 160)),
}

# Templates with more than two text positions.
_MULTI_LINE_TEMPLATES = {
    "distracted": 3,
    "expanding-brain": 4,
}


def _gradient(h: int, w: int, top: tuple[int, ...], bot: tuple[int, ...]) -> np.ndarray:
    """Return an RGBA gradient image transitioning from *top* to *bot*."""
    img = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        t = y / max(h - 1, 1)
        for c in range(3):
            img[y, :, c] = int(top[c] * (1 - t) + bot[c] * t)
    img[:, :, 3] = 255
    return img


def _get_template(template_id: str) -> Template:
    """Try the API first; fall back to a synthetic gradient background."""
    try:
        tmpl = _resolve_template(template_id)
        # Force image download so we fail fast on network issues
        tmpl.get_image()
        return tmpl
    except Exception:
        pass

    # Build a synthetic template
    lines_count = _MULTI_LINE_TEMPLATES.get(template_id, 2)
    colors = _COLORS.get(template_id, _COLORS["default"])
    bg = _gradient(600, 800, *colors)

    if lines_count <= 2:
        positions = list(DEFAULT_TEXT_POSITIONS)
    else:
        slot = 1.0 / lines_count
        positions = [
            TextPosition(anchor_x=0.0, anchor_y=i * slot, scale_x=1.0, scale_y=slot)
            for i in range(lines_count)
        ]

    tmpl = Template(
        id=template_id,
        name=template_id.replace("-", " ").title(),
        image_url="synthetic",
        text_positions=positions,
    )
    tmpl._image_array = bg
    return tmpl


def _save(fig: plt.Figure, name: str, dpi: int = 150) -> None:
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(str(path), dpi=dpi, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"  saved {path.relative_to(OUTPUT_DIR.parent.parent)}")


# --------------------------------------------------------------------------- #
#  README images
# --------------------------------------------------------------------------- #


def generate_readme_images() -> None:
    print("README images")

    # Quick Start – buzz
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "readme_buzz_basic")

    # Quick Start – doge
    tmpl = _get_template("doge")
    fig, _ = render_meme(tmpl, ["such code", "very bug"])
    _save(fig, "readme_doge_savefig")

    # Functional API – drake
    tmpl = _get_template("drake")
    fig, _ = render_meme(
        tmpl, ["writing tests", "shipping to prod"],
        font="impact", color="yellow",
    )
    _save(fig, "readme_drake_functional")

    # Functional API – distracted
    tmpl = _get_template("distracted")
    fig, _ = render_meme(
        tmpl, ["my project", "new framework", "me"],
    )
    _save(fig, "readme_distracted_functional")

    # OO API – buzz
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "readme_buzz_oo")

    # OO API – doge chained
    tmpl = _get_template("doge")
    fig, _ = render_meme(tmpl, ["such code", "very bug"])
    _save(fig, "readme_doge_oo")

    # Memify existing plot
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    render_memify(fig, ["stonks"])
    _save(fig, "readme_memify_stonks")


# --------------------------------------------------------------------------- #
#  Tutorial images
# --------------------------------------------------------------------------- #


def generate_tutorial_images() -> None:
    print("Tutorial images")

    # Your First Meme
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "tutorial_first_meme")

    # Saving to a File
    tmpl = _get_template("doge")
    fig, _ = render_meme(tmpl, ["such code", "very bug"])
    _save(fig, "tutorial_save_to_file")

    # Customizing Text
    tmpl = _get_template("drake")
    fig, _ = render_meme(
        tmpl, ["writing tests", "shipping to prod"],
        font="impact", color="yellow", style="upper",
    )
    _save(fig, "tutorial_custom_text")

    # Controlling Outline
    tmpl = _get_template("buzz")
    fig, _ = render_meme(
        tmpl, ["white on black", "the classic"],
        color="white", outline_color="black", outline_width=3.0,
    )
    _save(fig, "tutorial_outline")

    # Getting the Figure Back
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "tutorial_figure_back")


# --------------------------------------------------------------------------- #
#  User guide images
# --------------------------------------------------------------------------- #


def generate_user_guide_images() -> None:
    print("User guide images")

    # Functional API – distracted
    tmpl = _get_template("distracted")
    fig, _ = render_meme(tmpl, ["my project", "new framework", "me"])
    _save(fig, "ug_functional_distracted")

    # Functional API – drake styled
    tmpl = _get_template("drake")
    fig, _ = render_meme(
        tmpl, ["writing tests", "shipping to prod"],
        font="impact", color="yellow", outline_color="blue",
        outline_width=3.0, style="none",
    )
    _save(fig, "ug_functional_drake_styled")

    # OO API – doge chained
    tmpl = _get_template("doge")
    fig, _ = render_meme(tmpl, ["such code", "very bug"])
    _save(fig, "ug_oo_doge")

    # OO API – buzz step-by-step
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "ug_oo_buzz")

    # OO API – expanding brain
    tmpl = _get_template("expanding-brain")
    fig, _ = render_meme(
        tmpl, ["using print()", "using logging", "using a debugger", "reading the source"],
    )
    _save(fig, "ug_oo_expanding_brain")

    # OO API – buzz constructor shorthand
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "ug_oo_buzz_constructor")

    # Memify – basic
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Quadratic growth")
    render_memify(fig, ["stonks"])
    _save(fig, "ug_memify_basic")

    # Memify – bottom
    fig, ax = plt.subplots()
    ax.bar(["A", "B", "C"], [3, 7, 5])
    render_memify(fig, ["not stonks"], position="bottom")
    _save(fig, "ug_memify_bottom")

    # Global Configuration
    tmpl = _get_template("buzz")
    fig, _ = render_meme(
        tmpl, ["custom defaults", "applied everywhere"],
        font="comic", color="yellow", style="none",
    )
    _save(fig, "ug_config")

    # Rendering onto existing axes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    tmpl_buzz = _get_template("buzz")
    render_meme(tmpl_buzz, ["memes", "memes everywhere"], ax=ax1)
    tmpl_doge = _get_template("doge")
    render_meme(tmpl_doge, ["such code", "very bug"], ax=ax2)
    fig.subplots_adjust(wspace=0.05)
    _save(fig, "ug_subplots")


# --------------------------------------------------------------------------- #
#  API reference images
# --------------------------------------------------------------------------- #


def generate_api_images() -> None:
    print("API reference images")

    # meme() example
    tmpl = _get_template("buzz")
    fig, _ = render_meme(tmpl, ["memes", "memes everywhere"])
    _save(fig, "api_meme_example")

    # memify() example
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    render_memify(fig, ["stonks"])
    _save(fig, "api_memify_example")

    # Meme class example
    tmpl = _get_template("doge")
    fig, _ = render_meme(tmpl, ["such code", "very bug"])
    _save(fig, "api_meme_class_example")


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing images to {OUTPUT_DIR}\n")

    generate_readme_images()
    generate_tutorial_images()
    generate_user_guide_images()
    generate_api_images()

    print("\nDone.")


if __name__ == "__main__":
    main()
