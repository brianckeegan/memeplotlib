"""Alternative text (alt text) for rendered memes.

A meme is text inside a picture, so without a text alternative it is
invisible to screen-reader users. memeplotlib already knows the template
name and the captions, so every render gets a default description that
callers can override. The description is attached to the matplotlib
artists and embedded in files memeplotlib saves.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from memeplotlib._template import Template

_ALT_ATTR = "_memeplotlib_alt_text"

# Savefig metadata key that carries a description, per output format.
# PNG and SVG both define "Description"; PDF's document-info equivalent is
# "Subject". Formats without text metadata (e.g. JPEG) get none.
_METADATA_KEYS = {".png": "Description", ".svg": "Description", ".pdf": "Subject"}

_MEMIFY_LABELS = {
    "top-bottom": ["Top", "Bottom"],
    "top": ["Top"],
    "bottom": ["Bottom"],
    "center": ["Center"],
}


def _describe(subject: str, labels: Sequence[str], lines: Sequence[str]) -> str:
    parts = [
        f'{label} text: "{line.strip()}".'
        # Lines without a slot are not rendered, so they are not described.
        for label, line in zip(labels, lines, strict=False)
        if line and line.strip()
    ]
    if not parts:
        return f"{subject} with no caption."
    return " ".join([f"{subject}.", *parts])


def default_meme_alt_text(template: Template, lines: Sequence[str]) -> str:
    """Describe a meme from its template and captions.

    Captions are used as typed rather than in their rendered style, because
    many screen readers spell out ALL-CAPS words letter by letter.

    Parameters
    ----------
    template : Template
        The resolved template.
    lines : sequence of str
        Caption text per slot, as passed by the caller.

    Returns
    -------
    str
        A one-paragraph description.
    """
    name = template.name or template.id
    if template.is_memegen:
        subject = f'Meme using the "{name}" template'
    else:
        subject = f'Meme using the image "{name}"'
    slots = max(len(template.text_positions), template.lines_count)
    labels = ["Top", "Bottom"] if slots == 2 else [f"Line {i + 1}" for i in range(slots)]
    return _describe(subject, labels, lines)


def default_memify_alt_text(position: str, lines: Sequence[str]) -> str:
    """Describe the caption overlay that :func:`memify` adds to a figure.

    Parameters
    ----------
    position : str
        The ``memify`` position preset.
    lines : sequence of str
        Caption text, as passed by the caller.

    Returns
    -------
    str
        A one-paragraph description.
    """
    return _describe("Figure with a meme caption", _MEMIFY_LABELS.get(position, []), lines)


def set_alt_text(artist: Figure | Axes, text: str) -> None:
    """Attach *text* as the alt text of a Figure or Axes."""
    setattr(artist, _ALT_ATTR, text)


def get_alt_text(artist: Figure | Axes) -> str | None:
    """Return the alt text memeplotlib attached to a Figure or Axes.

    Every :func:`~memeplotlib.meme`, :func:`~memeplotlib.memify`, and
    :class:`~memeplotlib.Meme` render records a description of the image.
    Use it as the ``alt`` attribute when publishing the meme on the web,
    in chat, or in documentation.

    Parameters
    ----------
    artist : matplotlib.figure.Figure or matplotlib.axes.Axes
        A figure or axes returned by memeplotlib. For a figure holding
        several memes (e.g. subplots), the descriptions of its axes are
        joined in order.

    Returns
    -------
    str or None
        The description, or ``None`` if memeplotlib did not render it.

    Examples
    --------
    >>> import memeplotlib as memes
    >>> fig, ax = memes.meme("buzz", "memes", "memes everywhere")  # doctest: +SKIP
    >>> memes.get_alt_text(fig)  # doctest: +SKIP
    'Meme using the "Buzz Lightyear" template. Top text: "memes". Bottom text: "memes everywhere".'
    """
    own = getattr(artist, _ALT_ATTR, None)
    if own is not None:
        return str(own)
    axes = getattr(artist, "axes", None)
    if isinstance(axes, list):  # a Figure: combine its memes in order
        parts = [str(getattr(ax, _ALT_ATTR)) for ax in axes if hasattr(ax, _ALT_ATTR)]
        if parts:
            return " ".join(parts)
    return None


def savefig_metadata(path: str | Path, alt_text: str | None) -> dict[str, str]:
    """Return ``savefig`` metadata embedding *alt_text* for *path*'s format."""
    if not alt_text:
        return {}
    key = _METADATA_KEYS.get(Path(path).suffix.lower())
    return {key: alt_text} if key else {}
