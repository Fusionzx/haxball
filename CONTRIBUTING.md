# Contributing

Contributions are welcome. Keep pull requests focused and explain the behavior
being changed.

## Development Setup

```bash
git clone https://github.com/Fusionzx/haxball-python
cd haxball-python
pip install -e ".[dev]"
playwright install chromium
```

## Checks

Run these before opening a pull request:

```bash
ruff check .
pytest -m "not slow"
```

Tests marked `slow` require external HaxBall access and may require a
`HAXBALL_TOKEN`.

## Pull Requests

- Add or update tests for behavioral changes.
- Update the README when the public API changes.
- Do not commit tokens, private data, generated build artifacts, or local
  environment files.
