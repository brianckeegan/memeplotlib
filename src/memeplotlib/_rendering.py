"""Rendering pipeline for meme images.

Three backends share a single dispatcher (:func:`render_meme`):

- ``"memegen"`` — build a memegen rendering URL via
  :func:`memeplotlib._url.build_memegen_url`, fetch the rendered image, and
  display it. Server-side rendering only; honours ``style`` /
  ``font`` / ``color`` / ``width`` / ``height`` / ``layout`` /
  ``background`` / ``overlays`` / ``template_style``.
- ``"pillow"`` — fetch the blank, draw captions client-side with
  ``PIL.ImageDraw``. Honours per-line ``fontsize``, custom outlines, and
  custom ``TextPosition`` overrides.
- ``"matplotlib"`` — legacy path, draws captions with ``Axes.text`` plus
  ``patheffects.Stroke``. Kept for backwards compatibility.

The dispatcher's ``"auto"`` policy picks ``"memegen"`` for memegen
templates with no client-only knobs and ``"pillow"`` otherwise.
"""

from __future__ import annotations

import io
import textwrap
import threading
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patheffects
from matplotlib.font_manager import FontProperties, findfont, fontManager
from PIL import Image

from memeplotlib._cache import TemplateCache
from memeplotlib._config import DEFAULT_FIGSIZE_WIDTH, config
from memeplotlib._pillow import render_pillow
from memeplotlib._template import (
    DEFAULT_TEXT_POSITIONS,
    Template,
    TextPosition,
    _get_session,
)
from memeplotlib._text import apply_style
from memeplotlib._url import OverlaySpec, build_memegen_url, memegen_font_for

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.backend_bases import RendererBase
    from matplotlib.figure import Figure, SubFigure
    from matplotlib.text import Text

# --- Constants ---

_WRAP_CHARS_PER_FULL_WIDTH = 25  # estimated chars that fill full figure width at ~36pt
_MIN_WRAP_WIDTH = 10  # minimum characters per wrapped line
_FIT_TOLERANCE = 1.1  # allow text to exceed box by 10% before shrinking
_FIT_MAX_ITERATIONS = 20  # maximum iterations for text-fitting loop
_FIT_SHRINK_FACTOR = 0.95  # multiply by this when shrinking font to fit
_MIN_TEXT_EXTENT = 0.01  # guard against near-zero text dimensions

# --- Font handling ---

_FONTS_DIR = Path(__file__).parent / "fonts"

_FONT_MAP = {
    "impact": "Impact",
    "arial": "Arial",
    "comic": "Comic Sans MS",
    "times": "Times New Roman",
    "courier": "Courier New",
}

_bundled_font_registered = False
_font_lock = threading.Lock()


def _register_bundled_fonts() -> None:
    """Register bundled fonts with matplotlib's font manager (once)."""
    global _bundled_font_registered
    if _bundled_font_registered:
        return
    with _font_lock:
        if _bundled_font_registered:
            return
        _bundled_font_registered = True

        if _FONTS_DIR.is_dir():
            for font_path in _FONTS_DIR.glob("*.ttf"):
                fontManager.addfont(str(font_path))


def _resolve_font(font: str) -> str:
    """Map a friendly font name to a system font family name.

    Falls back to the bundled Anton font (Impact-like), then to DejaVu Sans
    if neither the requested font nor the bundled font is available.

    Parameters
    ----------
    font : str
        Friendly font name (e.g., ``"impact"``, ``"comic"``).

    Returns
    -------
    str
        Resolved font family name suitable for matplotlib.
    """
    _register_bundled_fonts()

    name = _FONT_MAP.get(font.lower(), font)

    # Check if the requested font is available
    fp = FontProperties(family=name)
    path = findfont(fp, fallback_to_default=True)

    if "dejavu" in path.lower() and name.lower() not in ("dejavu", "dejavu sans"):
        # Requested font not found — try bundled Anton as Impact substitute
        if font.lower() in ("impact", _FONT_MAP.get("impact", "").lower()):
            anton_fp = FontProperties(family="Anton")
            anton_path = findfont(anton_fp, fallback_to_default=True)
            if "dejavu" not in anton_path.lower():
                return "Anton"

        warnings.warn(
            f"Font '{font}' not found. Using fallback font. "
            f"Install '{font}' for best results.",
            UserWarning,
            stacklevel=3,
        )

    return name


# --- Auto font sizing ---


def _auto_fontsize(
    text: str,
    box_width_frac: float,
    box_height_frac: float,
    base_size: float = 36.0,
) -> float:
    """Estimate an initial font size based on text length and box dimensions.

    This is a starting heuristic; :func:`_fit_text_to_box` refines it
    further using the actual renderer.

    Parameters
    ----------
    text : str
        The text to size.
    box_width_frac : float
        Bounding box width as a fraction of the figure (0.0 to 1.0).
    box_height_frac : float
        Bounding box height as a fraction of the figure (0.0 to 1.0).
    base_size : float, optional
        Starting font size in points (default: 36.0).

    Returns
    -------
    float
        Estimated font size in points.
    """
    num_lines = text.count("\n") + 1
    max_line_len = max(len(line) for line in text.split("\n"))

    # Scale down for longer text
    length_factor = max(0.3, 1.0 - max_line_len / 60)
    # Scale down for more lines
    lines_factor = max(0.4, 1.0 / (num_lines**0.5))
    # Scale by box area
    area_factor = (box_width_frac * box_height_frac) ** 0.25

    return float(base_size * length_factor * lines_factor * area_factor)


def _get_renderer(fig: Figure | SubFigure) -> RendererBase:
    """Get a renderer from a figure, handling API differences across versions.

    Parameters
    ----------
    fig : Figure or SubFigure
        The matplotlib figure (or subfigure) whose canvas should provide a
        renderer.

    Returns
    -------
    matplotlib.backend_bases.RendererBase
        The figure's renderer.
    """
    canvas = fig.canvas
    get_renderer = getattr(canvas, "get_renderer", None)
    if get_renderer is not None:
        try:
            return cast("RendererBase", get_renderer())
        except (RuntimeError, AttributeError):
            pass
    # Fallback: draw to create renderer
    canvas.draw()
    # mypy: get_renderer is documented on Agg/PDF/SVG canvases but not on
    # FigureCanvasBase; rely on duck typing here.
    return cast("RendererBase", canvas.get_renderer())  # type: ignore[attr-defined]


def _fit_text_to_box(
    ax: Axes,
    txt: Text,
    box_w: float,
    box_h: float,
    min_fontsize: float = 8.0,
) -> None:
    """Iteratively reduce font size until text fits within the bounding box.

    Uses matplotlib's renderer to measure actual text extent in axes
    coordinates.

    Parameters
    ----------
    ax : Axes
        The axes containing the text.
    txt : Text
        The matplotlib Text object to resize.
    box_w : float
        Maximum width in axes-fraction coordinates.
    box_h : float
        Maximum height in axes-fraction coordinates.
    min_fontsize : float, optional
        Minimum allowed font size in points (default: 8.0).
    """
    fig = ax.get_figure()
    if fig is None:
        return  # detached axes; nothing to render against
    renderer = _get_renderer(fig)

    for _ in range(_FIT_MAX_ITERATIONS):
        bbox = txt.get_window_extent(renderer=renderer)
        # Convert to axes fraction
        inv = ax.transAxes.inverted()
        bbox_axes = bbox.transformed(inv)
        text_w = bbox_axes.width
        text_h = bbox_axes.height

        if text_w <= box_w * _FIT_TOLERANCE and text_h <= box_h * _FIT_TOLERANCE:
            break

        # mpl's Text.get_fontsize() is annotated as float|str, but it returns
        # a numeric size at runtime once the text has been added to an axes.
        current = float(txt.get_fontsize())
        if current <= min_fontsize:
            break

        # Scale down proportionally
        scale = min(
            box_w / max(text_w, _MIN_TEXT_EXTENT),
            box_h / max(text_h, _MIN_TEXT_EXTENT),
        )
        new_size = max(min_fontsize, current * scale * _FIT_SHRINK_FACTOR)
        txt.set_fontsize(new_size)


# --- Core drawing ---


def _draw_meme_text(
    ax: Axes,
    text: str,
    x: float,
    y: float,
    pos: TextPosition,
    font: str = "impact",
    color: str = "white",
    outline_color: str = "black",
    outline_width: float = 2.0,
    fontsize: float | None = None,
    style: str = "upper",
    **text_kwargs: Any,
) -> Text:
    """Draw meme-style text with outline at the given axes-coordinate position.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to draw on.
    text : str
        The text to render.
    x : float
        X position in axes coordinates (0--1).
    y : float
        Y position in axes coordinates (0--1, 0=bottom).
    pos : TextPosition
        TextPosition describing the text box dimensions and alignment.
    font : str, optional
        Font family name (default: ``"impact"``).
    color : str, optional
        Text fill color (default: ``"white"``).
    outline_color : str, optional
        Text outline/stroke color (default: ``"black"``).
    outline_width : float, optional
        Outline stroke width (default: 2.0).
    fontsize : float or None, optional
        Font size in points. Auto-calculated if ``None``.
    style : str, optional
        Text style (``"upper"``, ``"lower"``, ``"none"``).
    **text_kwargs
        Additional keyword arguments forwarded to :meth:`Axes.text`. User
        values take precedence over the meme-specific defaults above.

    Returns
    -------
    Text
        The matplotlib Text object.
    """
    display_text = apply_style(text, style)

    # Word-wrap long text
    display_text = _smart_wrap(display_text, pos.scale_x)

    if fontsize is None:
        fontsize = _auto_fontsize(
            display_text, pos.scale_x, pos.scale_y, base_size=config["fontsize"]
        )

    font_family = _resolve_font(font)

    text_call_kwargs: dict[str, Any] = dict(
        transform=ax.transAxes,
        fontsize=fontsize,
        fontfamily=font_family,
        fontweight="bold",
        color=color,
        ha=pos.align,
        va="center",
        linespacing=1.1,
        path_effects=[
            patheffects.Stroke(linewidth=outline_width * 2, foreground=outline_color),
            patheffects.Normal(),
        ],
    )
    text_call_kwargs.update(text_kwargs)

    txt = ax.text(x, y, display_text, **text_call_kwargs)

    # Refine font size to fit the bounding box
    _fit_text_to_box(ax, txt, pos.scale_x, pos.scale_y)

    return txt


def _smart_wrap(text: str, box_width_frac: float) -> str:
    """Wrap text based on the available box width.

    Already-wrapped text (containing newlines) is left as-is.

    Parameters
    ----------
    text : str
        The text to potentially wrap.
    box_width_frac : float
        Available box width as a fraction of the figure (0.0 to 1.0).

    Returns
    -------
    str
        Text with newlines inserted at wrap points, if needed.
    """
    if "\n" in text:
        return text

    # Estimate characters that fit based on box width fraction
    # At ~36pt on a typical figure, ~20 chars fill the full width
    chars_per_line = max(_MIN_WRAP_WIDTH, int(box_width_frac * _WRAP_CHARS_PER_FULL_WIDTH))
    if len(text) <= chars_per_line:
        return text

    return "\n".join(textwrap.wrap(text, width=chars_per_line))


# --- Main rendering functions ---


def _figure_for_image(
    img: np.ndarray,
    ax: Axes | None,
    figsize: tuple[float, float] | None,
    dpi: int,
) -> tuple[Figure, Axes]:
    """Create or reuse a Figure/Axes pair sized to *img*'s aspect ratio."""
    h, w = img.shape[:2]
    aspect = w / max(1, h)

    if ax is None:
        if figsize is None:
            fig_w = DEFAULT_FIGSIZE_WIDTH
            fig_h = fig_w / aspect
            figsize = (fig_w, fig_h)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        parent_fig = ax.get_figure()
        if parent_fig is None:
            raise RuntimeError("Provided ax has no associated Figure")
        fig = cast("Figure", parent_fig)

    ax.imshow(img, aspect="auto")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax


def _fetch_rendered_image(url: str, cache: TemplateCache | None) -> np.ndarray:
    """Fetch a memegen-rendered image (PNG/JPG/GIF/WebP) as an RGBA array."""
    if cache is not None and config["cache_enabled"]:
        cached = cache.get_image(url)
        if cached is not None:
            return cached

    resp = _get_session().get(url, timeout=config["image_timeout"])
    resp.raise_for_status()
    image_bytes = resp.content
    img = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGBA"))

    if cache is not None and config["cache_enabled"]:
        cache.set_image(url, image_bytes)

    return img


def _render_via_memegen(
    template: Template,
    lines: list[str],
    *,
    ax: Axes | None,
    figsize: tuple[float, float] | None,
    dpi: int,
    font: str,
    color: str,
    style: str,
    extension: str,
    width: int | None,
    height: int | None,
    layout: str | None,
    background: str | None,
    overlays: Sequence[OverlaySpec] | None,
    template_style: str | None,
    cache: TemplateCache | None,
) -> tuple[Figure, Axes]:
    """Render via the memegen API and ``imshow`` the result."""
    # Style transforms (upper/lower/none) are client-side; apply before
    # encoding so memegen receives the final visible string.
    transformed = [apply_style(line, style) if line else line for line in lines]

    memegen_font = memegen_font_for(font)
    url = build_memegen_url(
        template.id,
        transformed,
        api_base=config["api_base"],
        extension=extension,
        template_style=template_style,
        font=memegen_font,
        color=color,
        width=width,
        height=height,
        layout=layout,
        background=background,
        overlays=overlays,
    )

    img = _fetch_rendered_image(url, cache)
    return _figure_for_image(img, ax, figsize, dpi)


def _render_via_pillow(
    template: Template,
    lines: list[str],
    *,
    ax: Axes | None,
    figsize: tuple[float, float] | None,
    dpi: int,
    font: str,
    color: str,
    outline_color: str,
    outline_width: float,
    fontsize: float | None,
    style: str,
    per_line_overrides: dict[int, dict[str, object]] | None,
    cache: TemplateCache | None,
) -> tuple[Figure, Axes]:
    """Render via ``PIL.ImageDraw`` and ``imshow`` the result."""
    blank = template.get_image(cache=cache)
    composed = render_pillow(
        blank,
        lines,
        template.text_positions,
        font=font,
        color=color,
        outline_color=outline_color,
        outline_width=outline_width,
        fontsize=fontsize,
        style=style,
        per_line_overrides=per_line_overrides,
    )
    return _figure_for_image(composed, ax, figsize, dpi)


def _render_via_matplotlib(
    template: Template,
    lines: list[str],
    *,
    ax: Axes | None,
    figsize: tuple[float, float] | None,
    dpi: int,
    font: str,
    color: str,
    outline_color: str,
    outline_width: float,
    fontsize: float | None,
    style: str,
    cache: TemplateCache | None,
    text_kwargs: dict[str, Any],
) -> tuple[Figure, Axes]:
    """Legacy renderer: draw captions with matplotlib's ``Axes.text``."""
    img = template.get_image(cache=cache)
    fig, ax_out = _figure_for_image(img, ax, figsize, dpi)

    positions = template.text_positions
    for i, text in enumerate(lines):
        if not text or i >= len(positions):
            continue

        pos = positions[i]
        x = pos.anchor_x + pos.scale_x / 2
        y = 1.0 - (pos.anchor_y + pos.scale_y / 2)

        _draw_meme_text(
            ax_out,
            text,
            x,
            y,
            pos,
            font=font,
            color=color,
            outline_color=outline_color,
            outline_width=outline_width,
            fontsize=fontsize,
            style=style,
            **text_kwargs,
        )

    return fig, ax_out


def render_meme(
    template: Template,
    lines: list[str],
    ax: Axes | None = None,
    figsize: tuple[float, float] | None = None,
    dpi: int | None = None,
    font: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    outline_width: float | None = None,
    fontsize: float | None = None,
    style: str | None = None,
    cache: TemplateCache | None = None,
    backend: str = "auto",
    extension: str | None = None,
    width: int | None = None,
    height: int | None = None,
    layout: str | None = None,
    background: str | None = None,
    overlays: Sequence[OverlaySpec] | None = None,
    template_style: str | None = None,
    force_pillow: bool = False,
    per_line_overrides: dict[int, dict[str, object]] | None = None,
    **text_kwargs: Any,
) -> tuple[Figure, Axes]:
    """Render a meme using the configured backend.

    The ``"auto"`` backend selects ``"memegen"`` when the template originates
    from the memegen catalog and the user requested no client-only feature;
    otherwise ``"pillow"``. Pass ``backend="matplotlib"`` for the legacy
    ``Axes.text`` rendering retained for backwards compatibility.

    Parameters
    ----------
    template : Template
        Resolved template.
    lines : list of str
        Caption text per slot.
    ax : Axes or None, optional
        Existing axes to render onto.
    figsize : tuple of (float, float) or None, optional
        Figure size in inches.
    dpi : int or None, optional
        Dots per inch.
    font : str or None, optional
        Font family name.
    color : str or None, optional
        Text fill color.
    outline_color, outline_width : optional
        Stroke parameters (Pillow / matplotlib backends only).
    fontsize : float or None, optional
        Explicit font size; forces the Pillow backend under ``"auto"``.
    style : str or None, optional
        Text transform: ``"upper"``, ``"lower"``, or ``"none"``.
    cache : TemplateCache or None, optional
        Cache instance for image retrieval.
    backend : str, optional
        ``"auto"``, ``"memegen"``, ``"pillow"``, or ``"matplotlib"``.
    extension : str or None, optional
        Output format requested from memegen (``"png"``, ``"jpg"``,
        ``"gif"``, ``"webp"``). Defaults to ``config["extension"]``.
    width, height : int or None, optional
        Output dimensions for memegen.
    layout : str or None, optional
        memegen layout (e.g. ``"top"``).
    background : str or None, optional
        Custom background image URL for memegen.
    overlays : sequence of OverlaySpec or None, optional
        Ad-hoc overlay placements for memegen.
    template_style : str or None, optional
        memegen template-specific style name (e.g. ``"maga"``).
    force_pillow : bool, optional
        When ``True``, ``backend="auto"`` resolves to ``"pillow"``.
    per_line_overrides : dict, optional
        Per-line ``{font, color, fontsize, position}`` overrides for the
        Pillow renderer.
    **text_kwargs
        Forwarded to :meth:`Axes.text` (matplotlib backend only).

    Returns
    -------
    tuple of (Figure, Axes)
        The matplotlib Figure and Axes containing the rendered meme.
    """
    dpi_val = dpi if dpi is not None else config["dpi"]
    font_val = font or config["font"]
    color_val = color or config["color"]
    outline_color_val = outline_color or config["outline_color"]
    outline_width_val = outline_width if outline_width is not None else config["outline_width"]
    style_val = style or config["style"]
    extension_val = extension or config["extension"]
    width_val = width if width is not None else config["width"]
    height_val = height if height is not None else config["height"]
    layout_val = layout if layout is not None else config["layout"]
    background_val = background if background is not None else config["background"]

    # `auto` first delegates to ``config["backend"]`` (which may itself be
    # ``"auto"``) so callers reach into the same global override.
    backend_input = backend
    if backend_input == "auto":
        backend_input = config["backend"]

    chosen = _select_backend(
        backend_input,
        template,
        font=font_val,
        force_pillow=force_pillow,
        text_kwargs=text_kwargs,
        per_line_overrides=per_line_overrides,
    )

    if chosen == "memegen":
        return _render_via_memegen(
            template,
            lines,
            ax=ax,
            figsize=figsize,
            dpi=dpi_val,
            font=font_val,
            color=color_val,
            style=style_val,
            extension=extension_val,
            width=width_val,
            height=height_val,
            layout=layout_val,
            background=background_val,
            overlays=overlays,
            template_style=template_style,
            cache=cache,
        )

    if chosen == "pillow":
        return _render_via_pillow(
            template,
            lines,
            ax=ax,
            figsize=figsize,
            dpi=dpi_val,
            font=font_val,
            color=color_val,
            outline_color=outline_color_val,
            outline_width=outline_width_val,
            fontsize=fontsize,
            style=style_val,
            per_line_overrides=per_line_overrides,
            cache=cache,
        )

    return _render_via_matplotlib(
        template,
        lines,
        ax=ax,
        figsize=figsize,
        dpi=dpi_val,
        font=font_val,
        color=color_val,
        outline_color=outline_color_val,
        outline_width=outline_width_val,
        fontsize=fontsize,
        style=style_val,
        cache=cache,
        text_kwargs=text_kwargs,
    )


def _select_backend(
    requested: str,
    template: Template,
    *,
    font: str,
    force_pillow: bool,
    text_kwargs: dict[str, Any],
    per_line_overrides: dict[int, dict[str, object]] | None,
) -> str:
    """Resolve ``backend="auto"`` to a concrete backend name."""
    if requested != "auto":
        if requested not in {"memegen", "pillow", "matplotlib"}:
            raise ValueError(
                f"Unknown backend {requested!r}. Must be one of: "
                f"'auto', 'memegen', 'pillow', 'matplotlib'."
            )
        if requested == "memegen" and not template.is_memegen:
            warnings.warn(
                "backend='memegen' requested but template is not from the "
                "memegen catalog; falling back to 'pillow'.",
                UserWarning,
                stacklevel=3,
            )
            return "pillow"
        return requested

    if force_pillow:
        return "pillow"
    if not template.is_memegen:
        return "pillow"
    if per_line_overrides:
        return "pillow"
    if text_kwargs:
        return "pillow"
    if memegen_font_for(font) is None:
        return "pillow"
    return "memegen"


def render_memify(
    fig: Figure,
    lines: list[str],
    position: str = "top-bottom",
    font: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    outline_width: float | None = None,
    fontsize: float | None = None,
    style: str | None = None,
    **text_kwargs: Any,
) -> Figure:
    """Add meme text overlay to an existing matplotlib figure.

    Creates a transparent overlay axes spanning the full figure and draws
    meme-style text on top.

    Parameters
    ----------
    fig : Figure
        The matplotlib figure to add text to.
    lines : list of str
        Text lines to overlay.
    position : str, optional
        Layout preset -- ``"top-bottom"`` (default), ``"top"``,
        ``"bottom"``, or ``"center"``.
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
        Text style (``"upper"``, ``"lower"``, ``"none"``).
    **text_kwargs
        Additional keyword arguments forwarded to :meth:`Axes.text` for each
        rendered caption.

    Returns
    -------
    Figure
        The modified Figure with meme text overlay.
    """
    font = font or config["font"]
    color = color or config["color"]
    outline_color = outline_color or config["outline_color"]
    outline_width = outline_width if outline_width is not None else config["outline_width"]
    style = style or config["style"]

    # Determine text positions based on layout preset
    valid_positions = {"top-bottom", "top", "bottom", "center"}
    if position not in valid_positions:
        raise ValueError(
            f"Invalid position {position!r}. Must be one of: "
            f"{', '.join(sorted(valid_positions))}"
        )

    if position == "top-bottom":
        positions = list(DEFAULT_TEXT_POSITIONS)
    elif position == "top":
        positions = [DEFAULT_TEXT_POSITIONS[0]]
    elif position == "bottom":
        positions = [DEFAULT_TEXT_POSITIONS[1]]
    else:  # center
        positions = [TextPosition(anchor_x=0.0, anchor_y=0.4, scale_x=1.0, scale_y=0.2)]

    # Create a transparent overlay axes spanning the full figure
    overlay_ax = fig.add_axes((0.0, 0.0, 1.0, 1.0), facecolor="none")
    overlay_ax.set_xlim(0, 1)
    overlay_ax.set_ylim(0, 1)
    overlay_ax.axis("off")

    for i, text in enumerate(lines):
        if not text or i >= len(positions):
            continue

        pos = positions[i]
        x = pos.anchor_x + pos.scale_x / 2
        y = 1.0 - (pos.anchor_y + pos.scale_y / 2)

        _draw_meme_text(
            overlay_ax,
            text,
            x,
            y,
            pos,
            font=font,
            color=color,
            outline_color=outline_color,
            outline_width=outline_width,
            fontsize=fontsize,
            style=style,
            **text_kwargs,
        )

    return fig
