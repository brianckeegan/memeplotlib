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
import sys
import tempfile
from typing import Any

import matplotlib

# Force the Agg backend before any matplotlib import touches a GUI loop.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - exercised only without [mcp] extra
    raise ImportError(
        "memeplotlib-mcp requires the [mcp] extra (mcp>=1.0,<2). "
        f"Install with: pip install 'memeplotlib[mcp]'. Original error: {exc}"
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
        "HTTP(S) URL. Use 'top'/'bottom' for two-slot templates, or "
        "'lines' for templates with three or more caption slots."
    ),
)
def render_meme_tool(
    template: str,
    top: str | None = None,
    bottom: str | None = None,
    lines: list[str] | None = None,
    out_path: str | None = None,
    backend: str | None = None,
    extension: str | None = None,
    width: int | None = None,
    height: int | None = None,
    layout: str | None = None,
    background: str | None = None,
    template_style: str | None = None,
    font: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    outline_width: float | None = None,
    fontsize: float | None = None,
    style: str | None = None,
    dpi: int | None = None,
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
    lines : list of str, optional
        Caption text for every slot, in order. Use instead of
        ``top``/``bottom`` for templates with three or more slots.
    out_path : str, optional
        Where to save the PNG. If None, a tempfile is used.
    backend : str, optional
        Override the renderer (``"auto"``, ``"memegen"``, ``"pillow"``,
        ``"matplotlib"``).
    extension : str, optional
        Output format requested from memegen (``"png"``, ``"jpg"``,
        ``"gif"``, ``"webp"``).
    width, height : int, optional
        Memegen output dimensions.
    layout : str, optional
        Memegen layout (e.g. ``"top"``).
    background : str, optional
        Custom background image URL forwarded to memegen.
    template_style : str, optional
        Memegen template-specific style (e.g. ``"maga"``).
    font, color : str, optional
        Caption styling.
    outline_color : str, optional
        Caption outline color; forces the Pillow backend under ``"auto"``.
    outline_width : float, optional
        Caption outline width; forces the Pillow backend under ``"auto"``.
    fontsize : float, optional
        Explicit font size; forces the Pillow backend under ``"auto"``.
    style : str, optional
        Text transform -- ``"upper"``, ``"lower"``, or ``"none"``.
    dpi : int, optional
        Resolution of the saved PNG.

    Returns
    -------
    dict
        Keys: ``path`` (str), ``base64_png`` (str).

    Raises
    ------
    ValueError
        If ``lines`` is combined with ``top`` or ``bottom``.
    """
    if lines is not None:
        if top is not None or bottom is not None:
            raise ValueError("Pass either 'lines' or 'top'/'bottom', not both.")
        captions = list(lines)
    else:
        captions = []
        if top is not None:
            captions.append(top)
        if bottom is not None:
            captions.append(bottom)

    if out_path is None:
        fd, out_path = tempfile.mkstemp(prefix="memeplotlib-", suffix=".png")
        os.close(fd)

    options = {
        "backend": backend,
        "extension": extension,
        "width": width,
        "height": height,
        "layout": layout,
        "background": background,
        "template_style": template_style,
        "font": font,
        "color": color,
        "outline_color": outline_color,
        "outline_width": outline_width,
        "fontsize": fontsize,
        "style": style,
        "dpi": dpi,
    }
    # Only forward what the client set so meme()'s sentinel defaults (which
    # drive backend selection) stay intact.
    kwargs: dict[str, Any] = {k: v for k, v in options.items() if v is not None}
    kwargs.update(savefig=out_path, show=False)

    # The server is long-lived and pyplot keeps a reference to every figure
    # it creates, so release whatever this call opened -- even on error.
    open_before = set(plt.get_fignums())
    try:
        _meme(template, *captions, **kwargs)
    finally:
        for num in set(plt.get_fignums()) - open_before:
            plt.close(num)
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
    # stdout is the JSON-RPC channel on the stdio transport; anything else
    # written there corrupts the stream, so diagnostics go to stderr.
    print(f"memeplotlib-mcp {__version__} (stdio JSON-RPC)", file=sys.stderr, flush=True)
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
