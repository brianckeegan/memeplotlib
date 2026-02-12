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

    - A memegen template ID (e.g., ``"buzz"``, ``"drake"``, ``"doge"``)
    - A local file path to an image
    - An HTTP(S) URL to an image

    Parameters
    ----------
    template : str
        Template identifier -- memegen ID, file path, or URL.
    *lines : str
        Text lines for each text position (top, bottom, etc.).
    font : str or None, optional
        Font family name (default: ``"impact"``).
    color : str or None, optional
        Text fill color (default: ``"white"``).
    outline_color : str or None, optional
        Text outline color (default: ``"black"``).
    outline_width : float or None, optional
        Outline stroke width (default: 2.0).
    fontsize : float or None, optional
        Font size in points. Auto-calculated if ``None``.
    style : str or None, optional
        Text transform -- ``"upper"``, ``"lower"``, or ``"none"``
        (default: ``"upper"``).
    show : bool, optional
        Whether to call ``plt.show()`` (default: ``True``).
    savefig : str, Path, or None, optional
        Path to save the meme image to.
    figsize : tuple of (float, float) or None, optional
        Figure size as ``(width, height)`` in inches.
    dpi : int or None, optional
        Dots per inch (default: 150).
    ax : Axes or None, optional
        Existing matplotlib Axes to render onto.

    Returns
    -------
    tuple of (Figure, Axes)
        The matplotlib Figure and Axes for further customization.

    Examples
    --------
    >>> import memeplotlib as memes
    >>> memes.meme("buzz", "memes", "memes everywhere")  # doctest: +SKIP

    >>> memes.meme("drake", "writing tests", "shipping to prod",
    ...            font="impact", color="yellow", show=False)  # doctest: +SKIP
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

    Overlays bold, outlined text on top of any matplotlib figure -- useful
    for turning plots, charts, or other visualizations into memes.

    Parameters
    ----------
    fig : Figure
        The matplotlib figure to add text to.
    *lines : str
        Text lines to overlay.
    position : str, optional
        Layout -- ``"top-bottom"`` (default), ``"top"``, ``"bottom"``,
        or ``"center"``.
    font : str or None, optional
        Font family name.
    color : str or None, optional
        Text fill color.
    outline_color : str or None, optional
        Text outline color.
    outline_width : float or None, optional
        Outline stroke width.
    fontsize : float or None, optional
        Font size in points (auto if ``None``).
    style : str or None, optional
        Text transform -- ``"upper"``, ``"lower"``, or ``"none"``.
    show : bool, optional
        Whether to call ``plt.show()``.
    savefig : str, Path, or None, optional
        Path to save the result to.

    Returns
    -------
    Figure
        The modified Figure.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import memeplotlib as memes
    >>> fig, ax = plt.subplots()  # doctest: +SKIP
    >>> ax.plot([1, 2, 3], [1, 4, 9])  # doctest: +SKIP
    >>> memes.memify(fig, "stonks")  # doctest: +SKIP
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
