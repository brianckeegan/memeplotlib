"""
Memify Existing Plots
=====================

Overlay meme-style text on any matplotlib figure using
:func:`~memeplotlib.memify`.
"""

# %%
# Basic Memify
# -------------
#
# Turn an ordinary matplotlib plot into a meme by adding bold, outlined text.

import matplotlib.pyplot as plt
import memeplotlib as memes

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
ax.set_title("Quadratic growth")
memes.memify(fig, "stonks")

# %%
# Bottom-Only Text
# -----------------
#
# Use the ``position`` parameter to place text only at the bottom of the figure.

fig, ax = plt.subplots()
ax.bar(["A", "B", "C"], [3, 7, 5])
memes.memify(fig, "not stonks", position="bottom")
