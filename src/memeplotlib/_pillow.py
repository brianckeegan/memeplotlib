"""Pillow-based meme renderer.

Used as the fallback path for the ``meme()`` dispatcher when the memegen
rendering API can't express the requested operation:

- The template is a custom local file or arbitrary URL (memegen has no
  rendered endpoint for it).
- The user supplied an explicit ``fontsize`` (memegen always auto-fits).
- The user supplied a non-default ``outline_color`` / ``outline_width``
  (memegen draws a hard-coded black stroke).
- The user supplied custom ``TextPosition`` overrides or ``Axes.text``
  kwargs (memegen has no equivalent).

The rendered image is a NumPy RGBA array which the dispatcher then displays
in matplotlib via ``ax.imshow``.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from memeplotlib._template import TextPosition
from memeplotlib._text import apply_style

if TYPE_CHECKING:
    pass


_FONTS_DIR = Path(__file__).parent / "fonts"

# User-friendly font name → expected TTF filenames searched in `_FONTS_DIR`
# and on standard system paths. The lookup falls back gracefully if a font
# is missing; the bundled Anton font is the final fallback.
_PILLOW_FONT_FILES: dict[str, list[str]] = {
    "impact": ["Impact.ttf", "impact.ttf", "Anton-Regular.ttf"],
    "anton": ["Anton-Regular.ttf"],
    "arial": ["Arial.ttf", "arial.ttf"],
    "comic": ["Comic Sans MS.ttf", "comic.ttf", "ComicSansMS.ttf"],
    "times": ["Times New Roman.ttf", "times.ttf"],
    "courier": ["Courier New.ttf", "courier.ttf", "cour.ttf"],
}

_SYSTEM_FONT_DIRS = [
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path("C:/Windows/Fonts"),
    Path.home() / ".fonts",
    Path.home() / "Library/Fonts",
]

_FIT_MIN_FONTSIZE = 8
_FIT_MAX_ITERATIONS = 24
_FIT_SHRINK_FACTOR = 0.92
_WRAP_BASE_CHARS = 28


def _resolve_font_path(font: str) -> Path:
    """Find a TTF file for *font*. Falls back to the bundled Anton font.

    Parameters
    ----------
    font : str
        User-facing font name (case-insensitive).

    Returns
    -------
    pathlib.Path
        Path to a TTF file. Always succeeds — the bundled Anton font is
        the final fallback.
    """
    candidates = _PILLOW_FONT_FILES.get(font.lower(), [f"{font}.ttf"])

    search_dirs: list[Path] = [_FONTS_DIR, *_SYSTEM_FONT_DIRS]
    for fname in candidates:
        for dirpath in search_dirs:
            if not dirpath.is_dir():
                continue
            candidate = dirpath / fname
            if candidate.is_file():
                return candidate
            # Recursive search one level deep on Linux/macOS where fonts
            # are organised into subdirectories.
            for nested in dirpath.glob(f"*/{fname}"):
                if nested.is_file():
                    return nested

    # Final fallback: bundled Anton.
    bundled = _FONTS_DIR / "Anton-Regular.ttf"
    if bundled.is_file():
        return bundled

    raise FileNotFoundError(
        f"Could not find a TTF for font {font!r}. The bundled Anton font is "
        f"missing from {_FONTS_DIR}; this typically means the wheel was built "
        f"without `force-include` of the fonts directory."
    )


def _measure(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    """Return ``(width, height)`` of *text* rendered with *font*."""
    # Pillow ≥ 9.2 exposes `getbbox` which is multiline-aware via `Draw.textbbox`.
    # For consistency we rasterise into a throwaway draw and use textbbox.
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])


def _wrap_for_box(text: str, font: ImageFont.FreeTypeFont, box_width: int) -> str:
    """Word-wrap *text* greedily to fit *box_width* in pixels."""
    if "\n" in text:
        return text

    # Estimate average char width to pick a starting wrap width, then refine.
    avg_w = max(1, _measure(font, "abcdefghijklmnopqrstuvwxyz")[0] // 26)
    chars_per_line = max(_WRAP_BASE_CHARS // 4, box_width // max(1, avg_w))

    wrapped = textwrap.fill(text, width=chars_per_line)

    # If still too wide, shrink wrap width until it fits.
    while chars_per_line > 4 and _measure(font, wrapped)[0] > box_width:
        chars_per_line = max(4, chars_per_line - 2)
        wrapped = textwrap.fill(text, width=chars_per_line)

    return wrapped


def _fit_font_to_box(
    text: str,
    font_path: Path,
    box: tuple[int, int],
    initial: int,
) -> tuple[ImageFont.FreeTypeFont, str]:
    """Iteratively shrink the font size until *text* fits in *box*.

    Parameters
    ----------
    text : str
        Text to render (already style-transformed).
    font_path : pathlib.Path
        Path to the TTF file.
    box : tuple of (int, int)
        Available ``(width, height)`` in pixels.
    initial : int
        Starting font size in pixels.

    Returns
    -------
    tuple
        ``(font, wrapped_text)``.
    """
    box_w, box_h = box
    size = max(_FIT_MIN_FONTSIZE, int(initial))
    font = ImageFont.truetype(str(font_path), size=size)
    wrapped = _wrap_for_box(text, font, box_w)

    for _ in range(_FIT_MAX_ITERATIONS):
        w, h = _measure(font, wrapped)
        if w <= box_w and h <= box_h:
            return font, wrapped
        if size <= _FIT_MIN_FONTSIZE:
            return font, wrapped
        size = max(_FIT_MIN_FONTSIZE, int(size * _FIT_SHRINK_FACTOR))
        font = ImageFont.truetype(str(font_path), size=size)
        wrapped = _wrap_for_box(text, font, box_w)

    return font, wrapped


def _draw_caption(
    img: Image.Image,
    text: str,
    pos: TextPosition,
    *,
    font: str,
    color: str,
    outline_color: str,
    outline_width: float,
    fontsize: float | None,
    style: str,
) -> None:
    """Draw a single caption onto *img* in-place."""
    if not text:
        return

    display_text = apply_style(text, style)

    img_w, img_h = img.size
    box_w = max(1, int(round(pos.scale_x * img_w)))
    box_h = max(1, int(round(pos.scale_y * img_h)))
    box_x = int(round(pos.anchor_x * img_w))
    box_y = int(round(pos.anchor_y * img_h))

    initial_size = (
        int(round(fontsize)) if fontsize is not None else max(_FIT_MIN_FONTSIZE, box_h // 2)
    )

    font_path = _resolve_font_path(font)
    pil_font, wrapped = _fit_font_to_box(
        display_text, font_path, (box_w, box_h), initial=initial_size
    )

    text_w, text_h = _measure(pil_font, wrapped)

    if pos.align == "left":
        anchor_x = box_x
        align = "left"
    elif pos.align == "right":
        anchor_x = box_x + box_w - text_w
        align = "right"
    else:
        anchor_x = box_x + (box_w - text_w) // 2
        align = "center"
    anchor_y = box_y + (box_h - text_h) // 2

    # Stroke width in pixels. The matplotlib path-effect uses
    # `outline_width * 2` as the visual stroke; we mirror that here so
    # rough visual parity holds across backends.
    stroke = max(0, int(round(outline_width * 2)))

    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        (anchor_x, anchor_y),
        wrapped,
        font=pil_font,
        fill=color,
        stroke_width=stroke,
        stroke_fill=outline_color,
        align=align,
    )


def render_pillow(
    image: np.ndarray,
    lines: list[str],
    positions: list[TextPosition],
    *,
    font: str,
    color: str,
    outline_color: str,
    outline_width: float,
    fontsize: float | None,
    style: str,
    per_line_overrides: dict[int, dict[str, object]] | None = None,
) -> np.ndarray:
    """Composite caption text onto *image* using Pillow.

    Parameters
    ----------
    image : numpy.ndarray
        Background image as an RGBA array of shape ``(H, W, 4)``.
    lines : list of str
        Caption text per slot.
    positions : list of TextPosition
        Caption box per slot.
    font, color, outline_color, outline_width, fontsize, style :
        Default styling used for every slot unless overridden.
    per_line_overrides : dict, optional
        Mapping of ``line_index → {field: value}`` to override styling
        on a per-slot basis. Supported fields: ``font``, ``color``,
        ``fontsize``, ``position``.

    Returns
    -------
    numpy.ndarray
        New RGBA image with captions drawn on top.
    """
    overrides = per_line_overrides or {}
    img = Image.fromarray(image).convert("RGBA")

    for i, text in enumerate(lines):
        if not text:
            continue
        if i >= len(positions):
            break

        line_override = overrides.get(i, {})
        eff_font = str(line_override.get("font", font))
        eff_color = str(line_override.get("color", color))
        raw_fs = line_override.get("fontsize", fontsize)
        eff_fontsize: float | None = None if raw_fs is None else float(raw_fs)  # type: ignore[arg-type]
        pos_override = line_override.get("position")
        eff_pos = pos_override if isinstance(pos_override, TextPosition) else positions[i]

        _draw_caption(
            img,
            text,
            eff_pos,
            font=eff_font,
            color=eff_color,
            outline_color=outline_color,
            outline_width=outline_width,
            fontsize=eff_fontsize,
            style=style,
        )

    return np.array(img)
