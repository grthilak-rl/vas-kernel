# VAS Architecture Documentation

## Overview

The Video Aggregation Service (VAS) is a containerized video streaming system that converts RTSP camera feeds to WebRTC for low-latency viewing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Browser)                         │
│                   WebRTC + WebSocket                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Next.js Frontend (Port 3000)                │
│              - SSR Dashboard                                 │
│              - WebRTC Player                                 │
│              - Stream Management UI                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8080)                     │
│         - REST APIs                                          │
│         - WebSocket Signaling                                │
│         - PostgreSQL                                         │
└────────┬────────────────┬──────────────────┬───────────────┘
         │                │                  │
         ▼                ▼                  ▼
┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
│  MediaSoup Worker │  │RTSP Pipeline│  │Recording Svc │
│    (Port 5001)    │  │  (Port 5002)│  │              │
│                   │  │             │  │  - HLS       │
│  - WebRTC SFU     │  │ - FFmpeg    │  │  - Storage   │
│  - RTP Forward    │  │ - RTSP→RTP  │  │              │
└──────┬────────────┘  └────┬────────┘  └──────┬───────┘
       │                     │                  │
       └─────────────────────┴──────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Camera (RTSP)   │
                    └─────────────────┘
```

## Services

### Backend (FastAPI)
- **Port**: 8080 (REST API), 8081 (WebSocket)
- **Role**: Core business logic, APIs, coordination
- **Database**: PostgreSQL via SQLAlchemy

### MediaSoup Worker
- **Port**: 5001
- **Role**: SFU-based WebRTC routing
- **Responsibilities**: Router, Transport, Producer/Consumer management

### RTSP Pipeline
- **Port**: 5002
- **Role**: RTSP ingestion and RTP forwarding
- **Technology**: FFmpeg
- **Responsibilities**: Stream health, reconnection logic

### Recording Service
- **Role**: Video chunk recording
- **Technology**: FFmpeg HLS
- **Output**: `.m3u8` playlists + `.ts` segments

### Frontend (Next.js)
- **Port**: 3000
- **Technology**: React + SSR
- **Features**: Live viewing, stream management, recordings

## Database Schema

### Tables
- `devices` - Camera devices
- `streams` - Active video streams
- `recordings` - Video chunks
- `bookmarks` - Saved clips (±5 sec)
- `snapshots` - Single frame captures

## API Endpoints

### Devices
- `POST /api/v1/devices` - Add camera
- `GET /api/v1/devices` - List devices
- `DELETE /api/v1/devices/{id}` - Remove device

### Streams
- `GET /api/v1/streams` - List streams
- `POST /api/v1/streams/{id}/start` - Start stream
- `POST /api/v1/streams/{id}/stop` - Stop stream

## Deployment

### Development
```bash
docker-compose up -d
```

### Production
- Use Kubernetes manifests
- Configure load balancing
- Set up monitoring (Prometheus + Grafana)


