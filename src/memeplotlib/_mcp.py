"""MCP server: expose memeplotlib over the Model Context Protocol.

Run with the ``memeplotlib-mcp`` console script. The server speaks
JSON-RPC over stdio, so it's compatible with Claude Desktop, Claude
Code, and any other MCP client that supports the stdio transport.

Tools exposed:

- ``meme``: render a meme to a PNG file and return the path plus a
  base64-encoded PNG.
- ``search_templates``: return memegen template metadata matching a
  query string.
- ``list_templates``: return the full memegen template catalog.

This module is gated behind the optional ``[mcp]`` extra::

    pip install "memeplotlib[mcp]"
"""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any

import matplotlib

# Force the Agg backend before any matplotlib import touches a GUI loop.
matplotlib.use("Agg")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - exercised only without [mcp] extra
    raise ImportError(
        "memeplotlib-mcp requires the [mcp] extra. " "Install with: pip install 'memeplotlib[mcp]'"
    ) from exc

from memeplotlib import __version__
from memeplotlib import meme as _meme
from memeplotlib._template import TemplateRegistry

server = FastMCP(
    name="memeplotlib",
    instructions=(
        "memeplotlib MCP server. Render image-macro memes via matplotlib + "
        "memegen.link. Tools return file paths plus base64-encoded PNG bytes "
        "so clients can either reference the saved file or inline the image."
    ),
)


def _encode_png(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


@server.tool(
    name="meme",
    description=(
        "Render a meme image. Returns a dict with the saved file path "
        "and a base64-encoded PNG. The template can be a memegen ID "
        "(e.g. 'buzz', 'drake', 'doge'), a local file path, or an "
        "HTTP(S) URL."
    ),
)
def render_meme_tool(
    template: str,
    top: str | None = None,
    bottom: str | None = None,
    out_path: str | None = None,
) -> dict[str, str]:
    """Render a meme and return path + base64.

    Parameters
    ----------
    template : str
        Memegen template ID, file path, or URL.
    top : str, optional
        Top caption text.
    bottom : str, optional
        Bottom caption text.
    out_path : str, optional
        Where to save the PNG. If None, a tempfile is used.

    Returns
    -------
    dict
        Keys: ``path`` (str), ``base64_png`` (str).
    """
    lines: list[str] = []
    if top is not None:
        lines.append(top)
    if bottom is not None:
        lines.append(bottom)

    if out_path is None:
        fd, out_path = tempfile.mkstemp(prefix="memeplotlib-", suffix=".png")
        os.close(fd)

    _meme(template, *lines, savefig=out_path, show=False)
    return {"path": out_path, "base64_png": _encode_png(out_path)}


@server.tool(
    name="search_templates",
    description=(
        "Search the memegen template catalog by ID, name, or keyword. "
        "Returns a list of template metadata dicts with id, name, and "
        "preview_url fields."
    ),
)
def search_templates_tool(query: str) -> list[dict[str, Any]]:
    """Return template metadata matching the query."""
    registry = TemplateRegistry()
    results = registry.search(query)
    return [
        {
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "preview_url": item.get("blank", ""),
        }
        for item in results
    ]


@server.tool(
    name="list_templates",
    description=(
        "Return the full memegen template catalog. Useful for browsing "
        "available templates by ID and name."
    ),
)
def list_templates_tool() -> list[dict[str, str]]:
    """Return every template's id and name."""
    registry = TemplateRegistry()
    return [
        {"id": item.get("id", ""), "name": item.get("name", "")} for item in registry.list_all()
    ]


def main() -> int:
    """Console-script entry point."""
    print(f"memeplotlib-mcp {__version__} (stdio JSON-RPC)", flush=True)
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
