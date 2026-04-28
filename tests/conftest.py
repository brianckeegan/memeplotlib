"""Shared fixtures for memeplotlib tests."""

from __future__ import annotations

import re

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt  # noqa: E402

from memeplotlib._template import DEFAULT_TEXT_POSITIONS, Template  # noqa: E402


# Tests that pre-date the v0.5.0 backend split assume the old blank-image-
# fetch + matplotlib draw flow. Force ``backend="matplotlib"`` for those
# legacy tests via a config snapshot fixture; new tests for the memegen
# and pillow backends opt in explicitly with ``backend=...``.
@pytest.fixture(autouse=True)
def _legacy_matplotlib_backend(request):
    """Default tests to the legacy matplotlib backend.

    Tests opt out by adding ``@pytest.mark.uses_default_backend``; in that
    case ``config["backend"]`` is left at its default (``"auto"``) so the
    test exercises the new dispatcher.
    """
    from memeplotlib import config

    if request.node.get_closest_marker("uses_default_backend"):
        yield
        return

    original = config["backend"]
    config["backend"] = "matplotlib"
    try:
        yield
    finally:
        config["backend"] = original


def memegen_rendered_pattern(template_id: str = ".+") -> re.Pattern[str]:
    """Regex matching any memegen rendered URL for *template_id*.

    Useful with ``responses.add(..., url=memegen_rendered_pattern("buzz"))``
    when a test exercises the memegen backend and the exact URL depends on
    the caption text or query parameters.
    """
    return re.compile(
        rf"https://api\.memegen\.link/images/{template_id}/[^?]+\.(png|jpg|gif|webp)(\?.*)?"
    )


@pytest.fixture
def sample_image() -> np.ndarray:
    """A small 200x300 RGBA test image."""
    rng = np.random.default_rng(seed=0)
    return rng.integers(0, 255, (200, 300, 4), dtype=np.uint8)


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


@pytest.fixture(autouse=True)
def _block_real_network(request):
    """Block any real socket use to keep the suite offline-only.

    Tests that legitimately need a TCP socket (pytest-httpserver) opt out
    via ``@pytest.mark.allow_network``. The ``responses`` library installs
    an HTTP transport adapter that does not open real sockets, so existing
    HTTP-mocked tests are unaffected.
    """
    if request.node.get_closest_marker("allow_network"):
        yield
        return
    pytest_socket = pytest.importorskip("pytest_socket")
    pytest_socket.disable_socket(allow_unix_socket=True)
    try:
        yield
    finally:
        pytest_socket.enable_socket()
