# Quick Start - Viewing Video Feeds

## Current Status

The frontend is ready with UI components, but **full video streaming requires additional setup**:

### ✅ What's Ready
- Frontend UI (dashboard, devices, streams pages)
- Stream player components (WebRTCPlayer, HLSPlayer)
- Backend API with all services
- Device management
- Stream management APIs

### ⚠️ What's Needed for Full Video Streaming
1. **Video Player Integration** - Connect WebRTC player to MediaSoup signaling
2. **Active Camera Feed** - Requires actual RTSP camera or test stream
3. **MediaSoup Worker** - Full MediaSoup worker implementation (currently mocked)

## Quick Start

### 1. Start Services (Basic Setup)

```bash
# Start database and backend
docker-compose up db redis backend -d

# Wait for services to be healthy
docker-compose ps
```

### 2. Access Frontend

```bash
# Start frontend (development mode, not Docker)
cd frontend
npm run dev
```

Then open: http://localhost:3000

### 3. What You'll See

- **Dashboard** (`/`) - Overview of available streams
- **Devices** (`/devices`) - Add/manage cameras
- **Streams** (`/streams`) - Monitor active streams
- **Stream Viewer** (`/streams/[id]`) - WebRTC player for live viewing

### 4. Mock Streams

The current frontend shows mock data. To see real video:

1. Add a device via the Devices page
2. The device must have a valid RTSP URL
3. Start the stream via API or Streams page
4. Click on a stream to view it

## Development Setup

### Start Everything (Full Stack)

```bash
# Make sure you have the env variable set
export MEDIASOUP_WORKER_OPTIONS='{"logLevel": "debug", "rtcMinPort": 40000, "rtcMaxPort": 49999}'

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## Testing with Mock Stream

Since we don't have a real camera, here's how to test:

1. **Add a Test Device**:
   ```bash
   curl -X POST http://localhost:8080/api/v1/devices \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Camera",
       "ip_address": "192.168.1.100",
       "rtsp_url": "rtsp://example.com/stream1"
     }'
   ```

2. **Create a Stream**:
   ```bash
   curl -X POST http://localhost:8080/api/v1/streams \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Stream",
       "device_id": "your-device-id",
       "status": "active"
     }'
   ```

3. **View in Frontend**: 
   - Go to http://localhost:3000/streams
   - Click on a stream to view it

## What's Currently Working

✅ **Backend Services**:
- Device CRUD APIs
- Stream management APIs
- RTSP pipeline service
- MediaSoup service (mock)
- Recording service
- WebSocket signaling

✅ **Frontend**:
- Dashboard with stream listings
- Device management UI
- Stream management UI
- Basic player components (needs integration)

⚠️ **In Progress**:
- Full WebRTC player integration
- HLS playback for recordings
- Real-time stream status updates

## Next Steps for Full Video Support

1. Complete WebRTC player integration with MediaSoup signaling
2. Add HLS.js library for recording playback
3. Implement real-time status updates via WebSocket
4. Add snapshot gallery
5. Test with actual RTSP camera

## Troubleshooting

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### Backend won't start
```bash
# Check database connection
docker-compose logs db

# Check backend logs
docker-compose logs backend
```

### Cannot view streams
- Check that a device exists
- Verify the stream is marked as "active"
- Check WebSocket connection in browser console

## Need Help?

Check the phase summaries:
- `PHASE1_SUMMARY.md` - Foundation
- `PHASE7_SUMMARY.md` - Frontend
- `PHASE8_SUMMARY.md` - Integration

Or run tests:
```bash
cd backend
source ../.venv/bin/activate
pytest -v
```


