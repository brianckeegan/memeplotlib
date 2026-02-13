"""
Global Configuration
====================

Set project-wide defaults with :data:`~memeplotlib.config` so every meme
inherits the same look.
"""

# %%
# Changing Defaults
# ------------------
#
# Any attribute on ``config`` becomes the new default for all subsequent
# :func:`~memeplotlib.meme` and :class:`~memeplotlib.Meme` calls.

import memeplotlib as memes

memes.config.font = "comic"
memes.config.color = "yellow"
memes.config.fontsize = 120
memes.config.style = "none"

memes.meme("buzz", "custom defaults", "applied everywhere", show=False)

# %%
# Reset to defaults for the rest of the examples.

memes.config.font = "impact"
memes.config.color = "white"
memes.config.fontsize = 72.0
memes.config.style = "upper"
