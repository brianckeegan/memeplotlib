"""Global configuration defaults for memeplotlib."""

from dataclasses import dataclass

DEFAULT_API_BASE = "https://api.memegen.link"
DEFAULT_FONT = "impact"
DEFAULT_COLOR = "white"
DEFAULT_OUTLINE_COLOR = "black"
DEFAULT_OUTLINE_WIDTH = 2.0
DEFAULT_FONTSIZE = 72.0
DEFAULT_DPI = 150
DEFAULT_STYLE = "upper"
DEFAULT_FIGSIZE_WIDTH = 8.0

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}


@dataclass
class MemeplotlibConfig:
    """Global configuration for memeplotlib.

    Modify this object to change defaults for all meme creation calls.
    Individual function calls can still override via keyword arguments.

    Attributes
    ----------
    api_base : str
        Base URL for the memegen API.
    font : str
        Default font family name.
    color : str
        Default text fill color.
    outline_color : str
        Default text outline color.
    outline_width : float
        Default outline stroke width.
    fontsize : float
        Base font size in points for auto-sizing.
    dpi : int
        Default dots per inch for rendering.
    style : str
        Default text transform (``"upper"``, ``"lower"``, or ``"none"``).
    cache_enabled : bool
        Whether disk caching is enabled.
    cache_dir : str or None
        Custom cache directory path, or ``None`` for the platform default.

    Examples
    --------
    >>> import memeplotlib as memes
    >>> memes.config.font = "comic"  # doctest: +SKIP
    >>> memes.config.color = "yellow"  # doctest: +SKIP
    """

    api_base: str = DEFAULT_API_BASE
    font: str = DEFAULT_FONT
    color: str = DEFAULT_COLOR
    outline_color: str = DEFAULT_OUTLINE_COLOR
    outline_width: float = DEFAULT_OUTLINE_WIDTH
    fontsize: float = DEFAULT_FONTSIZE
    dpi: int = DEFAULT_DPI
    style: str = DEFAULT_STYLE
    cache_enabled: bool = True
    cache_dir: str | None = None


config = MemeplotlibConfig()
