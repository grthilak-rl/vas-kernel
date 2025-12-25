VAS – Video Aggregation Service (Reference Implementation)

This repository contains a stable reference implementation of the VAS (Video Aggregation Service).

VAS provides:
	•	RTSP camera ingestion
	•	Single-pass decode
	•	WebRTC streaming via MediaSoup
	•	Continuous recording (HLS)
	•	Snapshot capture
	•	Browser-based live and historical playback

⚠️ This repository is no longer the primary development target.
Future platform evolution (AI integration, orchestration, scaling) is being done in a separate repository named vas-kernel.

⸻

## Deployment Modes

### Production Mode (Docker)

Run the complete stack in Docker containers:

```bash
docker-compose up -d
```

**Access:**
- Frontend: http://10.30.250.245 (port 80) or http://localhost if accessing from the server itself
- Backend API: http://10.30.250.245:8080/docs
- MediaSoup: http://10.30.250.245:3001

**Note:** The frontend connects to the backend at `http://10.30.250.245:8080`. If deploying to a different server, update `NEXT_PUBLIC_API_URL` in docker-compose.yml to match your server's IP or domain.

### Development Mode (Local Frontend)

For frontend development without Docker:

1. Start backend services only:
   ```bash
   docker-compose up -d db redis backend mediasoup
   ```

2. Set up frontend environment:
   ```bash
   cd frontend
   cp .env.local.example .env.local
   npm install
   ```

3. Run frontend locally:
   ```bash
   npm run dev
   ```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080/docs

⸻

Architecture (High Level)

RTSP Camera → FFmpeg → MediaSoup → WebRTC → Browser

Tech Stack
FastAPI · MediaSoup · FFmpeg · Next.js · PostgreSQL

⸻

Repository Status
	•	Stable
	•	Feature-frozen
	•	Maintained for reference and production support only

No new features should be added to this repository.

All future development must happen in vas-kernel.

⸻

License

[Add license if applicable]