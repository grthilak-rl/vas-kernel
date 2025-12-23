# VAS Backend

FastAPI-based backend for the Video Aggregation Service.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Start Database
```bash
# Using Docker Compose
docker-compose up db redis -d
```

### 4. Run Migrations
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 5. Start Backend
```bash
python main.py
# OR
make dev
```

## Testing

### Quick Test
```bash
# Health check
curl http://localhost:8080/health

# API documentation
open http://localhost:8080/docs
```

### Running Test Suite
```bash
# Run all tests
pytest

# Run Phase 1 tests
pytest -m phase1 -v

# Run with test runner script
./run_tests.sh phase1
```

See `TESTING_GUIDE.md` for detailed testing instructions.

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── routes/          # API routes
│   └── services/       # Business logic
├── alembic/            # Database migrations
├── config.py           # Configuration
├── database.py          # DB connection
├── main.py             # FastAPI app
└── requirements.txt     # Dependencies
```

## Development

```bash
# Run with hot reload
make dev

# Run tests
make test

# Create new migration
make create-migration MESSAGE="description"
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /` - Root endpoint

More endpoints coming in Phase 2...

