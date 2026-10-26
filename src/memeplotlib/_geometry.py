"""Caption box geometry for memegen templates (generated; do not edit).

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
    "3hd": (
        TextPosition(anchor_x=0.0, anchor_y=0.65, scale_x=0.27, scale_y=0.13),
        TextPosition(anchor_x=0.365, anchor_y=0.55, scale_x=0.27, scale_y=0.13),
        TextPosition(anchor_x=0.73, anchor_y=0.6, scale_x=0.27, scale_y=0.13),
    ),
    "astronaut": (
        TextPosition(anchor_x=0.45, anchor_y=0.35, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.75, anchor_y=0.0, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.375, anchor_y=0.8, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.75, anchor_y=0.7, scale_x=0.25, scale_y=0.1),
    ),
    "balloon": (
        TextPosition(anchor_x=0.61, anchor_y=0.1, scale_x=0.39, scale_y=0.2),
        TextPosition(anchor_x=0.8, anchor_y=0.57, scale_x=0.39, scale_y=0.2),
        TextPosition(anchor_x=0.0, anchor_y=0.7, scale_x=0.27, scale_y=0.2),
    ),
    "because": (
        TextPosition(anchor_x=0.0, anchor_y=0.375, scale_x=1.0, scale_y=0.125),
        TextPosition(anchor_x=0.0, anchor_y=0.875, scale_x=1.0, scale_y=0.125),
    ),
    "bilbo": (
        TextPosition(anchor_x=0.0, anchor_y=0.4, scale_x=1.0, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.9, scale_x=1.0, scale_y=0.1),
    ),
    "bongo": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.48, scale_y=0.5),
        TextPosition(anchor_x=0.0, anchor_y=0.5, scale_x=0.48, scale_y=0.5),
    ),
    "both": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.2),
        TextPosition(anchor_x=0.0, anchor_y=0.75, scale_x=1.0, scale_y=0.2),
    ),
    "bus": (
        TextPosition(anchor_x=0.0, anchor_y=0.25, scale_x=0.4, scale_y=0.3),
        TextPosition(anchor_x=0.5, anchor_y=0.16, scale_x=0.4, scale_y=0.3),
    ),
    "captain-america": (
        TextPosition(anchor_x=0.0, anchor_y=0.23, scale_x=1.0, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.57, scale_x=0.4, scale_y=0.08),
        TextPosition(anchor_x=0.5, anchor_y=0.56, scale_x=0.5, scale_y=0.1),
    ),
    "chair": (
        TextPosition(anchor_x=0.0, anchor_y=0.2, scale_x=0.495, scale_y=0.13),
        TextPosition(anchor_x=0.495, anchor_y=0.2, scale_x=0.505, scale_y=0.13),
        TextPosition(anchor_x=0.0, anchor_y=0.535, scale_x=0.495, scale_y=0.13),
        TextPosition(anchor_x=0.495, anchor_y=0.525, scale_x=0.505, scale_y=0.14),
        TextPosition(anchor_x=0.0, anchor_y=0.87, scale_x=0.5, scale_y=0.13),
        TextPosition(anchor_x=0.5, anchor_y=0.87, scale_x=0.5, scale_y=0.13),
    ),
    "cmm": (TextPosition(anchor_x=0.33, anchor_y=0.33, scale_x=0.46, scale_y=0.25, angle=23.0),),
    "crow": (
        TextPosition(anchor_x=0.325, anchor_y=0.02, scale_x=0.15, scale_y=0.15),
        TextPosition(anchor_x=0.615, anchor_y=0.72, scale_x=0.3, scale_y=0.2, angle=12.0),
    ),
    "crowd": (
        TextPosition(anchor_x=0.14, anchor_y=0.01, scale_x=0.38, scale_y=0.3, angle=8.0),
        TextPosition(anchor_x=0.05, anchor_y=0.01, scale_x=0.38, scale_y=0.3, angle=8.0),
    ),
    "db": (
        TextPosition(anchor_x=0.12, anchor_y=0.7, scale_x=0.325, scale_y=0.1),
        TextPosition(anchor_x=0.55, anchor_y=0.45, scale_x=0.175, scale_y=0.1),
        TextPosition(anchor_x=0.74, anchor_y=0.66, scale_x=0.2, scale_y=0.1),
    ),
    "dbg": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.48, scale_y=0.5),
        TextPosition(anchor_x=0.0, anchor_y=0.5, scale_x=0.48, scale_y=0.5),
    ),
    "dg": (
        TextPosition(anchor_x=0.02, anchor_y=0.6, scale_x=0.35, scale_y=0.2),
        TextPosition(anchor_x=0.45, anchor_y=0.75, scale_x=0.25, scale_y=0.15),
        TextPosition(anchor_x=0.75, anchor_y=0.65, scale_x=0.225, scale_y=0.15),
    ),
    "dragon": (TextPosition(anchor_x=0.22, anchor_y=0.505, scale_x=0.25, scale_y=0.119),),
    "drowning": (
        TextPosition(anchor_x=0.03, anchor_y=0.33, scale_x=0.46, scale_y=0.15),
        TextPosition(anchor_x=0.51, anchor_y=0.14, scale_x=0.2, scale_y=0.2),
        TextPosition(anchor_x=0.03, anchor_y=0.82, scale_x=0.46, scale_y=0.15),
    ),
    "ds": (
        TextPosition(anchor_x=0.085, anchor_y=0.085, scale_x=0.32, scale_y=0.095, angle=12.5),
        TextPosition(anchor_x=0.455, anchor_y=0.055, scale_x=0.23, scale_y=0.09, angle=10.5),
        TextPosition(anchor_x=0.04, anchor_y=0.82, scale_x=0.92, scale_y=0.15),
    ),
    "elmo": (
        TextPosition(anchor_x=0.0, anchor_y=0.24, scale_x=0.3, scale_y=0.25),
        TextPosition(anchor_x=0.35, anchor_y=0.21, scale_x=0.3, scale_y=0.17),
        TextPosition(anchor_x=0.59, anchor_y=0.39, scale_x=0.3, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.69, scale_x=0.3, scale_y=0.25),
        TextPosition(anchor_x=0.59, anchor_y=0.87, scale_x=0.3, scale_y=0.1),
    ),
    "exit": (
        TextPosition(anchor_x=0.24, anchor_y=0.15, scale_x=0.15, scale_y=0.22),
        TextPosition(anchor_x=0.53, anchor_y=0.15, scale_x=0.22, scale_y=0.22),
        TextPosition(anchor_x=0.46, anchor_y=0.85, scale_x=0.32, scale_y=0.1, angle=9.0),
    ),
    "friends": (
        TextPosition(anchor_x=0.25, anchor_y=0.2, scale_x=0.6, scale_y=0.2, angle=-3.0),
        TextPosition(anchor_x=0.05, anchor_y=0.65, scale_x=0.4, scale_y=0.2, angle=5.0),
        TextPosition(anchor_x=0.46, anchor_y=0.69, scale_x=0.45, scale_y=0.2),
    ),
    "gb": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.49, scale_y=0.245),
        TextPosition(anchor_x=0.0, anchor_y=0.255, scale_x=0.49, scale_y=0.246),
        TextPosition(anchor_x=0.0, anchor_y=0.51, scale_x=0.489, scale_y=0.224),
        TextPosition(anchor_x=0.0, anchor_y=0.746, scale_x=0.49, scale_y=0.255),
    ),
    "glasses": (
        TextPosition(anchor_x=0.5, anchor_y=0.0, scale_x=0.5, scale_y=0.49),
        TextPosition(anchor_x=0.5, anchor_y=0.51, scale_x=0.5, scale_y=0.49),
    ),
    "grave": (
        TextPosition(anchor_x=0.14, anchor_y=0.23, scale_x=0.2, scale_y=0.23, angle=4.0),
        TextPosition(anchor_x=0.1, anchor_y=0.75, scale_x=0.4, scale_y=0.2, angle=5.0),
        TextPosition(anchor_x=0.5, anchor_y=0.48, scale_x=0.4, scale_y=0.2, angle=20.0),
    ),
    "gru": (
        TextPosition(anchor_x=0.275, anchor_y=0.2, scale_x=0.2075, scale_y=0.2),
        TextPosition(anchor_x=0.78, anchor_y=0.2, scale_x=0.205, scale_y=0.2),
        TextPosition(anchor_x=0.28, anchor_y=0.7, scale_x=0.205, scale_y=0.2),
        TextPosition(anchor_x=0.78, anchor_y=0.7, scale_x=0.205, scale_y=0.2),
    ),
    "handshake": (
        TextPosition(anchor_x=-0.0275, anchor_y=0.3, scale_x=0.4, scale_y=0.4, angle=-45.0),
        TextPosition(anchor_x=0.4, anchor_y=0.35, scale_x=0.4, scale_y=0.4, angle=27.5),
        TextPosition(anchor_x=0.15, anchor_y=0.1, scale_x=0.5, scale_y=0.2),
    ),
    "headaches": (TextPosition(anchor_x=0.5, anchor_y=0.64, scale_x=0.5, scale_y=0.08),),
    "home": (
        TextPosition(
            anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.1, align="left", angle=0.001
        ),
        TextPosition(anchor_x=0.0, anchor_y=0.1, scale_x=1.0, scale_y=0.1, align="left"),
        TextPosition(anchor_x=0.0, anchor_y=0.2, scale_x=1.0, scale_y=0.1, align="left"),
    ),
    "jim": (
        TextPosition(anchor_x=0.025, anchor_y=0.045, scale_x=0.61, scale_y=0.22, angle=1.0),
        TextPosition(anchor_x=0.02, anchor_y=0.56, scale_x=0.55, scale_y=0.35),
    ),
    "khaby-lame": (
        TextPosition(anchor_x=0.02, anchor_y=0.02, scale_x=0.45, scale_y=0.47),
        TextPosition(anchor_x=0.02, anchor_y=0.51, scale_x=0.45, scale_y=0.47),
    ),
    "kk": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.15),
        TextPosition(anchor_x=0.0, anchor_y=0.85, scale_x=1.0, scale_y=0.15),
    ),
    "kombucha": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.5, scale_y=0.3),
        TextPosition(anchor_x=0.5125, anchor_y=0.0, scale_x=0.4875, scale_y=0.3),
    ),
    "kramer": (
        TextPosition(anchor_x=0.3, anchor_y=0.12, scale_x=0.7, scale_y=0.2),
        TextPosition(anchor_x=0.0, anchor_y=0.8, scale_x=0.6, scale_y=0.2),
    ),
    "made": (
        TextPosition(anchor_x=0.01, anchor_y=0.28, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.74, anchor_y=0.28, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.27, anchor_y=0.04, scale_x=0.15, scale_y=0.1),
        TextPosition(anchor_x=0.525, anchor_y=0.03, scale_x=0.15, scale_y=0.1),
        TextPosition(anchor_x=0.345, anchor_y=0.725, scale_x=0.15, scale_y=0.1),
    ),
    "midwit": (
        TextPosition(anchor_x=0.02, anchor_y=0.46, scale_x=0.283, scale_y=0.1),
        TextPosition(anchor_x=0.13, anchor_y=0.02, scale_x=0.7, scale_y=0.1),
        TextPosition(anchor_x=0.687, anchor_y=0.386, scale_x=0.283, scale_y=0.1),
    ),
    "millers": (
        TextPosition(anchor_x=0.0, anchor_y=0.35, scale_x=0.5, scale_y=0.15),
        TextPosition(anchor_x=0.5, anchor_y=0.35, scale_x=0.5, scale_y=0.15),
        TextPosition(anchor_x=0.0, anchor_y=0.85, scale_x=0.5, scale_y=0.15),
        TextPosition(anchor_x=0.5, anchor_y=0.85, scale_x=0.5, scale_y=0.15),
    ),
    "mouth": (
        TextPosition(anchor_x=0.0, anchor_y=0.15, scale_x=0.4, scale_y=0.2),
        TextPosition(anchor_x=0.6, anchor_y=0.2, scale_x=0.4, scale_y=0.2),
        TextPosition(anchor_x=0.1, anchor_y=0.6, scale_x=0.4, scale_y=0.2),
    ),
    "nails": (
        TextPosition(anchor_x=0.05, anchor_y=0.19, scale_x=0.35, scale_y=0.1, angle=42.0),
        TextPosition(anchor_x=0.4, anchor_y=0.78, scale_x=0.35, scale_y=0.1, angle=-20.0),
        TextPosition(anchor_x=0.51, anchor_y=0.24, scale_x=0.45, scale_y=0.2, angle=-10.0),
    ),
    "noah": (
        TextPosition(anchor_x=0.79, anchor_y=0.3, scale_x=0.2, scale_y=0.1),
        TextPosition(anchor_x=0.68, anchor_y=0.7, scale_x=0.2, scale_y=0.1),
        TextPosition(anchor_x=0.06, anchor_y=0.68, scale_x=0.2, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.9, scale_x=1.0, scale_y=0.1),
    ),
    "ntot": (
        TextPosition(anchor_x=0.055, anchor_y=0.08, scale_x=0.21, scale_y=0.15, angle=12.0),
        TextPosition(anchor_x=0.46, anchor_y=0.15, scale_x=0.18, scale_y=0.15),
        TextPosition(anchor_x=0.7, anchor_y=0.135, scale_x=0.25, scale_y=0.15),
    ),
    "panik-kalm-panik": (
        TextPosition(anchor_x=0.01, anchor_y=0.01, scale_x=0.45, scale_y=0.32),
        TextPosition(anchor_x=0.01, anchor_y=0.35, scale_x=0.45, scale_y=0.32),
        TextPosition(anchor_x=0.01, anchor_y=0.69, scale_x=0.45, scale_y=0.305),
    ),
    "patrick": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.15),
        TextPosition(anchor_x=0.0, anchor_y=0.85, scale_x=1.0, scale_y=0.15),
    ),
    "perfection": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.5, scale_y=0.333),
        TextPosition(anchor_x=0.5, anchor_y=0.225, scale_x=0.5, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.333, scale_x=0.5, scale_y=0.333),
        TextPosition(anchor_x=0.5, anchor_y=0.56, scale_x=0.5, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.666, scale_x=0.5, scale_y=0.333),
        TextPosition(anchor_x=0.5, anchor_y=0.895, scale_x=0.5, scale_y=0.1),
    ),
    "pigeon": (
        TextPosition(anchor_x=0.15, anchor_y=0.0, scale_x=0.35, scale_y=0.2),
        TextPosition(anchor_x=0.71, anchor_y=0.3, scale_x=0.175, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.8, scale_x=1.0, scale_y=0.2),
    ),
    "pooh": (
        TextPosition(anchor_x=0.5, anchor_y=0.0, scale_x=0.5, scale_y=0.5),
        TextPosition(anchor_x=0.5, anchor_y=0.5, scale_x=0.5, scale_y=0.5),
    ),
    "pool": (
        TextPosition(anchor_x=0.33, anchor_y=0.4, scale_x=0.4, scale_y=0.15),
        TextPosition(anchor_x=0.05, anchor_y=0.85, scale_x=0.4, scale_y=0.15),
        TextPosition(anchor_x=0.6, anchor_y=0.65, scale_x=0.4, scale_y=0.15),
    ),
    "prop3": (TextPosition(anchor_x=0.15, anchor_y=0.31, scale_x=0.64, scale_y=0.31, angle=-3.0),),
    "ptj": (
        TextPosition(anchor_x=0.0, anchor_y=0.175, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.5, anchor_y=0.175, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.0, anchor_y=0.425, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.5, anchor_y=0.425, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.0, anchor_y=0.675, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.5, anchor_y=0.675, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.0, anchor_y=0.925, scale_x=0.5, scale_y=0.05),
        TextPosition(anchor_x=0.5, anchor_y=0.925, scale_x=0.5, scale_y=0.05),
    ),
    "reveal": (
        TextPosition(anchor_x=0.04, anchor_y=0.26, scale_x=0.3, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.36, scale_x=1.0, scale_y=0.15),
        TextPosition(anchor_x=0.04, anchor_y=0.8, scale_x=0.3, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.9, scale_x=1.0, scale_y=0.1),
    ),
    "right": (
        TextPosition(anchor_x=0.09, anchor_y=0.01, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.65, anchor_y=0.01, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.399, scale_x=0.499, scale_y=0.1),
        TextPosition(anchor_x=0.502, anchor_y=0.399, scale_x=0.499, scale_y=0.1),
        TextPosition(anchor_x=0.502, anchor_y=0.9, scale_x=0.499, scale_y=0.1),
    ),
    "same": (
        TextPosition(anchor_x=0.06, anchor_y=0.015, scale_x=0.35, scale_y=0.3, angle=-12.0),
        TextPosition(anchor_x=0.525, anchor_y=0.06, scale_x=0.45, scale_y=0.3, angle=-12.0),
        TextPosition(anchor_x=0.45, anchor_y=0.775, scale_x=0.4, scale_y=0.15),
    ),
    "say": (
        TextPosition(anchor_x=0.0, anchor_y=0.33, scale_x=1.0, scale_y=0.17),
        TextPosition(anchor_x=0.0, anchor_y=0.85, scale_x=1.0, scale_y=0.15),
    ),
    "seagull": (
        TextPosition(anchor_x=0.0, anchor_y=0.24, scale_x=0.25, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.75, scale_x=1.0, scale_y=0.25),
    ),
    "slap": (
        TextPosition(anchor_x=0.18, anchor_y=0.13, scale_x=0.35, scale_y=0.3, angle=44.0),
        TextPosition(anchor_x=0.5, anchor_y=0.7, scale_x=0.35, scale_y=0.3),
    ),
    "spiderman": (
        TextPosition(anchor_x=0.05, anchor_y=0.0, scale_x=0.45, scale_y=0.15),
        TextPosition(anchor_x=0.5, anchor_y=0.85, scale_x=0.45, scale_y=0.15),
    ),
    "spirit": (
        TextPosition(anchor_x=0.1, anchor_y=0.28, scale_x=0.35, scale_y=0.16),
        TextPosition(anchor_x=0.1, anchor_y=0.45, scale_x=0.34, scale_y=0.05, align="left"),
        TextPosition(anchor_x=0.1, anchor_y=0.51, scale_x=0.34, scale_y=0.08, align="left"),
        TextPosition(anchor_x=0.1, anchor_y=0.59, scale_x=0.34, scale_y=0.08, align="left"),
        TextPosition(anchor_x=0.1, anchor_y=0.67, scale_x=0.34, scale_y=0.08, align="left"),
    ),
    "stop": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.5, scale_y=0.06),
        TextPosition(anchor_x=0.5, anchor_y=0.0, scale_x=0.5, scale_y=0.075),
        TextPosition(anchor_x=0.18, anchor_y=0.335, scale_x=0.32, scale_y=0.18),
        TextPosition(anchor_x=0.5, anchor_y=0.335, scale_x=0.5, scale_y=0.07),
        TextPosition(anchor_x=0.0, anchor_y=0.67, scale_x=0.5, scale_y=0.075),
        TextPosition(anchor_x=0.5, anchor_y=0.67, scale_x=0.5, scale_y=0.075),
    ),
    "touch": (
        TextPosition(anchor_x=0.0, anchor_y=0.3, scale_x=1.0, scale_y=0.2),
        TextPosition(anchor_x=0.0, anchor_y=0.8, scale_x=1.0, scale_y=0.2),
    ),
    "vince": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.495, scale_y=0.315),
        TextPosition(anchor_x=0.0, anchor_y=0.32, scale_x=0.495, scale_y=0.357),
        TextPosition(anchor_x=0.0, anchor_y=0.68, scale_x=0.495, scale_y=0.32),
    ),
    "wallet": (
        TextPosition(anchor_x=0.0, anchor_y=0.17, scale_x=0.5, scale_y=0.08),
        TextPosition(anchor_x=0.5, anchor_y=0.18, scale_x=0.5, scale_y=0.07),
        TextPosition(anchor_x=0.0, anchor_y=0.4, scale_x=0.5, scale_y=0.1),
        TextPosition(anchor_x=0.5, anchor_y=0.43, scale_x=0.5, scale_y=0.07),
        TextPosition(anchor_x=0.0, anchor_y=0.65, scale_x=0.5, scale_y=0.1),
        TextPosition(anchor_x=0.5, anchor_y=0.67, scale_x=0.5, scale_y=0.08),
        TextPosition(anchor_x=0.0, anchor_y=0.92, scale_x=0.5, scale_y=0.08),
        TextPosition(anchor_x=0.5, anchor_y=0.92, scale_x=0.5, scale_y=0.08),
    ),
    "wddth": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=1.0, scale_y=0.15),
        TextPosition(anchor_x=0.1, anchor_y=0.85, scale_x=0.8, scale_y=0.15),
    ),
    "wishes": (TextPosition(anchor_x=0.0, anchor_y=0.48, scale_x=0.45, scale_y=0.15),),
    "wkh": (
        TextPosition(anchor_x=0.1, anchor_y=0.3, scale_x=0.3, scale_y=0.1),
        TextPosition(anchor_x=0.53, anchor_y=0.35, scale_x=0.3, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.875, scale_x=1.0, scale_y=0.125),
    ),
    "woman-cat": (
        TextPosition(anchor_x=0.0, anchor_y=0.0, scale_x=0.5, scale_y=0.22),
        TextPosition(anchor_x=0.5, anchor_y=0.0, scale_x=0.5, scale_y=0.22),
    ),
    "worst": (
        TextPosition(anchor_x=0.0, anchor_y=0.4, scale_x=1.0, scale_y=0.1),
        TextPosition(anchor_x=0.0, anchor_y=0.9, scale_x=1.0, scale_y=0.1),
    ),
    "zero-wing": (TextPosition(anchor_x=0.025, anchor_y=0.7, scale_x=0.95, scale_y=0.265),),
}
