"""Functional (simple) API for memeplotlib."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt

from memeplotlib._alt import (
    default_meme_alt_text,
    default_memify_alt_text,
    get_alt_text,
    savefig_metadata,
    set_alt_text,
)
from memeplotlib._cache import default_cache
from memeplotlib._config import config
from memeplotlib._rendering import render_meme, render_memify
from memeplotlib._template import _resolve_template
from memeplotlib._url import OverlaySpec

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


_cache = default_cache()


# Sentinel used to detect whether the caller explicitly supplied a value.
# We need this because `None` is also a legal user-supplied default for
# several knobs and the default-from-config behaviour was already in place.
_UNSET: Any = object()


def meme(
    template: str,
    *lines: str,
    font: Any = _UNSET,
    color: Any = _UNSET,
    outline_color: Any = _UNSET,
    outline_width: Any = _UNSET,
    fontsize: Any = _UNSET,
    style: Any = _UNSET,
    backend: str | None = None,
    extension: str | None = None,
    width: int | None = None,
    height: int | None = None,
    layout: str | None = None,
    background: str | None = None,
    overlays: Sequence[OverlaySpec] | None = None,
    template_style: str | None = None,
    alt_text: str | None = None,
    show: bool = False,
    savefig: str | Path | None = None,
    figsize: tuple[float, float] | None = None,
    dpi: int | None = None,
    ax: Axes | None = None,
    **text_kwargs: Any,
) -> tuple[Figure, Axes]:
    """Create a meme from a template with text lines.

    The default ``backend="auto"`` selects the memegen rendering API for
    memegen-catalogue templates, and falls back to a Pillow client-side
    renderer for custom local images or whenever the user supplies a
    feature memegen can't express (explicit ``fontsize`` or a custom
    outline). Extra ``Axes.text`` kwargs select the matplotlib renderer,
    the only one that can apply them.

    Parameters
    ----------
    template : str
        Template identifier -- memegen ID, file path, or URL.
    *lines : str
        Text lines for each text position (top, bottom, etc.).
    font : str, optional
        Font family name (default ``config["font"]``).
    color : str, optional
        Text fill color for every caption (default ``config["color"]``).
        On the memegen backend, a comma-separated list such as
        ``"white,red"`` sets one color per line; when no color is chosen,
        memegen templates keep their own caption colors.
    outline_color : str, optional
        Text outline color. Passing a non-default value under
        ``backend="auto"`` forces the Pillow backend, since memegen renders
        a hard-coded black stroke.
    outline_width : float, optional
        Outline stroke width. Under Pillow the stroke scales with the
        fitted font size (each unit adds 1/24 of it, so the default 2.0
        matches memegen's size / 12). Passing a non-default value under
        ``backend="auto"`` forces the Pillow backend.
    fontsize : float, optional
        Explicit font size. Forces the Pillow backend under
        ``backend="auto"`` (memegen always auto-fits). Units depend on the
        backend: points under ``"matplotlib"``; under ``"pillow"``, pixels
        at the template image's native resolution, used as a maximum
        (captions still shrink to fit their box).
    style : str, optional
        Text transform -- ``"upper"``, ``"lower"``, or ``"none"``. memegen
        applies each template's own casing (usually upper), so under
        ``backend="auto"`` anything but ``"upper"`` selects the Pillow
        backend.
    backend : str, optional
        ``"auto"`` (default), ``"memegen"``, ``"pillow"``, or
        ``"matplotlib"`` (legacy, draws captions with
        :meth:`matplotlib.axes.Axes.text`).
    extension : str, optional
        Output format requested from memegen -- ``"png"``, ``"jpg"``,
        ``"gif"``, or ``"webp"``. memegen backend only. Animated GIF/WebP
        responses are shown as their last frame (where every timed caption
        is visible); the figure cannot hold the animation.
    width, height : int, optional
        Output dimensions in pixels. memegen backend only.
    layout : str, optional
        memegen layout (e.g. ``"top"``). memegen backend only.
    background : str, optional
        Image URL to use **instead of** the template image. memegen only
        supports this on its ``custom`` template, so the render uses that
        template with your captions. memegen backend only.
    overlays : sequence of OverlaySpec, optional
        Ad-hoc overlay image placements. memegen backend only.
    template_style : str, optional
        memegen template-specific style (e.g. ``"maga"`` for ``"ds"``).
        memegen backend only.
    alt_text : str, optional
        Text alternative describing the meme for screen-reader users. If
        omitted, one is generated from the template name and captions.
        Retrieve it with :func:`get_alt_text`; it is also embedded in the
        file written by ``savefig`` (PNG/SVG ``Description``, PDF
        ``Subject``).
    show : bool, optional
        Whether to call :func:`matplotlib.pyplot.show` after rendering.
    savefig : str, Path, or None, optional
        Path to save the meme image to.
    figsize : tuple of (float, float) or None, optional
        Figure size as ``(width, height)`` in inches.
    dpi : int or None, optional
        Dots per inch.
    ax : Axes or None, optional
        Existing matplotlib Axes to render onto.
    **text_kwargs
        Additional keyword arguments forwarded to :meth:`Axes.text`. Only
        the ``"matplotlib"`` backend applies them, so passing any under
        ``backend="auto"`` selects it; an explicit ``"memegen"`` or
        ``"pillow"`` backend ignores them with a ``UserWarning``.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib Figure containing the rendered meme.
    ax : matplotlib.axes.Axes
        The matplotlib Axes containing the rendered meme.

    Raises
    ------
    TemplateNotFoundError
        If *template* looks like a memegen ID but memegen doesn't know it.
    FileNotFoundError
        If *template* looks like a file path but the file doesn't exist.
    ValueError
        If ``backend``, ``style``, or ``extension`` is not a valid choice.
    requests.HTTPError
        If memegen or an image URL returns an error status.

    Examples
    --------
    >>> import memeplotlib as memes
    >>> fig, ax = memes.meme("buzz", "memes", "memes everywhere")  # doctest: +SKIP

    >>> fig, ax = memes.meme(  # doctest: +SKIP
    ...     "drake", "writing tests", "shipping to prod",
    ...     font="impact", color="yellow",
    ... )

    >>> fig, ax = memes.meme(  # doctest: +SKIP
    ...     "buzz", "hello", "world",
    ...     fontsize=48,  # forces pillow backend under auto
    ... )
    """
    tmpl = _resolve_template(template)

    # Resolve sentinels: detect whether the caller passed each knob, then
    # collapse to the effective value (config default if not).
    user_outline_color = outline_color is not _UNSET
    user_outline_width = outline_width is not _UNSET
    user_fontsize = fontsize is not _UNSET

    eff_font = font if font is not _UNSET else None
    eff_color = color if color is not _UNSET else None
    eff_outline_color = outline_color if user_outline_color else None
    eff_outline_width = outline_width if user_outline_width else None
    eff_fontsize = fontsize if user_fontsize else None
    eff_style = style if style is not _UNSET else None

    # Force the pillow path when memegen can't honour the request:
    # explicit fontsize or non-default outline. (Extra Axes.text kwargs are
    # routed to the matplotlib backend by the dispatcher instead.)
    force_pillow = bool(user_fontsize or user_outline_color or user_outline_width)

    backend_val = backend if backend is not None else config["backend"]

    fig, ax_out = render_meme(
        tmpl,
        list(lines),
        ax=ax,
        figsize=figsize,
        dpi=dpi,
        font=eff_font,
        color=eff_color,
        outline_color=eff_outline_color,
        outline_width=eff_outline_width,
        fontsize=eff_fontsize,
        style=eff_style,
        cache=_cache,
        backend=backend_val,
        extension=extension,
        width=width,
        height=height,
        layout=layout,
        background=background,
        overlays=overlays,
        template_style=template_style,
        force_pillow=force_pillow,
        **text_kwargs,
    )
    set_alt_text(ax_out, alt_text or default_meme_alt_text(tmpl, lines))

    if savefig is not None:
        fig.savefig(
            str(savefig),
            dpi=dpi if dpi is not None else config["dpi"],
            bbox_inches="tight",
            pad_inches=0,
            **_metadata_kwargs(savefig, get_alt_text(ax_out)),
        )

    if show:
        plt.show()

    return fig, ax_out


def _metadata_kwargs(path: str | Path, alt: str | None) -> dict[str, Any]:
    """``savefig`` kwargs embedding *alt* (empty for formats without metadata)."""
    metadata = savefig_metadata(path, alt)
    return {"metadata": metadata} if metadata else {}


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
    alt_text: str | None = None,
    show: bool = False,
    savefig: str | Path | None = None,
    **text_kwargs: Any,
) -> Figure:
    """Add meme-style text to an existing matplotlib figure.

    Overlays bold, outlined text on top of any matplotlib figure -- useful
    for turning plots, charts, or other visualizations into memes.

    .. note::

       ``memify`` always renders text with matplotlib's ``Axes.text``
       (the figure isn't a memegen template, so the API doesn't apply).
       The ``backend`` parameter on :func:`meme` is intentionally not
       exposed here.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
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
    alt_text : str or None, optional
        Text alternative describing the result for screen-reader users.
        If omitted, the captions are described and appended to any alt
        text the figure already carries. Retrieve it with
        :func:`get_alt_text`; it is also embedded in the ``savefig`` file.
    show : bool, optional
        Whether to call :func:`matplotlib.pyplot.show` after rendering
        (default: ``False``).
    savefig : str, Path, or None, optional
        Path to save the result to.
    **text_kwargs
        Additional keyword arguments forwarded to :meth:`Axes.text` for each
        rendered caption.

    Returns
    -------
    matplotlib.figure.Figure
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
        **text_kwargs,
    )
    if alt_text is None:
        existing = get_alt_text(result)
        caption = default_memify_alt_text(position, lines)
        alt_text = f"{existing} {caption}" if existing else caption
    set_alt_text(result, alt_text)

    if savefig is not None:
        result.savefig(
            str(savefig),
            dpi=config["dpi"],
            bbox_inches="tight",
            pad_inches=0,
            **_metadata_kwargs(savefig, alt_text),
        )

    if show:
        plt.show()

    return result
