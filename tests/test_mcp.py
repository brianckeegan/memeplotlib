"""Tests for the optional MCP server (`memeplotlib._mcp`)."""

from __future__ import annotations

import base64
import io
import json

import numpy as np
import pytest
import responses
from PIL import Image

mcp = pytest.importorskip("mcp", reason="MCP extra not installed")
from memeplotlib import _mcp  # noqa: E402  imported after mcp guard

API_BASE = "https://api.memegen.link"


@pytest.fixture
def fake_png_bytes():
    rng = np.random.default_rng(seed=7)
    img = Image.fromarray(rng.integers(0, 255, (100, 200, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _isolate_registry(tmp_path, monkeypatch):
    """Reset the module-level registry singleton and force cache to tmp."""
    import memeplotlib._template as t
    from memeplotlib import config

    monkeypatch.setitem(config, "cache_dir", str(tmp_path / "cache"))
    monkeypatch.setitem(config, "cache_enabled", False)
    original = t._registry
    t._registry = None
    yield
    t._registry = original


class TestServerSurface:
    def test_server_is_named_memeplotlib(self):
        assert _mcp.server.name == "memeplotlib"

    def test_main_is_callable(self):
        # We don't actually run the server (it would block on stdio); we just
        # confirm the entry point exists with the expected signature.
        assert callable(_mcp.main)

    def test_main_keeps_stdout_clean(self, monkeypatch, capsys):
        # stdout carries JSON-RPC on the stdio transport; a banner there
        # breaks the client handshake.
        monkeypatch.setattr(_mcp.server, "run", lambda *a, **k: None)
        assert _mcp.main() == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "memeplotlib-mcp" in captured.err


class TestRenderMemeTool:
    @responses.activate
    def test_render_returns_image_content_path_and_alt_text(self, fake_png_bytes, tmp_path):
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
            body=fake_png_bytes,
            content_type="image/png",
        )

        out = tmp_path / "out.png"
        result = _mcp.render_meme_tool(
            template="buzz",
            top="hello",
            bottom="world",
            out_path=str(out),
        )
        image, text = result.content
        assert image.type == "image"
        assert image.mime_type == "image/png"
        assert base64.b64decode(image.data) == out.read_bytes()
        assert result.structured_content["path"] == str(out)
        assert result.structured_content["alt_text"].startswith('Meme using the "Buzz" template.')
        # Clients that ignore structured content still get path + alt text.
        assert json.loads(text.text) == result.structured_content

    @responses.activate
    def test_render_closes_its_figures(self, fake_png_bytes, tmp_path):
        import matplotlib.pyplot as plt

        responses.add(responses.GET, f"{API_BASE}/templates/", json=[])
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/buzz",
            json={
                "id": "buzz",
                "name": "Buzz",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
            },
        )
        responses.add(
            responses.GET,
            f"{API_BASE}/images/buzz.png",
            body=fake_png_bytes,
            content_type="image/png",
        )

        before = plt.get_fignums()
        for i in range(3):
            _mcp.render_meme_tool(
                template="buzz", top=f"call {i}", out_path=str(tmp_path / f"{i}.png")
            )
        assert plt.get_fignums() == before

    def test_render_closes_figures_on_error(self, tmp_path, monkeypatch):
        import matplotlib.pyplot as plt

        def boom(*args, **kwargs):
            plt.figure()
            raise RuntimeError("render failed")

        monkeypatch.setattr(_mcp, "_meme", boom)
        before = plt.get_fignums()
        with pytest.raises(RuntimeError):
            _mcp.render_meme_tool(template="buzz", out_path=str(tmp_path / "x.png"))
        assert plt.get_fignums() == before

    @responses.activate
    def test_render_without_out_path_uses_tempfile(self, fake_png_bytes):
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
            body=fake_png_bytes,
            content_type="image/png",
        )

        result = _mcp.render_meme_tool(template="buzz", top="hi")
        assert result.structured_content["path"].endswith(".png")
        assert "memeplotlib-" in result.structured_content["path"]


class TestSearchAndList:
    @responses.activate
    def test_search_returns_subset(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=[
                {
                    "id": "drake",
                    "name": "Drake",
                    "blank": f"{API_BASE}/images/drake.png",
                    "keywords": ["drake"],
                },
                {
                    "id": "buzz",
                    "name": "Buzz",
                    "blank": f"{API_BASE}/images/buzz.png",
                    "keywords": ["buzz"],
                },
            ],
        )
        results = _mcp.search_templates_tool("drake")
        assert len(results) == 1
        assert results[0]["id"] == "drake"
        assert results[0]["preview_url"].endswith("/drake.png")

    @responses.activate
    def test_list_returns_all(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=[
                {"id": "buzz", "name": "Buzz"},
                {"id": "drake", "name": "Drake"},
            ],
        )
        results = _mcp.list_templates_tool()
        assert len(results) == 2
        assert {r["id"] for r in results} == {"buzz", "drake"}


class TestRenderMemeToolForwarding:
    """The MCP tool should expose the same knobs as ``memeplotlib.meme``."""

    @pytest.fixture
    def spy(self, monkeypatch, tmp_path):
        calls: list[tuple[tuple, dict]] = []

        def fake_meme(*args, **kwargs):
            calls.append((args, kwargs))
            # The tool returns the saved file as image content, so write a real PNG.
            Image.new("RGB", (4, 4)).save(kwargs["savefig"])
            import matplotlib.pyplot as plt

            return plt.subplots()

        monkeypatch.setattr(_mcp, "_meme", fake_meme)
        return calls

    def test_lines_supports_three_or_more_slots(self, spy, tmp_path):
        _mcp.render_meme_tool(
            template="gru",
            lines=["plan", "step 2", "uh oh", "uh oh"],
            out_path=str(tmp_path / "a.png"),
        )
        args, _ = spy[0]
        assert args == ("gru", "plan", "step 2", "uh oh", "uh oh")

    def test_lines_and_top_are_mutually_exclusive(self, spy, tmp_path):
        with pytest.raises(ValueError, match="either 'lines'"):
            _mcp.render_meme_tool(template="buzz", top="a", lines=["b"])

    def test_styling_options_are_forwarded(self, spy, tmp_path):
        _mcp.render_meme_tool(
            template="buzz",
            top="a",
            out_path=str(tmp_path / "a.png"),
            outline_color="white",
            outline_width=3.0,
            style="none",
            layout="top",
            background="https://example.com/bg.png",
            dpi=72,
        )
        _, kwargs = spy[0]
        assert kwargs["outline_color"] == "white"
        assert kwargs["outline_width"] == 3.0
        assert kwargs["style"] == "none"
        assert kwargs["layout"] == "top"
        assert kwargs["background"] == "https://example.com/bg.png"
        assert kwargs["dpi"] == 72

    def test_unset_options_are_not_forwarded(self, spy, tmp_path):
        # meme() relies on sentinel defaults to pick a backend, so the tool
        # must not pass explicit None for knobs the client left unset.
        _mcp.render_meme_tool(template="buzz", top="a", out_path=str(tmp_path / "a.png"))
        _, kwargs = spy[0]
        assert set(kwargs) == {"savefig", "show"}


class TestWireFormat:
    # On Windows, asyncio's event loop builds its self-pipe from a loopback
    # TCP socketpair, which the offline fixture blocks. Allow sockets for
    # this test but restrict connections to loopback so it stays offline.
    @pytest.mark.allow_network
    @pytest.mark.allow_hosts(["127.0.0.1", "::1"])
    def test_call_tool_returns_image_and_structured_content(self, monkeypatch, tmp_path):
        """Through the server: the image is a content block, not JSON text."""
        import asyncio

        def fake_meme(*args, **kwargs):
            Image.new("RGB", (4, 4)).save(kwargs["savefig"])
            import matplotlib.pyplot as plt

            return plt.subplots()

        monkeypatch.setattr(_mcp, "_meme", fake_meme)
        out = tmp_path / "wire.jpg"
        result = asyncio.run(
            _mcp.server.call_tool("meme", {"template": "buzz", "top": "a", "out_path": str(out)})
        )
        assert [block.type for block in result.content] == ["image", "text"]
        assert result.content[0].mime_type == "image/jpeg"
        assert result.structured_content["path"] == str(out)
        assert "base64_png" not in result.structured_content
