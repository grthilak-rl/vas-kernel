# Phase 1 Testing Checklist

## ✅ What We Built

### Backend Infrastructure
- [x] FastAPI application structure
- [x] SQLAlchemy models (Device, Stream, Recording, Bookmark, Snapshot)
- [x] Pydantic schemas for validation
- [x] Database configuration with PostgreSQL
- [x] Alembic migrations setup
- [x] Structured logging with Loguru
- [x] Environment configuration
- [x] Docker Compose setup

### Services Placeholder
- [x] MediaSoup Worker stub (Phase 3)
- [x] RTSP Pipeline stub (Phase 4)
- [x] Recording Service stub (Phase 5)
- [x] Frontend stub (Phase 7)

## 🧪 How to Test Phase 1

### 1. Start Only Essential Services
```bash
# Start just database and Redis
docker-compose up db redis -d
```

### 2. Verify Database is Running
```bash
# Check if PostgreSQL is healthy
docker ps | grep vas-db
```

### 3. Setup Backend
```bash
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Install and setup Alembic
# Note: Alembic migrations will be created in Phase 2 after we test
```

### 4. Test Backend (Without Docker)
```bash
# Run backend directly
python main.py

# OR
make dev
```

### 5. Test Health Endpoint
```bash
# In another terminal
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","service":"VAS Backend","version":"1.0.0"}
```

### 6. Check API Documentation
```bash
# Open in browser
open http://localhost:8080/docs

# OR
curl http://localhost:8080/docs
```

### 7. Test Logging
```bash
# Check logs directory
ls -la backend/logs/

# Should see app_YYYY-MM-DD.log files
```

### 8. Test with Docker Compose (Optional)
```bash
# If you want to test backend in Docker
docker-compose up backend -d

# Check logs
docker-compose logs backend

# Test health
curl http://localhost:8080/health
```

## ✅ Success Criteria

- [ ] Backend starts without errors
- [ ] Health endpoint returns `{"status":"healthy",...}`
- [ ] API documentation is accessible at `/docs`
- [ ] Root endpoint works at `/`
- [ ] Logging is working (check console and logs/)
- [ ] Database connection established (check logs)
- [ ] All tables created automatically

## 🔧 If Something Fails

### Backend won't start
```bash
# Check if port 8080 is already in use
lsof -i :8080

# Kill the process if needed
kill -9 <PID>

# Check logs
tail -f backend/logs/app_*.log
```

### Database connection fails
```bash
# Make sure database is running
docker-compose up db redis -d

# Check database connection
docker exec -it vas-db psql -U vas -d vas_db -c "SELECT 1"
```

### Import errors
```bash
# Install dependencies
pip install -r backend/requirements.txt

# If still failing, check Python version (should be 3.11+)
python --version
```

## 📝 Next Steps

Once Phase 1 is tested and working:

1. **Phase 2**: Implement Core Backend APIs
   - Device CRUD endpoints
   - Stream management endpoints
   - Error handling

2. **Phase 3**: Build MediaSoup Worker
3. **Phase 4**: Build RTSP Pipeline
4. **Phase 5**: Build Recording Service
5. **Phase 6**: Add WebSocket signaling
6. **Phase 7**: Build Next.js frontend

## 🚀 Quick Start

```bash
# Start database
docker-compose up db redis -d

# Setup backend
cd backend
pip install -r requirements.txt
python main.py

# Test
curl http://localhost:8080/health
```

If you see: `{"status":"healthy","service":"VAS Backend","version":"1.0.0"}`, you're ready for Phase 2!


