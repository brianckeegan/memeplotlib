"""Disk and memory caching for template images and metadata."""

from __future__ import annotations

import hashlib
import io
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, cast

import numpy as np
import platformdirs
from PIL import Image

from memeplotlib._config import config


def _default_cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir("memeplotlib"))


class TemplateCache:
    """Two-level cache: in-memory LRU + on-disk file cache.

    Caches template catalog metadata and downloaded template images so that
    the memegen API is only hit once per template.

    Parameters
    ----------
    cache_dir : Path or None, optional
        Directory for on-disk cache files. If ``None``, the directory is
        resolved on every access from ``config["cache_dir"]``, falling back
        to the platform default (via :mod:`platformdirs`), so changing the
        config takes effect without rebuilding the cache.
    max_memory : int, optional
        Maximum number of images to keep in the in-memory LRU cache
        (default: 50).
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_memory: int = 50,
    ):
        self._explicit_dir = Path(cache_dir) if cache_dir is not None else None
        self._memory: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max_memory = max_memory

    @property
    def _cache_dir(self) -> Path:
        if self._explicit_dir is not None:
            return self._explicit_dir
        configured = config["cache_dir"]
        if configured:
            return Path(configured).expanduser()
        return _default_cache_dir()

    @property
    def _images_dir(self) -> Path:
        return self._cache_dir / "images"

    def _ensure_dirs(self) -> None:
        """Create cache directories if they don't exist."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._images_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create cache directory '{self._cache_dir}': {e}. "
                f"Set config['cache_dir'] to a writable path or set "
                f"config['cache_enabled'] = False to disable caching."
            ) from e

    # --- Catalog (template list) ---

    def get_catalog(self, ttl: int = 86400) -> list[dict[str, Any]] | None:
        """Get cached template catalog if it exists and hasn't expired.

        Parameters
        ----------
        ttl : int, optional
            Time-to-live in seconds (default: 86400, i.e. 24 hours).

        Returns
        -------
        list of dict or None
            List of template metadata dicts, or ``None`` on cache miss
            or expiry.
        """
        catalog_path = self._cache_dir / "catalog.json"
        if not catalog_path.exists():
            return None

        try:
            data = json.loads(catalog_path.read_text())
            if time.time() - data.get("timestamp", 0) > ttl:
                return None
            templates = data.get("templates")
            if templates is None:
                return None
            return cast("list[dict[str, Any]]", templates)
        except (json.JSONDecodeError, KeyError):
            return None

    def set_catalog(self, templates: list[dict[str, Any]]) -> None:
        """Cache template catalog to disk with current timestamp.

        Parameters
        ----------
        templates : list of dict
            Template metadata dicts to cache.
        """
        self._ensure_dirs()
        data = {"timestamp": time.time(), "templates": templates}
        (self._cache_dir / "catalog.json").write_text(json.dumps(data))

    # --- Images ---

    def _image_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def get_image(self, url: str) -> np.ndarray | None:
        """Get cached template image as a NumPy array.

        Checks the in-memory LRU cache first, then falls back to the
        on-disk file cache.

        Parameters
        ----------
        url : str
            The image URL used as the cache key.

        Returns
        -------
        numpy.ndarray or None
            RGBA image array, or ``None`` on cache miss.
        """
        key = self._image_key(url)

        # Check memory
        if key in self._memory:
            self._memory.move_to_end(key)
            return self._memory[key]

        # Check disk
        disk_path = self._images_dir / f"{key}.png"
        if disk_path.exists():
            try:
                img = np.array(Image.open(disk_path).convert("RGBA"))
                self._memory_put(key, img)
                return img
            except (OSError, Image.DecompressionBombError):
                return None

        return None

    def set_image(self, url: str, image_bytes: bytes) -> np.ndarray | None:
        """Cache template image to disk and memory.

        Parameters
        ----------
        url : str
            The image URL used as the cache key.
        image_bytes : bytes
            Raw image file bytes to store.

        Returns
        -------
        numpy.ndarray or None
            The decoded RGBA array (decoded once, from memory), or ``None``
            if the bytes are not a readable image. Callers should use it
            rather than decoding *image_bytes* a second time.
        """
        self._ensure_dirs()
        key = self._image_key(url)

        # Write to disk
        disk_path = self._images_dir / f"{key}.png"
        disk_path.write_bytes(image_bytes)

        # Decode from the bytes already in memory, not by re-reading the file.
        try:
            img = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGBA"))
        except (OSError, Image.DecompressionBombError):
            return None
        self._memory_put(key, img)
        return img

    def _memory_put(self, key: str, value: np.ndarray) -> None:
        """Add to in-memory LRU cache, evicting oldest if at capacity."""
        if key in self._memory:
            self._memory.move_to_end(key)
        else:
            if len(self._memory) >= self._max_memory:
                self._memory.popitem(last=False)
            self._memory[key] = value

    def clear(self) -> None:
        """Clear all caches (memory and disk)."""
        self._memory.clear()
        if self._cache_dir.exists():
            import shutil

            shutil.rmtree(self._cache_dir)


_default_cache: TemplateCache | None = None
_default_cache_lock = threading.Lock()


def default_cache() -> TemplateCache:
    """Return the process-wide cache shared by ``meme()``, ``Meme``, and registries.

    Sharing one instance means the in-memory LRU actually serves repeat
    renders (e.g. a loop of ``Meme("buzz", ...)`` calls) instead of each
    object re-reading and re-decoding images from disk.
    """
    global _default_cache
    if _default_cache is None:
        with _default_cache_lock:
            if _default_cache is None:
                _default_cache = TemplateCache()
    return _default_cache
