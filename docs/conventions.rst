API Conventions
================

memeplotlib follows the conventions of the scientific Python stack —
:mod:`matplotlib`, :mod:`numpy`, :mod:`pandas`, :mod:`seaborn`. If you
write a new public function or method, match these patterns so the
library feels native to anyone coming from those tools.

The ``ax=None`` pattern
------------------------

Public rendering functions accept an optional ``ax`` keyword argument.
If ``None`` (the default), they create a new ``Figure``/``Axes``. If
provided, they render onto the supplied ``Axes``.

.. code-block:: python

   import matplotlib.pyplot as plt
   import memeplotlib as memes

   fig, ax = plt.subplots()
   memes.meme("buzz", "memes", "everywhere", ax=ax)  # renders into ax

This mirrors :mod:`seaborn` and :func:`pandas.DataFrame.plot`.

Return ``(Figure, Axes)``, do not call ``plt.show``
----------------------------------------------------

:func:`~memeplotlib.meme` returns ``(fig, ax)`` so the caller can
continue customizing or save the figure. ``show=False`` is the default —
matching matplotlib's idiom of explicit display. Pass ``show=True`` if
you want auto-display in a script.

.. code-block:: python

   fig, ax = memes.meme("drake", "old way", "new way")
   ax.set_title("annotated by the caller", fontsize=10)
   fig.savefig("drake.png", dpi=200)

Forward ``**kwargs`` to ``Axes.text``
--------------------------------------

Both :func:`~memeplotlib.meme` and :func:`~memeplotlib.memify` accept
extra ``**kwargs`` that are passed through to :meth:`Axes.text` for each
rendered caption. This lets you tweak ``alpha``, ``rotation``, ``zorder``,
or any other matplotlib text parameter without library-side support:

.. code-block:: python

   memes.meme("buzz", "rotated", rotation=15, alpha=0.8)

User-supplied kwargs override the meme-specific defaults.

``rc_context`` for scoped config overrides
-------------------------------------------

The :data:`~memeplotlib.config` mapping is RcParams-style. For
short-lived overrides, use :func:`~memeplotlib.rc_context` — same shape
as :func:`matplotlib.rc_context`:

.. code-block:: python

   with memes.rc_context({"font": "comic", "color": "yellow"}):
       memes.meme("buzz", "scoped style")
   # config is restored on block exit

Setting ``config["..."] = ...`` mutates the singleton globally; use
``rc_context`` whenever you don't want that.

NumPy-format docstrings
------------------------

Every public function uses NumPy-format docstrings:

.. code-block:: python

   def meme(template, *lines, ax=None, font=None, **text_kwargs):
       """Render an image-macro meme.

       Parameters
       ----------
       template : str
           Memegen template ID, file path, or URL.
       *lines : str
           Caption lines.
       ax : matplotlib.axes.Axes, optional
           Render onto this axes. If None, a new figure is created.
       **text_kwargs
           Forwarded to :meth:`Axes.text`.

       Returns
       -------
       fig : matplotlib.figure.Figure
       ax : matplotlib.axes.Axes
       """

The docs use :mod:`numpydoc` (not ``napoleon``). Run
``numpydoc validate`` to check.

Test conventions
-----------------

* All network calls are mocked. The autouse ``_block_real_network``
  fixture in ``tests/conftest.py`` disables real TCP sockets. Tests
  using :mod:`pytest_httpserver` opt out via
  ``@pytest.mark.allow_network``.
* Image-comparison tests use :mod:`pytest_mpl`. Baselines live in
  ``tests/baseline/``. Regenerate with
  ``pytest --mpl-generate-path=tests/baseline``.
* Mocked HTTP responses use the :mod:`responses` library; for retry or
  timeout behavior that ``responses`` cannot model, use
  :mod:`pytest_httpserver`.
