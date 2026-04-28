# Changelog

All notable changes to memeplotlib are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] — 2026-04-28

This release rewires the rendering pipeline around the memegen API. By
default, memes are now composed **server-side** by memegen and fetched as a
finished image; a new client-side **Pillow** backend handles custom local
images and any feature the API can't express (per-line `fontsize`, custom
outlines, ``**text_kwargs``, per-line overrides). The legacy
matplotlib-text rendering is preserved as `backend="matplotlib"` for
explicit opt-in.

### Breaking

- **Default rendering pipeline changed.** `meme()` calls now hit
  `https://api.memegen.link/images/<id>/<line_1>/.../<line_n>.<ext>?...`
  and `imshow` the response — output appearance, fonts, and stroke shape
  may differ from v0.2 / v0.4 baselines. To preserve exact previous
  behaviour, pass `backend="matplotlib"` or set
  `config["backend"] = "matplotlib"`.
- **memegen never honours custom outlines or per-line `fontsize`.** Under
  `backend="auto"`, passing `outline_color`, `outline_width`, `fontsize`,
  any `**text_kwargs`, or per-line overrides routes to the Pillow
  backend automatically. Under `backend="memegen"` they are silently
  ignored.
- **Image baselines under `tests/baseline/` were regenerated.** Local
  forks pinning the old baselines should regenerate after upgrading.

### Added

- **memegen URL builder.** New public function
  `memeplotlib.build_memegen_url(template_id, lines, *, api_base, ...)` —
  see [docs/url_construction.rst](docs/url_construction.rst) for the full
  grammar (escape table, query parameters, font / style / overlay
  reference). Adapted from
  [jacebrowning/memegen#993](https://github.com/jacebrowning/memegen/issues/993).
- **`backend` parameter** on `meme()` and `Meme`. Values: `"auto"`
  (default), `"memegen"`, `"pillow"`, `"matplotlib"`. Also a
  `Meme.with_backend(...)` chainable setter.
- **memegen knobs on `meme()`**: `template_style`, `extension`, `width`,
  `height`, `layout`, `background`, `overlays`. Mirrors of the same
  query parameters memegen accepts.
- **Per-line overrides** via `Meme.line(index, text, *, fontsize=None,
  color=None, font=None, position=None)`. Using any override forces the
  Pillow backend.
- **Pillow backend** (`memeplotlib._pillow.render_pillow`) with
  TTF resolution from the bundled Anton font and standard system font
  paths, multiline shrink-to-fit via `ImageDraw.textbbox`, and
  stroke-aware caption drawing.
- **Template metadata fields**: `lines_count`, `overlays_count`,
  `styles`, `is_memegen`. The CLI `info` subcommand now surfaces all
  three.
- **CLI flags**: `--backend`, `--ext`, `--width`, `--height`, `--layout`,
  `--background`, `--template-style` on the `meme` / `create`
  subcommand.
- **MCP `meme` tool** accepts `backend`, `extension`, `width`, `height`,
  `template_style`, `font`, `color`, `fontsize`.
- **Config keys**: `backend`, `extension`, `width`, `height`, `layout`,
  `background`. Validated by `_VALIDATORS` like every existing key.
- **`OverlaySpec` `TypedDict`** for ad-hoc overlay placements
  (`{style, center, scale}`).
- **`memegen_rendered_pattern(template_id)` test helper** in
  `tests/conftest.py` for regex-mocking the dynamic rendered URLs.
- **`uses_default_backend` pytest marker** for tests that opt out of
  the legacy-matplotlib autouse fixture.

### Fixed

- **`Template.get_image()` now respects `config["cache_enabled"]`.**
  Previously it always consulted the cache instance regardless of the
  setting — tests that disabled caching via config could still read
  stale data from the user's real cache directory.

### Migration

```python
# Before (v0.4): matplotlib drew the captions client-side.
memes.meme("buzz", "memes", "memes everywhere")

# After (v0.5): memegen renders server-side by default.
# Pin the old behaviour with backend="matplotlib":
memes.meme("buzz", "memes", "memes everywhere", backend="matplotlib")

# Or globally:
memes.config["backend"] = "matplotlib"

# Existing fontsize / outline knobs still work — under backend="auto",
# they transparently route through the Pillow backend instead:
memes.meme("buzz", "hello", fontsize=48, outline_color="red")
```

## [0.2.0] — 2026-04-28

This release modernizes the public API to match scientific-Python
conventions, ships an MCP server for agent harnesses, and adds a real CI
matrix. **Two intentional breaking changes — see Migration below.**

### Breaking

- **`meme()` and `memify()` no longer call `plt.show()` by default.** The
  default for `show=` is now `False`, matching the matplotlib idiom of
  returning the Axes for further customization. Users who relied on
  auto-display can pass `show=True` explicitly.
- **`config` is now a `MutableMapping`, not a dataclass with attributes.**
  Replace `config.font = "comic"` with `config["font"] = "comic"`. Setting
  unknown keys raises `KeyError`; setting wrong-typed values raises
  `ValueError`. The set of valid keys is fixed in
  `MemeplotlibConfig.VALID_KEYS`.
- **`matplotlib >= 3.8`** is now required (was `>= 3.0`). 3.8 is the
  earliest version that exposes `matplotlib.typing` for type-hint use in
  the public API.

### Added

- **`memeplotlib.rc_context`** — a context manager mirroring
  `matplotlib.rc_context` for scoped overrides:
  ```python
  with memes.rc_context({"font": "comic", "color": "yellow"}):
      memes.meme("buzz", "scoped style")
  ```
- **`**kwargs` forwarding** — `meme()`, `memify()`, `render_meme()`, and
  `render_memify()` all forward extra keyword arguments to `Axes.text` for
  each rendered caption (e.g. `alpha`, `rotation`, `zorder`).
- **CLI `meme` subcommand**:
  ```bash
  memeplotlib meme buzz "hello" "world" --out hello.png
  ```
  The previous `create` subcommand stays as a backward-compatible alias.
- **CLI `--version` flag**.
- **CLI `--color`, `--fontsize`, `--dpi` options** on the meme/create
  subcommand.
- **MCP server** (`memeplotlib-mcp` console script, optional `[mcp]`
  extra). Exposes three tools — `meme`, `search_templates`,
  `list_templates` — over the [Model Context Protocol] for use from
  Claude Desktop, Claude Code, and any MCP-compatible client.
- **Conventions page** in the docs (`docs/conventions.rst`) documenting
  the matplotlib-style API contract for future contributors.
- **`CLAUDE.md`** at the repo root with operational guidance for future
  Claude Code sessions, plus an `AGENTS.md` symlink.
- **`pytest-mpl` image-comparison tests** with baselines under
  `tests/baseline/` for the public render APIs.
- **Offline test guarantee** — autouse `_block_real_network` fixture
  blocks raw socket creation; tests that need real TCP (httpserver) opt
  out via `@pytest.mark.allow_network`.
- **Network resilience tests** using `pytest-httpserver` to verify retry
  behavior on 503s and timeout enforcement.
- **CI matrix** (`.github/workflows/ci.yml`): Python {3.10, 3.11, 3.12,
  3.13} × OS {ubuntu, macos, windows}. Lint/format/type-check/test/docs
  on every PR.
- **Release-drafter** workflow (`.github/workflows/release-drafter.yml`)
  for auto-generated release notes from PR labels.
- **Dependabot config** (`.github/dependabot.yml`) — weekly grouped
  pip + GitHub Actions updates.
- **conda-forge recipe draft** at `packaging/conda-forge/meta.yaml` ready
  for submission to `conda-forge/staged-recipes` after the v0.2.0 PyPI
  release lands.

### Changed

- **Sphinx docs** now use `numpydoc` (replacing `napoleon` and
  `sphinx-autodoc-typehints`). Type information is rendered from the
  docstring itself.
- **`docs.yml`** workflow now triggers on push to `main` (was: release
  only) and runs `sphinx-build -W` so warnings are fatal.
- **`docs/api.rst`** rewritten to use direct `.. autoclass::` /
  `.. autofunction::` blocks instead of `autosummary`-with-toctree —
  works around a case-insensitive-filesystem collision between the
  `meme` function and `Meme` class.
- **README** rewritten with CI/codecov/docs badges, rendered example
  images per feature, a new "Use from agents" section, and a "Related
  projects" section.
- **`Template` dataclass** — `_image_array` is now initialized in
  `__post_init__` rather than as a `field(...)`, so `numpydoc validate`
  doesn't flag it as an undocumented public parameter.

### Fixed

- **Wheel ships the bundled Anton font** reliably via an explicit
  `[tool.hatch.build.targets.wheel.force-include]` block.
- **`pydata-sphinx-theme` was missing from docs extras** — referenced in
  `docs/conf.py` but not declared. Now in `[project.optional-dependencies]
  docs`. Stale `html_logo` filename also fixed.
- **mypy `--strict` clean** on `src/memeplotlib`. The 16 baseline errors
  are gone; only two narrow `# type: ignore[code]` comments remain for
  matplotlib internals that strict typing cannot express.
- **`numpydoc validate` clean** across the public API (excluding GL01
  same-line summaries — matplotlib's convention — and EX01/SA01/ES01).
- **Replaced legacy `np.random.randint`** with `np.random.default_rng` in
  test fixtures (NPY002).

### Internal

- New tooling configuration in `pyproject.toml`: `[tool.black]`,
  `[tool.mypy]` (strict), `[tool.coverage.run]`, `[tool.coverage.report]`
  (`fail_under = 85`), `[tool.numpydoc_validation]`, expanded
  `[tool.ruff.lint]` (E, W, F, I, N, UP, B, SIM, NPY).
- Test coverage rose from 75% to ~94%.
- Test count rose from 131 to 193.
- New baseline / inventory snapshots under `docs/_internal/` (excluded
  from sphinx build).

### Migration guide (0.1.0 → 0.2.0)

```python
# Before (0.1.0)
import memeplotlib as memes

memes.config.font = "comic"           # attribute access
memes.config.color = "yellow"
memes.meme("buzz", "memes", "memes everywhere")  # auto-displayed

# After (0.2.0)
import memeplotlib as memes

memes.config["font"] = "comic"        # mapping access
memes.config["color"] = "yellow"
fig, ax = memes.meme("buzz", "memes", "memes everywhere")  # returned, not shown

# Or use rc_context for scoped overrides:
with memes.rc_context({"font": "comic", "color": "yellow"}):
    fig, ax = memes.meme("buzz", "scoped style")
```

To restore the previous auto-display behavior at any single call site:

```python
memes.meme("buzz", "memes", show=True)
```

[Model Context Protocol]: https://modelcontextprotocol.io
