"""Tests for the caching system."""

from __future__ import annotations

import json
import time

import numpy as np
import pytest
from PIL import Image

from memeplotlib._cache import TemplateCache


@pytest.fixture
def cache(tmp_path) -> TemplateCache:
    return TemplateCache(cache_dir=tmp_path / "cache", max_memory=5)


@pytest.fixture
def sample_png_bytes(tmp_path) -> bytes:
    """Create a small PNG image in bytes."""
    img = Image.fromarray(np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8))
    path = tmp_path / "sample.png"
    img.save(str(path))
    return path.read_bytes()


class TestCatalogCache:
    def test_miss_when_empty(self, cache):
        assert cache.get_catalog() is None

    def test_store_and_retrieve(self, cache):
        templates = [{"id": "buzz", "name": "Buzz"}]
        cache.set_catalog(templates)
        result = cache.get_catalog()
        assert result == templates

    def test_ttl_expiry(self, cache):
        templates = [{"id": "buzz", "name": "Buzz"}]
        cache.set_catalog(templates)

        # Manually set timestamp to the past
        catalog_path = cache._cache_dir / "catalog.json"
        data = json.loads(catalog_path.read_text())
        data["timestamp"] = time.time() - 100000
        catalog_path.write_text(json.dumps(data))

        assert cache.get_catalog(ttl=86400) is None

    def test_corrupted_json_returns_none(self, cache):
        cache._ensure_dirs()
        (cache._cache_dir / "catalog.json").write_text("not valid json{{{")
        assert cache.get_catalog() is None


class TestImageCache:
    def test_miss_when_empty(self, cache):
        assert cache.get_image("https://example.com/test.png") is None

    def test_store_and_retrieve(self, cache, sample_png_bytes):
        url = "https://example.com/test.png"
        cache.set_image(url, sample_png_bytes)
        result = cache.get_image(url)
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.ndim == 3

    def test_memory_cache_hit(self, cache, sample_png_bytes):
        url = "https://example.com/test.png"
        cache.set_image(url, sample_png_bytes)

        # Clear disk cache but memory should still have it
        key = cache._image_key(url)
        disk_path = cache._images_dir / f"{key}.png"
        disk_path.unlink()

        result = cache.get_image(url)
        assert result is not None

    def test_memory_lru_eviction(self, cache, sample_png_bytes):
        # Fill cache beyond capacity (max_memory=5)
        for i in range(7):
            cache.set_image(f"https://example.com/{i}.png", sample_png_bytes)

        assert len(cache._memory) == 5

    def test_disk_fallback(self, cache, sample_png_bytes):
        url = "https://example.com/test.png"
        cache.set_image(url, sample_png_bytes)

        # Clear memory cache
        cache._memory.clear()

        # Should load from disk
        result = cache.get_image(url)
        assert result is not None


class TestCacheClear:
    def test_clear_removes_everything(self, cache, sample_png_bytes):
        cache.set_catalog([{"id": "test"}])
        cache.set_image("https://example.com/test.png", sample_png_bytes)

        cache.clear()

        assert len(cache._memory) == 0
        assert not cache._cache_dir.exists()


class TestCacheDirCreation:
    def test_dirs_created_on_set(self, tmp_path):
        cache_dir = tmp_path / "new" / "nested" / "cache"
        cache = TemplateCache(cache_dir=cache_dir)

        assert not cache_dir.exists()
        cache.set_catalog([{"id": "test"}])
        assert cache_dir.exists()
        assert (cache_dir / "images").exists()
