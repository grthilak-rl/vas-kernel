# Database Setup and Usage

## Database Already Implemented in Phase 1 ✅

The database infrastructure was built in **Phase 1** and is fully functional.

### What Was Built:
- ✅ SQLAlchemy models
- ✅ Async database connection
- ✅ Alembic migrations
- ✅ Docker Compose with PostgreSQL
- ✅ Database tables auto-created on startup

## How to Start Database

### Option 1: Docker Compose (Recommended)
```bash
# Start database
docker-compose up db -d

# Start database + backend
docker-compose up db redis backend -d
```

### Option 2: Just Database Container
```bash
docker-compose up db redis -d
```

### Check Database Status
```bash
docker ps | grep vas-db
# Should show vas-db running

# Test connection
docker exec -it vas-db psql -U vas -d vas_db -c "SELECT version();"
```

## Database Configuration

**Default credentials:**
- User: `vas`
- Password: `vas_password`  
- Database: `vas_db`
- Port: `5432`

Configured in `.env`:
```bash
DATABASE_URL=postgresql://vas:vas_password@localhost:5432/vas_db
```

## When to Start Database

### For Testing:
**Phase 1 tests**: ✅ Don't need database
**Phase 2 tests**: ⚠️ Need database for full tests

### For Running Backend:
Always start database when running backend:
```bash
# Terminal 1
docker-compose up db redis -d

# Terminal 2  
cd backend
source ../.venv/bin/activate
python main.py
```

### For Phase 2 Tests:
```bash
# Start database
docker-compose up db redis -d

# Run tests
cd backend
pytest -m phase2 -v
```

## Database Tables

Created automatically on backend startup:
1. `devices` - Camera devices
2. `streams` - Active video streams  
3. `recordings` - Video recordings
4. `bookmarks` - Bookmark clips
5. `snapshots` - Snapshots

## Next Steps

**Phase 2 APIs work** but need database running for full functionality.

To use APIs:
1. Start database: `docker-compose up db -d`
2. Start backend: `python main.py`
3. Test endpoints: http://localhost:8080/docs


