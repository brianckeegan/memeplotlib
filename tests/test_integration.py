"""End-to-end integration tests (require network access).

Run with: pytest tests/test_integration.py -v -m integration
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import pytest


pytestmark = [pytest.mark.slow, pytest.mark.integration]


class TestEndToEnd:
    def test_create_buzz_meme(self, tmp_path):
        import memeplotlib as memes

        output = tmp_path / "buzz.png"
        fig, ax = memes.meme(
            "buzz",
            "integration tests",
            "integration tests everywhere",
            show=False,
            savefig=str(output),
        )
        assert output.exists()
        assert output.stat().st_size > 1000  # non-trivial file
        assert fig is not None

    def test_create_drake_meme(self, tmp_path):
        import memeplotlib as memes

        output = tmp_path / "drake.png"
        fig, ax = memes.meme(
            "drake",
            "writing tests",
            "shipping to prod",
            show=False,
            savefig=str(output),
        )
        assert output.exists()

    def test_meme_oo_api(self, tmp_path):
        from memeplotlib import Meme

        output = tmp_path / "oo_meme.png"
        m = Meme("buzz")
        m.top("object oriented")
        m.bottom("meme creation")
        m.save(str(output))
        assert output.exists()

    def test_meme_chaining(self, tmp_path):
        from memeplotlib import Meme

        output = tmp_path / "chained.png"
        m = Meme("doge").top("such code").bottom("very test")
        m.save(str(output))
        assert output.exists()

    def test_memify_plot(self, tmp_path):
        import matplotlib.pyplot as plt
        import memeplotlib as memes

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        output = tmp_path / "memified.png"
        memes.memify(fig, "stonks", show=False, savefig=str(output))
        assert output.exists()

    def test_template_search(self):
        from memeplotlib import TemplateRegistry

        reg = TemplateRegistry()
        results = reg.search("dog")
        assert len(results) > 0

    def test_template_list(self):
        from memeplotlib import TemplateRegistry

        reg = TemplateRegistry()
        all_templates = reg.list_all()
        assert len(all_templates) > 50  # memegen has hundreds of templates
