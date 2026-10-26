"""Regenerate ``src/memeplotlib/_geometry.py`` from upstream memegen.

memegen's API does not expose caption box geometry, only the line count.
The geometry lives in each template's ``templates/<id>/config.yml`` in the
memegen repository. This script snapshots it for every catalog template
whose boxes differ from memeplotlib's top/bottom-or-equal-bands guess, so
the Pillow and matplotlib backends draw captions where memegen does.

Run it by hand when upstream adds or edits templates::

    python scripts/update_template_geometry.py

It needs network access, PyYAML and black (from the ``dev`` extra).
"""

from __future__ import annotations

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yaml

from memeplotlib._template import TextPosition, _default_text_positions

API = "https://api.memegen.link/templates/"
RAW = "https://raw.githubusercontent.com/jacebrowning/memegen/main/templates/{id}/config.yml"
OUT = Path(__file__).resolve().parent.parent / "src" / "memeplotlib" / "_geometry.py"
FIELDS = ("anchor_x", "anchor_y", "scale_x", "scale_y")

HEADER = '''"""Caption box geometry for memegen templates (generated; do not edit).

memegen's API reports only how many caption lines a template has, so
memeplotlib otherwise guesses top/bottom boxes (or equal horizontal bands
for three or more lines). This table snapshots the real boxes from each
template's ``templates/<id>/config.yml`` in the memegen repository, for
the templates where the guess is wrong. It only affects the Pillow and
matplotlib backends; memegen positions captions itself.

Regenerate with ``python scripts/update_template_geometry.py``.
"""

from __future__ import annotations

from memeplotlib._template import TextPosition

TEMPLATE_GEOMETRY: dict[str, tuple[TextPosition, ...]] = {
'''


def _positions(config: dict) -> list[TextPosition]:
    return [
        TextPosition(
            anchor_x=float(box.get("anchor_x", 0.0)),
            anchor_y=float(box.get("anchor_y", 0.0)),
            scale_x=float(box.get("scale_x", 1.0)),
            scale_y=float(box.get("scale_y", 0.2)),
            align=str(box.get("align", "center")),
            angle=float(box.get("angle", 0.0)),
        )
        for box in config.get("text") or []
    ]


def _same(a: list[TextPosition], b: list[TextPosition]) -> bool:
    return len(a) == len(b) and all(
        p.align == q.align
        and p.angle == q.angle
        and all(math.isclose(getattr(p, f), getattr(q, f), abs_tol=1e-6) for f in FIELDS)
        for p, q in zip(a, b, strict=True)
    )


def _fetch(template_id: str) -> tuple[str, list[TextPosition] | None]:
    resp = requests.get(RAW.format(id=template_id), timeout=30)
    if resp.status_code != 200:
        return template_id, None
    return template_id, _positions(yaml.safe_load(resp.text) or {})


def _render(pos: TextPosition) -> str:
    args = [f"{f}={getattr(pos, f)!r}" for f in FIELDS]
    if pos.align != "center":
        args.append(f'align="{pos.align}"')
    if pos.angle:
        args.append(f"angle={pos.angle!r}")
    return f"        TextPosition({', '.join(args)}),\n"


def main() -> int:
    catalog = requests.get(API, timeout=30).json()
    lines = {t["id"]: int(t.get("lines", 2)) for t in catalog}
    with ThreadPoolExecutor(max_workers=8) as pool:
        fetched = dict(pool.map(_fetch, sorted(lines)))

    body = []
    for template_id, positions in sorted(fetched.items()):
        if not positions or len(positions) != lines[template_id]:
            continue
        if _same(positions, _default_text_positions(len(positions))):
            continue
        body.append(f'    "{template_id}": (\n')
        body.extend(_render(p) for p in positions)
        body.append("    ),\n")

    OUT.write_text(HEADER + "".join(body) + "}\n")
    subprocess.run([sys.executable, "-m", "black", "-q", str(OUT)], check=True)
    missing = sorted(t for t, p in fetched.items() if p is None)
    print(f"wrote {OUT.name}: {body.count('    ),' + chr(10))} templates", file=sys.stderr)
    if missing:
        print(f"no config.yml for: {', '.join(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
