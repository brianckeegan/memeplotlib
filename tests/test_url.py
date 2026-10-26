"""Tests for the memegen URL builder."""

from __future__ import annotations

import pytest

from memeplotlib._url import (
    MEMEGEN_FONT_ALIASES,
    build_memegen_url,
    memegen_font_for,
)

API_BASE = "https://api.memegen.link"


class TestBuildMemegenUrl:
    def test_basic_url(self):
        url = build_memegen_url("buzz", ["hello", "world"], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/hello/world.png"

    def test_spaces_become_underscores(self):
        url = build_memegen_url("buzz", ["hello world", "memes everywhere"], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/hello_world/memes_everywhere.png"

    def test_empty_line_becomes_underscore(self):
        url = build_memegen_url("ds", ["a", "", "c"], api_base=API_BASE)
        # Middle empty slot must remain to preserve slot ordering.
        assert url == "https://api.memegen.link/images/ds/a/_/c.png"

    def test_single_empty_line(self):
        url = build_memegen_url("buzz", [""], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/_.png"

    def test_no_lines_uses_underscore(self):
        url = build_memegen_url("buzz", [], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/_.png"

    def test_special_chars_escaped(self):
        url = build_memegen_url("buzz", ["what?", "100% & rising"], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/what~q/100~p_~a_rising.png"

    def test_slash_escaped(self):
        url = build_memegen_url("buzz", ["a/b"], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/a~sb.png"

    def test_underscore_doubled(self):
        url = build_memegen_url("buzz", ["a_b"], api_base=API_BASE)
        assert url == "https://api.memegen.link/images/buzz/a__b.png"

    def test_extension_jpg(self):
        url = build_memegen_url("buzz", ["hello"], api_base=API_BASE, extension="jpg")
        assert url.endswith("/hello.jpg")

    def test_extension_with_leading_dot(self):
        url = build_memegen_url("buzz", ["hello"], api_base=API_BASE, extension=".webp")
        assert url.endswith(".webp")

    def test_invalid_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported extension"):
            build_memegen_url("buzz", ["hi"], api_base=API_BASE, extension="bmp")

    def test_template_style(self):
        url = build_memegen_url("ds", ["a", "b"], api_base=API_BASE, template_style="maga")
        assert url == "https://api.memegen.link/images/ds/a/b.png?style=maga"

    def test_font_color_dimensions(self):
        url = build_memegen_url(
            "buzz",
            ["a", "b"],
            api_base=API_BASE,
            font="comic",
            color="white,black",
            width=600,
            height=400,
        )
        # Order is style → font → color → width → height per the builder.
        assert url == (
            "https://api.memegen.link/images/buzz/a/b.png"
            "?font=comic&color=white,black&width=600&height=400"
        )

    def test_layout_and_background(self):
        url = build_memegen_url(
            "custom",
            ["a", "b"],
            api_base=API_BASE,
            layout="top",
            background="https://example.com/bg.png",
        )
        assert "layout=top" in url
        assert "background=" in url
        # The background URL gets quoted but ":/" should remain readable.
        assert "https://example.com/bg.png" in url

    def test_overlays(self):
        url = build_memegen_url(
            "ds",
            ["a", "b"],
            api_base=API_BASE,
            overlays=[{"style": "https://x/y.png", "center": (0.5, 0.5), "scale": 1.2}],
        )
        assert "style=https://x/y.png" in url
        assert "center=0.5,0.5" in url
        assert "scale=1.2" in url

    def test_tilde_not_percent_encoded(self):
        # `~` is the marker for memegen escapes; must not be % encoded by the
        # query-string builder.
        url = build_memegen_url(
            "buzz", ["a?b"], api_base=API_BASE, color="red", template_style="x~y"
        )
        assert "~" in url
        assert "%7E" not in url

    def test_api_base_with_trailing_slash(self):
        url = build_memegen_url("buzz", ["a"], api_base="https://api.memegen.link/")
        assert "memegen.link//" not in url
        assert url == "https://api.memegen.link/images/buzz/a.png"


class TestMemegenFontFor:
    def test_known_alias(self):
        assert memegen_font_for("impact") == "impact"

    def test_case_insensitive(self):
        assert memegen_font_for("Comic") == "comic"

    def test_default_means_template_font(self):
        # "" = send no font= so each template keeps its designed font.
        assert memegen_font_for("default") == ""

    @pytest.mark.parametrize(
        "font", ["thick", "titilliumweb", "thin", "tiny", "segoe", "kalam", "hgminchob"]
    )
    def test_live_upstream_fonts_are_known(self, font):
        assert memegen_font_for(font) == font

    def test_tw_is_not_a_memegen_font(self):
        # memegen returns 422 for font=tw.
        assert memegen_font_for("tw") is None

    def test_unknown_font_returns_none(self):
        assert memegen_font_for("arial") is None

    def test_alias_table_has_canonical_set(self):
        # Sanity check that the documented set is present.
        for name in ("impact", "thick", "thin", "tiny", "comic", "notosans", "kalam"):
            assert name in MEMEGEN_FONT_ALIASES


class TestBackgroundOnlyOnCustom:
    def test_background_on_other_template_warns(self):
        with pytest.warns(UserWarning, match="only|except on the 'custom'"):
            build_memegen_url("fine", ["a"], api_base=API_BASE, background="https://x/bg.png")


class TestOverlayStyleJoining:
    """memegen reads one style= value; overlays must be comma-joined."""

    def test_multiple_overlays_are_comma_joined(self):
        url = build_memegen_url(
            "drake",
            ["a", "b"],
            api_base=API_BASE,
            overlays=[{"style": "https://x/a.png"}, {"style": "https://x/b.png"}],
        )
        assert url.count("style=") == 1
        assert "style=https://x/a.png,https://x/b.png" in url

    def test_center_scale_only_from_first_overlay(self):
        with pytest.warns(UserWarning, match="first overlay only"):
            url = build_memegen_url(
                "drake",
                ["a"],
                api_base=API_BASE,
                overlays=[
                    {"style": "https://x/a.png", "center": (0.2, 0.3), "scale": 0.5},
                    {"style": "https://x/b.png", "center": (0.8, 0.8)},
                ],
            )
        assert url.count("center=") == 1 and "center=0.2,0.3" in url
        assert url.count("scale=") == 1

    def test_template_style_wins_over_overlays_with_warning(self):
        with pytest.warns(UserWarning, match="cannot combine template_style"):
            url = build_memegen_url(
                "ds",
                ["a"],
                api_base=API_BASE,
                template_style="maga",
                overlays=[{"style": "https://x/a.png"}],
            )
        assert "style=maga" in url and "x/a.png" not in url

    def test_center_without_url_positions_builtin_overlay(self):
        url = build_memegen_url(
            "pigeon", ["a"], api_base=API_BASE, overlays=[{"center": (0.4, 0.6)}]
        )
        assert "style=" not in url and "center=0.4,0.6" in url
