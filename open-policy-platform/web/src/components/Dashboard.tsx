import React, { useEffect, useState } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface DashboardData {
  system_status: string;
  database_status: string;
  scraper_status: string;
  api_status: string;
  total_records: number;
  active_scrapers: number;
  success_rate: number;
  last_update: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
  };
  active_processes: number;
  uptime: string;
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch dashboard overview
        const dashboardResponse = await fetch('/api/v1/dashboard/overview');
        if (dashboardResponse.ok) {
          const dashboard = await dashboardResponse.json();
          setDashboardData(dashboard);
        }

        // Fetch system metrics
        const systemResponse = await fetch('/api/v1/dashboard/system');
        if (systemResponse.ok) {
          const system = await systemResponse.json();
          setSystemMetrics(system);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl font-semibold mb-2">Error Loading Dashboard</div>
          <div className="text-gray-600">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">System Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Real-time monitoring and system status
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-3 ${
                dashboardData?.system_status === 'healthy' ? 'bg-green-500' : 
                dashboardData?.system_status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">System Status</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {dashboardData?.system_status || 'Unknown'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-3 ${
                dashboardData?.database_status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">Database Status</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {dashboardData?.database_status || 'Unknown'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-3 ${
                dashboardData?.scraper_status === 'active' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">Scraper Status</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {dashboardData?.scraper_status || 'Unknown'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-3 ${
                dashboardData?.api_status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-600">API Status</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {dashboardData?.api_status || 'Unknown'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* System Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">System Metrics</h2>
            {systemMetrics && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">CPU Usage</span>
                  <span className="font-semibold">{systemMetrics.cpu_usage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${systemMetrics.cpu_usage}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Memory Usage</span>
                  <span className="font-semibold">{systemMetrics.memory_usage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${systemMetrics.memory_usage}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Disk Usage</span>
                  <span className="font-semibold">{systemMetrics.disk_usage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-600 h-2 rounded-full"
                    style={{ width: `${systemMetrics.disk_usage}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Active Processes</span>
                  <span className="font-semibold">{systemMetrics.active_processes}</span>
                </div>
              </div>
            )}
          </div>

          {/* Data Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Metrics</h2>
            {dashboardData && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total Records</span>
                  <span className="font-semibold">{dashboardData.total_records.toLocaleString()}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Active Scrapers</span>
                  <span className="font-semibold">{dashboardData.active_scrapers}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Success Rate</span>
                  <span className="font-semibold">{dashboardData.success_rate.toFixed(1)}%</span>
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${dashboardData.success_rate}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Last Update</span>
                  <span className="font-semibold">
                    {new Date(dashboardData.last_update).toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
