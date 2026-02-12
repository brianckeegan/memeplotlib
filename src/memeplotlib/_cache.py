"""Disk and memory caching for template images and metadata."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

import platformdirs


def _default_cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir("memeplotlib"))


class TemplateCache:
    """Two-level cache: in-memory LRU + on-disk file cache.

    Caches template catalog metadata and downloaded template images so that
    the memegen API is only hit once per template.

    Parameters
    ----------
    cache_dir : Path or None, optional
        Directory for on-disk cache files. Uses the platform default
        (via :mod:`platformdirs`) if ``None``.
    max_memory : int, optional
        Maximum number of images to keep in the in-memory LRU cache
        (default: 50).
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_memory: int = 50,
    ):
        self._cache_dir = cache_dir or _default_cache_dir()
        self._images_dir = self._cache_dir / "images"
        self._memory: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max_memory = max_memory

    def _ensure_dirs(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._images_dir.mkdir(parents=True, exist_ok=True)

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
            return data.get("templates")
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
            except Exception:
                return None

        return None

    def set_image(self, url: str, image_bytes: bytes) -> None:
        """Cache template image to disk and memory.

        Parameters
        ----------
        url : str
            The image URL used as the cache key.
        image_bytes : bytes
            Raw image file bytes to store.
        """
        self._ensure_dirs()
        key = self._image_key(url)

        # Write to disk
        disk_path = self._images_dir / f"{key}.png"
        disk_path.write_bytes(image_bytes)

        # Load into memory as numpy array
        try:
            img = np.array(Image.open(disk_path).convert("RGBA"))
            self._memory_put(key, img)
        except Exception:
            pass

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
