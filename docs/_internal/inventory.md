# memeplotlib module inventory

Snapshot of `src/memeplotlib/` at the start of the comprehensive review.

| Module | LOC | Role |
|---|---:|---|
| `__init__.py` | 29 | Package surface — re-exports `meme`, `memify`, `Meme`, `Template`, `TemplateRegistry`, `config`, `__version__`. |
| `__main__.py` | 129 | CLI: `memeplotlib {list,search,info,create}` subcommands via argparse. |
| `_api.py` | 200 | Functional API. `meme(template, *lines, …)` and `memify(fig, *lines, …)`. Both currently default to `show=True`. |
| `_meme.py` | 219 | Object-oriented API. `Meme` class with chainable `.top()`, `.bottom()`, `.text()`, `.render(ax=…)`, `.show()`, `.save()`. |
| `_template.py` | 473 | Template system: `TextPosition`, `Template`, `TemplateRegistry`, `_resolve_template()`, memegen client with retry. |
| `_rendering.py` | 538 | Matplotlib rendering: bundled font registration, text fitting, outline draw, `render_meme`, `render_memify`. |
| `_text.py` | 182 | memegen URL text encoding/decoding, style transforms (`upper`/`lower`/`none`). |
| `_config.py` | 75 | Global defaults — `MemeplotlibConfig` dataclass + `config` singleton. (Phase 2: rewritten as `MutableMapping`.) |
| `_cache.py` | 179 | Two-level template cache: in-memory LRU + disk via `platformdirs.user_cache_dir`. |
| `fonts/Anton-Regular.ttf` | — | Bundled SIL OFL-licensed display font, registered at import time. |

Total: ~2024 lines of Python source across 9 modules.

## Public API surface

```python
from memeplotlib import (
    meme, memify, Meme, Template, TemplateRegistry, config, __version__,
)
```

After Phase 2, also: `rc_context`.

## Tests (pre-Phase 3)

| File | LOC | Covers |
|---|---:|---|
| `tests/conftest.py` | — | Shared fixtures (`sample_image`, `sample_image_file`, `sample_template`); autouse `_close_figures()`. |
| `tests/test_api.py` | — | `meme()` and `memify()` happy/edge paths. |
| `tests/test_meme.py` | — | `Meme` class chain, render/show/save. |
| `tests/test_template.py` | — | `responses`-mocked memegen client. |
| `tests/test_template_resolution.py` | — | Template ID dispatch (memegen ID vs path vs URL). |
| `tests/test_rendering.py` | — | Font registration, text fitting, wrapping. |
| `tests/test_text.py` | — | URL encoding, style transforms. |
| `tests/test_cache.py` | — | Disk and in-memory cache behavior. |
| `tests/test_integration.py` | — | End-to-end functional pathways. |

131 tests total, all passing at baseline. Network mocked via `responses`.

## CI workflows (pre-Phase 6)

| Workflow | Trigger | Matrix | Purpose |
|---|---|---|---|
| `docs.yml` | release, dispatch | py3.10 ubuntu | Build Sphinx → deploy GitHub Pages (OIDC) |
| `publish_pypi.yml` | release, dispatch | py3.10 ubuntu | `python -m build` → twine check → PyPI (OIDC trusted publisher) |
| `publish_conda.yml` | release, dispatch | py3.10 ubuntu | conda build → upload to user channel via `ANACONDA_API_TOKEN` |
| `regenerate-examples.yml` | release, dispatch | py3.10 ubuntu | Re-run `docs/generate_examples.py`, commit images back to `main` |

No test/lint CI exists at baseline. Phase 6 adds `ci.yml` with a matrix on
Python {3.10, 3.11, 3.12, 3.13} × OS {ubuntu, macos, windows}.
