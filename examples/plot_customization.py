"""
Text Customization
==================

Control font, color, outline, and case style for meme text.
"""

# %%
# Font and Color
# ---------------
#
# Use ``font``, ``color``, and ``style`` to customise the text appearance.

import memeplotlib as memes

memes.meme(
    "drake", "writing tests", "shipping to prod",
    font="impact", color="yellow", style="upper", show=False,
)

# %%
# Outline Control
# ----------------
#
# Adjust ``outline_color`` and ``outline_width`` for the classic meme look.

memes.meme(
    "buzz", "white on black", "the classic",
    color="white", outline_color="black", outline_width=3.0,
    show=False,
)
