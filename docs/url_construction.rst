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
``style=``        Template-specific style name (e.g. ``maga`` for ``ds``) **or**
                  one or more overlay image URLs joined with commas. Sent
                  once: memegen reads only the first ``style=`` value, and
                  it cannot mix a style name with overlay URLs.
``font=``         Memegen font ID or alias, mirroring upstream
                  ``/fonts/`` (:data:`memeplotlib._url.MEMEGEN_FONT_ALIASES`):
                  ``titilliumweb``/``thick``, ``titilliumweb-thin``/``thin``,
                  ``segoe``/``tiny``, ``kalam``/``comic``, ``impact``,
                  ``notosans``, ``hgminchob``/``jp``,
                  ``notosanshebrew``/``he``. Sent only when you choose a
                  font (per call, or by changing ``config["font"]``);
                  otherwise each template keeps its designed font.
                  ``font="default"`` forces that. Fonts outside the set
                  fall through to the Pillow backend under
                  ``backend="auto"``.
``color=``        One text color per caption line, comma-separated
                  (``"white,red"`` colors line 1 white and line 2 red).
                  HTML names or hex codes. memegen's outline is always
                  black. ``meme(color="yellow")`` repeats the color for
                  every line; when no color is chosen, nothing is sent and
                  each template keeps its own caption colors.
``width=``        Output width in pixels.
``height=``       Output height in pixels.
``layout=``       Alternate layout (e.g. ``top``).
``background=``   Custom background URL. memegen honours it **only** on the
                  ``custom`` template; :func:`~memeplotlib.meme` switches
                  to ``custom`` automatically when ``background`` is set.
                  Composes with ``style=<url>`` overlays.
``center=``       ``"x,y"`` overlay anchor (``[0, 1]`` floats). Applies to
                  the first overlay only.
``scale=``        Overlay scale factor. Applies to the first overlay only.
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
       "custom",  # the only template that honours background=
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
- ``Template.example`` holds the template's sample caption text (the API's
  ``example.text``). The API record's ``example.url`` (not stored by
  ``memeplotlib``) is memegen's guaranteed-valid render URL — useful as a
  smoke test that a template ID is live.
- Memegen's guide now recommends that clients ``POST /images`` and use the
  canonical URL it returns; its escape table lives in the upstream README.
  ``memeplotlib`` still builds URLs locally via
  :func:`~memeplotlib._text.encode_text_for_url`.
- Behaviour when ``lines`` exceeds ``Template.lines_count``: extra path
  segments are ignored by memegen. ``memeplotlib`` does not pre-truncate;
  pass exactly the slots you intend.
