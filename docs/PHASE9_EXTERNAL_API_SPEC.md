# Phase 9: External API Gateway - Specification

## 📋 Overview

Enable secure third-party access to VAS video streams through a dedicated external API gateway with OAuth2 authentication, ACL-based authorization, and rate limiting.

**Status**: ⏳ Planned (Not yet implemented)  
**Priority**: 🔴 High (Required for third-party integrations)  
**Dependencies**: Phase 8 (RTSP→WebRTC streaming must be working)

---

## 🎯 Requirements

### Functional Requirements

1. **Stream Exposure**
   - Third-party apps can access individual camera streams
   - Third-party apps can access multiple streams simultaneously
   - Same stream can be embedded multiple times in different contexts
   - Each instance maintains independent consumer connection

2. **Authentication**
   - OAuth2 client credentials flow
   - JWT token-based authentication
   - API key management system
   - Token expiration and refresh

3. **Authorization**
   - Stream-level Access Control Lists (ACL)
   - Per-client stream permissions
   - Visibility control (public/private/restricted streams)
   - Time-based access grants

4. **Security**
   - Rate limiting per client
   - Request throttling
   - IP whitelisting (optional)
   - Audit logging for all access

5. **API Documentation**
   - OpenAPI/Swagger specification
   - Interactive API explorer
   - Code examples in multiple languages
   - Integration guides

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Third-Party Applications                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Portal A    │  │  Dashboard B │  │  Mobile App  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │ HTTPS + JWT      │                  │
          └──────────────────┴──────────────────┘
                             │
          ┌──────────────────▼──────────────────────────┐
          │      External API Gateway (NEW)             │
          │  - OAuth2 Token Endpoint                    │
          │  - Authentication Middleware                │
          │  - Authorization (ACL Check)                │
          │  - Rate Limiting                            │
          │  - Request Validation                       │
          └──────────────────┬──────────────────────────┘
                             │
          ┌──────────────────▼──────────────────────────┐
          │      VAS Backend (Existing)                 │
          │  - Stream Manager                           │
          │  - Device Manager                           │
          │  - MediaSoup Service                        │
          └──────────────────┬──────────────────────────┘
                             │
          ┌──────────────────▼──────────────────────────┐
          │      MediaSoup Worker                       │
          │  - WebRTC Transport                         │
          │  - Producer/Consumer Management             │
          └──────────────────┬──────────────────────────┘
                             │
          ┌──────────────────▼──────────────────────────┐
          │      Video Streams (RTSP Cameras)           │
          └─────────────────────────────────────────────┘
```

### Database Schema Additions

```sql
-- OAuth2 Clients
CREATE TABLE external_clients (
    id UUID PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    redirect_uris TEXT[],
    allowed_scopes TEXT[],
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stream Access Control Lists
CREATE TABLE stream_acls (
    id UUID PRIMARY KEY,
    stream_id UUID REFERENCES devices(id),
    client_id UUID REFERENCES external_clients(id),
    permissions TEXT[] NOT NULL, -- ['view', 'record', 'snapshot']
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    granted_by UUID, -- Admin user who granted access
    UNIQUE(stream_id, client_id)
);

-- Access Tokens
CREATE TABLE access_tokens (
    id UUID PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    client_id UUID REFERENCES external_clients(id),
    scopes TEXT[],
    issued_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    last_used_at TIMESTAMP
);

-- API Access Logs
CREATE TABLE api_access_logs (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES external_clients(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    request_ip VARCHAR(45),
    user_agent TEXT,
    response_time_ms INTEGER,
    accessed_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔌 API Endpoints

### Base URL
```
https://vas.example.com/api/v1/external
```

### Authentication Endpoints

#### 1. Obtain Access Token (OAuth2 Client Credentials)

```http
POST /api/v1/external/auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=your_client_id&
client_secret=your_client_secret&
scope=streams:read streams:control
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "streams:read streams:control"
}
```

#### 2. Refresh Token

```http
POST /api/v1/external/auth/refresh
Content-Type: application/json
Authorization: Bearer <expired_token>

{
  "refresh_token": "refresh_token_value"
}
```

---

### Stream Endpoints

#### 3. List Available Streams

```http
GET /api/v1/external/streams
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "streams": [
    {
      "id": "stream-abc-123",
      "name": "Front Entrance Camera",
      "location": "Building A - Main Entrance",
      "status": "active",
      "permissions": ["view", "snapshot"],
      "thumbnail_url": "https://vas.example.com/thumbnails/abc123.jpg",
      "created_at": "2025-11-01T10:00:00Z"
    },
    {
      "id": "stream-def-456",
      "name": "Parking Lot Camera",
      "location": "Building B - Parking",
      "status": "active",
      "permissions": ["view"],
      "thumbnail_url": "https://vas.example.com/thumbnails/def456.jpg",
      "created_at": "2025-11-02T14:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

#### 4. Get Stream Details

```http
GET /api/v1/external/streams/{stream_id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "stream-abc-123",
  "name": "Front Entrance Camera",
  "location": "Building A - Main Entrance",
  "status": "active",
  "permissions": ["view", "snapshot"],
  "resolution": "1920x1080",
  "fps": 30,
  "codec": "H.264",
  "bitrate_kbps": 2500,
  "thumbnail_url": "https://vas.example.com/thumbnails/abc123.jpg",
  "created_at": "2025-11-01T10:00:00Z",
  "last_active": "2025-11-04T15:30:00Z"
}
```

#### 5. Connect to Stream (Get WebRTC Connection Info)

```http
POST /api/v1/external/streams/{stream_id}/connect
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "instance_id": "viewer-portal-1",  // Optional: for multiple instances
  "quality": "high"  // Optional: high, medium, low
}
```

**Response:**
```json
{
  "connection_id": "conn-xyz-789",
  "stream_id": "stream-abc-123",
  "instance_id": "viewer-portal-1",
  "websocket_url": "wss://vas.example.com/external/ws/streams/abc123",
  "ice_servers": [
    {
      "urls": ["stun:stun.vas.example.com:3478"]
    },
    {
      "urls": ["turn:turn.vas.example.com:3478"],
      "username": "temp_user",
      "credential": "temp_credential"
    }
  ],
  "sdp_offer": "v=0\r\no=...",
  "expires_at": "2025-11-04T16:30:00Z"
}
```

#### 6. Disconnect from Stream

```http
POST /api/v1/external/streams/{stream_id}/disconnect
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "connection_id": "conn-xyz-789"
}
```

**Response:**
```json
{
  "status": "disconnected",
  "connection_id": "conn-xyz-789",
  "duration_seconds": 1245
}
```

#### 7. Get Stream Snapshot

```http
GET /api/v1/external/streams/{stream_id}/snapshot
Authorization: Bearer <access_token>
```

**Response:** Image file (JPEG/PNG) or
```json
{
  "snapshot_url": "https://vas.example.com/snapshots/abc123-20251104-153000.jpg",
  "captured_at": "2025-11-04T15:30:00Z",
  "expires_at": "2025-11-04T16:30:00Z"
}
```

---

### Admin Endpoints (For Managing External Clients)

#### 8. Create External Client

```http
POST /api/v1/admin/external-clients
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Partner Portal Inc.",
  "description": "Integration for partner dashboard",
  "redirect_uris": ["https://partner.example.com/oauth/callback"],
  "allowed_scopes": ["streams:read", "streams:control"],
  "rate_limit_per_hour": 5000
}
```

**Response:**
```json
{
  "id": "client-uuid-123",
  "client_id": "partner_portal_12345",
  "client_secret": "secret_abc123xyz789",  // Only shown once!
  "name": "Partner Portal Inc.",
  "rate_limit_per_hour": 5000,
  "created_at": "2025-11-04T15:30:00Z"
}
```

#### 9. Grant Stream Access to Client

```http
POST /api/v1/admin/stream-access
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "client_id": "partner_portal_12345",
  "stream_ids": ["stream-abc-123", "stream-def-456"],
  "permissions": ["view", "snapshot"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "granted": 2,
  "acls": [
    {
      "stream_id": "stream-abc-123",
      "client_id": "partner_portal_12345",
      "permissions": ["view", "snapshot"],
      "expires_at": "2025-12-31T23:59:59Z"
    },
    {
      "stream_id": "stream-def-456",
      "client_id": "partner_portal_12345",
      "permissions": ["view", "snapshot"],
      "expires_at": "2025-12-31T23:59:59Z"
    }
  ]
}
```

---

## 🔐 Security Implementation

### OAuth2 Flow

```
┌─────────────┐                                    ┌──────────────┐
│  Third-Party│                                    │     VAS      │
│     App     │                                    │  Auth Server │
└──────┬──────┘                                    └──────┬───────┘
       │                                                  │
       │  1. POST /auth/token                            │
       │     (client_id, client_secret)                  │
       ├────────────────────────────────────────────────>│
       │                                                  │
       │  2. Validate credentials                        │
       │     Check client exists & is active             │
       │                                                  │
       │  3. Generate JWT with claims:                   │
       │     - client_id                                 │
       │     - scopes                                    │
       │     - expiration (1 hour)                       │
       │                                                  │
       │  4. Return access_token                         │
       │<────────────────────────────────────────────────┤
       │                                                  │
       │  5. Use token for API requests:                 │
       │     Authorization: Bearer <token>               │
       │                                                  │
```

### JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "client_id": "partner_portal_12345",
    "scopes": ["streams:read", "streams:control"],
    "iat": 1730736600,
    "exp": 1730740200,
    "aud": "vas-api",
    "iss": "vas-auth-server"
  }
}
```

### Rate Limiting Strategy

```python
# Per-client rate limits (sliding window)
RATE_LIMITS = {
    "tier_1": {  # Basic tier
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "concurrent_streams": 5
    },
    "tier_2": {  # Premium tier
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "concurrent_streams": 20
    },
    "tier_3": {  # Enterprise tier
        "requests_per_minute": 1000,
        "requests_per_hour": 50000,
        "concurrent_streams": 100
    }
}
```

---

## 📝 Implementation Checklist

### Phase 9.1: Foundation (Week 1)
- [ ] Create database schema for external clients and ACLs
- [ ] Implement OAuth2 token endpoint (`/auth/token`)
- [ ] Add JWT generation and validation middleware
- [ ] Create external client CRUD admin endpoints
- [ ] Add unit tests for authentication flow

### Phase 9.2: Stream Access (Week 1)
- [ ] Implement `/external/streams` list endpoint with ACL filtering
- [ ] Implement `/external/streams/{id}` detail endpoint
- [ ] Implement `/external/streams/{id}/connect` WebRTC connection
- [ ] Add ACL check middleware for all stream endpoints
- [ ] Add integration tests for stream access

### Phase 9.3: Security & Rate Limiting (Week 2)
- [ ] Implement rate limiting middleware (Redis-backed)
- [ ] Add request/response logging for audit trail
- [ ] Implement token revocation mechanism
- [ ] Add IP whitelisting (optional, configurable)
- [ ] Security testing and penetration testing

### Phase 9.4: Documentation & Examples (Week 2)
- [ ] Generate OpenAPI/Swagger specification
- [ ] Create interactive API documentation portal
- [ ] Write integration guides for common languages:
  - [ ] JavaScript/TypeScript
  - [ ] Python
  - [ ] Java
  - [ ] C#
- [ ] Create sample applications demonstrating integration

### Phase 9.5: Monitoring & Analytics
- [ ] Add Prometheus metrics for external API usage
- [ ] Create Grafana dashboard for API analytics
- [ ] Implement alerting for rate limit violations
- [ ] Add usage reports for clients (requests, bandwidth, etc.)

---

## 🧪 Testing Strategy

### Unit Tests
- OAuth2 token generation and validation
- JWT encoding/decoding
- ACL permission checks
- Rate limiting logic

### Integration Tests
- Full OAuth2 flow (token request → API call)
- Stream connection with valid/invalid tokens
- ACL enforcement (access granted/denied)
- Rate limiting triggers and recovery

### Load Tests
- 1000 concurrent client connections
- 100 requests/second per client
- Multiple stream instances from same client

### Security Tests
- Token tampering attempts
- Expired token handling
- Invalid client credentials
- SQL injection attempts
- Rate limit bypassing attempts

---

## 📊 Success Metrics

- **Availability**: 99.9% uptime for external API
- **Latency**: <200ms for token generation, <500ms for stream connection
- **Rate Limiting**: 0% false positives (legitimate requests blocked)
- **Security**: 0 unauthorized access incidents
- **Documentation**: 100% API coverage in OpenAPI spec

---

## 🔮 Future Enhancements (Post-Phase 9)

- **Webhook Notifications**: Alert clients when streams go online/offline
- **Usage Analytics API**: Let clients query their own usage stats
- **GraphQL Support**: Alternative to REST for flexible queries
- **Multi-region Support**: Geographic distribution of API gateways
- **Advanced ACLs**: Time-of-day restrictions, IP-based rules
- **Stream Recording API**: Let clients trigger and download recordings

---

## 📚 References

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [MediaSoup API](https://mediasoup.org/documentation/v3/mediasoup/api/)

---

**Document Version**: 1.0  
**Last Updated**: November 4, 2025  
**Status**: Draft - Awaiting Phase 8 completion before implementation

