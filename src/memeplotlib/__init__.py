"""memeplotlib -- Memes with Python's matplotlib.

Create image macro memes using matplotlib for rendering and the memegen API
for template discovery.

Quick start::

    import memeplotlib as memes

    memes.meme("buzz", "memes", "memes everywhere")

"""

from memeplotlib._api import meme, memify
from memeplotlib._config import config
from memeplotlib._meme import Meme
from memeplotlib._template import Template, TemplateRegistry

__version__ = "0.1.0"

__all__ = [
    "meme",
    "memify",
    "Meme",
    "Template",
    "TemplateRegistry",
    "config",
    "__version__",
]
