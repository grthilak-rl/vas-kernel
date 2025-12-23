'use client';

import { useState, useRef, useImperativeHandle, forwardRef, useEffect } from 'react';
import MediaSoupPlayer from './MediaSoupPlayer';
import dynamic from 'next/dynamic';

const HLSPlayer = dynamic(() => import('./HLSPlayer'), { ssr: false });

interface DualModePlayerProps {
  deviceId: string;
  deviceName: string;
  shouldConnect?: boolean;
  onLog?: (message: string) => void;
  onModeChange?: (mode: 'live' | 'historical') => void;
  selectedDate?: string | null;
  startTime?: string;
  endTime?: string;
}

export interface DualModePlayerRef {
  getMode: () => 'live' | 'historical';
  getVideoElement: () => HTMLVideoElement | null;
}

type StreamMode = 'live' | 'historical';

const DualModePlayer = forwardRef<DualModePlayerRef, DualModePlayerProps>(
  ({ deviceId, deviceName, shouldConnect = false, onLog, onModeChange, selectedDate: initialSelectedDate, startTime: initialStartTime = '00:00', endTime: initialEndTime = '23:59' }, ref) => {
    const [mode, setMode] = useState<StreamMode>('live');
    const hlsPlayerRef = useRef<any>(null);

    // Date/time selection state
    const [selectedDate, setSelectedDate] = useState<string | null>(initialSelectedDate || null);
    const [startTime, setStartTime] = useState<string>(initialStartTime);
    const [endTime, setEndTime] = useState<string>(initialEndTime);
    const [recordingDates, setRecordingDates] = useState<Array<{date: string, formatted: string, segments_count: number}>>([]);

    const handleModeChange = (newMode: StreamMode) => {
      setMode(newMode);
      if (onModeChange) {
        onModeChange(newMode);
      }
    };

    // Fetch available recording dates when in historical mode
    useEffect(() => {
      if (mode === 'historical' && deviceId) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://10.30.250.245:8080';
        fetch(`${apiUrl}/api/v1/recordings/devices/${deviceId}/dates`)
          .then(res => res.json())
          .then(data => {
            if (data.dates) {
              setRecordingDates(data.dates);
            }
          })
          .catch(err => console.error('Failed to fetch recording dates:', err));
      }
    }, [mode, deviceId]);

    useImperativeHandle(ref, () => ({
      getMode: () => mode,
      getVideoElement: () => hlsPlayerRef.current?.getVideoElement() || null,
    }));

  return (
    <div className="relative w-full h-full">
      {/* Mode selector */}
      <div className="absolute top-4 left-4 z-20 flex gap-2">
        <button
          onClick={() => handleModeChange('live')}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            mode === 'live'
              ? 'bg-red-600 text-white shadow-lg'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          <div className="flex items-center gap-2">
            {mode === 'live' && (
              <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
            )}
            LIVE
          </div>
        </button>

        <button
          onClick={() => handleModeChange('historical')}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            mode === 'historical'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            Historical
          </div>
        </button>
      </div>

      {/* Date/Time Selection Controls - Only show in historical mode */}
      {mode === 'historical' && recordingDates.length > 0 && (
        <div className="absolute top-20 left-4 z-30 bg-black bg-opacity-90 rounded-lg p-3 shadow-lg">
          <div className="flex flex-col gap-2">
            {/* Date selector */}
            <div className="flex gap-2 items-center">
              <label className="text-white text-sm font-medium min-w-[40px]">Date:</label>
              <select
                value={selectedDate || ''}
                onChange={(e) => setSelectedDate(e.target.value || null)}
                className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Live Buffer (24h)</option>
                {recordingDates.map(date => (
                  <option key={date.date} value={date.date}>
                    {date.formatted} ({date.segments_count} segments)
                  </option>
                ))}
              </select>
            </div>

            {/* Time range selector - Only show when a specific date is selected */}
            {selectedDate && (
              <div className="flex gap-2 items-center">
                <label className="text-white text-sm font-medium min-w-[40px]">Time:</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="bg-gray-800 text-white px-2 py-1 rounded text-sm border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
                <span className="text-white text-sm">to</span>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="bg-gray-800 text-white px-2 py-1 rounded text-sm border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}

            {/* Quick select buttons */}
            <div className="flex gap-1 mt-1">
              <button
                onClick={() => {
                  const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
                  setSelectedDate(today);
                  setStartTime('00:00');
                  setEndTime('23:59');
                }}
                className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
              >
                Today
              </button>
              <button
                onClick={() => {
                  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0].replace(/-/g, '');
                  setSelectedDate(yesterday);
                  setStartTime('00:00');
                  setEndTime('23:59');
                }}
                className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
              >
                Yesterday
              </button>
              <button
                onClick={() => setSelectedDate(null)}
                className="px-2 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700 transition-colors"
              >
                Live Buffer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Player based on mode */}
      <div className="w-full h-full">
        {mode === 'live' ? (
          <MediaSoupPlayer
            roomId={deviceId}
            mediasoupUrl="ws://10.30.250.245:8080/ws/mediasoup"
            shouldConnect={shouldConnect}
            onLog={onLog}
          />
        ) : (
          <HLSPlayer
            ref={hlsPlayerRef}
            streamUrl={`${process.env.NEXT_PUBLIC_API_URL || 'http://10.30.250.245:8080'}/api/v1/recordings/devices/${deviceId}/playlist${
              selectedDate ? `?date=${selectedDate}&start_time=${startTime}:00&end_time=${endTime}:59` : ''
            }`}
            deviceName={deviceName}
            deviceId={deviceId}
            hideControls={true}
          />
        )}
      </div>
    </div>
  );
});

DualModePlayer.displayName = 'DualModePlayer';

export default DualModePlayer;
