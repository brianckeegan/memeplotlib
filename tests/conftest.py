"""Shared fixtures for memeplotlib tests."""

from __future__ import annotations

import numpy as np
import pytest

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt  # noqa: E402

from memeplotlib._template import Template, TextPosition, DEFAULT_TEXT_POSITIONS  # noqa: E402


@pytest.fixture
def sample_image() -> np.ndarray:
    """A small 200x300 RGBA test image."""
    return np.random.randint(0, 255, (200, 300, 4), dtype=np.uint8)


@pytest.fixture
def sample_image_file(tmp_path, sample_image) -> str:
    """Write a sample image to a temp file and return its path."""
    from PIL import Image
    img = Image.fromarray(sample_image)
    path = tmp_path / "test_image.png"
    img.save(str(path))
    return str(path)


@pytest.fixture
def sample_template(sample_image) -> Template:
    """A Template with a test image and default text positions."""
    t = Template(
        id="test",
        name="Test Template",
        image_url="https://example.com/test.png",
        text_positions=list(DEFAULT_TEXT_POSITIONS),
    )
    t._image_array = sample_image
    return t


@pytest.fixture(autouse=True)
def _close_figures():
    """Close all matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")
