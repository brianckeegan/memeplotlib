# Contributing to memeplotlib

Thanks for your interest in contributing to memeplotlib!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/brianckeegan/memeplotlib.git
   cd memeplotlib
   ```

2. Install in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the tests:
   ```bash
   pytest
   ```

## Code Style

- **Type hints**: Use type annotations on all public functions (PEP 604 union syntax `X | Y`).
- **Docstrings**: NumPy-style docstrings on all public classes and functions.
- **Imports**: Always include `from __future__ import annotations` at the top of each module.
- **Linting**: We use [ruff](https://docs.astral.sh/ruff/) with a line length of 99. Run `ruff check .` before submitting.
- **Naming**: Private modules use a leading underscore (e.g., `_api.py`). Public API is re-exported from `__init__.py`.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=memeplotlib

# Skip slow (network) tests
pytest -m "not slow"
```

## Pull Request Process

1. Create a feature branch from `main`.
2. Make your changes with clear, descriptive commits.
3. Add or update tests for any new or changed functionality.
4. Ensure `pytest` and `ruff check .` pass.
5. Open a PR with a description of what changed and why.

## Adding New Templates

memeplotlib discovers templates dynamically from the [memegen API](https://api.memegen.link).
To add custom default text positions for a specific template, modify the
`_from_api_data` method in `src/memeplotlib/_template.py`.
