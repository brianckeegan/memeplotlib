"""
Functional API
==============

Create memes using the :func:`~memeplotlib.meme` function with text styling
options and figure access.
"""

# %%
# Customizing Text
# -----------------
#
# Pass ``font``, ``color``, and ``style`` keyword arguments to control text
# appearance.

import memeplotlib as memes

memes.meme(
    "drake", "writing tests", "shipping to prod",
    font="impact", color="yellow", show=False,
)

# %%
# Getting the Figure Back
# ------------------------
#
# :func:`~memeplotlib.meme` returns a ``(Figure, Axes)`` tuple, so you can
# continue to modify the plot.

fig, ax = memes.meme(
    "distracted", "my project", "new framework", "me",
    show=False,
)
