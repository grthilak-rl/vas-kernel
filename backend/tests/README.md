# VAS Backend Tests

Incremental test suite organized by development phases.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run Phase 1 tests only
pytest -m phase1 -v
```

## Test Files

- `conftest.py` - Pytest fixtures and configuration
- `test_phase1_foundation.py` - Phase 1 foundation tests ✅
- `test_phase2_apis.py` - Phase 2 API tests (placeholder)
- `test_incremental.py` - Phase tracking and verification
- `utils.py` - Test utilities and helpers

## Available Markers

```bash
# Run by phase
pytest -m phase1  # Phase 1 tests
pytest -m phase2  # Phase 2 tests
pytest -m phase3  # Phase 3 tests

# Run multiple phases
pytest -m "phase1 or phase2"

# Run all implemented
pytest -m "phase1"
```

## Test Structure

Each phase has its own test file that validates:
- ✅ Phase 1: Foundation (12 tests)
- ⏳ Phase 2: APIs (0 tests - not yet implemented)
- ⏳ Phase 3: MediaSoup (0 tests - not yet implemented)

## Adding Tests

When adding tests for Phase 2:

1. Open `test_phase2_apis.py`
2. Remove `@pytest.mark.skip` from tests
3. Implement test logic
4. Run: `pytest -m phase2 -v`

## Fixtures

Available fixtures in `conftest.py`:

- `client` - FastAPI TestClient
- `test_db` - Async database session
- `test_engine` - Database engine
- `test_device_data()` - Sample device data
- `test_stream_data()` - Sample stream data

## Running Tests

```bash
# Basic
pytest

# Verbose
pytest -v

# Specific file
pytest tests/test_phase1_foundation.py

# Specific test
pytest tests/test_phase1_foundation.py::TestPhase1Foundation::test_health_endpoint

# With coverage
pytest --cov=app --cov-report=html
```

## Current Status

**Phase 1**: ✅ 12/12 tests passing  
**Phase 2**: ⏳ 0/5 tests (placeholder)  
**Overall**: ✅ 12/12 tests implemented

## Next Steps

After Phase 2 implementation:
1. Implement tests in `test_phase2_apis.py`
2. Run: `pytest -m phase2 -v`
3. Verify all pass before Phase 3


