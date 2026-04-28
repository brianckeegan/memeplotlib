"""
Global Configuration
====================

Set project-wide defaults via the :data:`~memeplotlib.config` mapping so
every meme inherits the same look. The mapping behaves like
:data:`matplotlib.rcParams` -- treat it as a validated key-value store.
"""

# %%
# Changing Defaults
# ------------------
#
# ``config`` is a :class:`~memeplotlib.MemeplotlibConfig` mapping. Set keys
# to override defaults for all subsequent :func:`~memeplotlib.meme` and
# :class:`~memeplotlib.Meme` calls.

import memeplotlib as memes

memes.config["font"] = "comic"
memes.config["color"] = "yellow"
memes.config["fontsize"] = 120
memes.config["style"] = "none"

memes.meme("buzz", "custom defaults", "applied everywhere")

# %%
# Reset back to the original defaults.

memes.config.reset()

# %%
# Scoped overrides with ``rc_context``
# -------------------------------------
#
# Use :func:`~memeplotlib.rc_context` to apply config changes only inside a
# ``with`` block, mirroring :func:`matplotlib.rc_context`.

with memes.rc_context({"color": "yellow", "font": "comic"}):
    memes.meme("buzz", "yellow comic", "for this block only")

# Outside the block, defaults are unchanged.
assert memes.config["color"] == "white"
