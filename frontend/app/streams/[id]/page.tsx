'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import WebRTCPlayer from '@/components/players/WebRTCPlayer';
import { getDevices, Device, startStream } from '@/lib/api';
import { useAIEvents } from '@/hooks/useAIEvents';

export default function StreamViewPage() {
  const params = useParams();
  const router = useRouter();
  const deviceId = params.id as string;
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 6.1: Fetch AI events for this stream (live mode only, with polling)
  const { events: aiEvents, loading: aiLoading, error: aiError } = useAIEvents({
    cameraId: device?.is_active ? deviceId : undefined, // Only fetch when stream is active
    enablePolling: true,
    pollingInterval: 5000, // 5 seconds
    startTime: new Date(Date.now() - 30000).toISOString(), // Last 30 seconds
    endTime: new Date().toISOString(),
    limit: 50,
  });

  useEffect(() => {
    // Fetch device details
    const fetchDevice = async () => {
      try {
        const devices = await getDevices();
        const foundDevice = devices.find(d => d.id === deviceId);
        if (!foundDevice) {
          setError('Device not found');
          return;
        }
        setDevice(foundDevice);
      } catch (err: any) {
        console.error('Failed to fetch device:', err);
        setError(err.message || 'Failed to load device');
      } finally {
        setLoading(false);
      }
    };

    fetchDevice();
  }, [deviceId]);

  // Phase 6.1: Log AI events for debugging (data wiring demonstration)
  useEffect(() => {
    if (aiEvents.length > 0) {
      console.log(`[Phase 6.1] AI events for device ${deviceId}:`, {
        count: aiEvents.length,
        latestTimestamp: aiEvents[0]?.timestamp,
        events: aiEvents.slice(0, 3), // Log first 3 events
      });
    }
  }, [aiEvents, deviceId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading device...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !device) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error || 'Device not found'}</p>
          <button
            onClick={() => router.push('/devices')}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            ← Back to Devices
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <button
            onClick={() => router.push('/devices')}
            className="text-gray-600 hover:text-gray-900 mb-2 inline-flex items-center"
          >
            ← Back to Devices
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{device.name}</h1>
          <p className="mt-2 text-gray-600">Live video stream</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="aspect-video w-full bg-gray-900 rounded-lg overflow-hidden mb-6">
          <WebRTCPlayer
            streamId={deviceId}
            signalingUrl="ws://10.30.250.245:8080/ws/signaling"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-2 text-gray-900">Device Details</h3>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-800 font-medium">Device Name</dt>
                <dd className="text-sm font-medium text-gray-900">{device.name}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-800 font-medium">RTSP URL</dt>
                <dd className="text-sm font-mono text-gray-900">{device.rtsp_url}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-800 font-medium">Status</dt>
                <dd className="text-sm font-medium capitalize">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    device.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {device.is_active ? 'Active' : 'Inactive'}
                  </span>
                </dd>
              </div>
            </dl>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2 text-gray-900">Controls</h3>
            <div className="space-y-2">
              <button
                onClick={() => router.push('/devices')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Manage Devices
              </button>
            </div>
          </div>
        </div>

        {/* Phase 6.1: AI Event Data Status (debug panel) */}
        {device.is_active && (
          <div className="mt-6 border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">AI Event Data (Phase 6.1)</h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">AI Events Fetched:</span>
                <span className="font-mono font-medium text-gray-900">
                  {aiEvents.length} events
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Polling Status:</span>
                <span className="inline-flex items-center">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></span>
                  <span className="text-gray-900">Active (5s interval)</span>
                </span>
              </div>
              {aiEvents.length > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Latest Event:</span>
                  <span className="font-mono text-xs text-gray-700">
                    {new Date(aiEvents[0].timestamp).toLocaleString()}
                  </span>
                </div>
              )}
              <div className="text-xs text-gray-500 mt-3 italic">
                Phase 6.1: Data wiring complete. Overlay rendering in Phase 6.2.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


