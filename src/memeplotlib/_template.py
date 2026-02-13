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

    All coordinates are fractional (0.0 to 1.0) relative to the image
    dimensions. ``(0, 0)`` is the top-left corner.

    Attributes
    ----------
    anchor_x : float
        Left edge of the text box (0.0 to 1.0).
    anchor_y : float
        Top edge of the text box (0.0 to 1.0).
    scale_x : float
        Width of the text box as a fraction of image width.
    scale_y : float
        Height of the text box as a fraction of image height.
    align : str
        Horizontal text alignment (``"center"``, ``"left"``, ``"right"``).
    style : str
        Default text style for this position (``"upper"``, ``"lower"``,
        ``"none"``).
    angle : float
        Text rotation angle in degrees.
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
    """A meme template with a background image and text position metadata.

    Attributes
    ----------
    id : str
        Template identifier (e.g., ``"buzz"``, ``"drake"``).
    name : str
        Human-readable display name.
    image_url : str
        URL or local file path to the background image.
    text_positions : list of TextPosition
        Regions where text lines are rendered.
    keywords : list of str
        Search keywords associated with the template.
    example : list of str
        Example text lines for the template.
    """

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

        Parameters
        ----------
        template_id : str
            The memegen template ID (e.g., ``"buzz"``, ``"drake"``).
        api_base : str or None, optional
            Override the API base URL.

        Returns
        -------
        Template
            A Template instance with metadata populated from the API.

        Raises
        ------
        TemplateNotFoundError
            If the template ID doesn't exist in the memegen API.

        Examples
        --------
        >>> t = Template.from_memegen("buzz")  # doctest: +SKIP
        >>> t.name  # doctest: +SKIP
        'Buzz Lightyear'
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
        try:
            lines_count = max(1, int(data.get("lines", 2)))
        except (TypeError, ValueError):
            lines_count = 2
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

        Parameters
        ----------
        path_or_url : str
            Path to a local image file, or an HTTP(S) URL.
        lines : int, optional
            Number of text lines, which determines the number of text
            positions (default: 2).
        name : str, optional
            Display name for the template. Defaults to the file stem.

        Returns
        -------
        Template
            A Template instance backed by the given image.

        Examples
        --------
        >>> t = Template.from_image("photo.jpg")  # doctest: +SKIP
        >>> t = Template.from_image("https://example.com/img.png", lines=3)  # doctest: +SKIP
        """
        if lines < 1:
            raise ValueError("lines must be >= 1")

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
        """Return the template background image as a NumPy RGBA array.

        Downloads from the image URL if not already loaded or cached.

        Parameters
        ----------
        cache : TemplateCache or None, optional
            Cache instance for storing/retrieving downloaded images.

        Returns
        -------
        numpy.ndarray
            RGBA image array with shape ``(height, width, 4)``.
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
    """Registry that discovers and caches templates from the memegen API.

    Parameters
    ----------
    api_base : str or None, optional
        Base URL for the memegen API. Uses :attr:`config.api_base
        <MemeplotlibConfig.api_base>` if ``None``.
    cache : TemplateCache or None, optional
        Cache instance for storing template metadata.

    Examples
    --------
    >>> reg = TemplateRegistry()  # doctest: +SKIP
    >>> results = reg.search("dog")  # doctest: +SKIP
    >>> all_templates = reg.list_all()  # doctest: +SKIP
    """

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
        """Get a template by ID, fetching from the API if needed.

        Parameters
        ----------
        template_id : str
            The memegen template ID.

        Returns
        -------
        Template
            The resolved template.

        Raises
        ------
        TemplateNotFoundError
            If the template ID is not found.
        """
        catalog = self._fetch_catalog()

        for item in catalog:
            if item.get("id") == template_id:
                return Template._from_api_data(item, self._api_base)

        # Not in catalog — try direct fetch (might be a valid ID not in listing)
        return Template.from_memegen(template_id, api_base=self._api_base)

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search templates by keyword, name, or ID.

        Parameters
        ----------
        query : str
            Search term to match against template IDs, names, and
            keywords (case-insensitive).

        Returns
        -------
        list of dict
            Matching template metadata dicts.
        """
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
        """List all available templates.

        Returns
        -------
        list of dict
            Full template catalog from the memegen API.
        """
        return self._fetch_catalog()

    def refresh(self) -> None:
        """Force re-fetch of the template catalog from the API."""
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

    1. Local file path (contains ``/`` or ``\\`` or ends with an image
       extension)
    2. URL (starts with ``http://`` or ``https://``)
    3. memegen template ID

    Parameters
    ----------
    template : str
        Template identifier -- file path, URL, or memegen ID.
    registry : TemplateRegistry or None, optional
        Registry to use for memegen ID lookups.

    Returns
    -------
    Template
        The resolved template.
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
        raise FileNotFoundError(f"Template image file not found: {template}")

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
