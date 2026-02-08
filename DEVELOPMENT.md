# Development Guide

## Setup Development Environment

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov --cov-report=term-missing
```

Run specific test file:
```bash
pytest tests/test_switch.py
```

## Code Quality

### Linting

Check for linting issues:
```bash
ruff check custom_components/unifiprotect_2way_audio tests
```

Auto-fix linting issues:
```bash
ruff check --fix custom_components/unifiprotect_2way_audio tests
```

### Formatting

Check formatting:
```bash
ruff format --check custom_components/unifiprotect_2way_audio tests
```

Auto-format code:
```bash
ruff format custom_components/unifiprotect_2way_audio tests
```

### Type Checking

Run type checking:
```bash
mypy custom_components/unifiprotect_2way_audio
```

## Running All Checks

To run all quality checks at once:
```bash
ruff check custom_components/unifiprotect_2way_audio tests && \
ruff format --check custom_components/unifiprotect_2way_audio tests && \
mypy custom_components/unifiprotect_2way_audio && \
pytest
```

## CI Workflows

The repository includes a comprehensive CI workflow (`.github/workflows/ci.yml`) that runs:

1. **Linting**: Checks code with ruff
2. **Formatting**: Ensures consistent code style
3. **Type Checking**: Validates type annotations with mypy
4. **Tests**: Runs pytest test suite with coverage
5. **Validation**: Validates manifest.json and Python syntax

All checks must pass before merging PRs.

## Project Structure

```
custom_components/unifiprotect_2way_audio/
├── __init__.py           # Integration setup
├── config_flow.py        # Configuration flow
├── const.py              # Constants
├── frontend.py           # Frontend utilities
├── manager.py            # Stream config manager
├── switch.py             # Switch platform (talkback control)
└── websocket_api.py      # WebSocket API handlers

tests/
├── conftest.py           # Pytest fixtures
├── test_config_flow.py   # Config flow tests
├── test_const.py         # Constants tests
├── test_init.py          # Integration tests
└── test_switch.py        # Switch platform tests
```

## Code Coverage

Current code coverage: ~27%

The test suite focuses on:
- Integration setup and teardown
- Config flow behavior
- Switch entity properties
- Constant definitions

Future improvements could include:
- Integration tests for WebSocket API
- Tests for audio streaming functionality
- Tests for frontend utilities
- More comprehensive switch behavior tests
