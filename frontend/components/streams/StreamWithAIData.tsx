// ============================================================================
// Phase 6.1: Stream Player with AI Event Data Wiring
// ============================================================================
// Wrapper component that combines video playback with AI event data fetching.
// Handles mode-specific time windows and polling strategies.
// No rendering of overlays - pure data wiring only.

'use client';

import { useEffect, useState, useRef } from 'react';
import { useAIEvents } from '@/hooks/useAIEvents';
import { AIEvent } from '@/lib/api';
import DualModePlayer, { DualModePlayerRef } from '@/components/players/DualModePlayer';

interface StreamWithAIDataProps {
  deviceId: string;
  deviceName: string;
  shouldConnect: boolean;
  onModeChange?: (mode: 'live' | 'historical') => void;
  playerRef?: (ref: DualModePlayerRef | null) => void;
}

/**
 * Phase 6.1: Stream player with AI event data wiring.
 *
 * This component:
 * - Renders the video player (DualModePlayer)
 * - Fetches AI events based on playback mode and time window
 * - Manages polling for live mode
 * - Handles time window calculation for historical mode
 * - DOES NOT render overlays (Phase 6.2)
 *
 * Data flow:
 * 1. Player mode changes (live/historical) → update fetch strategy
 * 2. Time window changes → refetch events
 * 3. AI events fetched → stored in state (ready for Phase 6.2)
 *
 * Failure semantics:
 * - AI fetch failures are silent
 * - Video playback is unaffected by AI data availability
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

  // Phase 6.1: Log AI event data for debugging
  // In Phase 6.2, this data will be passed to overlay renderer
  useEffect(() => {
    if (events.length > 0) {
      console.log(`[Phase 6.1] AI events for ${deviceName} (${playerMode}):`, {
        count: events.length,
        latestTimestamp: events[0]?.timestamp,
        oldestTimestamp: events[events.length - 1]?.timestamp,
      });
    }
  }, [events, deviceName, playerMode]);

  return (
    <DualModePlayer
      ref={internalPlayerRef}
      deviceId={deviceId}
      deviceName={deviceName}
      shouldConnect={shouldConnect}
      onModeChange={handleModeChange}
      // Phase 6.1: AI events are fetched but not yet used for rendering
      // Phase 6.2 will add overlay rendering based on this data
    />
  );
}
