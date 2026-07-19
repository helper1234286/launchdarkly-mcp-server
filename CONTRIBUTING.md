# Contributing

## Setup

```bash
git clone https://github.com/your-org/launchdarkly-mcp-server
cd launchdarkly-mcp-server
uv venv
uv pip install -e ".[dev]"
```

## Tests

```bash
uv run pytest
```

Add tests in `tests/` using `pytest` and `respx` for HTTP mocking.

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Add tests for any new functionality
4. Ensure all tests pass
5. Open a PR with a clear description

## Release

```bash
uv build
uv publish
```
