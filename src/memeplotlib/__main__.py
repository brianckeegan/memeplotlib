"""CLI interface for memeplotlib: ``python -m memeplotlib``."""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memeplotlib",
        description="Create memes from the command line using matplotlib.",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="List all available meme templates")

    # search
    sp_search = sub.add_parser("search", help="Search templates by keyword")
    sp_search.add_argument("query", help="Search term")

    # info
    sp_info = sub.add_parser("info", help="Show details for a template")
    sp_info.add_argument("template_id", help="Template ID (e.g. 'buzz', 'drake')")

    # create
    sp_create = sub.add_parser("create", help="Create a meme and save to file")
    sp_create.add_argument("template", help="Template ID, image path, or URL")
    sp_create.add_argument("lines", nargs="+", help="Text lines (top, bottom, ...)")
    sp_create.add_argument(
        "-o", "--output", default="meme.png", help="Output file path (default: meme.png)"
    )
    sp_create.add_argument("--font", default=None, help="Font family name")
    sp_create.add_argument("--style", default=None, help="Text style: upper, lower, none")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "list":
        return _cmd_list()
    elif args.command == "search":
        return _cmd_search(args.query)
    elif args.command == "info":
        return _cmd_info(args.template_id)
    elif args.command == "create":
        return _cmd_create(args)

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
    print(f"Lines:    {len(tmpl.text_positions)}")
    print(f"Keywords: {', '.join(tmpl.keywords) or '(none)'}")
    if tmpl.example:
        print(f"Example:  {' / '.join(tmpl.example)}")
    return 0


def _cmd_create(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")

    from memeplotlib._api import meme

    kwargs: dict[str, Any] = {"show": False, "savefig": args.output}
    if args.font:
        kwargs["font"] = args.font
    if args.style:
        kwargs["style"] = args.style

    meme(args.template, *args.lines, **kwargs)
    print(f"Saved to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
