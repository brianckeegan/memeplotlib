"""Tests for the template system."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import responses

from memeplotlib._cache import TemplateCache
from memeplotlib._template import (
    DEFAULT_TEXT_POSITIONS,
    Template,
    TemplateNotFoundError,
    TemplateRegistry,
    TextPosition,
    _resolve_template,
)


API_BASE = "https://api.memegen.link"


@pytest.fixture
def isolated_cache(tmp_path) -> TemplateCache:
    """A cache in a temp directory so tests don't share state."""
    return TemplateCache(cache_dir=tmp_path / "test_cache")


class TestTextPosition:
    def test_defaults(self):
        tp = TextPosition()
        assert tp.anchor_x == 0.0
        assert tp.anchor_y == 0.0
        assert tp.scale_x == 1.0
        assert tp.scale_y == 0.2
        assert tp.align == "center"
        assert tp.style == "upper"
        assert tp.angle == 0.0

    def test_frozen(self):
        tp = TextPosition()
        with pytest.raises(AttributeError):
            tp.anchor_x = 0.5  # type: ignore[misc]


class TestDefaultTextPositions:
    def test_has_two_positions(self):
        assert len(DEFAULT_TEXT_POSITIONS) == 2

    def test_top_position(self):
        top = DEFAULT_TEXT_POSITIONS[0]
        assert top.anchor_y == 0.0
        assert top.scale_y == 0.2

    def test_bottom_position(self):
        bottom = DEFAULT_TEXT_POSITIONS[1]
        assert bottom.anchor_y == 0.8
        assert bottom.scale_y == 0.2


class TestTemplate:
    def test_basic_creation(self):
        t = Template(id="test", name="Test", image_url="https://example.com/test.png")
        assert t.id == "test"
        assert t.name == "Test"
        assert len(t.text_positions) == 2

    @responses.activate
    def test_from_memegen_success(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/buzz",
            json={
                "id": "buzz",
                "name": "Buzz Lightyear",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
                "keywords": ["toy story", "everywhere"],
                "example": {"text": ["memes", "memes everywhere"]},
            },
            status=200,
        )

        t = Template.from_memegen("buzz", api_base=API_BASE)
        assert t.id == "buzz"
        assert t.name == "Buzz Lightyear"
        assert len(t.text_positions) == 2
        assert "toy story" in t.keywords

    @responses.activate
    def test_from_memegen_not_found(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/nonexistent",
            json={"error": "not found"},
            status=404,
        )

        with pytest.raises(TemplateNotFoundError):
            Template.from_memegen("nonexistent", api_base=API_BASE)

    @responses.activate
    def test_from_memegen_multi_line(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/multi",
            json={
                "id": "multi",
                "name": "Multi Line",
                "lines": 4,
                "blank": f"{API_BASE}/images/multi.png",
                "keywords": [],
                "example": {"text": ["a", "b", "c", "d"]},
            },
            status=200,
        )

        t = Template.from_memegen("multi", api_base=API_BASE)
        assert len(t.text_positions) == 4
        # Positions should be evenly distributed
        assert t.text_positions[0].anchor_y == 0.0
        assert t.text_positions[1].anchor_y == pytest.approx(0.25)

    def test_from_image_local(self, sample_image_file):
        t = Template.from_image(sample_image_file)
        assert t.id == "test_image"
        assert len(t.text_positions) == 2

    def test_from_image_url(self):
        t = Template.from_image("https://example.com/meme.png", lines=3)
        assert t.id == "meme"
        assert len(t.text_positions) == 3

    def test_from_image_custom_name(self, sample_image_file):
        t = Template.from_image(sample_image_file, name="My Template")
        assert t.name == "My Template"

    def test_get_image_preloaded(self, sample_template, sample_image):
        img = sample_template.get_image()
        assert isinstance(img, np.ndarray)
        assert img.shape == sample_image.shape

    def test_get_image_from_local_file(self, sample_image_file):
        t = Template.from_image(sample_image_file)
        img = t.get_image()
        assert isinstance(img, np.ndarray)
        assert img.ndim == 3
        assert img.shape[2] == 4  # RGBA


class TestTemplateRegistry:
    @responses.activate
    def test_get_from_catalog(self, isolated_cache):
        catalog = [
            {
                "id": "buzz",
                "name": "Buzz Lightyear",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
                "keywords": ["toy story"],
                "example": {"text": ["memes", "memes everywhere"]},
            },
        ]
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=catalog,
            status=200,
        )

        reg = TemplateRegistry(api_base=API_BASE, cache=isolated_cache)
        t = reg.get("buzz")
        assert t.id == "buzz"

    @responses.activate
    def test_search(self, isolated_cache):
        catalog = [
            {"id": "buzz", "name": "Buzz Lightyear", "keywords": ["toy story"]},
            {"id": "doge", "name": "Doge", "keywords": ["dog", "shiba"]},
        ]
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=catalog,
            status=200,
        )

        reg = TemplateRegistry(api_base=API_BASE, cache=isolated_cache)
        results = reg.search("dog")
        assert len(results) == 1
        assert results[0]["id"] == "doge"

    @responses.activate
    def test_list_all(self, isolated_cache):
        catalog = [
            {"id": "buzz", "name": "Buzz"},
            {"id": "doge", "name": "Doge"},
        ]
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=catalog,
            status=200,
        )

        reg = TemplateRegistry(api_base=API_BASE, cache=isolated_cache)
        all_templates = reg.list_all()
        assert len(all_templates) == 2


class TestResolveTemplate:
    def test_resolves_file_path(self, sample_image_file):
        t = _resolve_template(sample_image_file)
        assert isinstance(t, Template)

    def test_resolves_url(self):
        t = _resolve_template("https://example.com/meme.png")
        assert isinstance(t, Template)
        assert t.image_url == "https://example.com/meme.png"

    @responses.activate
    def test_resolves_memegen_id(self):
        responses.add(
            responses.GET,
            f"{API_BASE}/templates/",
            json=[{
                "id": "buzz",
                "name": "Buzz",
                "lines": 2,
                "blank": f"{API_BASE}/images/buzz.png",
                "keywords": [],
                "example": {"text": []},
            }],
            status=200,
        )

        t = _resolve_template("buzz")
        assert t.id == "buzz"
