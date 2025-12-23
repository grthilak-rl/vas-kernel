'use client';

export default function StatsGrid() {
  const stats = [
    {
      name: 'Total Cameras',
      value: '12',
      change: '+2',
      changeType: 'positive',
      icon: '📹',
    },
    {
      name: 'Active Streams',
      value: '8',
      change: '+3',
      changeType: 'positive',
      icon: '▶️',
    },
    {
      name: 'Storage Used',
      value: '2.4 TB',
      change: '45%',
      changeType: 'neutral',
      icon: '💾',
    },
    {
      name: 'Recordings',
      value: '342',
      change: '+18',
      changeType: 'positive',
      icon: '🎬',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.name} className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-3xl">{stat.icon}</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                      stat.changeType === 'positive' ? 'text-green-600' : 
                      stat.changeType === 'negative' ? 'text-red-600' : 
                      'text-gray-600'
                    }`}>
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}


