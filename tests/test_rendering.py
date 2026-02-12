"""Tests for the matplotlib rendering pipeline."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import patheffects

from memeplotlib._rendering import (
    _auto_fontsize,
    _draw_meme_text,
    _resolve_font,
    _smart_wrap,
    render_meme,
    render_memify,
)
from memeplotlib._template import DEFAULT_TEXT_POSITIONS, TextPosition


class TestResolveFont:
    def test_returns_string(self):
        result = _resolve_font("impact")
        assert isinstance(result, str)

    def test_known_fonts_mapped(self):
        # Even if Impact isn't installed, should return a string
        result = _resolve_font("impact")
        assert result in ("Impact", "Anton")

    def test_unknown_font_warns(self):
        with pytest.warns(UserWarning, match="not found"):
            _resolve_font("ZZZNonexistentFont123")


class TestAutoFontsize:
    def test_returns_positive_float(self):
        size = _auto_fontsize("hello", 1.0, 0.2)
        assert size > 0

    def test_longer_text_smaller_font(self):
        short = _auto_fontsize("hi", 1.0, 0.2)
        long = _auto_fontsize("this is a much longer piece of text for the meme", 1.0, 0.2)
        assert long < short

    def test_multi_line_smaller_font(self):
        single = _auto_fontsize("hello", 1.0, 0.2)
        multi = _auto_fontsize("hello\nworld\nfoo", 1.0, 0.2)
        assert multi < single

    def test_wider_box_larger_font(self):
        narrow = _auto_fontsize("hello", 0.3, 0.2)
        wide = _auto_fontsize("hello", 1.0, 0.2)
        assert wide > narrow


class TestSmartWrap:
    def test_short_text_no_wrap(self):
        assert _smart_wrap("hello", 1.0) == "hello"

    def test_long_text_wrapped(self):
        text = "this is a really long text that should definitely be wrapped into lines"
        result = _smart_wrap(text, 1.0)
        assert "\n" in result

    def test_already_wrapped_unchanged(self):
        text = "line1\nline2"
        assert _smart_wrap(text, 1.0) == text


class TestDrawMemeText:
    def test_creates_text_object(self):
        fig, ax = plt.subplots()
        pos = TextPosition()
        txt = _draw_meme_text(ax, "hello", 0.5, 0.9, pos)
        assert txt is not None
        assert txt.get_text() == "HELLO"  # default style is upper

    def test_text_has_path_effects(self):
        fig, ax = plt.subplots()
        pos = TextPosition()
        txt = _draw_meme_text(ax, "hello", 0.5, 0.9, pos)
        effects = txt.get_path_effects()
        assert len(effects) == 2
        assert isinstance(effects[0], patheffects.Stroke)

    def test_custom_color(self):
        fig, ax = plt.subplots()
        pos = TextPosition()
        txt = _draw_meme_text(ax, "hello", 0.5, 0.9, pos, color="yellow")
        assert txt.get_color() == "yellow"

    def test_style_none_preserves_case(self):
        fig, ax = plt.subplots()
        pos = TextPosition()
        txt = _draw_meme_text(ax, "Hello World", 0.5, 0.9, pos, style="none")
        assert txt.get_text() == "Hello World"

    def test_style_lower(self):
        fig, ax = plt.subplots()
        pos = TextPosition()
        txt = _draw_meme_text(ax, "HELLO", 0.5, 0.9, pos, style="lower")
        assert txt.get_text() == "hello"


class TestRenderMeme:
    def test_returns_figure_and_axes(self, sample_template):
        fig, ax = render_meme(sample_template, ["top", "bottom"])
        assert isinstance(fig, plt.Figure)
        assert ax is not None

    def test_axis_is_off(self, sample_template):
        fig, ax = render_meme(sample_template, ["hello", "world"])
        # Check that axis frame/ticks are hidden
        assert not ax.axison

    def test_renders_with_no_text(self, sample_template):
        fig, ax = render_meme(sample_template, [])
        assert isinstance(fig, plt.Figure)

    def test_renders_with_one_line(self, sample_template):
        fig, ax = render_meme(sample_template, ["top only"])
        assert isinstance(fig, plt.Figure)

    def test_renders_onto_existing_axes(self, sample_template):
        fig, ax = plt.subplots()
        fig_out, ax_out = render_meme(sample_template, ["hi", "there"], ax=ax)
        assert fig_out is fig
        assert ax_out is ax

    def test_custom_figsize(self, sample_template):
        fig, ax = render_meme(sample_template, ["test"], figsize=(4, 3))
        w, h = fig.get_size_inches()
        assert w == pytest.approx(4)
        assert h == pytest.approx(3)

    def test_custom_dpi(self, sample_template):
        fig, ax = render_meme(sample_template, ["test"], dpi=72)
        assert fig.dpi == 72

    def test_text_objects_present(self, sample_template):
        fig, ax = render_meme(sample_template, ["top text", "bottom text"])
        texts = ax.texts
        assert len(texts) == 2

    def test_extra_lines_ignored(self, sample_template):
        # Template has 2 positions, 3 lines given — third should be ignored
        fig, ax = render_meme(sample_template, ["one", "two", "three"])
        texts = ax.texts
        assert len(texts) == 2


class TestRenderMemify:
    def test_adds_overlay_axes(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        result = render_memify(fig, ["stonks"])
        assert result is fig
        # Should have added an overlay axes
        assert len(fig.axes) == 2

    def test_overlay_has_text(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["top", "bottom"])
        overlay_ax = fig.axes[-1]
        assert len(overlay_ax.texts) == 2

    def test_position_top_only(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["header"], position="top")
        overlay_ax = fig.axes[-1]
        assert len(overlay_ax.texts) == 1

    def test_position_bottom_only(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["footer"], position="bottom")
        overlay_ax = fig.axes[-1]
        assert len(overlay_ax.texts) == 1

    def test_position_center(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["centered"], position="center")
        overlay_ax = fig.axes[-1]
        assert len(overlay_ax.texts) == 1
