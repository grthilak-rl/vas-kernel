import StatsGrid from "@/components/dashboard/StatsGrid";
import RecentActivity from "@/components/dashboard/RecentActivity";
import ActiveStreams from "@/components/dashboard/ActiveStreams";
import SystemHealth from "@/components/dashboard/SystemHealth";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of your video streaming system
        </p>
      </div>

      {/* Statistics Grid */}
      <StatsGrid />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Streams */}
        <div className="lg:col-span-2">
          <ActiveStreams />
        </div>

        {/* System Health */}
        <div>
          <SystemHealth />
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <RecentActivity />
      </div>
    </div>
  );
}


