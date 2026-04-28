"""Object-oriented Meme API."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt

from memeplotlib._cache import TemplateCache
from memeplotlib._config import config
from memeplotlib._rendering import render_meme
from memeplotlib._template import Template, TextPosition, _resolve_template
from memeplotlib._url import OverlaySpec

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class Meme:
    """A meme builder with a fluent (chainable) API.

    Parameters
    ----------
    template : str or Template
        Template identifier (memegen ID, file path, URL) or a
        :class:`Template` instance.
    *lines : str
        Initial text lines.
    font : str or None, optional
        Font family name.
    color : str or None, optional
        Text fill color.
    outline_color : str or None, optional
        Text outline color.
    outline_width : float or None, optional
        Outline stroke width.
    fontsize : float or None, optional
        Font size in points.
    style : str or None, optional
        Text transform -- ``"upper"``, ``"lower"``, or ``"none"``.
    backend : str or None, optional
        Override the rendering backend (``"auto"``, ``"memegen"``,
        ``"pillow"``, ``"matplotlib"``). ``None`` uses ``config["backend"]``.

    Examples
    --------
    >>> from memeplotlib import Meme
    >>> Meme("buzz").top("memes").bottom("memes everywhere").show()  # doctest: +SKIP

    >>> m = Meme("drake")  # doctest: +SKIP
    >>> m.top("writing tests")  # doctest: +SKIP
    >>> m.bottom("shipping to prod")  # doctest: +SKIP
    >>> fig, ax = m.render()  # doctest: +SKIP
    >>> m.save("output.png")  # doctest: +SKIP

    >>> # Per-line override forces the Pillow backend.
    >>> Meme("buzz").top("hi").line(1, "world", fontsize=48).save("out.png")  # doctest: +SKIP
    """

    def __init__(
        self,
        template: str | Template,
        *lines: str,
        font: str | None = None,
        color: str | None = None,
        outline_color: str | None = None,
        outline_width: float | None = None,
        fontsize: float | None = None,
        style: str | None = None,
        backend: str | None = None,
        extension: str | None = None,
        width: int | None = None,
        height: int | None = None,
        layout: str | None = None,
        background: str | None = None,
        overlays: Sequence[OverlaySpec] | None = None,
        template_style: str | None = None,
    ):
        self._template_str: str | None = None
        self._template: Template | None = None

        if isinstance(template, Template):
            self._template = template
        else:
            self._template_str = template

        self._lines: list[str] = list(lines)
        self._font = font
        self._color = color
        self._outline_color = outline_color
        self._outline_width = outline_width
        self._fontsize = fontsize
        self._style = style
        self._backend = backend
        self._extension = extension
        self._width = width
        self._height = height
        self._layout = layout
        self._background = background
        self._overlays = list(overlays) if overlays else None
        self._template_style = template_style
        self._per_line_overrides: dict[int, dict[str, object]] = {}
        self._fig: Figure | None = None
        self._ax: Axes | None = None
        self._cache = TemplateCache()

    def _get_template(self) -> Template:
        if self._template is None:
            assert self._template_str is not None  # set by __init__ when _template is None
            self._template = _resolve_template(self._template_str)
        return self._template

    def top(self, text: str) -> Meme:
        """Set the top text line (index 0).

        Parameters
        ----------
        text : str
            The text to place at the top of the meme.

        Returns
        -------
        Meme
            Self, for method chaining.
        """
        if len(self._lines) == 0:
            self._lines.append(text)
        else:
            self._lines[0] = text
        return self

    def bottom(self, text: str) -> Meme:
        """Set the bottom text line (index 1).

        Parameters
        ----------
        text : str
            The text to place at the bottom of the meme.

        Returns
        -------
        Meme
            Self, for method chaining.
        """
        while len(self._lines) < 2:
            self._lines.append("")
        self._lines[1] = text
        return self

    def text(self, index: int, text: str) -> Meme:
        """Set text at a specific line index.

        Parameters
        ----------
        index : int
            Zero-based line index.
        text : str
            The text to place at the given position.

        Returns
        -------
        Meme
            Self, for method chaining.
        """
        while len(self._lines) <= index:
            self._lines.append("")
        self._lines[index] = text
        return self

    def line(
        self,
        index: int,
        text: str,
        *,
        fontsize: float | None = None,
        color: str | None = None,
        font: str | None = None,
        position: TextPosition | None = None,
    ) -> Meme:
        """Set text and per-line styling overrides for a single slot.

        Passing any of ``fontsize``, ``color``, ``font``, or ``position``
        forces the Pillow backend on render (memegen has no equivalent).

        Parameters
        ----------
        index : int
            Zero-based line index.
        text : str
            The text to place at the given slot.
        fontsize : float, optional
            Override font size for this slot.
        color : str, optional
            Override fill colour for this slot.
        font : str, optional
            Override font family for this slot.
        position : TextPosition, optional
            Override the text-box position metadata for this slot.

        Returns
        -------
        Meme
            Self, for method chaining.
        """
        self.text(index, text)
        override: dict[str, object] = {}
        if fontsize is not None:
            override["fontsize"] = fontsize
        if color is not None:
            override["color"] = color
        if font is not None:
            override["font"] = font
        if position is not None:
            override["position"] = position
        if override:
            self._per_line_overrides[index] = override
        return self

    def with_backend(self, backend: str) -> Meme:
        """Set the rendering backend.

        Parameters
        ----------
        backend : str
            One of ``"auto"``, ``"memegen"``, ``"pillow"``, ``"matplotlib"``.

        Returns
        -------
        Meme
            Self, for method chaining.
        """
        self._backend = backend
        return self

    def render(
        self,
        ax: Axes | None = None,
        figsize: tuple[float, float] | None = None,
        dpi: int | None = None,
    ) -> tuple[Figure, Axes]:
        """Render the meme and return the Figure and Axes.

        Parameters
        ----------
        ax : Axes or None, optional
            Existing axes to render onto.
        figsize : tuple of (float, float) or None, optional
            Figure size in inches ``(width, height)``.
        dpi : int or None, optional
            Dots per inch.

        Returns
        -------
        tuple of (Figure, Axes)
            The rendered matplotlib Figure and Axes.
        """
        template = self._get_template()
        force_pillow = bool(self._per_line_overrides)
        backend_val = self._backend if self._backend is not None else config["backend"]
        fig, ax_out = render_meme(
            template,
            self._lines,
            ax=ax,
            figsize=figsize,
            dpi=dpi,
            font=self._font,
            color=self._color,
            outline_color=self._outline_color,
            outline_width=self._outline_width,
            fontsize=self._fontsize,
            style=self._style,
            cache=self._cache,
            backend=backend_val,
            extension=self._extension,
            width=self._width,
            height=self._height,
            layout=self._layout,
            background=self._background,
            overlays=self._overlays,
            template_style=self._template_style,
            force_pillow=force_pillow,
            per_line_overrides=self._per_line_overrides or None,
        )
        self._fig = fig
        self._ax = ax_out
        return fig, ax_out

    def show(self) -> None:
        """Render and display the meme.

        Calls :meth:`render` if the meme has not been rendered yet,
        then displays the figure with ``matplotlib.pyplot.show()``.
        """
        if self._fig is None:
            self.render()
        plt.show()

    def save(self, path: str | Path, dpi: int | None = None, **kwargs: Any) -> None:
        """Render and save the meme to a file.

        Parameters
        ----------
        path : str or Path
            Output file path (e.g., ``"meme.png"``).
        dpi : int or None, optional
            Dots per inch for the saved image.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.figure.Figure.savefig`.
        """
        if self._fig is None:
            self.render(dpi=dpi)
        assert self._fig is not None  # render() always assigns self._fig
        self._fig.savefig(
            str(path),
            dpi=dpi if dpi is not None else config["dpi"],
            bbox_inches="tight",
            pad_inches=0,
            **kwargs,
        )
