"""Tests for generated and user-supplied alt text."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from memeplotlib import Meme, Template, get_alt_text, meme, memify  # noqa: E402
from memeplotlib._alt import (  # noqa: E402
    default_meme_alt_text,
    default_memify_alt_text,
    savefig_metadata,
)
from memeplotlib._template import DEFAULT_TEXT_POSITIONS, TextPosition  # noqa: E402


def _template(**kwargs) -> Template:
    defaults = dict(id="buzz", name="Buzz Lightyear", image_url="x", is_memegen=True)
    defaults.update(kwargs)
    return Template(**defaults)


class TestDefaultText:
    def test_two_slot_memegen_template(self):
        assert default_meme_alt_text(_template(), ["memes", "memes everywhere"]) == (
            'Meme using the "Buzz Lightyear" template. '
            'Top text: "memes". Bottom text: "memes everywhere".'
        )

    def test_custom_image(self):
        tmpl = _template(id="photo", name="photo", is_memegen=False)
        assert default_meme_alt_text(tmpl, ["hi"]).startswith('Meme using the image "photo".')

    def test_multi_slot_template_numbers_lines(self):
        positions = [TextPosition(anchor_y=i / 4, scale_y=0.25) for i in range(4)]
        tmpl = _template(text_positions=positions, lines_count=4)
        alt = default_meme_alt_text(tmpl, ["a", "", "c"])
        assert alt.endswith('Line 1 text: "a". Line 3 text: "c".')

    def test_no_caption(self):
        assert default_meme_alt_text(_template(), ["", "  "]).endswith("with no caption.")

    def test_lines_without_a_slot_are_not_described(self):
        tmpl = _template(text_positions=list(DEFAULT_TEXT_POSITIONS))
        assert "three" not in default_meme_alt_text(tmpl, ["one", "two", "three"])

    def test_memify(self):
        assert default_memify_alt_text("bottom", ["not stonks"]) == (
            'Figure with a meme caption. Bottom text: "not stonks".'
        )


class TestSavefigMetadata:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("a.png", {"Description": "alt"}),
            ("a.SVG", {"Description": "alt"}),
            ("a.pdf", {"Subject": "alt"}),
            ("a.jpg", {}),
        ],
    )
    def test_key_per_format(self, path, expected):
        assert savefig_metadata(path, "alt") == expected

    def test_empty_alt(self):
        assert savefig_metadata("a.png", None) == {}


class TestMeme:
    def test_alt_uses_captions_as_typed(self, sample_image_file):
        fig, ax = meme(sample_image_file, "Hello there", "General Kenobi")
        alt = get_alt_text(fig)
        assert 'Top text: "Hello there".' in alt
        assert 'Bottom text: "General Kenobi".' in alt
        # The image itself is upper-cased; the description is not.
        assert "HELLO THERE" in [t.get_text() for t in ax.texts]

    def test_user_alt_text_wins(self, sample_image_file):
        fig, ax = meme(sample_image_file, "a", alt_text="A custom description")
        assert get_alt_text(fig) == get_alt_text(ax) == "A custom description"

    def test_png_embeds_description(self, sample_image_file, tmp_path):
        out = tmp_path / "m.png"
        fig, _ = meme(sample_image_file, "a", "b", savefig=out)
        assert Image.open(out).info["Description"] == get_alt_text(fig)

    def test_jpg_saves_without_metadata(self, sample_image_file, tmp_path):
        out = tmp_path / "m.jpg"
        meme(sample_image_file, "a", savefig=out)
        assert out.exists()

    def test_subplots_join_descriptions(self, sample_image_file):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        meme(sample_image_file, "left", ax=ax1)
        meme(sample_image_file, "right", ax=ax2)
        alt = get_alt_text(fig)
        assert alt.index('"left"') < alt.index('"right"')

    def test_plain_figure_has_none(self):
        fig, ax = plt.subplots()
        assert get_alt_text(fig) is None
        assert get_alt_text(ax) is None


class TestMemify:
    def test_default_and_png_metadata(self, tmp_path):
        fig, ax = plt.subplots()
        out = tmp_path / "m.png"
        memify(fig, "stonks", savefig=out)
        assert get_alt_text(fig) == 'Figure with a meme caption. Top text: "stonks".'
        assert Image.open(out).info["Description"] == get_alt_text(fig)

    def test_appends_to_existing_alt(self, sample_image_file):
        fig, _ = meme(sample_image_file, "base")
        memify(fig, "overlay", position="bottom")
        alt = get_alt_text(fig)
        assert '"base"' in alt and 'Bottom text: "overlay".' in alt

    def test_override(self):
        fig, _ = plt.subplots()
        memify(fig, "x", alt_text="custom")
        assert get_alt_text(fig) == "custom"


class TestMemeClass:
    def test_property_and_chaining(self, sample_template):
        m = Meme(sample_template, "a", "b")
        assert 'Top text: "a".' in m.alt_text
        assert m.with_alt_text("custom") is m
        assert m.alt_text == "custom"
        assert m.with_alt_text(None).alt_text != "custom"

    def test_render_attaches_and_save_embeds(self, sample_template, tmp_path):
        m = Meme(sample_template, "a", "b", alt_text="described")
        fig, _ = m.render()
        assert get_alt_text(fig) == "described"
        m.save(tmp_path / "m.png")
        assert Image.open(tmp_path / "m.png").info["Description"] == "described"

    def test_with_alt_text_after_render_updates_figure(self, sample_template):
        m = Meme(sample_template, "a")
        fig, _ = m.render()
        m.with_alt_text("later")
        assert get_alt_text(fig) == "later"

    def test_user_metadata_takes_precedence(self, sample_template, tmp_path):
        m = Meme(sample_template, "a", alt_text="auto")
        m.save(tmp_path / "m.png", metadata={"Description": "mine", "Author": "me"})
        info = Image.open(tmp_path / "m.png").info
        assert info["Description"] == "mine"
        assert info["Author"] == "me"
