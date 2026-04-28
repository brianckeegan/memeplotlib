"""Tests for the memeplotlib CLI (`python -m memeplotlib`)."""

from __future__ import annotations

import io

import numpy as np
import pytest
import responses
from PIL import Image

from memeplotlib.__main__ import main

API_BASE = "https://api.memegen.link"


@pytest.fixture
def fake_catalog():
    return [
        {
            "id": "buzz",
            "name": "Buzz Lightyear",
            "lines": 2,
            "blank": f"{API_BASE}/images/buzz.png",
            "keywords": ["buzz", "memes"],
            "example": {"text": ["x", "x everywhere"]},
        },
        {
            "id": "drake",
            "name": "Drake Hotline Bling",
            "lines": 2,
            "blank": f"{API_BASE}/images/drake.png",
            "keywords": ["drake"],
            "example": {"text": ["thing 1", "thing 2"]},
        },
    ]


@pytest.fixture
def fake_image_bytes():
    """A small PNG image as bytes."""
    rng = np.random.default_rng(seed=42)
    img = Image.fromarray(rng.integers(0, 255, (100, 200, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _isolate_registry_and_cache(tmp_path, monkeypatch):
    """Reset the module-level registry singleton and force cache to tmp."""
    import memeplotlib._template as t
    from memeplotlib import config

    monkeypatch.setitem(config, "cache_dir", str(tmp_path / "cache"))
    monkeypatch.setitem(config, "cache_enabled", False)
    original = t._registry
    t._registry = None
    yield
    t._registry = original


class TestNoCommand:
    def test_no_args_prints_help(self, capsys):
        rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "memeplotlib" in out


class TestList:
    @responses.activate
    def test_list_prints_catalog(self, fake_catalog, capsys):
        responses.add(responses.GET, f"{API_BASE}/templates/", json=fake_catalog)
        rc = main(["list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "buzz" in out
        assert "drake" in out
        assert "2 templates available" in out


class TestSearch:
    @responses.activate
    def test_search_finds_match(self, fake_catalog, capsys):
        responses.add(responses.GET, f"{API_BASE}/templates/", json=fake_catalog)
        rc = main(["search", "drake"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "drake" in out
        assert "buzz" not in out

    @responses.activate
    def test_search_no_results(self, fake_catalog, capsys):
        responses.add(responses.GET, f"{API_BASE}/templates/", json=fake_catalog)
        rc = main(["search", "nonexistent-template-xyz"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No templates found" in out


class TestInfo:
    @responses.activate
    def test_info_prints_metadata(self, capsys):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/buzz",
            json={
                "id": "buzz",
                "name": "Buzz Lightyear",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
                "keywords": ["buzz", "memes"],
                "example": {"text": ["foo", "bar"]},
            },
        )
        rc = main(["info", "buzz"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Buzz Lightyear" in out
        assert "buzz, memes" in out

    @responses.activate
    def test_info_unknown_returns_1(self, capsys):
        responses.add(responses.GET, f"{API_BASE}/templates/zzz", status=404)
        rc = main(["info", "zzz"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "not found" in out


class TestCreate:
    @staticmethod
    def _mock_buzz(fake_image_bytes):
        # The CLI calls meme() → _resolve_template() → registry.get().
        # When cache is disabled the registry first fetches the full catalog.
        responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/buzz",
            json={
                "id": "buzz",
                "name": "Buzz",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
                "keywords": [],
                "example": {"text": []},
            },
        )
        responses.add(
            responses.GET,
            f"{API_BASE}/images/buzz.png",
            body=fake_image_bytes,
            content_type="image/png",
        )

    @responses.activate
    def test_create_saves_png(self, fake_image_bytes, tmp_path, capsys):
        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "out.png"
        rc = main(["create", "buzz", "hello", "world", "-o", str(out_path)])
        assert rc == 0
        assert out_path.exists()
        captured = capsys.readouterr().out
        assert f"Saved to {out_path}" in captured

    @responses.activate
    def test_create_with_font_and_style(self, fake_image_bytes, tmp_path):
        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "styled.png"
        rc = main(
            [
                "create",
                "buzz",
                "hello",
                "--font",
                "impact",
                "--style",
                "none",
                "-o",
                str(out_path),
            ]
        )
        assert rc == 0
        assert out_path.exists()
