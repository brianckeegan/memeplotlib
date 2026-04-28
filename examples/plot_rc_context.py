"""
Scoped Overrides with rc_context
================================

:func:`~memeplotlib.rc_context` mirrors :func:`matplotlib.rc_context` —
apply config changes only inside a ``with`` block, then auto-restore the
prior values on exit.
"""

import memeplotlib as memes

# %%
# Scoping a custom palette
# ------------------------
#
# Inside the block, any meme call uses the temporarily-overridden config.

memes.config["color"] = "white"  # global default

with memes.rc_context({"color": "yellow", "font": "comic"}):
    memes.meme("buzz", "yellow comic", "(scoped)")

# Outside the block, the original "white" default is restored.
assert memes.config["color"] == "white"

# %%
# Setting individual keys
# -----------------------
#
# ``config`` itself is a :class:`~memeplotlib.MemeplotlibConfig` mapping —
# treat it like ``matplotlib.rcParams``.

memes.config["fontsize"] = 96
memes.config["style"] = "lower"
memes.meme("buzz", "Lowercase Memes", "Everywhere")

# Reset back to the shipped defaults at the end of the example.
memes.config.reset()
