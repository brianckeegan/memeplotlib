"""
Rendering onto Existing Axes
=============================

Render memes side-by-side using matplotlib's subplot system.
"""

# %%
# Side-by-Side Memes
# --------------------
#
# Pass an existing ``Axes`` via the ``ax`` parameter to embed a meme in a
# subplot layout.

import matplotlib.pyplot as plt
import memeplotlib as memes

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

memes.meme("buzz", "memes", "memes everywhere", ax=ax1, show=False)
memes.meme("doge", "such code", "very bug", ax=ax2, show=False)

plt.tight_layout()
