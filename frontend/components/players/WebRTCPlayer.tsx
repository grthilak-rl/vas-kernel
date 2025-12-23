'use client';

import { useEffect, useRef, useState } from 'react';

interface WebRTCPlayerProps {
  streamId: string;
  signalingUrl: string;
}

export default function WebRTCPlayer({ streamId, signalingUrl }: WebRTCPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState<string>('Connecting...');
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);

  useEffect(() => {
    if (!videoRef.current) return;

    const connectWebRTC = async () => {
      try {
        setStatus('Connecting to signaling server...');
        
        // Create WebSocket connection
        const ws = new WebSocket(`${signalingUrl}/${streamId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus('Connected to signaling server');
          ws.send(JSON.stringify({ type: 'connect' }));
        };

        ws.onmessage = async (event) => {
          const message = JSON.parse(event.data);
          
          if (message.type === 'connected') {
            setStatus('Negotiating WebRTC connection...');
            
            // Create peer connection (mock implementation)
            const pc = new RTCPeerConnection({
              iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });
            pcRef.current = pc;

            pc.ontrack = (event) => {
              if (videoRef.current) {
                videoRef.current.srcObject = event.streams[0];
                setStatus('Streaming');
              }
            };

            pc.onicecandidate = (event) => {
              if (event.candidate) {
                ws.send(JSON.stringify({
                  type: 'ice_candidate',
                  candidate: event.candidate
                }));
              }
            };

            // For demo purposes, this is a simplified implementation
            // Real implementation would handle offer/answer exchange
            setStatus('Waiting for stream...');
          } else if (message.type === 'room_info') {
            setStatus(`Room: ${message.connections} connections`);
          }
        };

        ws.onerror = (error) => {
          setError('WebSocket connection error');
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          setStatus('Disconnected');
        };

      } catch (err) {
        console.error('WebRTC setup error:', err);
        setError('Failed to setup WebRTC connection');
      }
    };

    connectWebRTC();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pcRef.current) {
        pcRef.current.close();
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [streamId, signalingUrl]);

  return (
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-contain"
      />
      
      {/* Status overlay */}
      <div className="absolute top-4 left-4 bg-black bg-opacity-75 text-white px-4 py-2 rounded-lg">
        <div className="text-sm font-medium">{status}</div>
        {error && (
          <div className="text-xs text-red-400 mt-1">{error}</div>
        )}
      </div>

      {/* Placeholder when no stream */}
      {!error && status !== 'Streaming' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-center">
            <div className="animate-pulse">
              <svg className="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
              <p className="text-lg">{status}</p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-900 bg-opacity-50">
          <div className="text-white text-center">
            <p className="text-lg font-bold mb-2">Connection Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}


