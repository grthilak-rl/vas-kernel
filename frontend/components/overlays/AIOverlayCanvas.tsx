// ============================================================================
// Phase 6.2: AI Overlay Rendering Component
// ============================================================================
// Canvas-based overlay rendering for AI detection results.
// Renders bounding boxes, labels, and confidence scores on top of video.
// Model-agnostic, time-aligned, non-blocking, fail-silent.

'use client';

import { useEffect, useRef } from 'react';
import { AIEvent } from '@/lib/api';

interface AIOverlayCanvasProps {
  /**
   * Video element to overlay on top of
   */
  videoElement: HTMLVideoElement | null;

  /**
   * AI events to render (from Phase 6.1)
   */
  events: AIEvent[];

  /**
   * Current playback timestamp for time-based filtering
   * ISO 8601 format or null for live mode
   */
  currentTimestamp?: string | null;

  /**
   * Time tolerance for event matching (milliseconds)
   * Events within ±tolerance of currentTimestamp will be displayed
   * Default: 2000ms (2 seconds)
   */
  timeTolerance?: number;

  /**
   * Optional className for styling
   */
  className?: string;
}

/**
 * Normalized detection structure for model-agnostic rendering.
 * Phase 6.2: We attempt to extract common fields from various model formats.
 */
interface NormalizedDetection {
  x: number;          // Bounding box x (0-1 normalized or pixel)
  y: number;          // Bounding box y (0-1 normalized or pixel)
  width: number;      // Bounding box width
  height: number;     // Bounding box height
  label?: string;     // Class label (e.g., "person", "car")
  confidence?: number; // Confidence score (0-1)
  isNormalized: boolean; // Whether coordinates are normalized (0-1) vs pixels
}

/**
 * Phase 6.2: AI Overlay Canvas Component
 *
 * Renders AI detection results as visual overlays on top of video streams.
 *
 * Features:
 * - Canvas-based rendering for performance
 * - Bounding boxes with labels and confidence scores
 * - Time-based filtering for historical playback
 * - Model-agnostic detection parsing
 * - Automatic resize handling
 * - Silent failure on malformed data
 * - Zero impact on video playback
 *
 * Failure Semantics:
 * - Rendering errors are caught and logged (no propagation)
 * - Malformed detections are skipped silently
 * - Missing data renders nothing (no error state)
 * - Video playback never affected
 *
 * @example
 * <AIOverlayCanvas
 *   videoElement={videoRef.current}
 *   events={aiEvents}
 *   currentTimestamp={new Date().toISOString()}
 *   timeTolerance={2000}
 * />
 */
export function AIOverlayCanvas({
  videoElement,
  events,
  currentTimestamp = null,
  timeTolerance = 2000,
  className = '',
}: AIOverlayCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);

  /**
   * Parse detection data from various model formats.
   * Phase 6.2: Best-effort extraction of bounding box data.
   *
   * Supported formats:
   * - { boxes: [{ x, y, w, h, class, confidence }] } (YOLOv8 style)
   * - { detections: [{ bbox: [x, y, w, h], label, score }] }
   * - { objects: [{ x, y, width, height, name, conf }] }
   *
   * Returns empty array for unknown formats (silent failure).
   */
  const parseDetections = (detections: Record<string, any>): NormalizedDetection[] => {
    try {
      const normalized: NormalizedDetection[] = [];

      // Format 1: { boxes: [...] } (YOLOv8 / common format)
      if (Array.isArray(detections.boxes)) {
        for (const box of detections.boxes) {
          if (typeof box === 'object' && box !== null) {
            normalized.push({
              x: box.x ?? box.left ?? 0,
              y: box.y ?? box.top ?? 0,
              width: box.w ?? box.width ?? 0,
              height: box.h ?? box.height ?? 0,
              label: box.class ?? box.label ?? box.name ?? undefined,
              confidence: box.confidence ?? box.conf ?? box.score ?? undefined,
              isNormalized: box.normalized ?? true, // Default assume normalized
            });
          }
        }
      }

      // Format 2: { detections: [{ bbox: [...], ... }] }
      if (Array.isArray(detections.detections)) {
        for (const det of detections.detections) {
          if (typeof det === 'object' && det !== null) {
            if (Array.isArray(det.bbox) && det.bbox.length >= 4) {
              normalized.push({
                x: det.bbox[0],
                y: det.bbox[1],
                width: det.bbox[2],
                height: det.bbox[3],
                label: det.label ?? det.class_name ?? undefined,
                confidence: det.score ?? det.confidence ?? undefined,
                isNormalized: det.normalized ?? true,
              });
            }
          }
        }
      }

      // Format 3: { objects: [...] }
      if (Array.isArray(detections.objects)) {
        for (const obj of detections.objects) {
          if (typeof obj === 'object' && obj !== null) {
            normalized.push({
              x: obj.x ?? obj.left ?? 0,
              y: obj.y ?? obj.top ?? 0,
              width: obj.width ?? obj.w ?? 0,
              height: obj.height ?? obj.h ?? 0,
              label: obj.name ?? obj.label ?? obj.class ?? undefined,
              confidence: obj.conf ?? obj.confidence ?? obj.score ?? undefined,
              isNormalized: obj.normalized ?? true,
            });
          }
        }
      }

      return normalized;
    } catch (err) {
      // Silent failure - log and return empty array
      console.warn('[Phase 6.2] Failed to parse detections:', err);
      return [];
    }
  };

  /**
   * Filter events by time proximity.
   * Phase 6.2: Only render events close to current playback position.
   */
  const filterEventsByTime = (events: AIEvent[]): AIEvent[] => {
    if (!currentTimestamp) {
      // Live mode: show all recent events
      return events;
    }

    try {
      const currentTime = new Date(currentTimestamp).getTime();
      return events.filter((event) => {
        try {
          const eventTime = new Date(event.timestamp).getTime();
          const diff = Math.abs(currentTime - eventTime);
          return diff <= timeTolerance;
        } catch {
          // Invalid timestamp - skip
          return false;
        }
      });
    } catch {
      // Invalid currentTimestamp - show all events
      return events;
    }
  };

  /**
   * Render overlays on canvas.
   * Phase 6.2: Draw bounding boxes, labels, and confidence scores.
   */
  const renderOverlays = () => {
    const canvas = canvasRef.current;
    const video = videoElement;

    if (!canvas || !video) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return;
    }

    try {
      // Match canvas size to video display size
      const videoRect = video.getBoundingClientRect();
      if (canvas.width !== videoRect.width || canvas.height !== videoRect.height) {
        canvas.width = videoRect.width;
        canvas.height = videoRect.height;
      }

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Filter events by time
      const relevantEvents = filterEventsByTime(events);

      if (relevantEvents.length === 0) {
        return;
      }

      // Get video natural dimensions for normalization
      const videoWidth = video.videoWidth || canvas.width;
      const videoHeight = video.videoHeight || canvas.height;
      const scaleX = canvas.width / videoWidth;
      const scaleY = canvas.height / videoHeight;

      // Render each event's detections
      for (const event of relevantEvents) {
        const detections = parseDetections(event.detections);

        for (const detection of detections) {
          let { x, y, width, height } = detection;

          // Convert normalized coordinates to pixels if needed
          if (detection.isNormalized) {
            x = x * videoWidth;
            y = y * videoHeight;
            width = width * videoWidth;
            height = height * videoHeight;
          }

          // Scale to canvas dimensions
          x *= scaleX;
          y *= scaleY;
          width *= scaleX;
          height *= scaleY;

          // Skip invalid boxes
          if (width <= 0 || height <= 0 || x < 0 || y < 0) {
            continue;
          }

          // Draw bounding box
          ctx.strokeStyle = '#00FF00'; // Green box
          ctx.lineWidth = 2;
          ctx.strokeRect(x, y, width, height);

          // Draw label background and text
          if (detection.label || detection.confidence !== undefined) {
            const labelParts: string[] = [];
            if (detection.label) {
              labelParts.push(detection.label);
            }
            if (detection.confidence !== undefined) {
              labelParts.push(`${(detection.confidence * 100).toFixed(0)}%`);
            }
            const labelText = labelParts.join(' ');

            ctx.font = '14px sans-serif';
            const textMetrics = ctx.measureText(labelText);
            const textWidth = textMetrics.width;
            const textHeight = 16;

            // Label background (black with opacity)
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(x, y - textHeight - 4, textWidth + 8, textHeight + 4);

            // Label text (white)
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(labelText, x + 4, y - 6);
          }
        }
      }
    } catch (err) {
      // Silent failure - log but don't crash
      console.warn('[Phase 6.2] Overlay rendering error:', err);
    }
  };

  /**
   * Animation loop for continuous rendering.
   * Phase 6.2: Render at ~30 FPS for smooth updates.
   */
  useEffect(() => {
    const animate = () => {
      renderOverlays();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    // Start animation loop
    animate();

    // Cleanup on unmount
    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [videoElement, events, currentTimestamp, timeTolerance]);

  /**
   * Handle window resize to update canvas dimensions.
   */
  useEffect(() => {
    const handleResize = () => {
      renderOverlays();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [videoElement]);

  if (!videoElement) {
    // No video element - don't render canvas
    return null;
  }

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none ${className}`}
      style={{ zIndex: 10 }}
    />
  );
}
