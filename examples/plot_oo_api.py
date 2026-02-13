"""
Object-Oriented API
===================

Build memes step-by-step or with method chaining using the
:class:`~memeplotlib.Meme` class.
"""

# %%
# Step-by-Step Construction
# --------------------------
#
# Create a :class:`~memeplotlib.Meme`, set text on each position, then render.

from memeplotlib import Meme

m = Meme("buzz")
m.top("memes")
m.bottom("memes everywhere")
fig, ax = m.render()

# %%
# Method Chaining
# ----------------
#
# The fluent interface lets you build a meme in a single expression.

Meme("doge").top("such code").bottom("very bug").render()

# %%
# Constructor Shorthand
# ----------------------
#
# Text lines can also be passed directly to the constructor.

m = Meme("buzz", "memes", "memes everywhere")
m.render()
