API Reference
=============

.. currentmodule:: memeplotlib

Top-level Functions
--------------------

.. autofunction:: meme

.. autofunction:: memify

Meme Class
-----------

.. autoclass:: Meme
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
--------------

.. autodata:: config
   :annotation: = MemeplotlibConfig()

.. autoclass:: memeplotlib._config.MemeplotlibConfig
   :members:
   :show-inheritance:
   :no-index:

Templates
----------

.. autoclass:: Template
   :members:
   :show-inheritance:
   :exclude-members: id, name, image_url, text_positions, keywords, example

.. autoclass:: memeplotlib._template.TextPosition
   :members:
   :show-inheritance:
   :no-index:

.. autoclass:: TemplateRegistry
   :members:
   :undoc-members:
   :show-inheritance:

.. autoexception:: memeplotlib._template.TemplateNotFoundError
   :show-inheritance:

Rendering
----------

.. automodule:: memeplotlib._rendering
   :members:
   :undoc-members:
   :show-inheritance:

Text Utilities
---------------

.. automodule:: memeplotlib._text
   :members:
   :undoc-members:
   :show-inheritance:

Caching
--------

.. automodule:: memeplotlib._cache
   :members:
   :undoc-members:
   :show-inheritance:
