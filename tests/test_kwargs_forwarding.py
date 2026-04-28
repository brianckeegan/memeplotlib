"""Tests for **kwargs forwarding to Axes.text in meme() and memify()."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from memeplotlib._rendering import render_meme, render_memify  # noqa: E402


class TestRenderMemeKwargs:
    def test_alpha_forwarded_to_text(self, sample_template):
        fig, ax = render_meme(sample_template, ["hello", "world"], alpha=0.5)
        for txt in ax.texts:
            assert txt.get_alpha() == 0.5

    def test_rotation_forwarded(self, sample_template):
        fig, ax = render_meme(sample_template, ["hello"], rotation=15)
        assert ax.texts[0].get_rotation() == 15

    def test_user_kwarg_overrides_default(self, sample_template):
        # Default zorder for text is 3; user value should win.
        fig, ax = render_meme(sample_template, ["hello"], zorder=99)
        assert ax.texts[0].get_zorder() == 99


class TestRenderMemifyKwargs:
    def test_alpha_forwarded(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["caption"], alpha=0.7)
        overlay_ax = fig.axes[-1]
        assert overlay_ax.texts[0].get_alpha() == 0.7

    def test_rotation_forwarded(self):
        fig, ax = plt.subplots()
        render_memify(fig, ["sideways"], rotation=45)
        overlay_ax = fig.axes[-1]
        assert overlay_ax.texts[0].get_rotation() == 45
