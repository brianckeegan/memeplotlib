"""Tests for the caching system."""

from __future__ import annotations

import json
import time

import numpy as np
import pytest
import responses
from PIL import Image

from memeplotlib._cache import TemplateCache


@pytest.fixture
def cache(tmp_path) -> TemplateCache:
    return TemplateCache(cache_dir=tmp_path / "cache", max_memory=5)


@pytest.fixture
def sample_png_bytes(tmp_path) -> bytes:
    """Create a small PNG image in bytes."""
    rng = np.random.default_rng(seed=0)
    img = Image.fromarray(rng.integers(0, 255, (50, 50, 3), dtype=np.uint8))
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

    def test_permission_error_raises_clear_message(self, tmp_path, mocker):
        cache = TemplateCache(cache_dir=tmp_path / "cache")
        mocker.patch.object(
            type(cache._cache_dir),
            "mkdir",
            side_effect=PermissionError("Permission denied"),
        )
        with pytest.raises(PermissionError, match="Cannot create cache directory"):
            cache._ensure_dirs()


class TestCorruptImageHandling:
    def test_corrupt_disk_image_returns_none(self, cache):
        cache._ensure_dirs()
        key = cache._image_key("https://example.com/corrupt.png")
        disk_path = cache._images_dir / f"{key}.png"
        disk_path.write_bytes(b"not a valid image")

        result = cache.get_image("https://example.com/corrupt.png")
        assert result is None


class TestSharedDefaultCache:
    def test_meme_api_meme_class_and_registry_share_one_cache(self, sample_template):
        from memeplotlib import Meme, TemplateRegistry
        from memeplotlib._api import _cache as api_cache
        from memeplotlib._cache import default_cache

        shared = default_cache()
        assert api_cache is shared
        assert Meme(sample_template)._cache is shared
        assert TemplateRegistry()._cache is shared

    def test_explicit_registry_cache_is_respected(self, tmp_path):
        from memeplotlib import TemplateRegistry

        own = TemplateCache(cache_dir=tmp_path)
        assert TemplateRegistry(cache=own)._cache is own


class TestSingleDecode:
    def test_set_image_returns_decoded_array(self, cache, sample_png_bytes):
        arr = cache.set_image("https://example.com/a.png", sample_png_bytes)
        assert arr is not None and arr.shape[-1] == 4

    def test_set_image_returns_none_for_garbage(self, cache):
        assert cache.set_image("https://example.com/bad.png", b"not an image") is None

    @responses.activate
    def test_template_download_is_decoded_once(self, cache, sample_png_bytes, mocker):
        from PIL import Image

        from memeplotlib import Template, config

        mocker.patch.dict(config._data, {"cache_enabled": True})
        url = "https://example.com/blank.png"
        responses.add(responses.GET, url, body=sample_png_bytes, content_type="image/png")
        spy = mocker.spy(Image, "open")
        Template(id="t", name="t", image_url=url).get_image(cache=cache)
        assert spy.call_count == 1
