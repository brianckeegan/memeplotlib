"""Object-oriented Meme API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from memeplotlib._cache import TemplateCache
from memeplotlib._config import config
from memeplotlib._rendering import render_meme
from memeplotlib._template import Template, _resolve_template

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class Meme:
    """A meme builder with a fluent (chainable) API.

    Example::

        from memeplotlib import Meme

        Meme("buzz").top("memes").bottom("memes everywhere").show()

        # Or step by step
        m = Meme("drake")
        m.top("writing tests")
        m.bottom("shipping to prod")
        fig, ax = m.render()
        m.save("output.png")
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
    ):
        if isinstance(template, Template):
            self._template = template
        else:
            self._template_str = template
            self._template: Template | None = None

        self._lines: list[str] = list(lines)
        self._font = font
        self._color = color
        self._outline_color = outline_color
        self._outline_width = outline_width
        self._fontsize = fontsize
        self._style = style
        self._fig: Figure | None = None
        self._ax: Axes | None = None
        self._cache = TemplateCache()

    def _get_template(self) -> Template:
        if self._template is None:
            self._template = _resolve_template(self._template_str)
        return self._template

    def top(self, text: str) -> Meme:
        """Set the top text line (index 0)."""
        if len(self._lines) == 0:
            self._lines.append(text)
        else:
            self._lines[0] = text
        return self

    def bottom(self, text: str) -> Meme:
        """Set the bottom text line (index 1)."""
        while len(self._lines) < 2:
            self._lines.append("")
        self._lines[1] = text
        return self

    def text(self, index: int, text: str) -> Meme:
        """Set text at a specific line index."""
        while len(self._lines) <= index:
            self._lines.append("")
        self._lines[index] = text
        return self

    def render(
        self,
        ax: Axes | None = None,
        figsize: tuple[float, float] | None = None,
        dpi: int | None = None,
    ) -> tuple[Figure, Axes]:
        """Render the meme and return (Figure, Axes)."""
        template = self._get_template()
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
        )
        self._fig = fig
        self._ax = ax_out
        return fig, ax_out

    def show(self) -> None:
        """Render and display the meme."""
        if self._fig is None:
            self.render()
        plt.show()

    def save(self, path: str | Path, dpi: int | None = None, **kwargs) -> None:
        """Render and save the meme to a file."""
        if self._fig is None:
            self.render(dpi=dpi)
        self._fig.savefig(
            str(path),
            dpi=dpi or config.dpi,
            bbox_inches="tight",
            pad_inches=0,
            **kwargs,
        )
