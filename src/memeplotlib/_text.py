"""Text encoding and wrapping utilities for memeplotlib."""

from __future__ import annotations

import textwrap


# memegen URL encoding table
_ENCODE_MAP = [
    ("_", "__"),
    ("-", "--"),
    ("?", "~q"),
    ("&", "~a"),
    ("%", "~p"),
    ("#", "~h"),
    ("/", "~s"),
    ("\\", "~b"),
    ("<", "~l"),
    (">", "~g"),
    ('"', "''"),
    ("\n", "~n"),
    (" ", "_"),
]


def encode_text_for_url(text: str) -> str:
    """Encode text for use in memegen API URLs.

    Transforms special characters according to the memegen URL encoding scheme.
    Spaces become underscores, and other special characters use tilde-escapes.
    """
    result = text
    for char, replacement in _ENCODE_MAP:
        result = result.replace(char, replacement)
    return result


_SENTINEL = "\x00"

# Tilde-escape decode pairs (no ambiguity, safe to apply directly)
_TILDE_DECODE_MAP = [
    ("?", "~q"),
    ("&", "~a"),
    ("%", "~p"),
    ("#", "~h"),
    ("/", "~s"),
    ("\\", "~b"),
    ("<", "~l"),
    (">", "~g"),
    ("\n", "~n"),
]


def decode_text_from_url(text: str) -> str:
    """Decode text from memegen API URL format back to plain text."""
    result = text

    # First pass: protect doubled sequences with sentinels
    result = result.replace("__", _SENTINEL + "UNDERSCORE")
    result = result.replace("--", _SENTINEL + "DASH")
    result = result.replace("''", _SENTINEL + "QUOTE")

    # Decode single-char mappings
    result = result.replace("_", " ")

    # Decode tilde escapes
    for char, replacement in _TILDE_DECODE_MAP:
        result = result.replace(replacement, char)

    # Restore sentinels to their original characters
    result = result.replace(_SENTINEL + "UNDERSCORE", "_")
    result = result.replace(_SENTINEL + "DASH", "-")
    result = result.replace(_SENTINEL + "QUOTE", '"')

    return result


def wrap_text(text: str, max_chars_per_line: int = 30) -> str:
    """Word-wrap text to fit within a bounding box.

    Tries to balance line lengths for a visually appealing result.
    Returns text with newlines inserted at wrap points.
    """
    if len(text) <= max_chars_per_line:
        return text

    lines = textwrap.wrap(text, width=max_chars_per_line)
    return "\n".join(lines)


def apply_style(text: str, style: str) -> str:
    """Apply text style transformation.

    Args:
        text: The raw text.
        style: One of "upper", "lower", or "none".

    Returns:
        Transformed text.
    """
    if style == "upper":
        return text.upper()
    elif style == "lower":
        return text.lower()
    return text
