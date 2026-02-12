"""Template system: data classes, registry, and memegen API client."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import requests
from PIL import Image

from memeplotlib._cache import TemplateCache
from memeplotlib._config import DEFAULT_API_BASE, IMAGE_EXTENSIONS, config


class TemplateNotFoundError(Exception):
    """Raised when a template ID is not found in the memegen API."""


@dataclass(frozen=True)
class TextPosition:
    """Defines where and how a text line is rendered on a template.

    All coordinates are fractional (0.0 to 1.0) relative to the image dimensions.
    (0, 0) is the top-left corner.
    """

    anchor_x: float = 0.0
    anchor_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 0.2
    align: str = "center"
    style: str = "upper"
    angle: float = 0.0


# Classic top/bottom meme layout
DEFAULT_TEXT_POSITIONS = [
    TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.2),
    TextPosition(anchor_x=0.0, anchor_y=0.8, scale_x=1.0, scale_y=0.2),
]


@dataclass
class Template:
    """A meme template with a background image and text position metadata."""

    id: str
    name: str
    image_url: str
    text_positions: list[TextPosition] = field(default_factory=lambda: list(DEFAULT_TEXT_POSITIONS))
    keywords: list[str] = field(default_factory=list)
    example: list[str] = field(default_factory=list)
    _image_array: np.ndarray | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_memegen(
        cls,
        template_id: str,
        api_base: str | None = None,
    ) -> Template:
        """Fetch template metadata and blank image from the memegen API.

        Args:
            template_id: The memegen template ID (e.g., "buzz", "drake").
            api_base: Override the API base URL.

        Returns:
            A Template instance with metadata populated.

        Raises:
            TemplateNotFoundError: If the template ID doesn't exist.
        """
        base = api_base or config.api_base
        url = f"{base}/templates/{template_id}"
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        resp.raise_for_status()

        data = resp.json()
        return cls._from_api_data(data, base)

    @classmethod
    def _from_api_data(cls, data: dict[str, Any], api_base: str) -> Template:
        """Build a Template from a memegen API response dict."""
        template_id = data.get("id", "")
        name = data.get("name", template_id)
        blank_url = data.get("blank", f"{api_base}/images/{template_id}.png")
        keywords = data.get("keywords", [])
        example_lines = data.get("example", {}).get("text", [])

        # Parse text positions from API data if available, otherwise use defaults
        lines_count = data.get("lines", 2)
        if lines_count <= 2:
            text_positions = list(DEFAULT_TEXT_POSITIONS)
        else:
            # Distribute text positions evenly across the image
            text_positions = []
            slot_height = 1.0 / lines_count
            for i in range(lines_count):
                text_positions.append(
                    TextPosition(
                        anchor_x=0.0,
                        anchor_y=i * slot_height,
                        scale_x=1.0,
                        scale_y=slot_height,
                    )
                )

        return cls(
            id=template_id,
            name=name,
            image_url=blank_url,
            text_positions=text_positions,
            keywords=keywords,
            example=example_lines,
        )

    @classmethod
    def from_image(
        cls,
        path_or_url: str,
        lines: int = 2,
        name: str = "",
    ) -> Template:
        """Create a template from a local image file or URL.

        Args:
            path_or_url: Path to a local image file, or an HTTP(S) URL.
            lines: Number of text lines (determines text positions).
            name: Optional display name for the template.

        Returns:
            A Template instance.
        """
        if path_or_url.startswith(("http://", "https://")):
            image_url = path_or_url
            template_id = Path(path_or_url).stem
        else:
            path = Path(path_or_url).expanduser().resolve()
            image_url = str(path)
            template_id = path.stem

        if lines <= 2:
            text_positions = list(DEFAULT_TEXT_POSITIONS[:lines])
        else:
            slot_height = 1.0 / lines
            text_positions = [
                TextPosition(
                    anchor_x=0.0,
                    anchor_y=i * slot_height,
                    scale_x=1.0,
                    scale_y=slot_height,
                )
                for i in range(lines)
            ]

        return cls(
            id=template_id,
            name=name or template_id,
            image_url=image_url,
            text_positions=text_positions,
        )

    def get_image(self, cache: TemplateCache | None = None) -> np.ndarray:
        """Return the template background image as a numpy RGBA array.

        Downloads from the image URL if not already loaded or cached.
        """
        if self._image_array is not None:
            return self._image_array

        # Check cache
        if cache is not None:
            cached = cache.get_image(self.image_url)
            if cached is not None:
                self._image_array = cached
                return cached

        # Load from local file or URL
        if self.image_url.startswith(("http://", "https://")):
            resp = requests.get(self.image_url, timeout=15)
            resp.raise_for_status()
            image_bytes = resp.content
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            # Cache the downloaded image
            if cache is not None:
                cache.set_image(self.image_url, image_bytes)
        else:
            img = Image.open(self.image_url).convert("RGBA")

        self._image_array = np.array(img)
        return self._image_array


class TemplateRegistry:
    """Registry that discovers and caches templates from the memegen API."""

    def __init__(
        self,
        api_base: str | None = None,
        cache: TemplateCache | None = None,
    ):
        self._api_base = api_base or config.api_base
        self._cache = cache or TemplateCache()
        self._catalog: list[dict[str, Any]] | None = None

    def _fetch_catalog(self) -> list[dict[str, Any]]:
        """Fetch or return cached template catalog."""
        if self._catalog is not None:
            return self._catalog

        # Try disk cache
        if config.cache_enabled:
            cached = self._cache.get_catalog()
            if cached is not None:
                self._catalog = cached
                return cached

        # Fetch from API
        resp = requests.get(f"{self._api_base}/templates/", timeout=10)
        resp.raise_for_status()
        self._catalog = resp.json()

        if config.cache_enabled:
            self._cache.set_catalog(self._catalog)

        return self._catalog

    def get(self, template_id: str) -> Template:
        """Get a template by ID, fetching from API if needed."""
        catalog = self._fetch_catalog()

        for item in catalog:
            if item.get("id") == template_id:
                return Template._from_api_data(item, self._api_base)

        # Not in catalog — try direct fetch (might be a valid ID not in listing)
        return Template.from_memegen(template_id, api_base=self._api_base)

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search templates by keyword, name, or ID."""
        catalog = self._fetch_catalog()
        query_lower = query.lower()
        results = []
        for item in catalog:
            searchable = " ".join([
                item.get("id", ""),
                item.get("name", ""),
                " ".join(item.get("keywords", [])),
            ]).lower()
            if query_lower in searchable:
                results.append(item)
        return results

    def list_all(self) -> list[dict[str, Any]]:
        """List all available templates."""
        return self._fetch_catalog()

    def refresh(self) -> None:
        """Force re-fetch of the template catalog."""
        self._catalog = None
        resp = requests.get(f"{self._api_base}/templates/", timeout=10)
        resp.raise_for_status()
        self._catalog = resp.json()
        if config.cache_enabled:
            self._cache.set_catalog(self._catalog)


def _resolve_template(
    template: str,
    registry: TemplateRegistry | None = None,
) -> Template:
    """Resolve a template string to a Template object.

    Resolution order:
    1. Local file path (contains / or \\ or ends with image extension)
    2. URL (starts with http:// or https://)
    3. memegen template ID
    """
    # Check if it's a file path
    p = Path(template)
    if (
        "/" in template
        or "\\" in template
        or p.suffix.lower() in IMAGE_EXTENSIONS
    ):
        if p.exists():
            return Template.from_image(template)

    # Check if it's a URL
    if template.startswith(("http://", "https://")):
        return Template.from_image(template)

    # Treat as memegen template ID
    reg = registry or _default_registry()
    return reg.get(template)


# Module-level singleton
_registry: TemplateRegistry | None = None


def _default_registry() -> TemplateRegistry:
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
