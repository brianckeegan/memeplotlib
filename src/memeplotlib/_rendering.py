"""Matplotlib rendering pipeline for meme images."""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.font_manager import FontProperties, findfont, fontManager

from memeplotlib._cache import TemplateCache
from memeplotlib._config import DEFAULT_FIGSIZE_WIDTH, config
from memeplotlib._template import DEFAULT_TEXT_POSITIONS, Template, TextPosition
from memeplotlib._text import apply_style

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.text import Text

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


def _register_bundled_fonts() -> None:
    """Register bundled fonts with matplotlib's font manager (once)."""
    global _bundled_font_registered
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

    This is a starting heuristic; _fit_text_to_box refines it further.
    """
    num_lines = text.count("\n") + 1
    max_line_len = max(len(line) for line in text.split("\n"))

    # Scale down for longer text
    length_factor = max(0.3, 1.0 - max_line_len / 60)
    # Scale down for more lines
    lines_factor = max(0.4, 1.0 / (num_lines ** 0.5))
    # Scale by box area
    area_factor = (box_width_frac * box_height_frac) ** 0.25

    return base_size * length_factor * lines_factor * area_factor


def _get_renderer(fig: Figure) -> matplotlib.backend_bases.RendererBase:
    """Get a renderer from a figure, handling API differences across versions."""
    canvas = fig.canvas
    if hasattr(canvas, "get_renderer"):
        try:
            return canvas.get_renderer()
        except Exception:
            pass
    # Fallback: draw to create renderer
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _fit_text_to_box(
    ax: Axes,
    txt: Text,
    box_w: float,
    box_h: float,
    min_fontsize: float = 8.0,
) -> None:
    """Iteratively reduce font size until text fits within the bounding box.

    Uses matplotlib's renderer to measure actual text extent in axes coordinates.
    """
    fig = ax.get_figure()
    renderer = _get_renderer(fig)

    for _ in range(20):
        bbox = txt.get_window_extent(renderer=renderer)
        # Convert to axes fraction
        inv = ax.transAxes.inverted()
        bbox_axes = bbox.transformed(inv)
        text_w = bbox_axes.width
        text_h = bbox_axes.height

        if text_w <= box_w * 1.1 and text_h <= box_h * 1.1:
            break

        current = txt.get_fontsize()
        if current <= min_fontsize:
            break

        # Scale down proportionally
        scale = min(box_w / max(text_w, 0.01), box_h / max(text_h, 0.01))
        new_size = max(min_fontsize, current * scale * 0.95)
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
) -> Text:
    """Draw meme-style text with outline at the given axes-coordinate position.

    Args:
        ax: The matplotlib axes to draw on.
        text: The text to render.
        x: X position in axes coordinates (0-1).
        y: Y position in axes coordinates (0-1, 0=bottom).
        pos: TextPosition describing the text box.
        font: Font family name.
        color: Text fill color.
        outline_color: Text outline/stroke color.
        outline_width: Outline stroke width.
        fontsize: Font size in points (auto-calculated if None).
        style: Text style ("upper", "lower", "none").

    Returns:
        The matplotlib Text object.
    """
    display_text = apply_style(text, style)

    # Word-wrap long text
    display_text = _smart_wrap(display_text, pos.scale_x)

    if fontsize is None:
        fontsize = _auto_fontsize(display_text, pos.scale_x, pos.scale_y)

    font_family = _resolve_font(font)

    txt = ax.text(
        x,
        y,
        display_text,
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

    # Refine font size to fit the bounding box
    _fit_text_to_box(ax, txt, pos.scale_x, pos.scale_y)

    return txt


def _smart_wrap(text: str, box_width_frac: float) -> str:
    """Wrap text based on the available box width.

    Already-wrapped text (containing newlines) is left as-is.
    """
    if "\n" in text:
        return text

    # Estimate characters that fit based on box width fraction
    # At ~36pt on a typical figure, ~20 chars fill the full width
    chars_per_line = max(10, int(box_width_frac * 25))
    if len(text) <= chars_per_line:
        return text

    return "\n".join(textwrap.wrap(text, width=chars_per_line))


# --- Main rendering functions ---


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
) -> tuple[Figure, Axes]:
    """Render a meme image using matplotlib.

    Args:
        template: The Template to render.
        lines: Text lines for each text position.
        ax: Optional existing axes to render onto.
        figsize: Figure size in inches (width, height).
        dpi: Dots per inch for rendering.
        font: Font family name.
        color: Text fill color.
        outline_color: Text outline color.
        outline_width: Outline stroke width.
        fontsize: Font size in points (auto if None).
        style: Text style ("upper", "lower", "none").
        cache: Optional template cache.

    Returns:
        Tuple of (Figure, Axes).
    """
    # Apply defaults from config
    dpi = dpi or config.dpi
    font = font or config.font
    color = color or config.color
    outline_color = outline_color or config.outline_color
    outline_width = outline_width if outline_width is not None else config.outline_width
    style = style or config.style

    # Load the background image
    img = template.get_image(cache=cache)
    h, w = img.shape[:2]
    aspect = w / h

    if ax is None:
        if figsize is None:
            fig_w = DEFAULT_FIGSIZE_WIDTH
            fig_h = fig_w / aspect
            figsize = (fig_w, fig_h)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.get_figure()

    # Display the background image edge-to-edge
    ax.imshow(img, aspect="auto")
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Draw text for each line
    positions = template.text_positions
    for i, text in enumerate(lines):
        if not text or i >= len(positions):
            continue

        pos = positions[i]
        # Center of the text box in axes coordinates (y flipped: mpl 0=bottom)
        x = pos.anchor_x + pos.scale_x / 2
        y = 1.0 - (pos.anchor_y + pos.scale_y / 2)

        _draw_meme_text(
            ax,
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
        )

    return fig, ax


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
) -> Figure:
    """Add meme text overlay to an existing matplotlib figure.

    Creates a transparent overlay axes spanning the full figure and draws
    meme-style text on top.

    Args:
        fig: The matplotlib figure to add text to.
        lines: Text lines to overlay.
        position: Layout preset — "top-bottom", "top", "bottom", or "center".
        font: Font family name.
        color: Text fill color.
        outline_color: Text outline color.
        outline_width: Outline stroke width.
        fontsize: Font size in points (auto if None).
        style: Text style ("upper", "lower", "none").

    Returns:
        The modified Figure.
    """
    font = font or config.font
    color = color or config.color
    outline_color = outline_color or config.outline_color
    outline_width = outline_width if outline_width is not None else config.outline_width
    style = style or config.style

    # Determine text positions based on layout preset
    if position == "top-bottom":
        positions = list(DEFAULT_TEXT_POSITIONS)
    elif position == "top":
        positions = [DEFAULT_TEXT_POSITIONS[0]]
    elif position == "bottom":
        positions = [DEFAULT_TEXT_POSITIONS[1]]
    elif position == "center":
        positions = [TextPosition(anchor_x=0.0, anchor_y=0.4, scale_x=1.0, scale_y=0.2)]
    else:
        positions = list(DEFAULT_TEXT_POSITIONS)

    # Create a transparent overlay axes spanning the full figure
    overlay_ax = fig.add_axes([0, 0, 1, 1], facecolor="none")
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
        )

    return fig
