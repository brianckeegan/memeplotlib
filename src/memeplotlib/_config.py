"""Global configuration for memeplotlib (RcParams-style mapping).

The :data:`config` singleton is a :class:`MemeplotlibConfig` mapping with
validated keys. Modify it to change defaults for all subsequent meme calls,
or use :func:`rc_context` for scoped overrides.

Examples
--------
>>> import memeplotlib as memes
>>> memes.config["font"] = "comic"  # doctest: +SKIP
>>> with memes.rc_context({"color": "yellow"}):  # doctest: +SKIP
...     memes.meme("buzz", "hello", "world")
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from typing import Any

DEFAULT_API_BASE = "https://api.memegen.link"
DEFAULT_FONT = "impact"
DEFAULT_COLOR = "white"
DEFAULT_OUTLINE_COLOR = "black"
DEFAULT_OUTLINE_WIDTH = 2.0
DEFAULT_FONTSIZE = 72.0
DEFAULT_DPI = 150
DEFAULT_STYLE = "upper"
DEFAULT_FIGSIZE_WIDTH = 8.0
DEFAULT_API_TIMEOUT = 10
DEFAULT_IMAGE_TIMEOUT = 15
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF = 0.5
DEFAULT_BACKEND = "auto"
DEFAULT_EXTENSION = "png"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

_VALID_STYLES = {"upper", "lower", "none"}
_VALID_BACKENDS = {"auto", "memegen", "pillow", "matplotlib"}
_VALID_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _check_str(name: str) -> Callable[[Any], str]:
    def validator(v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError(f"{name!r} must be a string, got {type(v).__name__}")
        return v

    return validator


def _check_optional_str(name: str) -> Callable[[Any], str | None]:
    def validator(v: Any) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError(f"{name!r} must be a string or None, got {type(v).__name__}")
        return v

    return validator


def _check_non_negative_float(name: str) -> Callable[[Any], float]:
    def validator(v: Any) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"{name!r} must be a number, got {type(v).__name__}")
        if v < 0:
            raise ValueError(f"{name!r} must be non-negative, got {v}")
        return float(v)

    return validator


def _check_non_negative_int(name: str) -> Callable[[Any], int]:
    def validator(v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{name!r} must be an int, got {type(v).__name__}")
        if v < 0:
            raise ValueError(f"{name!r} must be non-negative, got {v}")
        return int(v)

    return validator


def _check_optional_non_negative_int(name: str) -> Callable[[Any], int | None]:
    def validator(v: Any) -> int | None:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{name!r} must be an int or None, got {type(v).__name__}")
        if v < 0:
            raise ValueError(f"{name!r} must be non-negative, got {v}")
        return int(v)

    return validator


def _check_choice(name: str, choices: set[str]) -> Callable[[Any], str]:
    def validator(v: Any) -> str:
        if v not in choices:
            raise ValueError(f"{name!r} must be one of {sorted(choices)}, got {v!r}")
        return str(v)

    return validator


def _check_style(name: str) -> Callable[[Any], str]:
    def validator(v: Any) -> str:
        if v not in _VALID_STYLES:
            raise ValueError(f"{name!r} must be one of {sorted(_VALID_STYLES)}, got {v!r}")
        return str(v)

    return validator


def _check_bool(name: str) -> Callable[[Any], bool]:
    def validator(v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f"{name!r} must be a bool, got {type(v).__name__}")
        return v

    return validator


_VALIDATORS: dict[str, Callable[[Any], Any]] = {
    "api_base": _check_str("api_base"),
    "font": _check_str("font"),
    "color": _check_str("color"),
    "outline_color": _check_str("outline_color"),
    "outline_width": _check_non_negative_float("outline_width"),
    "fontsize": _check_non_negative_float("fontsize"),
    "dpi": _check_non_negative_int("dpi"),
    "style": _check_style("style"),
    "cache_enabled": _check_bool("cache_enabled"),
    "cache_dir": _check_optional_str("cache_dir"),
    "api_timeout": _check_non_negative_int("api_timeout"),
    "image_timeout": _check_non_negative_int("image_timeout"),
    "max_retries": _check_non_negative_int("max_retries"),
    "retry_backoff": _check_non_negative_float("retry_backoff"),
    "backend": _check_choice("backend", _VALID_BACKENDS),
    "extension": _check_choice("extension", _VALID_EXTENSIONS),
    "width": _check_optional_non_negative_int("width"),
    "height": _check_optional_non_negative_int("height"),
    "layout": _check_optional_str("layout"),
    "background": _check_optional_str("background"),
}


_DEFAULTS: dict[str, Any] = {
    "api_base": DEFAULT_API_BASE,
    "font": DEFAULT_FONT,
    "color": DEFAULT_COLOR,
    "outline_color": DEFAULT_OUTLINE_COLOR,
    "outline_width": DEFAULT_OUTLINE_WIDTH,
    "fontsize": DEFAULT_FONTSIZE,
    "dpi": DEFAULT_DPI,
    "style": DEFAULT_STYLE,
    "cache_enabled": True,
    "cache_dir": None,
    "api_timeout": DEFAULT_API_TIMEOUT,
    "image_timeout": DEFAULT_IMAGE_TIMEOUT,
    "max_retries": DEFAULT_MAX_RETRIES,
    "retry_backoff": DEFAULT_RETRY_BACKOFF,
    "backend": DEFAULT_BACKEND,
    "extension": DEFAULT_EXTENSION,
    "width": None,
    "height": None,
    "layout": None,
    "background": None,
}


class MemeplotlibConfig(MutableMapping[str, Any]):
    """RcParams-style validated mapping of memeplotlib defaults.

    Backed by an internal dictionary. Setting an unknown key raises
    ``KeyError``. Setting a known key with an invalid value raises
    ``ValueError``. Use :func:`rc_context` for scoped overrides.

    Notes
    -----
    Only the keys defined in :data:`MemeplotlibConfig.VALID_KEYS` are
    accepted. The set of keys is fixed at class definition time.

    Examples
    --------
    >>> from memeplotlib import config
    >>> config["font"] = "comic"  # doctest: +SKIP
    >>> config["dpi"]
    150
    """

    VALID_KEYS: frozenset[str] = frozenset(_VALIDATORS)

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(_DEFAULTS)

    def __getitem__(self, key: str) -> Any:
        try:
            return self._data[key]
        except KeyError as exc:
            raise KeyError(
                f"Unknown config key {key!r}. Valid keys: {sorted(self.VALID_KEYS)}"
            ) from exc

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in _VALIDATORS:
            raise KeyError(f"Unknown config key {key!r}. Valid keys: {sorted(self.VALID_KEYS)}")
        self._data[key] = _VALIDATORS[key](value)

    def __delitem__(self, key: str) -> None:
        if key not in _DEFAULTS:
            raise KeyError(f"Unknown config key {key!r}. Valid keys: {sorted(self.VALID_KEYS)}")
        self._data[key] = _DEFAULTS[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        body = ",\n  ".join(f"{k!r}: {v!r}" for k, v in sorted(self._data.items()))
        return f"MemeplotlibConfig({{\n  {body}\n}})"

    def reset(self) -> None:
        """Restore every key to its default value."""
        self._data = dict(_DEFAULTS)


config = MemeplotlibConfig()


@contextlib.contextmanager
def rc_context(rc: Mapping[str, Any] | None = None) -> Iterator[MemeplotlibConfig]:
    """Temporarily override config keys, restoring originals on exit.

    Mirrors :func:`matplotlib.rc_context`. Useful for scoped styling that
    should not leak to other code.

    Parameters
    ----------
    rc : Mapping or None, optional
        Mapping of key-value pairs to apply within the context. If ``None``,
        the active config is yielded unchanged but still snapshotted for
        restoration on exit.

    Yields
    ------
    MemeplotlibConfig
        The active config singleton.

    Examples
    --------
    >>> from memeplotlib import config, rc_context
    >>> config["font"] = "impact"
    >>> with rc_context({"font": "comic", "color": "yellow"}):
    ...     config["font"]
    'comic'
    >>> config["font"]
    'impact'
    """
    snapshot = dict(config._data)
    try:
        if rc is not None:
            for key, value in rc.items():
                config[key] = value
        yield config
    finally:
        config._data = snapshot
