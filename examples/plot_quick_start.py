"""
Quick Start
===========

The simplest way to create a meme with memeplotlib.
"""

# %%
# Your First Meme
# ----------------
#
# The :func:`~memeplotlib.meme` function creates a meme from a template ID.
# The first positional argument is the template, and subsequent arguments are
# text lines placed at the template's text positions (typically top and bottom).

import memeplotlib as memes

memes.meme("buzz", "memes", "memes everywhere", show=False)

# %%
# Saving to a File
# -----------------
#
# Pass ``savefig`` to write the meme to disk.  Set ``show=False`` to suppress
# the interactive window.

memes.meme("doge", "such code", "very bug", savefig="doge_example.png", show=False)
