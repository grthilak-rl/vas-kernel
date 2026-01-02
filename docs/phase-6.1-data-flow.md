# Phase 6.1 - Data Flow Architecture

## Overview

Phase 6.1 establishes a clean, unidirectional data flow from backend AI event storage to frontend state management, ready for Phase 6.2 overlay rendering.

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Phase 6.1)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Multi-Stream Viewer (/streams)                              │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │ StreamWithAIData (wrapper component)                   │  │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │  │  │
│  │  │  │ useAIEvents hook                                 │  │  │  │
│  │  │  │  - config: { cameraId, polling, timeWindow }     │  │  │  │
│  │  │  │  - returns: { events[], loading, error }         │  │  │  │
│  │  │  └──────────────────────────────────────────────────┘  │  │  │
│  │  │       │                                                 │  │  │
│  │  │       ├─ listAIEvents(filters) [API client]           │  │  │
│  │  │       │                                                 │  │  │
│  │  │  ┌────▼──────────────────────────────────────────────┐ │  │  │
│  │  │  │ DualModePlayer (video player)                     │ │  │  │
│  │  │  │  - Live / Historical mode                         │ │  │  │
│  │  │  │  - AI events available in state (not rendered)    │ │  │  │
│  │  │  └───────────────────────────────────────────────────┘ │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Single Stream Detail (/streams/[id])                       │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │ useAIEvents hook (direct usage)                        │  │  │
│  │  │  - Live mode only                                      │  │  │
│  │  │  - 5s polling                                          │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │       │                                                       │  │
│  │  ┌────▼──────────────────────────────────────────────────┐  │  │
│  │  │ Debug Panel (Phase 6.1 verification)                  │  │  │
│  │  │  - Event count                                         │  │  │
│  │  │  - Polling status                                      │  │  │
│  │  │  - Latest event timestamp                              │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP GET (polling / on-demand)
                                  │ /api/v1/ai-events?camera_id=...
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                    BACKEND (Phase 5.3 - FROZEN)                   │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ AI Events API (/api/v1/ai-events)                           │ │
│  │  - GET /ai-events/{id}                                      │ │
│  │  - GET /ai-events?filters                                   │ │
│  │  - GET /ai-events/cameras/{id}/events                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ SQL SELECT                         │
│                              │                                    │
│  ┌───────────────────────────▼──────────────────────────────────┐ │
│  │ PostgreSQL Database (ai_events table)                       │ │
│  │  - Indexed by: camera_id, timestamp, model_id              │ │
│  │  - Phase 5.1 persistence layer                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ▲                                    │
│                              │ INSERT (inference results)         │
│                              │                                    │
│  ┌───────────────────────────┴──────────────────────────────────┐ │
│  │ AI Core (Phase 4.x - FROZEN)                                │ │
│  │  - Inference execution                                      │ │
│  │  - Event publishing                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Sequence

### Live Mode (with Polling)

```
1. User starts stream → shouldConnect = true

2. StreamWithAIData mounted
   └─> useAIEvents({
         cameraId: device.id,
         enablePolling: true,
         pollingInterval: 5000,
         startTime: Date.now() - 30000,
         endTime: Date.now()
       })

3. Initial fetch (immediate)
   └─> listAIEvents(filters)
       └─> fetch('/api/v1/ai-events?camera_id=...&start_time=...&end_time=...')
           └─> Backend queries ai_events table
               └─> Returns { events: [...], total: N }

4. State update
   └─> setEvents([...]), setTotal(N), setLoading(false)

5. Polling interval starts (every 5s)
   └─> Repeat step 3-4 every 5000ms

6. User stops stream → shouldConnect = false
   └─> useAIEvents disabled (cameraId = undefined)
       └─> Polling interval cleared
       └─> Events cleared from state
```

### Historical Mode (no Polling)

```
1. User switches to historical mode
   └─> setPlayerMode('historical')

2. useAIEvents reconfigures
   └─> enablePolling = false
   └─> timeWindow = null (no events fetched yet)

3. User selects time range (future: Phase 6.3)
   └─> setTimeWindow({ start, end })

4. Single fetch
   └─> listAIEvents({ camera_id, start_time, end_time })
       └─> Returns events for specific time range

5. Events displayed (Phase 6.2: as overlays)
```

---

## State Management Flow

### Hook State

```typescript
useAIEvents() {
  // Internal state
  const [events, setEvents] = useState<AIEvent[]>([])
  const [total, setTotal] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Polling control
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const isMountedRef = useRef<boolean>(true)

  // Fetch function
  const fetchEvents = useCallback(async () => {
    const response = await listAIEvents(filters)
    if (isMountedRef.current) {
      setEvents(response.events)
      setTotal(response.total)
    }
  }, [filters])

  // Effects
  useEffect(() => fetchEvents(), [fetchEvents])  // Initial + dependency fetch
  useEffect(() => setupPolling(), [polling])     // Polling management
  useEffect(() => cleanup(), [])                 // Unmount cleanup

  return { events, total, loading, error, refetch, clear }
}
```

### Component State Flow

```
StreamWithAIData
  ├─> [playerMode, setPlayerMode] - 'live' | 'historical'
  ├─> [timeWindow, setTimeWindow] - { start, end } | null
  └─> useAIEvents({ cameraId, polling, timeWindow })
        └─> returns { events, loading, error }
              └─> passed to DualModePlayer (Phase 6.2: as prop)
                    └─> Phase 6.2: overlays rendered from events
```

---

## Error Handling Flow

```
API Request Failure
  │
  ├─ Network Error (timeout, unreachable)
  │   └─> catch block
  │       └─> console.warn('[Phase 6.1] AI events fetch error:', err)
  │       └─> return { events: [], total: 0 }
  │       └─> User sees: nothing (silent failure)
  │
  ├─ HTTP 500 (backend error)
  │   └─> response.ok = false
  │       └─> console.warn('[Phase 6.1] Failed to fetch AI events: HTTP 500')
  │       └─> return { events: [], total: 0 }
  │       └─> User sees: nothing (silent failure)
  │
  ├─ HTTP 404 (no events)
  │   └─> response.ok = true, events = []
  │       └─> return { events: [], total: 0 }
  │       └─> User sees: nothing (expected behavior)
  │
  └─ AbortController Timeout (10s)
      └─> err.name = 'AbortError'
          └─> console.warn('[Phase 6.1] AI events fetch error: timeout')
          └─> return { events: [], total: 0 }
          └─> User sees: nothing (silent failure)

Result: Video playback NEVER affected by AI data failures
```

---

## Polling Lifecycle

```
Component Mount (Live Mode)
  │
  ├─> useAIEvents({ enablePolling: true, ... })
  │
  ├─> Initial fetch (immediate)
  │     └─> fetchEvents() executes once
  │
  ├─> Polling effect activates
  │     └─> setInterval(fetchEvents, 5000)
  │           └─> pollingIntervalRef.current = intervalId
  │
  ├─> Every 5 seconds:
  │     └─> fetchEvents()
  │           └─> fetch('/api/v1/ai-events?...')
  │                 └─> Update state
  │
  ├─> Dependency change (e.g., timeWindow changes)
  │     └─> Clear old interval
  │     └─> Create new interval with updated config
  │
  └─> Component Unmount or enablePolling = false
        └─> clearInterval(pollingIntervalRef.current)
        └─> isMountedRef.current = false
        └─> No state updates after unmount
```

---

## Request/Response Flow

### Request Example (Live Mode)

```http
GET /api/v1/ai-events?camera_id=abc-123&start_time=2024-01-01T12:00:00Z&end_time=2024-01-01T12:00:30Z&limit=50
```

### Response Example

```json
{
  "events": [
    {
      "id": "event-uuid-1",
      "camera_id": "abc-123",
      "model_id": "yolov8-person-detection",
      "timestamp": "2024-01-01T12:00:28Z",
      "frame_id": 1234567,
      "detections": {
        "boxes": [
          { "x": 100, "y": 200, "w": 50, "h": 100, "class": "person", "confidence": 0.95 }
        ]
      },
      "confidence": 0.95,
      "event_metadata": {
        "model_version": "v8.0",
        "inference_time_ms": 45
      },
      "created_at": "2024-01-01T12:00:29Z"
    },
    // ... more events
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### Frontend State Update

```typescript
// After successful fetch
setEvents(response.events)  // Array of 15 AIEvent objects
setTotal(response.total)    // 15
setLoading(false)
setError(null)

// Phase 6.2 will render overlays from response.events[].detections
```

---

## Performance Characteristics

### Request Frequency

| Scenario | Requests/sec | Requests/min | Notes |
|----------|--------------|--------------|-------|
| 1 live stream | 0.2 | 12 | Every 5s |
| 4 live streams | 0.8 | 48 | Independent polling |
| 1 historical stream | 0 | 0 | On-demand only |
| Mixed (2 live + 2 historical) | 0.4 | 24 | Only live streams poll |

### Request Size

- **Query**: ~200 bytes (URL with params)
- **Response**: ~50KB (100 events × ~500 bytes)
- **Total per request**: ~50KB

### Timeout Budget

- Request timeout: 10 seconds (AbortController)
- Polling interval: 5 seconds
- No overlap: Requests complete before next poll

---

## Phase 6.2 Integration Points

Phase 6.2 (Overlay Rendering) will consume this data:

### Option 1: Via StreamWithAIData
```typescript
// In StreamWithAIData component
const { events } = useAIEvents(config)

// Pass to DualModePlayer
<DualModePlayer
  aiEvents={events}  // NEW PROP
  // ... existing props
/>

// DualModePlayer renders overlays from aiEvents prop
```

### Option 2: Direct Hook Usage
```typescript
// In any component
const { events } = useAIEvents({ cameraId, ... })

// Render overlay canvas/SVG
<OverlayCanvas events={events} videoElement={videoRef.current} />
```

### Available Data Fields

Phase 6.2 can access:
- `events[].detections` - Model-specific detection data (boxes, labels, etc.)
- `events[].timestamp` - For timeline synchronization
- `events[].confidence` - For filtering/styling
- `events[].model_id` - For model-specific rendering

---

**Phase 6.1 Data Flow Complete** - Ready for Phase 6.2 overlay rendering implementation.
