"""Tests for the functional (simple) API."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from memeplotlib._api import meme, memify
from memeplotlib._template import Template, DEFAULT_TEXT_POSITIONS


class TestMemeFunction:
    def test_returns_figure_axes(self, sample_template, mocker):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = meme("test", "top", "bottom")
        assert isinstance(fig, plt.Figure)
        assert ax is not None

    def test_show_false_no_plt_show(self, sample_template, mocker):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mock_show = mocker.patch("matplotlib.pyplot.show")
        fig, ax = meme("test", "hello", show=False)
        mock_show.assert_not_called()

    def test_show_true_calls_plt_show(self, sample_template, mocker):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mock_show = mocker.patch("matplotlib.pyplot.show")
        meme("test", "hello", show=True)
        mock_show.assert_called_once()

    def test_savefig(self, sample_template, mocker, tmp_path):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mocker.patch("matplotlib.pyplot.show")
        output = tmp_path / "meme.png"
        meme("test", "top", "bottom", savefig=str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_custom_figsize(self, sample_template, mocker):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = meme("test", "hello", figsize=(4, 3))
        w, h = fig.get_size_inches()
        assert w == pytest.approx(4)
        assert h == pytest.approx(3)

    def test_render_onto_existing_axes(self, sample_template, mocker):
        mocker.patch("memeplotlib._api._resolve_template", return_value=sample_template)
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = plt.subplots()
        fig_out, ax_out = meme("test", "text", ax=ax)
        assert fig_out is fig
        assert ax_out is ax


class TestMemifyFunction:
    def test_returns_figure(self, mocker):
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        result = memify(fig, "stonks")
        assert result is fig

    def test_adds_overlay(self, mocker):
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = plt.subplots()
        memify(fig, "top", "bottom")
        assert len(fig.axes) == 2

    def test_savefig(self, mocker, tmp_path):
        mocker.patch("matplotlib.pyplot.show")
        fig, ax = plt.subplots()
        output = tmp_path / "memified.png"
        memify(fig, "stonks", savefig=str(output))
        assert output.exists()

    def test_show_false(self, mocker):
        mock_show = mocker.patch("matplotlib.pyplot.show")
        fig, ax = plt.subplots()
        memify(fig, "test", show=False)
        mock_show.assert_not_called()

    def test_position_options(self, mocker):
        mocker.patch("matplotlib.pyplot.show")
        for pos in ("top-bottom", "top", "bottom", "center"):
            fig, ax = plt.subplots()
            result = memify(fig, "text", position=pos)
            assert result is fig
