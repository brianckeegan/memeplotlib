"""Tests for the Meme OO API."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from memeplotlib._meme import Meme
from memeplotlib._template import Template, DEFAULT_TEXT_POSITIONS


class TestMemeInit:
    def test_from_template_object(self, sample_template):
        m = Meme(sample_template)
        assert m._get_template() is sample_template

    def test_from_string_with_lines(self, sample_template):
        m = Meme(sample_template, "top", "bottom")
        assert m._lines == ["top", "bottom"]


class TestMemeChaining:
    def test_top_returns_self(self, sample_template):
        m = Meme(sample_template)
        result = m.top("hello")
        assert result is m

    def test_bottom_returns_self(self, sample_template):
        m = Meme(sample_template)
        result = m.bottom("world")
        assert result is m

    def test_text_returns_self(self, sample_template):
        m = Meme(sample_template)
        result = m.text(0, "hello")
        assert result is m

    def test_chain_top_bottom(self, sample_template):
        m = Meme(sample_template).top("hello").bottom("world")
        assert m._lines == ["hello", "world"]

    def test_top_overwrites(self, sample_template):
        m = Meme(sample_template, "original")
        m.top("replaced")
        assert m._lines[0] == "replaced"

    def test_bottom_pads_empty(self, sample_template):
        m = Meme(sample_template)
        m.bottom("world")
        assert m._lines == ["", "world"]

    def test_text_at_index(self, sample_template):
        m = Meme(sample_template)
        m.text(3, "fourth")
        assert len(m._lines) == 4
        assert m._lines[3] == "fourth"


class TestMemeRender:
    def test_render_returns_figure_axes(self, sample_template):
        m = Meme(sample_template, "top", "bottom")
        fig, ax = m.render()
        assert isinstance(fig, plt.Figure)
        assert ax is not None

    def test_render_onto_existing_axes(self, sample_template):
        fig, ax = plt.subplots()
        m = Meme(sample_template, "hello")
        fig_out, ax_out = m.render(ax=ax)
        assert fig_out is fig
        assert ax_out is ax

    def test_save(self, sample_template, tmp_path):
        m = Meme(sample_template, "save", "test")
        output = tmp_path / "output.png"
        m.save(str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_show_triggers_render(self, sample_template, mocker):
        mocker.patch("matplotlib.pyplot.show")
        m = Meme(sample_template, "hello")
        m.show()
        plt.show.assert_called_once()  # type: ignore[attr-defined]
        assert m._fig is not None
