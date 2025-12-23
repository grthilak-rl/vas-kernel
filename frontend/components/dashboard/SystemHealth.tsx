'use client';

export default function SystemHealth() {
  const services = [
    { name: 'Backend API', status: 'healthy', uptime: '99.9%' },
    { name: 'Database', status: 'healthy', uptime: '99.9%' },
    { name: 'Redis Cache', status: 'healthy', uptime: '99.9%' },
    { name: 'MediaSoup', status: 'healthy', uptime: '99.9%' },
  ];

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          System Health
        </h2>
      </div>
      <div className="p-6">
        <div className="space-y-4">
          {services.map((service) => (
            <div key={service.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  service.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm font-medium text-gray-900">
                  {service.name}
                </span>
              </div>
              <span className="text-xs text-gray-600">{service.uptime}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


