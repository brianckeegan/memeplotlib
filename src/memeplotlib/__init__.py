"""memeplotlib -- Memes with Python's matplotlib + memegen.

Render image-macro memes by either letting the memegen API compose them
server-side (the default) or falling back to a local Pillow renderer for
custom images and per-line styling that the API can't express.

Quick start::

    import memeplotlib as memes

    fig, ax = memes.meme("buzz", "memes", "memes everywhere")

    # Force the local Pillow renderer for fine-grained control:
    fig, ax = memes.meme(
        "buzz", "memes", "memes everywhere",
        fontsize=48, outline_width=4,
    )
"""

from memeplotlib._api import meme, memify
from memeplotlib._config import MemeplotlibConfig, config, rc_context
from memeplotlib._meme import Meme
from memeplotlib._template import Template, TemplateRegistry
from memeplotlib._url import OverlaySpec, build_memegen_url

__version__ = "0.5.0"

__all__ = [
    "Meme",
    "MemeplotlibConfig",
    "OverlaySpec",
    "Template",
    "TemplateRegistry",
    "__version__",
    "build_memegen_url",
    "config",
    "meme",
    "memify",
    "rc_context",
]
