"""Tests for the memegen / pillow rendering backends and the dispatcher."""

from __future__ import annotations

import io

import numpy as np
import pytest
import responses
from PIL import Image

import memeplotlib as memes
from memeplotlib import meme
from memeplotlib._rendering import _select_backend
from memeplotlib._template import Template
from tests.conftest import memegen_rendered_pattern

API_BASE = "https://api.memegen.link"

pytestmark = pytest.mark.uses_default_backend


@pytest.fixture
def fake_png_bytes():
    rng = np.random.default_rng(seed=7)
    img = Image.fromarray(rng.integers(0, 255, (80, 160, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def buzz_metadata_response():
    """Register a memegen catalogue + per-template metadata mock."""
    responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
    responses.add(
        responses.GET,
        f"{API_BASE}/templates/buzz",
        json={
            "id": "buzz",
            "name": "Buzz Lightyear",
            "lines": 2,
            "overlays": 0,
            "styles": [],
            "blank": f"{API_BASE}/images/buzz.png",
            "keywords": [],
            "example": {"text": []},
        },
    )


@pytest.fixture(autouse=True)
def _isolate_registry_and_cache(tmp_path, monkeypatch):
    import memeplotlib._template as t
    from memeplotlib import config

    monkeypatch.setitem(config, "cache_dir", str(tmp_path / "cache"))
    monkeypatch.setitem(config, "cache_enabled", False)
    original = t._registry
    t._registry = None
    yield
    t._registry = original


class TestBackendSelection:
    def _tmpl(self, *, is_memegen: bool):
        return Template(
            id="x",
            name="x",
            image_url="https://example.com/x.png",
            is_memegen=is_memegen,
        )

    def test_explicit_backend_passes_through(self):
        assert (
            _select_backend(
                "pillow",
                self._tmpl(is_memegen=True),
                font="impact",
                force_pillow=False,
                text_kwargs={},
                per_line_overrides=None,
            )
            == "pillow"
        )

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            _select_backend(
                "qubit",
                self._tmpl(is_memegen=True),
                font="impact",
                force_pillow=False,
                text_kwargs={},
                per_line_overrides=None,
            )

    def test_memegen_falls_back_when_template_not_memegen(self):
        with pytest.warns(UserWarning, match="not from the memegen catalog"):
            chosen = _select_backend(
                "memegen",
                self._tmpl(is_memegen=False),
                font="impact",
                force_pillow=False,
                text_kwargs={},
                per_line_overrides=None,
            )
        assert chosen == "pillow"

    def test_auto_picks_memegen_for_memegen_template(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=True),
            font="impact",
            force_pillow=False,
            text_kwargs={},
            per_line_overrides=None,
        )
        assert chosen == "memegen"

    def test_auto_picks_pillow_for_custom_template(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=False),
            font="impact",
            force_pillow=False,
            text_kwargs={},
            per_line_overrides=None,
        )
        assert chosen == "pillow"

    def test_auto_picks_pillow_when_force_pillow(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=True),
            font="impact",
            force_pillow=True,
            text_kwargs={},
            per_line_overrides=None,
        )
        assert chosen == "pillow"

    def test_auto_picks_pillow_for_unknown_font(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=True),
            font="papyrus",  # not in MEMEGEN_FONT_ALIASES
            force_pillow=False,
            text_kwargs={},
            per_line_overrides=None,
        )
        assert chosen == "pillow"

    def test_auto_picks_pillow_with_text_kwargs(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=True),
            font="impact",
            force_pillow=False,
            text_kwargs={"alpha": 0.5},
            per_line_overrides=None,
        )
        assert chosen == "pillow"

    def test_auto_picks_pillow_with_per_line_overrides(self):
        chosen = _select_backend(
            "auto",
            self._tmpl(is_memegen=True),
            font="impact",
            force_pillow=False,
            text_kwargs={},
            per_line_overrides={1: {"fontsize": 48}},
        )
        assert chosen == "pillow"


class TestMemeMemegenBackend:
    @responses.activate
    def test_meme_calls_memegen_render_url(self, buzz_metadata_response, fake_png_bytes, tmp_path):
        # The dispatcher constructs an `/images/buzz/<lines>.png` URL; mock
        # the whole pattern so any caption text returns the same fake PNG.
        responses.add(
            responses.GET,
            memegen_rendered_pattern("buzz"),
            body=fake_png_bytes,
            content_type="image/png",
        )
        out = tmp_path / "out.png"
        fig, ax = meme("buzz", "memes", "everywhere", savefig=out, backend="auto")
        assert out.exists()
        # The blank URL must NOT have been fetched under the memegen backend.
        called = [str(c.request.url) for c in responses.calls]
        assert any("/images/buzz/" in u for u in called)
        assert not any(u.endswith("/images/buzz.png") for u in called)

    @responses.activate
    def test_meme_with_template_style_and_dimensions(
        self, buzz_metadata_response, fake_png_bytes, tmp_path
    ):
        responses.add(
            responses.GET,
            memegen_rendered_pattern("buzz"),
            body=fake_png_bytes,
            content_type="image/png",
        )
        meme(
            "buzz",
            "hi",
            "world",
            template_style="x",
            width=600,
            height=400,
            extension="jpg",
            backend="memegen",
            savefig=tmp_path / "x.jpg",
        )
        assert any(
            "style=x" in str(c.request.url) and "width=600" in str(c.request.url)
            for c in responses.calls
        )

    @responses.activate
    def test_fontsize_forces_pillow_under_auto(
        self, buzz_metadata_response, fake_png_bytes, tmp_path
    ):
        # When the user passes fontsize=, auto must fall through to pillow,
        # which fetches the blank (NOT a rendered URL).
        responses.add(
            responses.GET,
            f"{API_BASE}/images/buzz.png",
            body=fake_png_bytes,
            content_type="image/png",
        )
        meme("buzz", "hello", fontsize=48, savefig=tmp_path / "p.png")
        called = [str(c.request.url) for c in responses.calls]
        assert any(u.endswith("/images/buzz.png") for u in called)
        # No rendered-URL request.
        assert not any("/images/buzz/" in u for u in called)


class TestMemeCustomTemplate:
    @responses.activate
    def test_custom_url_uses_pillow(self, fake_png_bytes, tmp_path):
        responses.add(
            responses.GET,
            "https://example.com/foo.png",
            body=fake_png_bytes,
            content_type="image/png",
        )
        meme(
            "https://example.com/foo.png",
            "hello",
            "world",
            savefig=tmp_path / "out.png",
        )
        called = [str(c.request.url) for c in responses.calls]
        # The custom URL was fetched; nothing routed to memegen.
        assert any(u == "https://example.com/foo.png" for u in called)
        assert not any("api.memegen.link" in u for u in called)


class TestBuildMemegenUrlReexport:
    def test_reexported(self):
        assert hasattr(memes, "build_memegen_url")
        url = memes.build_memegen_url("buzz", ["hi"], api_base="https://api.memegen.link")
        assert url == "https://api.memegen.link/images/buzz/hi.png"
