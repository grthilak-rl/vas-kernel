// ============================================================================
// Phase 6.1: Stream Player with AI Event Data Wiring
// Phase 6.2: AI Overlay Rendering Integration
// ============================================================================
// Wrapper component that combines video playback with AI event data fetching
// and overlay rendering.
// Handles mode-specific time windows, polling strategies, and visual overlays.

'use client';

import { useEffect, useState, useRef } from 'react';
import { useAIEvents } from '@/hooks/useAIEvents';
import { AIEvent } from '@/lib/api';
import DualModePlayer, { DualModePlayerRef } from '@/components/players/DualModePlayer';
import { AIOverlayCanvas } from '@/components/overlays/AIOverlayCanvas';

interface StreamWithAIDataProps {
  deviceId: string;
  deviceName: string;
  shouldConnect: boolean;
  onModeChange?: (mode: 'live' | 'historical') => void;
  playerRef?: (ref: DualModePlayerRef | null) => void;
}

/**
 * Phase 6.1: Stream player with AI event data wiring.
 * Phase 6.2: AI overlay rendering integration.
 *
 * This component:
 * - Renders the video player (DualModePlayer)
 * - Fetches AI events based on playback mode and time window (Phase 6.1)
 * - Manages polling for live mode (Phase 6.1)
 * - Handles time window calculation for historical mode (Phase 6.1)
 * - Renders AI overlays on top of video (Phase 6.2)
 *
 * Data flow:
 * 1. Player mode changes (live/historical) → update fetch strategy
 * 2. Time window changes → refetch events
 * 3. AI events fetched → passed to overlay renderer
 * 4. Overlay canvas renders bounding boxes and labels
 *
 * Failure semantics:
 * - AI fetch failures are silent (Phase 6.1)
 * - Overlay rendering failures are silent (Phase 6.2)
 * - Video playback is unaffected by AI data or rendering issues
 */
export function StreamWithAIData({
  deviceId,
  deviceName,
  shouldConnect,
  onModeChange,
  playerRef,
}: StreamWithAIDataProps) {
  const [playerMode, setPlayerMode] = useState<'live' | 'historical'>('live');
  const [timeWindow, setTimeWindow] = useState<{ start: string; end: string } | null>(null);
  const internalPlayerRef = useRef<DualModePlayerRef | null>(null);
  const [videoElement, setVideoElement] = useState<HTMLVideoElement | null>(null);

  // Phase 6.1: Fetch AI events based on player mode
  // Live mode: Rolling 30-second window with polling
  // Historical mode: Explicit time window, no polling
  const aiEventConfig = playerMode === 'live'
    ? {
        cameraId: shouldConnect ? deviceId : undefined, // Only fetch when stream is active
        enablePolling: true,
        pollingInterval: 5000, // 5 seconds
        startTime: new Date(Date.now() - 30000).toISOString(), // Last 30 seconds
        endTime: new Date().toISOString(),
        limit: 50, // Recent events only
      }
    : {
        cameraId: timeWindow ? deviceId : undefined,
        enablePolling: false,
        startTime: timeWindow?.start,
        endTime: timeWindow?.end,
        limit: 100,
      };

  const { events, loading: aiLoading, error: aiError } = useAIEvents(aiEventConfig);

  // Handle player mode changes
  const handleModeChange = (mode: 'live' | 'historical') => {
    setPlayerMode(mode);
    onModeChange?.(mode);

    // Reset time window when switching to live mode
    if (mode === 'live') {
      setTimeWindow(null);
    }
  };

  // Update time window for historical mode
  // This would be triggered by user interaction with timeline controls in Phase 6.2+
  const updateTimeWindow = (start: string, end: string) => {
    if (playerMode === 'historical') {
      setTimeWindow({ start, end });
    }
  };

  // Expose player ref to parent
  useEffect(() => {
    if (playerRef) {
      playerRef(internalPlayerRef.current);
    }
  }, [playerRef]);

  // Phase 6.2: Track video element for overlay rendering
  useEffect(() => {
    const updateVideoElement = () => {
      const video = internalPlayerRef.current?.getVideoElement();
      setVideoElement(video || null);
    };

    // Initial check
    updateVideoElement();

    // Periodic check for video element availability
    const interval = setInterval(updateVideoElement, 500);
    return () => clearInterval(interval);
  }, [shouldConnect, playerMode]);

  // Phase 6.1: Log AI event data for debugging
  useEffect(() => {
    if (events.length > 0) {
      console.log(`[Phase 6.1] AI events for ${deviceName} (${playerMode}):`, {
        count: events.length,
        latestTimestamp: events[0]?.timestamp,
        oldestTimestamp: events[events.length - 1]?.timestamp,
      });
    }
  }, [events, deviceName, playerMode]);

  // Phase 6.2: Calculate current timestamp for overlay filtering
  const getCurrentTimestamp = (): string | null => {
    if (playerMode === 'live') {
      // Live mode: use current time
      return new Date().toISOString();
    }
    // Historical mode: would use video currentTime + playlist start time
    // For now, return null to show all events in time window
    return null;
  };

  return (
    <div className="relative w-full h-full">
      <DualModePlayer
        ref={internalPlayerRef}
        deviceId={deviceId}
        deviceName={deviceName}
        shouldConnect={shouldConnect}
        onModeChange={handleModeChange}
      />
      {/* Phase 6.2: AI Overlay Rendering */}
      {videoElement && events.length > 0 && (
        <AIOverlayCanvas
          videoElement={videoElement}
          events={events}
          currentTimestamp={getCurrentTimestamp()}
          timeTolerance={2000}
        />
      )}
    </div>
  );
}
