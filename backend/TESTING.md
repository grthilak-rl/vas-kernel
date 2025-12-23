# VAS Backend Testing Guide

## Phase 1 Testing

### Prerequisites
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Copy environment file
cp env.example .env
```

### Test Database Setup

1. **Start PostgreSQL** (using Docker)
```bash
docker-compose up db -d
```

2. **Run Migrations**
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migrations
alembic upgrade head
```

3. **Verify Tables**
```bash
# Connect to database
docker exec -it vas-db psql -U vas -d vas_db

# List tables
\dt

# Should show: devices, streams, recordings, bookmarks, snapshots
```

### Test Backend Startup

1. **Start Backend Server**
```bash
python main.py
# OR
make dev
```

2. **Check Health Endpoint**
```bash
curl http://localhost:8080/health
# Expected: {"status":"healthy","service":"VAS Backend","version":"1.0.0"}
```

3. **Check API Docs**
```bash
# Open browser
http://localhost:8080/docs
```

4. **Check Root Endpoint**
```bash
curl http://localhost:8080/
```

### Verify Logging

Check logs directory for structured logging:
```bash
ls -la logs/
# Should see: app_YYYY-MM-DD.log files
```

### Expected Results

✅ PostgreSQL database running  
✅ All tables created successfully  
✅ Backend API responding on port 8080  
✅ Health endpoint returns healthy status  
✅ API documentation accessible  
✅ Logging working (both console and file)  

## Next Steps

After Phase 1 is verified, proceed to Phase 2: Core Backend APIs


