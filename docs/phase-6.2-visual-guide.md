# Phase 6.2 - Overlay Rendering - Visual Guide

## Overview

This document provides visual examples and rendering specifications for the Phase 6.2 AI overlay implementation.

---

## Overlay Components

### 1. Bounding Box

```
┌───────────────────────────────────┐
│ Video Frame                       │
│                                   │
│     ┏━━━━━━━━━━━━━━━━┓            │
│     ┃ person 95%     ┃            │  ← Label (black bg, white text)
│     ┃                ┃            │
│     ┃                ┃            │  ← Bounding Box (green, 2px)
│     ┃                ┃            │
│     ┗━━━━━━━━━━━━━━━━┛            │
│                                   │
└───────────────────────────────────┘
```

**Specifications**:
- Box Color: #00FF00 (green)
- Line Width: 2px
- Box Style: Solid stroke
- Label Background: rgba(0, 0, 0, 0.7)
- Label Text: #FFFFFF (white)
- Label Font: 14px sans-serif
- Label Position: 4px above box, 4px left padding

---

## Rendering Examples

### Example 1: Single Detection (Person)

```
Input Event:
{
  "id": "event-123",
  "camera_id": "camera-1",
  "timestamp": "2024-01-01T12:00:00Z",
  "detections": {
    "boxes": [
      {
        "x": 0.4, "y": 0.3, "w": 0.2, "h": 0.4,
        "class": "person",
        "confidence": 0.95
      }
    ]
  }
}

Rendered Output:
┌────────────────────────────┐
│                            │
│      ┏━━━━━━━━┓            │
│      ┃ person ┃            │
│      ┃  95%   ┃            │
│      ┃        ┃            │
│      ┃        ┃            │
│      ┗━━━━━━━━┛            │
│                            │
└────────────────────────────┘
```

### Example 2: Multiple Detections

```
Input Event:
{
  "detections": {
    "boxes": [
      { "x": 0.2, "y": 0.2, "class": "person", "confidence": 0.92 },
      { "x": 0.6, "y": 0.4, "class": "car", "confidence": 0.88 },
      { "x": 0.1, "y": 0.6, "class": "dog", "confidence": 0.75 }
    ]
  }
}

Rendered Output:
┌───────────────────────────┐
│  ┏━━━━┓                   │
│  ┃per-┃    ┏━━━━━┓        │
│  ┃son ┃    ┃ car ┃        │
│  ┃92% ┃    ┃ 88% ┃        │
│  ┗━━━━┛    ┗━━━━━┛        │
│                           │
│ ┏━━━━┓                    │
│ ┃dog ┃                    │
│ ┃75% ┃                    │
│ ┗━━━━┛                    │
└───────────────────────────┘
```

---

## Coordinate Systems

### Normalized Coordinates (0-1)

```
(0,0) ─────────────── (1,0)
  │                    │
  │   Detection:       │
  │   x=0.5, y=0.5     │
  │   w=0.2, h=0.3     │
  │                    │
(0,1) ─────────────── (1,1)
```

**Conversion to Pixels**:
```typescript
pixelX = normalizedX * videoWidth
pixelY = normalizedY * videoHeight
pixelW = normalizedW * videoWidth
pixelH = normalizedH * videoHeight
```

### Pixel Coordinates

```
(0,0) ──────────────── (1920,0)
  │                      │
  │   Detection:         │
  │   x=960, y=540       │
  │   w=200, h=300       │
  │                      │
(0,1080) ─────────── (1920,1080)
```

### Canvas Scaling

```
Video Natural Size: 1920x1080
Canvas Display Size: 640x360
Scale Factor: 640/1920 = 0.333

Detection:
  Natural: x=960, y=540, w=200, h=300
  Scaled:  x=320, y=180, w=66.7, h=100
```

---

## Time-Based Filtering

### Live Mode Timeline

```
Current Time: 12:00:30
Tolerance: ±2s

Time:    12:00:26 ──── 12:00:28 ──── 12:00:30 ──── 12:00:32 ──── 12:00:34
Events:      ❌            ✅            ✅            ✅            ❌
           (too old)    (in range)   (current)    (in range)    (too new)
```

**Filtering Logic**:
```
Event at 12:00:28: |12:00:30 - 12:00:28| = 2s ≤ 2s → Show ✅
Event at 12:00:26: |12:00:30 - 12:00:26| = 4s > 2s → Hide ❌
```

### Historical Mode

```
Fetched Range: 10:00:00 - 11:00:00
Current Position: 10:30:00

Time:    10:00:00 ──────── 10:30:00 ──────── 11:00:00
Events:      ✅              ✅              ✅
          (all shown, no filtering)
```

---

## Rendering Pipeline

### Step-by-Step Process

```
1. Filter Events by Time
   ┌─────────┐
   │ Events  │ → Time filter → [Event1, Event3, Event5]
   │ (all)   │
   └─────────┘

2. Parse Detections
   ┌───────────┐
   │ Event1    │ → parseDetections() → [Box1, Box2]
   │ detections│
   └───────────┘

3. Normalize Coordinates
   ┌──────────┐
   │ Box1     │ → normalize() → { x: 320, y: 180, ... }
   │ (0-1)    │
   └──────────┘

4. Scale to Canvas
   ┌──────────┐
   │ Box1     │ → scale() → { x: 106, y: 60, ... }
   │ (pixels) │
   └──────────┘

5. Draw on Canvas
   ┌──────────┐
   │ Canvas   │ → ctx.strokeRect() → Visual box
   │          │ → ctx.fillText()   → Label
   └──────────┘
```

### Animation Loop

```
Frame 0 (0ms):
  - Clear canvas
  - Filter events
  - Render boxes
  - requestAnimationFrame()

Frame 1 (33ms):
  - Clear canvas
  - Filter events (new data?)
  - Render boxes
  - requestAnimationFrame()

Frame 2 (66ms):
  - ...

~30 FPS continuous rendering
```

---

## Detection Format Examples

### Format 1: YOLOv8 Style

```json
{
  "boxes": [
    {
      "x": 0.5,          // Center X (normalized 0-1)
      "y": 0.3,          // Center Y (normalized 0-1)
      "w": 0.2,          // Width (normalized 0-1)
      "h": 0.4,          // Height (normalized 0-1)
      "class": "person", // Class label
      "confidence": 0.95 // Confidence score
    }
  ]
}
```

### Format 2: Array Bbox

```json
{
  "detections": [
    {
      "bbox": [100, 200, 50, 100], // [x, y, width, height] in pixels
      "label": "car",
      "score": 0.87
    }
  ]
}
```

### Format 3: Objects

```json
{
  "objects": [
    {
      "x": 150,          // Top-left X (pixels)
      "y": 250,          // Top-left Y (pixels)
      "width": 60,       // Width (pixels)
      "height": 120,     // Height (pixels)
      "name": "person",  // Class name
      "conf": 0.92       // Confidence
    }
  ]
}
```

---

## Error Handling

### Malformed Data Examples

#### Invalid Coordinates

```json
Input:
{
  "boxes": [
    { "x": -10, "y": 50, "w": 0, "h": 100 }
  ]
}

Result: Skipped (width <= 0)
Console: No error logged (silent skip)
```

#### Missing Fields

```json
Input:
{
  "boxes": [
    { "x": 0.5, "y": 0.3 }  // Missing w, h
  ]
}

Result: Box with w=0, h=0 → Skipped
Console: No error
```

#### Unknown Format

```json
Input:
{
  "predictions": [...]  // Unknown key
}

Result: parseDetections() returns []
Console: "[Phase 6.2] Failed to parse detections: ..."
Video: Continues playing normally
```

---

## Performance Metrics

### Rendering Overhead

```
┌─────────────────┬──────────┬──────────┐
│ Events Count    │ FPS      │ CPU %    │
├─────────────────┼──────────┼──────────┤
│ 0               │ N/A      │ 0%       │
│ 1-10            │ 30       │ 2-5%     │
│ 10-50           │ 30       │ 5-8%     │
│ 50-100          │ 28-30    │ 8-12%    │
│ 100+            │ 25-30    │ 10-15%   │
└─────────────────┴──────────┴──────────┘
```

### Canvas Operations

```
Per Detection:
  - 1x ctx.strokeRect()  (~0.1ms)
  - 1x ctx.fillRect()    (~0.1ms)
  - 1x ctx.fillText()    (~0.2ms)
  - 1x ctx.measureText() (~0.05ms)

Total: ~0.45ms per detection
For 10 detections: 4.5ms per frame
Frame budget (30 FPS): 33ms
Headroom: 28.5ms ✅
```

---

## Layout & Positioning

### Canvas Overlay Structure

```
┌────────────────────────────────────┐
│ Player Container (relative)        │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Video Element (absolute)       │ │
│ │                                │ │
│ │   Video stream here            │ │
│ │                                │ │
│ └────────────────────────────────┘ │
│ ┌────────────────────────────────┐ │
│ │ Canvas Overlay (absolute)      │ │ ← z-index: 10
│ │ pointer-events: none           │ │
│ │                                │ │
│ │   AI overlays here             │ │
│ │                                │ │
│ └────────────────────────────────┘ │
│                                    │
└────────────────────────────────────┘
```

### Z-Index Layers

```
Layer 0: Video element (base)
Layer 10: Canvas overlay (AI detections)
Layer 20: Player controls (future)
Layer 30: Mode selector buttons
```

---

## Integration Points

### Multi-Stream Grid

```
┌──────────┬──────────┐
│ Stream 1 │ Stream 2 │
│ + AI     │ + AI     │  ← Independent overlays
├──────────┼──────────┤
│ Stream 3 │ Stream 4 │
│ + AI     │ + AI     │
└──────────┴──────────┘
```

Each stream has:
- Independent `AIOverlayCanvas` instance
- Own video element reference
- Own AI events array
- No cross-contamination

### Single Stream Detail

```
┌─────────────────────────────┐
│ Device Name                 │
├─────────────────────────────┤
│                             │
│   Video + AI Overlay        │
│                             │
├─────────────────────────────┤
│ AI Event Stats Panel        │
└─────────────────────────────┘
```

---

## Future Enhancements (Phase 6.3+)

### Planned UX Controls

```
┌─────────────────────────────────┐
│ ☑ Show AI Overlays              │
│ ☑ Show Labels                   │
│ ☑ Show Confidence Scores        │
│                                 │
│ Confidence Threshold: 0.7 ──●─  │
│                                 │
│ Model Filter: [All Models ▼]    │
│                                 │
│ Box Color:  [Green ▼]           │
│ Box Opacity: 0.8 ──────●──      │
└─────────────────────────────────┘
```

**NOT in Phase 6.2** - These are Phase 6.3 features.

---

**Phase 6.2 Complete** - Visual overlays are now rendered on all video streams.
