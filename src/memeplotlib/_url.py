"""memegen API URL construction.

Builds rendering URLs for the memegen API following the path/query rules
described in the public docs and unified by jacebrowning/memegen #993.

The URL shape is::

    {api_base}/images/{template_id}/{line_1}/{line_2}/.../{line_n}.{ext}?...

Each line segment is encoded via :func:`memeplotlib._text.encode_text_for_url`,
with the special case that an empty line is rendered as a single underscore
(``_``) so memegen preserves slot ordering for non-trailing empty slots.

Query parameters cover:

- ``style`` — template style name (e.g. ``"maga"`` for ``ds``) or an arbitrary
  overlay image URL
- ``font`` — memegen-side font alias (e.g. ``"impact"``, ``"thick"``,
  ``"comic"``); see :data:`MEMEGEN_FONT_ALIASES`
- ``color`` — ``"fg"`` or ``"fg,bg"`` (HTML name or hex)
- ``width`` / ``height`` — output dimensions in pixels
- ``layout`` — alternate layout (e.g. ``"top"``)
- ``background`` — custom background image URL
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict
from urllib.parse import quote

from memeplotlib._text import encode_text_for_url

if TYPE_CHECKING:
    from collections.abc import Sequence


# memegen-side font aliases. Distinct from the matplotlib/Pillow font map in
# `_rendering._FONT_MAP` because memegen accepts a specific named set served by
# the upstream `/fonts/` endpoint. Keys are the user-facing names accepted by
# memeplotlib; values are the strings memegen recognises in the `font=` query.
MEMEGEN_FONT_ALIASES: dict[str, str] = {
    "impact": "impact",
    "thick": "thick",
    "thin": "thin",
    "tiny": "tiny",
    "comic": "comic",
    "notosans": "notosans",
    "kalam": "kalam",
    "he": "he",
    "jp": "jp",
    "tw": "tw",
    "default": "impact",
}


class OverlaySpec(TypedDict, total=False):
    """An ad-hoc overlay placement passed alongside a memegen render."""

    style: str
    """Overlay image URL, or a template style name."""
    center: tuple[float, float]
    """Overlay anchor as ``(x, y)`` fractions in the range ``[0, 1]``."""
    scale: float
    """Overlay scale factor."""


_VALID_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})


def memegen_font_for(font: str) -> str | None:
    """Return the memegen font alias for *font*, or ``None`` if unsupported.

    Parameters
    ----------
    font : str
        User-facing font name (case-insensitive).

    Returns
    -------
    str or None
        The memegen-side alias, or ``None`` if the font has no memegen
        equivalent (in which case the caller should fall back to the
        Pillow renderer).

    Examples
    --------
    >>> memegen_font_for("impact")
    'impact'
    >>> memegen_font_for("Comic")
    'comic'
    >>> memegen_font_for("arial") is None
    True
    """
    return MEMEGEN_FONT_ALIASES.get(font.lower())


def _encode_segment(line: str) -> str:
    """Encode a single line for a memegen URL path.

    Empty strings become ``_`` so memegen still allocates the slot. Non-empty
    strings are passed through :func:`encode_text_for_url`.
    """
    if not line:
        return "_"
    return encode_text_for_url(line)


def _format_query_value(value: object) -> str:
    """Format a query-parameter value preserving memegen's tilde escapes.

    memegen's URL escape table uses ``~q`` / ``~a`` / etc. We must NOT
    percent-encode the tilde, so this helper quotes everything except the
    safe set ``~,/:`` (the comma is significant for ``color=fg,bg``).
    """
    return quote(str(value), safe="~,/:")


def build_memegen_url(
    template_id: str,
    lines: Sequence[str],
    *,
    api_base: str,
    extension: str = "png",
    template_style: str | None = None,
    font: str | None = None,
    color: str | None = None,
    width: int | None = None,
    height: int | None = None,
    layout: str | None = None,
    background: str | None = None,
    overlays: Sequence[OverlaySpec] | None = None,
) -> str:
    """Construct a memegen rendering URL.

    Parameters
    ----------
    template_id : str
        memegen template identifier (e.g. ``"buzz"``, ``"drake"``).
    lines : sequence of str
        Caption lines in slot order. Empty strings become ``_`` to preserve
        the slot.
    api_base : str
        Base URL of the memegen API (e.g. ``"https://api.memegen.link"``).
    extension : str, optional
        Output format. One of ``"png"``, ``"jpg"``, ``"jpeg"``, ``"gif"``,
        ``"webp"``. Default ``"png"``.
    template_style : str or None, optional
        Template-specific style (e.g. ``"maga"``). May also be an arbitrary
        image URL for ad-hoc overlays.
    font : str or None, optional
        memegen font alias (see :data:`MEMEGEN_FONT_ALIASES`).
    color : str or None, optional
        ``"fg"`` or ``"fg,bg"`` colour spec (HTML name or hex).
    width : int or None, optional
        Output width in pixels.
    height : int or None, optional
        Output height in pixels.
    layout : str or None, optional
        Alternate layout (e.g. ``"top"``).
    background : str or None, optional
        Custom background image URL.
    overlays : sequence of OverlaySpec or None, optional
        Ad-hoc overlay placements.

    Returns
    -------
    str
        Fully-formed memegen rendering URL.

    Raises
    ------
    ValueError
        If *extension* is unsupported.

    Examples
    --------
    >>> build_memegen_url(
    ...     "buzz", ["memes", "memes everywhere"],
    ...     api_base="https://api.memegen.link",
    ... )
    'https://api.memegen.link/images/buzz/memes/memes_everywhere.png'

    >>> build_memegen_url(
    ...     "ds", ["a", "b"],
    ...     api_base="https://api.memegen.link",
    ...     template_style="maga",
    ...     font="comic",
    ...     color="white,black",
    ...     width=600,
    ... )  # doctest: +ELLIPSIS
    'https://api.memegen.link/images/ds/a/b.png?style=maga&font=comic&...'
    """
    ext = extension.lower().lstrip(".")
    if ext not in _VALID_EXTENSIONS:
        raise ValueError(
            f"Unsupported extension {extension!r}. " f"Must be one of: {sorted(_VALID_EXTENSIONS)}"
        )

    base = api_base.rstrip("/")
    encoded = [_encode_segment(line) for line in lines]
    path = "/".join(encoded) if encoded else "_"

    url = f"{base}/images/{template_id}/{path}.{ext}"

    # Build query string preserving insertion order (style, font, color first
    # to match the docs' usual presentation; remaining params follow).
    params: list[tuple[str, str]] = []
    if template_style is not None:
        params.append(("style", template_style))
    if font is not None:
        params.append(("font", font))
    if color is not None:
        params.append(("color", color))
    if width is not None:
        params.append(("width", str(int(width))))
    if height is not None:
        params.append(("height", str(int(height))))
    if layout is not None:
        params.append(("layout", layout))
    if background is not None:
        params.append(("background", background))

    if overlays:
        for ov in overlays:
            ov_style = ov.get("style")
            if ov_style is not None:
                params.append(("style", ov_style))
            ov_center = ov.get("center")
            if ov_center is not None:
                params.append(("center", f"{ov_center[0]},{ov_center[1]}"))
            ov_scale = ov.get("scale")
            if ov_scale is not None:
                params.append(("scale", str(ov_scale)))

    if params:
        query = "&".join(f"{k}={_format_query_value(v)}" for k, v in params)
        url = f"{url}?{query}"

    return url
