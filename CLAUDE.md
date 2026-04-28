# memeplotlib — guidance for Claude Code sessions

Read this before making non-trivial changes. The full conventions are in
[docs/conventions.rst](docs/conventions.rst); this file is the operational
distillation.

## Project layout

`memeplotlib` is a small library that renders image-macro memes via
`matplotlib` and the [memegen](https://api.memegen.link) API. Public API is
re-exported from `memeplotlib/__init__.py`. The source lives under
`src/memeplotlib/`.

| Module | Role |
|---|---|
| `_api.py` | Functional API: `meme()`, `memify()`. |
| `_meme.py` | OO API: `Meme` builder with chainable `top/bottom/text` and a `render/show/save` cycle. |
| `_template.py` | `Template`, `TemplateRegistry`, memegen client (retry-aware via `requests.Session` + `urllib3.Retry`). |
| `_rendering.py` | matplotlib-side rendering: bundled font registration, text fitting, outline drawing, `render_meme`, `render_memify`. |
| `_text.py` | Text styling helpers (`upper`/`lower`/`none`) and memegen URL encoding. |
| `_config.py` | RcParams-style `MemeplotlibConfig` mapping + `rc_context` context manager. |
| `_cache.py` | Two-level cache: in-memory LRU + disk cache via `platformdirs`. |
| `__main__.py` | Argparse CLI: `memeplotlib {list,search,info,create}`. |
| `_mcp.py` | (Phase 8) MCP server using the official `mcp` SDK. |
| `fonts/Anton-Regular.ttf` | Bundled SIL OFL display font, registered at import time. |

## API contract — match this for new code

- **`ax=None` pattern.** Public rendering functions accept `ax: Axes | None = None` and create a new figure/axes when `None`. Mirrors `seaborn` and `pandas.plot`.
- **Return `(Figure, Axes)`** (or just `Axes` for single-axes helpers). Do **not** call `plt.show()` implicitly. `meme()` and `memify()` default to `show=False`.
- **Forward `**kwargs` to `Axes.text`** for caption rendering. User values override the meme-specific defaults.
- **`Meme` class is chainable** — `top/bottom/text` return `self`. Don't break this.
- **`config` is a `MutableMapping`**, not an attribute namespace. Use `config["font"] = ...`, never `config.font = ...`. For scoped overrides, use `with rc_context({"font": "comic"}):`.
- **`config` keys are validated**: setting an unknown key raises `KeyError`; setting a wrong-typed value raises `ValueError`. The set of keys is fixed in `_config._VALIDATORS`.
- **NumPy-format docstrings** for every public function and method. Sections in this order: Parameters, Returns, Raises, Notes, Examples. Same-line summaries (`"""Do X."""\n\nLong body...`) are the matplotlib convention and are excluded from `numpydoc validate` (GL01).
- **Type hints on every public signature**, `mypy --strict src/memeplotlib` clean. Use `# type: ignore[code]` only for matplotlib internals that strict typing genuinely cannot express, with a one-line comment explaining why.

## Test conventions

- Tests live in `tests/`, mirroring `src/memeplotlib/` modules.
- All network is mocked. The autouse `_block_real_network` fixture in
  `tests/conftest.py` disables real TCP socket creation. Tests that
  legitimately need a TCP listener (pytest-httpserver) opt out via
  `@pytest.mark.allow_network`.
- HTTP responses are mocked with `responses`. For retry / timeout
  behavior `responses` cannot model, use `pytest-httpserver`.
- Image-comparison tests use `pytest-mpl` with baselines under
  `tests/baseline/`. Regenerate with
  `pytest --mpl-generate-path=tests/baseline`.
- Coverage gate: `fail_under = 85` (currently ~94%).

## Definitions of done

**Adding a new public function** — needs all of: numpy-format docstring;
`ax=None` if it draws; type hints; tests in the matching `tests/test_*.py`
including a `**kwargs` forward test if applicable; entry in `docs/api.rst`;
addition to `__init__.__all__` and re-export.

**Changing the rendering pipeline** — regenerate `tests/baseline/` with
`pytest --mpl-generate-path=tests/baseline` and visually inspect the diffs
before committing. If a baseline change is intentional, mention it in the
commit body.

**Bumping a runtime dependency** — update `pyproject.toml` and the conda
recipe at `conda-recipe/meta.yaml`. If it's matplotlib, also update
`packaging/conda-forge/meta.yaml` (uses `matplotlib-base`, not
`matplotlib`).

**Cutting a release** — bump `pyproject.toml::project.version` and
`src/memeplotlib/__init__.py::__version__` together (they must match).
Add a CHANGELOG entry. Open a PR to `main`. After merge, the release
workflow takes over via OIDC trusted publishing — no API token in
repo secrets. Stop and ask before publishing to PyPI.

## Commands

```bash
# Install
pip install -e ".[dev,docs,mcp]"

# Quality gates
ruff check .
black --check .
mypy --strict src/memeplotlib

# Tests (with image comparison and coverage)
pytest --cov --mpl

# Regenerate image baselines
pytest --mpl-generate-path=tests/baseline

# Docs (warnings as errors)
sphinx-build -W docs docs/_build

# numpydoc validation (uses [tool.numpydoc_validation] from pyproject.toml)
python -c "from numpydoc.validate import validate; \
           [print(n, validate(n)['errors']) for n in [...]]"

# Build & inspect wheel
python -m build && unzip -l dist/*.whl | grep -E "Anton|LICENSE"

# CLI
memeplotlib list
memeplotlib meme buzz "hello" "world" --out /tmp/hello.png

# MCP server (after Phase 8)
memeplotlib-mcp   # reads JSON-RPC on stdin
```

## Things that bit us

- **macOS APFS is case-insensitive** by default. `Meme` (class) and
  `meme` (function) collide as autosummary stub filenames. Use direct
  `.. autoclass::` / `.. autofunction::` blocks in `docs/api.rst`
  instead of `.. autosummary:: :toctree: generated`.
- **Sphinx-gallery hits the live memegen API** when building docs. We
  set `suppress_warnings = ["sphinx_gallery"]` in `docs/conf.py` so
  transient network blips don't fail `-W` builds.
- **`pydata-sphinx-theme`** must be in the `docs` extras of
  `pyproject.toml`. It's referenced from `docs/conf.py::html_theme` and
  `sphinx-build` will hard-fail without it.
- **Hatch's default file-include misses `src/memeplotlib/fonts/*.ttf`**
  in some configurations — we set
  `[tool.hatch.build.targets.wheel.force-include]` explicitly to
  guarantee the bundled Anton font ships in the wheel.
- **`responses` doesn't model timeout / connection errors** — use
  `pytest-httpserver` for retry-and-timeout tests, opt out of the global
  socket block with `@pytest.mark.allow_network`.
- **`cache_enabled = True` in tests will read from the user's real
  cache directory.** Tests touching the registry should
  `monkeypatch.setitem(config, "cache_enabled", False)` and supply a
  `tmp_path` cache dir.

## Branching / PRs

- Feature branches: `feat/<short-name>`.
- Bugfix branches: `fix/<short-name>`.
- This refactor branch: `chore/comprehensive-review` (or whatever name
  the worktree was created with).
- Open one PR per logical change. The CI matrix on `ci.yml` runs across
  Python 3.10–3.13 × ubuntu/macos/windows. Wait for green before merge.
- Release-drafter (if configured) auto-builds the changelog from PR
  labels: `breaking`, `feature`, `fix`, `docs`, `internal`.
