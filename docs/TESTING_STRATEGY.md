# VAS Testing Strategy

## Incremental Testing Approach

We use an **incremental testing strategy** where tests are organized by development phases. This ensures:

1. **No regression** - Each phase's tests remain valid
2. **Quick verification** - Can test individual phases
3. **Clear progress** - Know exactly what's working
4. **Safe development** - Don't break existing functionality

## Test Organization

```
tests/
├── test_phase1_foundation.py    ✅ Phase 1 Complete
├── test_phase2_apis.py          🔜 Phase 2 Next
├── test_phase3_mediasoup.py     🔜 Phase 3 Future
├── test_phase4_rtsp.py          🔜 Phase 4 Future
├── test_phase5_recording.py     🔜 Phase 5 Future
└── test_incremental.py          📊 Progress Tracker
```

## Phase-by-Phase Testing

### Phase 1: Foundation ✅
**Tests: 12**  
**Status: COMPLETE**

- Application startup
- Health check endpoint
- Database models
- Configuration
- Logging

**Run tests:**
```bash
pytest -m phase1 -v
```

### Phase 2: Core APIs 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- Device CRUD operations
- Stream management
- Error handling
- Validation

**Run tests:**
```bash
pytest -m phase2 -v
```

### Phase 3: MediaSoup 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- Router management
- WebRTC transport
- Producer/Consumer handling

**Run tests:**
```bash
pytest -m phase3 -v
```

### Phase 4: RTSP Pipeline 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- RTSP ingestion
- Stream health monitoring
- Auto-reconnection

**Run tests:**
```bash
pytest -m phase4 -v
```

### Phase 5: Recording 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- HLS generation
- Segment management
- Storage abstraction

**Run tests:**
```bash
pytest -m phase5 -v
```

### Phase 6: WebSocket 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- Signaling protocol
- Connection management
- ICE handling

**Run tests:**
```bash
pytest -m phase6 -v
```

### Phase 7: Frontend 🔜
**Tests: Will be implemented**  
**Status: PENDING**

- UI components
- Integration tests
- E2E flows

**Run tests:**
```bash
pytest -m phase7 -v
```

## Test Execution

### Development Workflow

```bash
# After each phase completion, run tests
pytest tests/ -v

# Or run specific phase
pytest -m phase1 -v

# Or run all tests up to current phase
pytest -m "phase1 or phase2" -v
```

### Before Committing

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest --cov=app tests/

# Verify no regressions
pytest -m "phase1" -v
```

## Test Types

### Unit Tests
- Test individual functions
- Mock external dependencies
- Fast execution

### Integration Tests
- Test component interactions
- Use test database
- Real dependencies

### API Tests
- Test HTTP endpoints
- Use TestClient
- Verify responses

### E2E Tests
- Test complete workflows
- Multiple services
- Production-like setup

## Coverage Goals

- **Phase 1**: 100% of foundation code ✅
- **Phase 2**: 90%+ of API code
- **Phase 3**: 85%+ of MediaSoup code
- **Overall**: 80%+ code coverage

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

CI pipeline:
1. Run all tests
2. Check coverage
3. Run linters
4. Build Docker images
5. Deploy if green

## Best Practices

1. **Write tests before implementation** (TDD approach)
2. **Run tests frequently** during development
3. **Fix failing tests immediately**
4. **Keep tests independent** - no test dependencies
5. **Use descriptive names** - `test_phase1_health_check`
6. **Mock external services** - don't hit real APIs
7. **Clean up after tests** - reset database state

## Test Data Management

- Use fixtures for reusable test data
- Clean database before each test
- Use UUIDs for unique identifiers
- Mock time-dependent operations

## Incremental Verification

After completing each phase:

1. **Run phase tests**: `pytest -m phase{N} -v`
2. **Verify all pass**: Should see 100% pass rate
3. **Check coverage**: `pytest --cov=app tests/`
4. **Document results**: Update test documentation
5. **Proceed to next phase**: Only if tests pass

## Monitoring Test Health

```bash
# Run all tests with verbose output
pytest tests/ -vv

# Run with timing
pytest --durations=10

# Run with coverage
pytest --cov=app --cov-report=html

# View slowest tests
pytest --durations=0
```

## Next: Phase 2 Testing

When Phase 2 is implemented, we'll add tests for:
- POST /api/v1/devices
- GET /api/v1/devices
- DELETE /api/v1/devices/{id}
- POST /api/v1/streams/{id}/start
- POST /api/v1/streams/{id}/stop

These tests will be added to `test_phase2_apis.py`.


