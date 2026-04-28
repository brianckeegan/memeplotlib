Constructing memegen URLs
==========================

When ``memeplotlib`` renders a memegen-catalogue meme it does so by
asking the upstream API to compose the image — same path-and-query
grammar documented for ``api.memegen.link``. This page is the
``memeplotlib``-flavoured version of the unified guide proposed in
`jacebrowning/memegen#993 <https://github.com/jacebrowning/memegen/issues/993>`_.

You normally don't need to write a URL by hand — :func:`memeplotlib.meme`
forwards every relevant knob — but the builder is a public API
(:func:`memeplotlib.build_memegen_url`) for agents and scripts that need
deterministic URLs.

URL shape
---------

.. code-block::

   {api_base}/images/{template_id}/{line_1}/{line_2}/.../{line_n}.{ext}?{query}

Each ``line_i`` is encoded so it survives a URL path. Empty slots are
encoded as ``_`` to preserve slot ordering. Up to ``Template.lines_count``
slots are accepted; trailing empty slots may be omitted but middle empty
slots must remain.

Escape table
------------

Memegen uses a tilde-escape scheme for characters that are illegal or
ambiguous in a URL path. ``memeplotlib`` ships
:func:`memeplotlib._text.encode_text_for_url` which applies it.

==========  =========
Character   Encoding
==========  =========
space       ``_``
``_``       ``__``
``-``       ``--``
``"``       ``''``
``?``       ``~q``
``&``       ``~a``
``%``       ``~p``
``#``       ``~h``
``/``       ``~s``
``\``       ``~b``
``<``       ``~l``
``>``       ``~g``
newline     ``~n``
==========  =========

Empty caption slots become a single ``_`` rather than the empty string.
Emoji and HTML aliases (``:thumbsup:``, ``:fire:``) are passed through
verbatim — memegen resolves them server-side.

Query parameters
----------------

Every parameter below is optional. ``memeplotlib`` only emits a query
string when at least one parameter is supplied.

================  ================================================================
``style=``        Template-specific style name (e.g. ``maga`` for ``ds``) **or** an
                  arbitrary image URL for an ad-hoc overlay. May appear multiple
                  times when overlays are stacked.
``font=``         Memegen font alias. The closed set
                  (:data:`memeplotlib._url.MEMEGEN_FONT_ALIASES`) is
                  ``impact``, ``thick``, ``thin``, ``tiny``, ``comic``,
                  ``notosans``, ``kalam``, ``he``, ``jp``, ``tw``,
                  ``default``. Fonts outside that set fall through to the
                  Pillow backend automatically under ``backend="auto"``.
``color=``        ``"fg"`` or ``"fg,bg"``. HTML names or hex codes.
``width=``        Output width in pixels.
``height=``       Output height in pixels.
``layout=``       Alternate layout (e.g. ``top``).
``background=``   Custom background URL. Composes with ``style=<url>`` overlays.
``center=``       ``"x,y"`` overlay anchor (``[0, 1]`` floats). Paired with an
                  ``style=`` overlay.
``scale=``        Overlay scale factor. Paired with an ``style=`` overlay.
================  ================================================================

Output formats
--------------

The path extension selects the format:

- ``.png`` — default; lossless transparency.
- ``.jpg`` / ``.jpeg`` — smaller, lossy.
- ``.gif`` — animated when the template's blank is animated; static
  background + animated text otherwise.
- ``.webp`` — modern lossy/lossless hybrid.

Set with ``meme(..., extension="jpg")`` or ``config["extension"] = "jpg"``.

Worked examples
---------------

A plain caption pair:

.. code-block:: python

   from memeplotlib import build_memegen_url

   build_memegen_url(
       "buzz",
       ["memes", "memes everywhere"],
       api_base="https://api.memegen.link",
   )
   # → https://api.memegen.link/images/buzz/memes/memes_everywhere.png

A template style plus dimensions plus a two-colour caption:

.. code-block:: python

   build_memegen_url(
       "ds",
       ["the dress is black and blue.", "the dress is gold and white."],
       api_base="https://api.memegen.link",
       template_style="maga",
       font="comic",
       color="white,black",
       width=600,
       extension="jpg",
   )
   # → /images/ds/the_dress_is_black_and_blue./the_dress_is_gold_and_white..jpg
   #   ?style=maga&font=comic&color=white,black&width=600

A custom-background ad-hoc overlay:

.. code-block:: python

   build_memegen_url(
       "fine",
       ["this is fine"],
       api_base="https://api.memegen.link",
       background="https://example.com/bg.png",
       overlays=[{"style": "https://example.com/dog.png",
                  "center": (0.5, 0.7), "scale": 0.4}],
   )

Notes for automated clients
---------------------------

- Bootstrap with ``GET /templates/`` once and cache. Per-template metadata
  (``Template.from_memegen``) hits ``GET /templates/<id>``.
- ``Template.example`` is the canonical "guaranteed-valid URL" smoke test
  — useful for asserting that a template id is live without composing a
  caption yourself.
- Memegen normalises raw POSTed text to the escape forms above and returns
  the canonical URL. ``memeplotlib`` performs the same encoding locally
  via :func:`encode_text_for_url`.
- Behaviour when ``lines`` exceeds ``Template.lines_count``: extra path
  segments are ignored by memegen. ``memeplotlib`` does not pre-truncate;
  pass exactly the slots you intend.
