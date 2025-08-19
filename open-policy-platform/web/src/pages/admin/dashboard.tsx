import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import { 
  ChartBarIcon, 
  ServerIcon, 
  DatabaseIcon, 
  UserGroupIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface DashboardStats {
  totalPolicies: number;
  totalScrapers: number;
  activeScrapers: number;
  totalBills: number;
  totalRepresentatives: number;
  totalVotes: number;
  totalCommittees: number;
  newBillsThisWeek: number;
  lastUpdate: string;
}

interface ContainerStatus {
  container_id: string;
  name: string;
  status: string;
  exit_code?: number;
  created: string;
  last_updated: string;
  restart_count: number;
  health_status?: string;
}

interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  active_processes: number;
  uptime: string;
}

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  endpoint: string;
  latency?: number;
  lastCheck: string;
}

interface Alert {
  type: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
}

const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalPolicies: 0,
    totalScrapers: 0,
    activeScrapers: 0,
    totalBills: 0,
    totalRepresentatives: 0,
    totalVotes: 0,
    totalCommittees: 0,
    newBillsThisWeek: 0,
    lastUpdate: new Date().toISOString()
  });
  const [containers, setContainers] = useState<ContainerStatus[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 30 seconds
    const interval = autoRefresh ? setInterval(fetchAllData, 30000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchDashboardStats(),
        fetchContainerStatus(),
        fetchSystemMetrics(),
        fetchServiceStatus(),
        fetchAlerts()
      ]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/v1/admin/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  };

  const fetchContainerStatus = async () => {
    try {
      const response = await fetch('http://localhost:8001/containers/status');
      if (response.ok) {
        const data = await response.json();
        setContainers(data.containers || []);
      }
    } catch (error) {
      console.error('Failed to fetch container status:', error);
    }
  };

  const fetchSystemMetrics = async () => {
    try {
      const response = await fetch('/api/v1/admin/system/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSystemMetrics(data.system);
      }
    } catch (error) {
      console.error('Failed to fetch system metrics:', error);
    }
  };

  const fetchServiceStatus = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/overview');
      if (response.ok) {
        const data = await response.json();
        // Transform the data into service status format
        const serviceList: ServiceStatus[] = [
          {
            name: 'API',
            status: data.system_status?.api === 'healthy' ? 'healthy' : 'unhealthy',
            endpoint: 'http://localhost:8000',
            latency: data.performance_metrics?.api_response_time,
            lastCheck: new Date().toISOString()
          },
          {
            name: 'Database',
            status: data.system_status?.database === 'connected' ? 'healthy' : 'unhealthy',
            endpoint: 'PostgreSQL',
            lastCheck: new Date().toISOString()
          },
          {
            name: 'Redis',
            status: data.system_status?.redis === 'connected' ? 'healthy' : 'unhealthy',
            endpoint: 'Redis Cache',
            lastCheck: new Date().toISOString()
          },
          {
            name: 'Scrapers',
            status: data.scraper_status?.active_scrapers > 0 ? 'healthy' : 'degraded',
            endpoint: 'Scraper Service',
            lastCheck: new Date().toISOString()
          }
        ];
        setServices(serviceList);
      }
    } catch (error) {
      console.error('Failed to fetch service status:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/admin/alerts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'exited':
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />;
      default:
        return <CheckCircleIcon className="h-5 w-5 text-blue-600" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Admin Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center space-x-2 px-3 py-1 rounded ${
                  autoRefresh ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}
              >
                <ArrowPathIcon className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                <span className="text-sm">{autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}</span>
              </button>
              <span className="text-sm text-gray-700">
                Welcome, {user?.username}
              </span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="mb-6">
            <div className="bg-white shadow rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">System Alerts</h3>
              <div className="space-y-2">
                {alerts.slice(0, 5).map((alert, index) => (
                  <div key={index} className="flex items-start space-x-3 p-2 rounded-lg bg-gray-50">
                    {getAlertIcon(alert.type)}
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{alert.message}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* System Metrics */}
        {systemMetrics && (
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">CPU Usage</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {systemMetrics.cpu_percent.toFixed(1)}%
                  </p>
                </div>
                <ServerIcon className="h-8 w-8 text-gray-400" />
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.cpu_percent > 80 ? 'bg-red-600' : 
                    systemMetrics.cpu_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${systemMetrics.cpu_percent}%` }}
                />
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Memory Usage</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {systemMetrics.memory_percent.toFixed(1)}%
                  </p>
                </div>
                <ChartBarIcon className="h-8 w-8 text-gray-400" />
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.memory_percent > 80 ? 'bg-red-600' : 
                    systemMetrics.memory_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${systemMetrics.memory_percent}%` }}
                />
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Disk Usage</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {systemMetrics.disk_percent.toFixed(1)}%
                  </p>
                </div>
                <DatabaseIcon className="h-8 w-8 text-gray-400" />
              </div>
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.disk_percent > 80 ? 'bg-red-600' : 
                    systemMetrics.disk_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                  }`}
                  style={{ width: `${systemMetrics.disk_percent}%` }}
                />
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">System Uptime</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {systemMetrics.uptime}
                  </p>
                </div>
                <ClockIcon className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
        )}

        {/* Database Stats */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Bills</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalBills}</p>
                <p className="text-xs text-green-600">+{stats.newBillsThisWeek} this week</p>
              </div>
              <DatabaseIcon className="h-8 w-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Representatives</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalRepresentatives}</p>
              </div>
              <UserGroupIcon className="h-8 w-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Votes</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalVotes}</p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Committees</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalCommittees}</p>
              </div>
              <UserGroupIcon className="h-8 w-8 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Services Status */}
        <div className="mb-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Service Status</h3>
            <div className="space-y-3">
              {services.map((service, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <div className={`h-3 w-3 rounded-full ${
                      service.status === 'healthy' ? 'bg-green-500' :
                      service.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{service.name}</p>
                      <p className="text-xs text-gray-500">{service.endpoint}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${getStatusColor(service.status).split(' ')[0]}`}>
                      {service.status.toUpperCase()}
                    </p>
                    {service.latency && (
                      <p className="text-xs text-gray-500">{service.latency}ms</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex space-x-2">
              <a 
                href="/docs" 
                target="_blank" 
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                API Documentation →
              </a>
              <a 
                href="http://localhost:5555" 
                target="_blank" 
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Celery Monitor →
              </a>
            </div>
          </div>

          {/* Container Status */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Docker Containers</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {containers.map((container, index) => (
                <div key={index} className="flex items-center justify-between p-2 rounded bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <div className={`h-2 w-2 rounded-full ${
                      container.status === 'running' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{container.name}</p>
                      <p className="text-xs text-gray-500">
                        Restarts: {container.restart_count} | 
                        {container.health_status && ` Health: ${container.health_status}`}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(container.status)}`}>
                    {container.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scrapers Overview */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Scrapers Overview</h3>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Active: {stats.activeScrapers}/{stats.totalScrapers}
              </span>
              <a 
                href="/admin/scrapers" 
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Manage Scrapers →
              </a>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Last Update</p>
              <p className="text-sm text-gray-900">
                {new Date(stats.lastUpdate).toLocaleString()}
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Total Policies</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalPolicies}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">Data Sources</p>
              <p className="text-sm text-gray-900">Federal, Provincial, Municipal</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <a href="/admin/scrapers" className="bg-white shadow rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h4 className="font-medium text-gray-900">Manage Scrapers</h4>
            <p className="text-sm text-gray-500">Schedule and monitor</p>
          </a>
          <a href="/admin/system" className="bg-white shadow rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h4 className="font-medium text-gray-900">System Settings</h4>
            <p className="text-sm text-gray-500">Configure platform</p>
          </a>
          <a href="/admin/entities" className="bg-white shadow rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h4 className="font-medium text-gray-900">Data Management</h4>
            <p className="text-sm text-gray-500">Browse entities</p>
          </a>
          <a href="/admin/users" className="bg-white shadow rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h4 className="font-medium text-gray-900">User Management</h4>
            <p className="text-sm text-gray-500">Manage access</p>
          </a>
          <a href="http://localhost:3000" target="_blank" className="bg-white shadow rounded-lg p-4 hover:shadow-lg transition-shadow">
            <h4 className="font-medium text-gray-900">Grafana Dashboard</h4>
            <p className="text-sm text-gray-500">View metrics</p>
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;