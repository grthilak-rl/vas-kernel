# VAS Backend Testing Guide

## Overview

This project uses an **incremental testing approach** where tests are organized by phase. Each phase has its own test file that verifies the functionality added in that phase.

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_phase1_foundation.py  # Phase 1 tests ✅
├── test_phase2_apis.py      # Phase 2 tests (placeholder)
├── test_incremental.py     # Phase tracking
└── utils.py                 # Test utilities and helpers
```

## Running Tests

### Quick Start

```bash
cd backend

# Run all tests
pytest

# OR use the test runner
./run_tests.sh

# Run specific phase
./run_tests.sh phase1
```

### Phase 1 Tests (Current)

```bash
# Run Phase 1 tests only
pytest tests/test_phase1_foundation.py -v

# OR
pytest -m phase1 -v

# OR use script
./run_tests.sh phase1
```

### What Phase 1 Tests Cover

✅ Application startup  
✅ Health check endpoint (`/health`)  
✅ Root endpoint (`/`)  
✅ API documentation accessibility (`/docs`)  
✅ OpenAPI schema (`/openapi.json`)  
✅ CORS headers  
✅ 404 error handling  
✅ Database models exist  
✅ Configuration loaded  
✅ Database connection  

## Test Markers

Tests are marked by phase to allow incremental testing:

```bash
# Run only Phase 1 tests
pytest -m phase1

# Run only Phase 2 tests
pytest -m phase2

# Run all implemented tests
pytest -m "phase1 or phase2"
```

## Incremental Testing Strategy

### Phase 1 ✅ Foundation & Infrastructure
- Application structure
- Database models
- Configuration
- Basic endpoints

### Phase 2 (Next)
- Device CRUD APIs
- Stream management APIs
- Error handling
- Validation

### Phase 3 (Future)
- MediaSoup Worker integration
- Router management
- Transport handling

### Phase 4 (Future)
- RTSP Pipeline
- Stream health monitoring
- Auto-reconnection

### Phase 5 (Future)
- Recording service
- HLS generation
- Storage abstraction

### Phase 6 (Future)
- WebSocket signaling
- WebRTC negotiation
- Connection management

### Phase 7 (Future)
- Frontend integration
- E2E testing

## Test Fixtures

Available fixtures in `conftest.py`:

- `client` - TestClient for FastAPI requests
- `test_db` - Async database session
- `test_engine` - Database engine
- `test_device_data()` - Sample device data
- `test_stream_data()` - Sample stream data

## Example Test

```python
def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

## Adding New Tests

When adding tests for a new phase:

1. Create a test file: `test_phase{N}_{feature}.py`
2. Use the phase marker: `@pytest.mark.phase{N}`
3. Use fixtures from `conftest.py`
4. Follow the naming convention: `test_{feature}_{action}`

## Continuous Integration

Tests can be integrated into CI/CD:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pytest tests/ -v --cov=app --cov-report=xml
```

## Coverage Reports

Generate coverage reports:

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

### Database Errors

Tests use a separate test database. Make sure test database exists:

```bash
# Test database will be created automatically
pytest -v
```

### Async Test Issues

All async tests use `pytest-asyncio`. Make sure it's installed:

```bash
pip install pytest-asyncio
```

## Next Steps

After completing Phase 1, tests for Phase 2 will be uncommented and implemented.

To run only Phase 1 tests to verify setup:

```bash
pytest tests/test_phase1_foundation.py -v
```

Expected output:
```
tests/test_phase1_foundation.py::TestPhase1Foundation::test_health_endpoint PASSED
tests/test_phase1_foundation.py::TestPhase1Foundation::test_root_endpoint PASSED
...
================================ 12 passed in X.XXs ================================
```


