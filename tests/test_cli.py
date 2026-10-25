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
        responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
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
        responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
        responses.add(responses.GET, f"{API_BASE}/templates/zzz", status=404)
        rc = main(["info", "zzz"])
        assert rc == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.startswith("memeplotlib: error:")
        assert "not found" in captured.err

    @responses.activate
    def test_info_uses_cached_catalog(self, fake_catalog, capsys):
        # Only the catalog is mocked: info must not need a per-template call.
        responses.add(responses.GET, f"{API_BASE}/templates/", json=fake_catalog)
        assert main(["info", "drake"]) == 0
        assert "Drake Hotline Bling" in capsys.readouterr().out


class TestMemeRender:
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
    def test_meme_subcommand_saves_png(self, fake_image_bytes, tmp_path, capsys):
        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "out.png"
        rc = main(["meme", "buzz", "hello", "world", "--out", str(out_path)])
        assert rc == 0
        assert out_path.exists()
        captured = capsys.readouterr().out
        assert f"Saved to {out_path}" in captured
        assert 'Alt text: Meme using the "Buzz" template. Top text: "hello".' in captured

    @responses.activate
    def test_meme_alt_text_flag(self, fake_image_bytes, tmp_path, capsys):
        from PIL import Image

        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "out.png"
        rc = main(["meme", "buzz", "hi", "--alt-text", "Custom words", "--out", str(out_path)])
        assert rc == 0
        assert "Alt text: Custom words" in capsys.readouterr().out
        assert Image.open(out_path).info["Description"] == "Custom words"

    @responses.activate
    def test_create_alias_still_works(self, fake_image_bytes, tmp_path):
        """Backward-compat: 'create' is an alias for 'meme'."""
        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "alias.png"
        rc = main(["create", "buzz", "hello", "world", "-o", str(out_path)])
        assert rc == 0
        assert out_path.exists()

    @responses.activate
    def test_meme_with_font_and_style(self, fake_image_bytes, tmp_path):
        self._mock_buzz(fake_image_bytes)
        out_path = tmp_path / "styled.png"
        rc = main(
            [
                "meme",
                "buzz",
                "hello",
                "--font",
                "impact",
                "--style",
                "none",
                "--fontsize",
                "60",
                "-o",
                str(out_path),
            ]
        )
        assert rc == 0
        assert out_path.exists()


class TestVersionFlag:
    def test_version_prints(self, capsys):
        from memeplotlib import __version__

        with pytest.raises(SystemExit) as excinfo:
            main(["--version"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert __version__ in out


class TestErrors:
    """Expected failures exit 1 with one line on stderr, never a traceback."""

    @responses.activate
    def test_unknown_template_for_meme(self, capsys, tmp_path):
        responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
        responses.add(responses.GET, f"{API_BASE}/templates/nope", status=404)
        rc = main(["meme", "nope", "hi", "-o", str(tmp_path / "x.png")])
        assert rc == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Traceback" not in captured.err
        assert captured.err.count("\n") == 1

    def test_missing_image_file(self, capsys, tmp_path):
        rc = main(["meme", str(tmp_path / "missing.png"), "hi", "-o", str(tmp_path / "x.png")])
        assert rc == 1
        assert "not found" in capsys.readouterr().err

    @responses.activate
    def test_network_error_on_list(self, capsys):
        import requests

        responses.add(
            responses.GET, f"{API_BASE}/templates/", body=requests.ConnectionError("offline")
        )
        rc = main(["list"])
        assert rc == 1
        assert "offline" in capsys.readouterr().err


class TestOutlineFlags:
    def test_outline_flags_are_forwarded(self, monkeypatch, tmp_path):
        import memeplotlib._api as api

        captured: dict = {}

        def fake_meme(template, *lines, **kwargs):
            import matplotlib.pyplot as plt

            captured.update(kwargs)
            return plt.subplots()

        monkeypatch.setattr(api, "meme", fake_meme)
        rc = main(
            [
                "meme",
                "buzz",
                "a",
                "--outline-color",
                "white",
                "--outline-width",
                "3",
                "-o",
                str(tmp_path / "x.png"),
            ]
        )
        assert rc == 0
        assert captured["outline_color"] == "white"
        assert captured["outline_width"] == 3.0
