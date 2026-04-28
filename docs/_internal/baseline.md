# Baseline tooling output

Captured at the start of the comprehensive review (before any changes).
Python: 3.12.2 in `.venv/`.

## ruff check (13 errors)

All 13 issues are unused imports in `tests/`. None in `src/`.

| File | Code | Issue |
|---|---|---|
| `tests/test_rendering.py:8` | F401 | `numpy as np` unused |
| `tests/test_rendering.py:20` | F401 | `DEFAULT_TEXT_POSITIONS` unused |
| `tests/test_template.py:5` | F401 | `json` unused |
| `tests/test_template.py:6` | F401 | `Path` unused |
| ... and ~9 more | F401 | unused test imports |

All `[*] fixable` via `ruff check --fix`.

## black --check (17 files)

```
17 files would be reformatted, 18 files would be left unchanged.
```

Touches: `src/memeplotlib/_rendering.py`, `src/memeplotlib/_template.py`,
`tests/test_meme.py`, `tests/test_text.py`, `tests/test_rendering.py`,
`tests/test_template.py`, `docs/generate_examples.py`, plus 10 others.

## mypy --strict src/memeplotlib (16 errors, 5 files)

Highlights:
- `src/memeplotlib/_rendering.py` — 9 errors (figure / SubFigure narrowing,
  fontsize union types, `add_axes` overload mismatch).
- `src/memeplotlib/_template.py:12,14` — missing `types-requests` stubs.
- `src/memeplotlib/_meme.py` — 3 errors (None template, missing annotations).
- `src/memeplotlib/_cache.py:84` — `Any` return on typed function.
- `src/memeplotlib/__main__.py:117` — bare `dict` generic.

Phase 2 will fix these, with targeted `# type: ignore[code]` comments only
where strict typing genuinely cannot express the matplotlib internals.

## pytest (131 tests, all passing)

```
131 passed in 4.94s
```

No coverage measured at baseline (no `pytest-cov` invocation in CI).

## sphinx-build -W docs (FAILS at baseline)

Two pre-existing problems:

1. **Missing theme dependency**: `pydata-sphinx-theme` is referenced in
   `docs/conf.py:97` but not declared in the `docs` extras of
   `pyproject.toml`. Phase 1 fixes this.
2. **Sphinx-gallery hits the live memegen API** to render every example,
   so a missing template or any network hiccup fails the build. The
   `distracted` template referenced in `examples/plot_*.py` no longer exists
   at api.memegen.link and produces:
   `TemplateNotFoundError: Template 'distracted' not found`.
   Build ends with `8 warnings (with warnings treated as errors)`.

Phase 4 makes the gallery offline-capable (or replaces dead templates).

## numpydoc validate

Not run at baseline; tooling not installed. Phase 2 will run it after
docstring touch-ups.

## Coverage

Not measured at baseline. Phase 3 sets `fail_under = 85`.
