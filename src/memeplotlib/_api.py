"""Functional (simple) API for memeplotlib."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from memeplotlib._cache import TemplateCache
from memeplotlib._config import config
from memeplotlib._rendering import render_meme, render_memify
from memeplotlib._template import _resolve_template

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


_cache = TemplateCache()


def meme(
    template: str,
    *lines: str,
    font: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    outline_width: float | None = None,
    fontsize: float | None = None,
    style: str | None = None,
    show: bool = True,
    savefig: str | Path | None = None,
    figsize: tuple[float, float] | None = None,
    dpi: int | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Create a meme from a template with text lines.

    This is the main entry point for creating memes. The template can be:
    - A memegen template ID (e.g., "buzz", "drake", "doge")
    - A local file path to an image
    - An HTTP(S) URL to an image

    Args:
        template: Template identifier — memegen ID, file path, or URL.
        *lines: Text lines for each text position (top, bottom, etc.).
        font: Font family name (default: "impact").
        color: Text fill color (default: "white").
        outline_color: Text outline color (default: "black").
        outline_width: Outline stroke width (default: 2.0).
        fontsize: Font size in points. Auto-calculated if None.
        style: Text transform — "upper", "lower", or "none" (default: "upper").
        show: Whether to call plt.show() (default: True).
        savefig: Path to save the meme image to.
        figsize: Figure size as (width, height) in inches.
        dpi: Dots per inch (default: 150).
        ax: Existing matplotlib Axes to render onto.

    Returns:
        Tuple of (Figure, Axes) for further customization.

    Example::

        import memeplotlib as memes

        # Quick one-liner
        memes.meme("buzz", "memes", "memes everywhere")

        # With customization
        memes.meme("drake", "writing tests", "shipping to prod",
                    font="impact", color="yellow", show=False)
    """
    tmpl = _resolve_template(template)

    fig, ax_out = render_meme(
        tmpl,
        list(lines),
        ax=ax,
        figsize=figsize,
        dpi=dpi,
        font=font,
        color=color,
        outline_color=outline_color,
        outline_width=outline_width,
        fontsize=fontsize,
        style=style,
        cache=_cache,
    )

    if savefig is not None:
        fig.savefig(
            str(savefig),
            dpi=dpi or config.dpi,
            bbox_inches="tight",
            pad_inches=0,
        )

    if show:
        plt.show()

    return fig, ax_out


def memify(
    fig: Figure,
    *lines: str,
    position: str = "top-bottom",
    font: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    outline_width: float | None = None,
    fontsize: float | None = None,
    style: str | None = None,
    show: bool = True,
    savefig: str | Path | None = None,
) -> Figure:
    """Add meme-style text to an existing matplotlib figure.

    Overlays bold, outlined text on top of any matplotlib figure — useful
    for turning plots, charts, or other visualizations into memes.

    Args:
        fig: The matplotlib figure to add text to.
        *lines: Text lines to overlay.
        position: Layout — "top-bottom", "top", "bottom", or "center".
        font: Font family name.
        color: Text fill color.
        outline_color: Text outline color.
        outline_width: Outline stroke width.
        fontsize: Font size in points (auto if None).
        style: Text transform — "upper", "lower", or "none".
        show: Whether to call plt.show().
        savefig: Path to save the result to.

    Returns:
        The modified Figure.

    Example::

        import matplotlib.pyplot as plt
        import memeplotlib as memes

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        memes.memify(fig, "stonks")
    """
    result = render_memify(
        fig,
        list(lines),
        position=position,
        font=font,
        color=color,
        outline_color=outline_color,
        outline_width=outline_width,
        fontsize=fontsize,
        style=style,
    )

    if savefig is not None:
        result.savefig(
            str(savefig),
            dpi=config.dpi,
            bbox_inches="tight",
            pad_inches=0,
        )

    if show:
        plt.show()

    return result
