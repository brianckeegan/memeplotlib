Command Line and MCP
====================

memeplotlib ships two entry points besides the Python API: a command-line
tool for scripts and shells, and a `Model Context Protocol
<https://modelcontextprotocol.io>`_ (MCP) server for AI assistants.

Command line
------------

The ``memeplotlib`` command (also ``python -m memeplotlib``) has four
subcommands:

.. code-block:: bash

   memeplotlib list                   # every memegen template ID and name
   memeplotlib search dog             # templates matching a keyword
   memeplotlib info buzz              # caption slots, styles, keywords
   memeplotlib meme buzz "hello" "world" -o hello.png

``meme`` accepts the template (a memegen ID, an image path, or a URL)
followed by one argument per caption slot. Useful options:

``-o / --out PATH``
    Output file (default ``meme.png``).
``--font``, ``--color``, ``--style {upper,lower,none}``, ``--fontsize``
    Caption styling.
``--backend {auto,memegen,pillow,matplotlib}``
    Force a rendering backend.
``--ext``, ``--width``, ``--height``, ``--layout``, ``--background``, ``--template-style``
    Options forwarded to the memegen service.
``--dpi``
    Resolution of the saved file.

Run ``memeplotlib meme --help`` for the full list. Listings print as plain
aligned text columns, which read cleanly in screen readers and pipe well
into ``grep``/``awk``.

MCP server
----------

Install the optional extra and start the server over stdio:

.. code-block:: bash

   pip install "memeplotlib[mcp]"
   memeplotlib-mcp

Register it with any MCP client that supports the stdio transport. For
example, Claude Code:

.. code-block:: bash

   claude mcp add memeplotlib -- memeplotlib-mcp

The server exposes three tools:

``meme``
    Render a meme and return ``path`` (the saved PNG) and ``base64_png``.
    Takes the template, ``top`` / ``bottom`` captions, and the same styling
    options as :func:`~memeplotlib.meme`.
``search_templates``
    Search the memegen catalog by ID, name, or keyword.
``list_templates``
    Return every template's ID and name.
