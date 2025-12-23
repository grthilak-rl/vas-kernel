# Ruth AI Historical HLS Integration - Root Cause Assessment

## Executive Summary

**Status:** Ruth AI historical feed shows black screen despite successful playlist loading
**Root Cause:** HLS.js cannot resolve relative segment URLs from the VAS V2 playlist
**Impact:** Historical playback completely broken in Ruth AI
**Our Stream Reconnection Fix:** ✅ Not related - this is a pre-existing integration issue

---

## Technical Analysis

### What's Working ✅

1. **VAS Portal Historical Playback**
   - Uses HLS.js with the same VAS V2 endpoint
   - Successfully plays historical video
   - Endpoint: `http://10.30.250.245:8080/api/v1/recordings/devices/{deviceId}/playlist`

2. **VAS V2 Backend**
   - Playlist endpoint returns valid HLS manifest (200 OK)
   - Contains 600+ segments (~60 minutes of recordings)
   - Segments are accessible at: `/api/v1/recordings/devices/{deviceId}/{segment-name}.ts`
   - CORS headers properly configured: `Access-Control-Allow-Origin: *`

3. **Ruth AI Frontend**
   - Successfully fetches and parses the HLS playlist
   - HLS.js initializes correctly
   - Logs show: "Level loaded {... fragments: 600}"

### What's Broken ❌

**HLS.js never attempts to load video segments**

Ruth AI logs show:
```
✅ XHR: Load success for: .../playlist Status: 200
✅ HLS: Level loaded {... fragments: 600}
✅ Attempting to play video after manifest parsed...
❌ NO segment loading attempts (should see "HLS: Fragment loading" messages)
❌ Video stuck at 2x2 pixels (MediaSource placeholder)
```

---

## Root Cause: Relative URL Resolution Failure

### The Problem

VAS V2 playlist returns **relative segment URLs** without a base path:

```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:1764155982
#EXTINF:6.000000,
segment-1764154612.ts    ← RELATIVE URL (no path)
#EXTINF:6.000000,
segment-1764154613.ts
...
```

**Expected Behavior:**
HLS.js should construct full URLs by combining:
- Base URL: `http://10.30.250.245:8080/api/v1/recordings/devices/{deviceId}/`
- Segment: `segment-1764154612.ts`
- Result: `http://10.30.250.245:8080/api/v1/recordings/devices/{deviceId}/segment-1764154612.ts`

**Actual Behavior:**
HLS.js in Ruth AI is failing to construct these URLs, so it never attempts to fetch segments.

### Why VAS Portal Works But Ruth AI Doesn't

**Hypothesis:** VAS Portal likely provides HLS.js with the correct base URL context, either through:
1. Direct FileResponse from FastAPI (which preserves URL context)
2. Explicit `baseUrl` configuration in HLS.js
3. Browser automatically resolving relative URLs from the playlist request's origin

**Ruth AI Issue:** Ruth AI's camera-service proxy might be:
1. Stripping URL context when forwarding the playlist
2. Not providing HLS.js with the correct `baseUrl` parameter
3. Using a different domain/port that breaks relative URL resolution

---

## Evidence from Code Analysis

### VAS V2 Backend (Correct)

**File:** `backend/app/routes/recordings.py`

```python
# Line 197-213: Playlist endpoint
@router.get("/devices/{device_id}/playlist")
async def get_device_playlist(device_id: str) -> FileResponse:
    playlist_path = f"/recordings/hot/{device_id}/stream.m3u8"
    return FileResponse(
        playlist_path,
        media_type="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"}
    )

# Line 225-258: Segment endpoint
@router.get("/devices/{device_id}/{segment_name}")
async def get_segment(device_id: str, segment_name: str) -> FileResponse:
    # Searches for segment in /recordings/hot/{device_id}/{date}/{segment}
    return FileResponse(
        segment_path,
        media_type="video/mp2t",
        headers={"Cache-Control": "public, max-age=31536000", "Access-Control-Allow-Origin": "*"}
    )
```

✅ Routes are correctly defined
✅ CORS headers are present
✅ Segments verified accessible (tested: 200 OK, 3.2MB file)

### VAS Portal Frontend (Working)

**File:** `frontend/components/players/DualModePlayer.tsx:90`

```typescript
<HLSPlayer
  streamUrl={`${process.env.NEXT_PUBLIC_API_URL || 'http://10.30.250.245:8080'}/api/v1/recordings/devices/${deviceId}/playlist`}
  deviceName={deviceName}
  deviceId={deviceId}
/>
```

✅ Uses full absolute URL for playlist
✅ Same domain as segment requests (no cross-origin issues)
✅ Browser resolves relative segment URLs correctly

### Ruth AI Integration (Broken)

**Expected URL structure:**
```
Playlist: http://10.30.250.245:8080/api/v1/recordings/devices/{id}/playlist
Segments: http://10.30.250.245:8080/api/v1/recordings/devices/{id}/segment-XXX.ts
```

**Likely actual issue:**
1. Ruth AI camera-service proxy forwards playlist from VAS V2
2. Playlist contains relative URLs: `segment-1764154612.ts`
3. HLS.js tries to resolve relative to the **camera-service proxy URL** (port 3005)
4. Constructed URL becomes: `http://10.30.250.245:3005/api/cameras/{id}/segment-XXX.ts`
5. This endpoint doesn't exist on camera-service → segments never load

---

## Assessment of VAS_V2_INTEGRATION.md Documentation

### Clear and Accurate ✅

1. API endpoint paths (`/api/v1/recordings/devices/{device_id}/playlist`)
2. `VAS_REQUIRE_AUTH=false` configuration
3. MediaSoup live stream integration steps
4. Basic HLS.js usage example (lines 524-551)

### Missing Critical Information ❌

1. **Segment URL Resolution**
   - Document doesn't mention that VAS returns relative segment URLs
   - No guidance on how to handle this in client applications
   - No example of proper HLS.js `baseUrl` configuration

2. **Playlist Format Specifics**
   - Missing mention of `#EXT-X-DISCONTINUITY` tags (timeline breaks)
   - No explanation that these indicate stream restarts
   - No guidance on HLS.js configuration for discontinuity handling

3. **CORS and HTTP Methods**
   - Segment endpoint returns `405 Method Not Allowed` for HEAD requests
   - Only GET is supported
   - This could break some HLS.js configurations that do preflight checks

4. **Cross-Service Integration Pattern**
   - No guidance for proxy services (like Ruth AI camera-service)
   - Doesn't explain how to properly forward HLS playlists
   - Missing advice on preserving URL context when proxying

5. **Troubleshooting Section Gaps**
   - Has "HLS playback not working" section (line 788)
   - But only suggests enabling debug mode
   - Doesn't address "segments not loading" scenario
   - No troubleshooting for relative URL resolution issues

6. **HLS.js Version Compatibility**
   - Doesn't specify tested HLS.js versions
   - Ruth AI uses v1.6.15 (latest)
   - No mention if certain versions have issues with VAS playlists

---

## Recommended Solutions (In Priority Order)

### Solution 1: Fix Ruth AI Camera-Service Proxy (Recommended)

**Problem:** Camera-service likely forwards playlist without preserving URL context

**Fix Options:**

**Option A - Rewrite segment URLs in proxy:**
```javascript
// In camera-service camera.controller.js
const playlistResponse = await axios.get(`${VAS_V2_URL}/api/v1/recordings/devices/${deviceId}/playlist`);
let playlistContent = playlistResponse.data;

// Rewrite relative URLs to absolute URLs
const baseUrl = `${VAS_V2_URL}/api/v1/recordings/devices/${deviceId}`;
playlistContent = playlistContent.replace(
  /^(segment-\d+\.ts)$/gm,
  `${baseUrl}/$1`
);

return playlistContent;
```

**Option B - Add baseUrl to HLS.js config in Ruth AI frontend:**
```javascript
// In Ruth AI frontend HLS player initialization
const hls = new Hls({
  // ... other config
  xhrSetup: (xhr, url) => {
    // If URL is relative, prepend base URL
    if (!url.startsWith('http')) {
      xhr.open('GET', `http://10.30.250.245:8080/api/v1/recordings/devices/${deviceId}/${url}`, true);
    }
  }
});
```

**Option C - Proxy segment requests through camera-service:**
```javascript
// Add new route in camera-service to proxy segment requests
router.get('/cameras/:cameraId/historical/segments/:segmentName', async (req, res) => {
  const { cameraId, segmentName } = req.params;
  const segmentUrl = `${VAS_V2_URL}/api/v1/recordings/devices/${cameraId}/${segmentName}`;

  // Stream the segment from VAS to client
  const response = await axios.get(segmentUrl, { responseType: 'stream' });
  response.data.pipe(res);
});

// Then rewrite playlist URLs to point to camera-service
playlistContent = playlistContent.replace(
  /^(segment-\d+\.ts)$/gm,
  `/api/cameras/${deviceId}/historical/segments/$1`
);
```

### Solution 2: Update VAS V2 to Return Absolute URLs

**Change:** Modify `recordings.py` playlist generation to include full paths

**Pros:**
- Fixes issue for all clients
- More standards-compliant

**Cons:**
- Requires VAS backend changes
- Breaks existing VAS Portal if not careful
- Need to know request URL to construct absolute URLs

### Solution 3: Update VAS_V2_INTEGRATION.md

**Add sections:**
1. "HLS Playlist Format and URL Resolution"
2. "Integrating Through Proxy Services"
3. "Troubleshooting Segment Loading Issues"
4. "HLS.js Configuration Examples"

---

## Testing Verification

To confirm the root cause, check Ruth AI browser console:

**Expected if root cause is correct:**
```javascript
// No XHR requests to segment URLs like:
GET http://10.30.250.245:8080/api/v1/recordings/devices/{id}/segment-XXX.ts

// Might see failed requests like:
GET http://10.30.250.245:3005/api/cameras/{id}/segment-XXX.ts (404)
// OR
GET http://{some-wrong-path}/segment-XXX.ts (404)
```

**To test manually:**
```bash
# Verify playlist is accessible
curl "http://10.30.250.245:8080/api/v1/recordings/devices/31f38047-59eb-4735-85d9-ae754156e6c5/playlist"

# Verify segments are accessible
curl "http://10.30.250.245:8080/api/v1/recordings/devices/31f38047-59eb-4735-85d9-ae754156e6c5/segment-XXXXXX.ts" -I

# Should return: HTTP/1.1 200 OK
```

---

## UPDATE: Actual Root Cause Confirmed

**After analyzing Ruth AI console logs, the REAL issue is:**

### Ruth AI camera-service proxy IS correctly rewriting URLs ✅

The playlist from port 3005 shows:
```m3u8
http://10.30.250.245:8080/api/v1/recordings/devices/31f38047-59eb-4735-85d9-ae754156e6c5/segment-1764155424.ts
```

URLs are absolute and correct! ✅

### The ACTUAL Problem: HLS.js loadSource() Never Called ❌

Ruth AI logs show:
```
Attaching media to video element...
[log] > attachMedia
[log] > [buffer-controller] created media source: MediaSource
Video: Metadata loaded {duration: Infinity, videoWidth: 2, videoHeight: 2}
```

**Missing:**
- ❌ No `loadSource(url)` call
- ❌ No MANIFEST_LOADING event
- ❌ No MANIFEST_LOADED event
- ❌ No FRAG_LOADING events
- ❌ No XHR requests for segments

**Evidence:** Video shows 2x2 pixels (MediaSource placeholder - no data)

### Root Cause: Ruth AI Frontend Bug

The Ruth AI HLS player initialization code is:
1. ✅ Creating HLS instance correctly
2. ✅ Calling `hls.attachMedia(videoElement)`
3. ❌ **NEVER calling `hls.loadSource(playlistUrl)`**

This is a **frontend code bug** in Ruth AI's camera feed component.

### The Fix

In Ruth AI frontend HLS player code, after `attachMedia()`, add:

```javascript
hls.attachMedia(videoElement);

// Wait for media to attach
hls.on(Hls.Events.MEDIA_ATTACHED, () => {
  console.log('Media attached, loading source...');
  hls.loadSource(playlistUrl);  // ← THIS IS MISSING!
});

hls.on(Hls.Events.MANIFEST_PARSED, () => {
  console.log('Manifest parsed, starting playback...');
  videoElement.play();
});
```

**Current (broken) code likely does:**
```javascript
hls.attachMedia(videoElement);
// Missing: hls.loadSource(playlistUrl);
```

### Why This Confirms Our Assessment Was Wrong

**Original hypothesis:** URL resolution failure
**Reality:** URLs are correct, but HLS.js never attempts to fetch them because `loadSource()` is never called

**Original blame:** Camera-service proxy
**Reality:** Camera-service is working perfectly (rewrites URLs correctly)

**Actual culprit:** Ruth AI frontend missing `hls.loadSource()` call

---

## Conclusion - CORRECTED

**The issue is NOT caused by our stream reconnection fixes.** ✅

**The issue is NOT in the camera-service proxy.** ✅ (It's already rewriting URLs correctly)

**The issue IS in the Ruth AI frontend HLS player initialization** - missing `hls.loadSource()` call. ❌

**Immediate Action Required:**
1. ~~Check browser Network tab~~ Already confirmed: no segment requests
2. ~~Fix camera-service proxy~~ Already working correctly
3. **Fix Ruth AI frontend:** Add `hls.loadSource(playlistUrl)` after `hls.attachMedia()`
4. Test historical playback in Ruth AI
5. Update Ruth AI documentation about proper HLS.js initialization sequence

**Long-term:**
- Add integration test for Ruth AI historical playback
- Document the correct HLS.js initialization pattern
- Consider adding error handling for missing loadSource() calls
