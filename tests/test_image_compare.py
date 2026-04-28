"""Image-comparison tests using pytest-mpl.

Run ``pytest --mpl`` to compare against committed baselines, or
``pytest --mpl-generate-path=tests/baseline`` to regenerate them.

All tests pass ``font="Anton"`` explicitly. Anton is the bundled font
that ships with the package, so every platform — macOS dev (which has
Impact installed) and Linux/Windows CI (which don't) — renders with the
same glyph shapes. Without this, baselines generated on macOS with
Impact diverge from CI's Anton renderings by ~36-48 RMS, far past any
reasonable tolerance.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from memeplotlib import meme, memify  # noqa: E402

_TOLERANCE = 30  # generous because text rasterization still varies slightly
_BUNDLED_FONT = "Anton"


@pytest.fixture
def local_template(tmp_path):
    """Write a deterministic 200x300 RGBA PNG to disk for use as a template."""
    rng = np.random.default_rng(seed=1234)
    arr = rng.integers(0, 255, (200, 300, 4), dtype=np.uint8)
    arr[..., 3] = 255  # full opacity
    path = tmp_path / "template.png"
    Image.fromarray(arr).save(str(path))
    return str(path)


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=_TOLERANCE)
def test_meme_local_template(local_template):
    fig, _ = meme(local_template, "TOP CAPTION", "BOTTOM CAPTION", font=_BUNDLED_FONT)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=_TOLERANCE)
def test_meme_custom_color(local_template):
    fig, _ = meme(local_template, "yellow", color="yellow", font=_BUNDLED_FONT)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=_TOLERANCE)
def test_memify_overlay():
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([0, 1, 2, 3], [0, 1, 4, 9], lw=3)
    ax.set_facecolor("white")
    memify(fig, "STONKS", "STILL GOING UP", font=_BUNDLED_FONT)
    return fig
