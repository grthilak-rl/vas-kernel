'use client';

export default function ActiveStreams() {
  const streams = [
    {
      id: 'stream_001',
      name: 'Main Entrance Camera',
      device: 'Camera-01',
      status: 'active',
      viewers: 5,
      quality: '1080p',
      fps: 30,
      bandwidth: '2.4 Mbps',
      duration: '2h 34m',
    },
    {
      id: 'stream_002',
      name: 'Parking Lot Camera',
      device: 'Camera-02',
      status: 'active',
      viewers: 3,
      quality: '720p',
      fps: 25,
      bandwidth: '1.8 Mbps',
      duration: '4h 12m',
    },
    {
      id: 'stream_003',
      name: 'Back Door Camera',
      device: 'Camera-03',
      status: 'active',
      viewers: 1,
      quality: '720p',
      fps: 20,
      bandwidth: '1.5 Mbps',
      duration: '1h 23m',
    },
  ];

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Active Streams
          </h2>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All
          </button>
        </div>
      </div>
      <div className="p-6">
        <div className="space-y-4">
          {streams.map((stream) => (
            <div
              key={stream.id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="flex-shrink-0">
                  <div className="relative">
                    <div className="w-16 h-12 bg-gray-300 rounded flex items-center justify-center overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 opacity-20"></div>
                      <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {stream.name}
                  </p>
                  <p className="text-xs text-gray-500">{stream.device}</p>
                  <div className="flex items-center space-x-3 mt-1">
                    <span className="text-xs text-gray-600">
                      👥 {stream.viewers} viewers
                    </span>
                    <span className="text-xs text-gray-600">
                      ⏱️ {stream.duration}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <p className="text-xs text-gray-500">Quality</p>
                  <p className="text-sm font-medium text-gray-900">{stream.quality}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">FPS</p>
                  <p className="text-sm font-medium text-gray-900">{stream.fps}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Bandwidth</p>
                  <p className="text-sm font-medium text-gray-900">{stream.bandwidth}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


