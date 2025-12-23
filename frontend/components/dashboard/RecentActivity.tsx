'use client';

export default function RecentActivity() {
  const activities = [
    { action: 'Stream Started', stream: 'Main Entrance Camera', time: '2 minutes ago', icon: '▶️' },
    { action: 'Recording Stopped', stream: 'Parking Lot Camera', time: '15 minutes ago', icon: '⏹️' },
    { action: 'Snapshot Captured', stream: 'Back Door Camera', time: '32 minutes ago', icon: '📸' },
    { action: 'Device Added', stream: 'Camera-12', time: '1 hour ago', icon: '➕' },
    { action: 'Stream Started', stream: 'Reception Camera', time: '2 hours ago', icon: '▶️' },
  ];

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Activity
          </h2>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All
          </button>
        </div>
      </div>
      <div className="p-6">
        <div className="flow-root">
          <ul className="-mb-8">
            {activities.map((activity, index) => (
              <li key={index}>
                <div className="relative pb-8">
                  {index !== activities.length - 1 && (
                    <span className="absolute left-4 top-8 -ml-px h-full w-0.5 bg-gray-200" />
                  )}
                  <div className="relative flex items-start space-x-3">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-lg">
                      {activity.icon}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          {activity.action}
                        </p>
                        <p className="text-xs text-gray-500">{activity.time}</p>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {activity.stream}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}


