"""CLI interface for memeplotlib: ``python -m memeplotlib``."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from memeplotlib import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memeplotlib",
        description="Create memes from the command line using matplotlib.",
    )
    parser.add_argument("--version", action="version", version=f"memeplotlib {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all available meme templates.")

    sp_search = sub.add_parser("search", help="Search templates by keyword.")
    sp_search.add_argument("query", help="Search term.")

    sp_info = sub.add_parser("info", help="Show details for a template.")
    sp_info.add_argument("template_id", help="Template ID (e.g. 'buzz', 'drake').")

    # 'meme' (canonical) and 'create' (alias for backward compatibility)
    for name, help_text in (
        ("meme", "Render a meme and save it to a file."),
        ("create", "Alias for 'meme'."),
    ):
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("template", help="Template ID, image path, or URL.")
        sp.add_argument("lines", nargs="*", help="Caption text lines (top, bottom, ...).")
        sp.add_argument(
            "-o",
            "--out",
            "--output",
            dest="out",
            default="meme.png",
            help="Output file path (default: meme.png).",
        )
        sp.add_argument("--font", default=None, help="Font family name.")
        sp.add_argument(
            "--color", default=None, help="Caption text color (any matplotlib color spec)."
        )
        sp.add_argument(
            "--style",
            default=None,
            choices=["upper", "lower", "none"],
            help="Caption text transform.",
        )
        sp.add_argument("--fontsize", type=float, default=None, help="Font size in points.")
        sp.add_argument("--dpi", type=int, default=None, help="DPI for the rendered output.")
        sp.add_argument(
            "--backend",
            default=None,
            choices=["auto", "memegen", "pillow", "matplotlib"],
            help="Rendering backend (default: 'auto').",
        )
        sp.add_argument(
            "--ext",
            dest="extension",
            default=None,
            choices=["png", "jpg", "jpeg", "gif", "webp"],
            help="Output format requested from memegen (default: png).",
        )
        sp.add_argument(
            "--width", type=int, default=None, help="Output width in pixels (memegen)."
        )
        sp.add_argument(
            "--height", type=int, default=None, help="Output height in pixels (memegen)."
        )
        sp.add_argument("--layout", default=None, help="Memegen layout (e.g. 'top').")
        sp.add_argument(
            "--background",
            default=None,
            help="Custom background URL forwarded to memegen.",
        )
        sp.add_argument(
            "--template-style",
            dest="template_style",
            default=None,
            help="Memegen template-specific style (e.g. 'maga').",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "list":
        return _cmd_list()
    if args.command == "search":
        return _cmd_search(args.query)
    if args.command == "info":
        return _cmd_info(args.template_id)
    if args.command in ("meme", "create"):
        return _cmd_meme(args)

    return 0


def _cmd_list() -> int:
    from memeplotlib._template import TemplateRegistry

    registry = TemplateRegistry()
    catalog = registry.list_all()
    print(f"{'ID':<20} {'Name':<40}")
    print("-" * 60)
    for item in catalog:
        tid = item.get("id", "")
        name = item.get("name", "")
        print(f"{tid:<20} {name:<40}")
    print(f"\n{len(catalog)} templates available")
    return 0


def _cmd_search(query: str) -> int:
    from memeplotlib._template import TemplateRegistry

    registry = TemplateRegistry()
    results = registry.search(query)
    if not results:
        print(f"No templates found matching '{query}'")
        return 0
    print(f"{'ID':<20} {'Name':<40}")
    print("-" * 60)
    for item in results:
        tid = item.get("id", "")
        name = item.get("name", "")
        print(f"{tid:<20} {name:<40}")
    print(f"\n{len(results)} results")
    return 0


def _cmd_info(template_id: str) -> int:
    from memeplotlib._template import Template, TemplateNotFoundError

    try:
        tmpl = Template.from_memegen(template_id)
    except TemplateNotFoundError:
        print(f"Template '{template_id}' not found")
        return 1

    print(f"ID:       {tmpl.id}")
    print(f"Name:     {tmpl.name}")
    print(f"URL:      {tmpl.image_url}")
    print(f"Lines:    {tmpl.lines_count}")
    print(f"Overlays: {tmpl.overlays_count}")
    print(f"Styles:   {', '.join(tmpl.styles) or '(default)'}")
    print(f"Keywords: {', '.join(tmpl.keywords) or '(none)'}")
    if tmpl.example:
        print(f"Example:  {' / '.join(tmpl.example)}")
    return 0


def _cmd_meme(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")

    from memeplotlib._api import meme

    kwargs: dict[str, Any] = {"show": False, "savefig": args.out}
    for key in (
        "font",
        "color",
        "style",
        "fontsize",
        "dpi",
        "backend",
        "extension",
        "width",
        "height",
        "layout",
        "background",
        "template_style",
    ):
        value = getattr(args, key, None)
        if value is not None:
            kwargs[key] = value

    meme(args.template, *args.lines, **kwargs)
    print(f"Saved to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
