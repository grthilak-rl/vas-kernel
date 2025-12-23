# VAS - Video Aggregation Service

A production-ready RTSP to WebRTC streaming platform with recording capabilities.

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Access
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8080/docs
```

## 📚 Documentation

- **[Project Overview](./PROJECT_README.md)** - Full architecture, tech stack, API docs
- **[Current Issue](./CURRENT_ISSUE_RTSP_WEBRTC.md)** - RTSP→WebRTC streaming troubleshooting
- **[Phase 9 External API Spec](./docs/PHASE9_EXTERNAL_API_SPEC.md)** - Third-party API integration design
- **[Archive](./docs/archive/)** - Historical development documentation

## 🔴 Current Status

**Phase 8/11 Complete (73%)** - Core platform operational, debugging streaming issue

**Current Issue**: WebRTC video track mutes after connection (SSRC matching problem)

See [`CURRENT_ISSUE_RTSP_WEBRTC.md`](./CURRENT_ISSUE_RTSP_WEBRTC.md) for:
- Detailed problem analysis
- 6 attempted fixes
- Current solution being tested
- Next debugging steps

## 🏗️ Architecture

```
RTSP Camera → FFmpeg → MediaSoup → WebRTC → Browser
```

**Tech Stack**: FastAPI + MediaSoup + FFmpeg + Next.js + PostgreSQL

## ✅ What's Working

- ✅ Device management (CRUD cameras)
- ✅ Stream control (start/stop)
- ✅ MediaSoup WebRTC routing
- ✅ Recording service (HLS)
- ✅ Frontend dashboard
- ✅ 85+ tests passing

## 🔧 Development

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8080

# MediaSoup Worker
cd mediasoup-server && node server.js

# Frontend
cd frontend && npm run dev
```

## 📞 Getting Help

1. Check [`CURRENT_ISSUE_RTSP_WEBRTC.md`](./CURRENT_ISSUE_RTSP_WEBRTC.md) for streaming issues
2. Review [`PROJECT_README.md`](./PROJECT_README.md) for full documentation
3. API docs at http://localhost:8080/docs

---

**Version**: 0.8.0 | **Last Updated**: Nov 4, 2025
