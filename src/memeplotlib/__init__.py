"""memeplotlib -- Memes with Python's matplotlib.

Create image macro memes using matplotlib for rendering and the memegen API
for template discovery.

Quick start::

    import memeplotlib as memes

    fig, ax = memes.meme("buzz", "memes", "memes everywhere")

"""

from memeplotlib._api import meme, memify
from memeplotlib._config import MemeplotlibConfig, config, rc_context
from memeplotlib._meme import Meme
from memeplotlib._template import Template, TemplateRegistry

__version__ = "0.1.0"

__all__ = [
    "Meme",
    "MemeplotlibConfig",
    "Template",
    "TemplateRegistry",
    "__version__",
    "config",
    "meme",
    "memify",
    "rc_context",
]
