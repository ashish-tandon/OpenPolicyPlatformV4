import React, { useEffect, useState } from 'react';
import api from '../../api/axios';
import { 
  UserGroupIcon,
  DocumentTextIcon,
  UsersIcon,
  HandRaisedIcon,
  CalendarIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

type EntityType = 'representatives' | 'bills' | 'committees' | 'votes' | 'events';

type ApiList<T> = {
  items: T[];
  count: number;
  limit: number;
  offset: number;
};

interface EntityStats {
  total: number;
  lastUpdated?: string;
  newThisWeek?: number;
  jurisdiction?: {
    federal: number;
    provincial: number;
    municipal: number;
  };
}

interface FilterOptions {
  jurisdiction?: string;
  status?: string;
  dateRange?: string;
  party?: string;
}

const AdminEntities: React.FC = () => {
  const [type, setType] = useState<EntityType>('representatives');
  const [items, setItems] = useState<any[]>([]);
  const [limit, setLimit] = useState<number>(25);
  const [offset, setOffset] = useState<number>(0);
  const [q, setQ] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Record<EntityType, EntityStats>>({
    representatives: { total: 0 },
    bills: { total: 0 },
    committees: { total: 0 },
    votes: { total: 0 },
    events: { total: 0 }
  });
  const [filters, setFilters] = useState<FilterOptions>({});
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchData();
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, limit, offset]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit, offset };
      if (q) params.q = q;
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });

      const res = await api.get(`/api/v1/entities/${type}`, { params });
      const data = res.data as ApiList<any>;
      setItems(data.items || []);
      
      // Update total count
      setStats(prev => ({
        ...prev,
        [type]: { ...prev[type], total: data.count || prev[type].total }
      }));
    } catch (e: any) {
      setError(e?.message || 'Failed to load entities');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    // Fetch statistics for the current entity type
    try {
      const res = await api.get(`/api/v1/entities/${type}/stats`);
      setStats(prev => ({
        ...prev,
        [type]: res.data
      }));
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  };

  const exportData = async () => {
    try {
      const params = { type, format: 'csv', ...filters };
      if (selectedItems.size > 0) {
        params.ids = Array.from(selectedItems).join(',');
      }
      
      const res = await api.get('/api/v1/entities/export', { 
        params,
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_export_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      console.error('Export failed:', e);
      alert('Failed to export data');
    }
  };

  const nextPage = () => setOffset(offset + limit);
  const prevPage = () => setOffset(Math.max(0, offset - limit));

  const toggleSelectItem = (id: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    if (selectedItems.size === items.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(items.map(item => item.id)));
    }
  };

  const getEntityIcon = (entityType: EntityType) => {
    switch (entityType) {
      case 'representatives':
        return <UserGroupIcon className="h-5 w-5" />;
      case 'bills':
        return <DocumentTextIcon className="h-5 w-5" />;
      case 'committees':
        return <UsersIcon className="h-5 w-5" />;
      case 'votes':
        return <HandRaisedIcon className="h-5 w-5" />;
      case 'events':
        return <CalendarIcon className="h-5 w-5" />;
    }
  };

  const columns = () => {
    switch (type) {
      case 'representatives':
        return ['id', 'name', 'party', 'district', 'email', 'phone', 'jurisdiction'];
      case 'bills':
        return ['id', 'title', 'classification', 'session', 'status', 'sponsor'];
      case 'committees':
        return ['id', 'name', 'classification', 'chair', 'members_count'];
      case 'votes':
        return ['id', 'bill_id', 'member', 'vote', 'date'];
      case 'events':
        return ['id', 'title', 'date', 'location', 'type'];
      default:
        return [];
    }
  };

  const getFilterOptions = () => {
    switch (type) {
      case 'representatives':
        return (
          <>
            <select 
              className="border rounded px-2 py-1"
              value={filters.jurisdiction || ''}
              onChange={(e) => setFilters({ ...filters, jurisdiction: e.target.value })}
            >
              <option value="">All Jurisdictions</option>
              <option value="federal">Federal</option>
              <option value="provincial">Provincial</option>
              <option value="municipal">Municipal</option>
            </select>
            <select 
              className="border rounded px-2 py-1"
              value={filters.party || ''}
              onChange={(e) => setFilters({ ...filters, party: e.target.value })}
            >
              <option value="">All Parties</option>
              <option value="liberal">Liberal</option>
              <option value="conservative">Conservative</option>
              <option value="ndp">NDP</option>
              <option value="bloc">Bloc Québécois</option>
              <option value="green">Green</option>
              <option value="independent">Independent</option>
            </select>
          </>
        );
      case 'bills':
        return (
          <>
            <select 
              className="border rounded px-2 py-1"
              value={filters.status || ''}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All Status</option>
              <option value="introduced">Introduced</option>
              <option value="committee">In Committee</option>
              <option value="passed">Passed</option>
              <option value="defeated">Defeated</option>
            </select>
            <select 
              className="border rounded px-2 py-1"
              value={filters.dateRange || ''}
              onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
            >
              <option value="">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="year">This Year</option>
            </select>
          </>
        );
      default:
        return null;
    }
  };

  const currentStats = stats[type];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Data Management</h1>
          <p className="text-sm text-gray-600 mt-1">Browse and manage platform entities</p>
        </div>

        {/* Entity Type Selector */}
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {(['representatives', 'bills', 'committees', 'votes', 'events'] as EntityType[]).map((entityType) => (
              <button
                key={entityType}
                onClick={() => {
                  setType(entityType);
                  setOffset(0);
                  setSelectedItems(new Set());
                }}
                className={`flex items-center justify-center space-x-2 p-3 rounded-lg transition-colors ${
                  type === entityType 
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-300' 
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-2 border-transparent'
                }`}
              >
                {getEntityIcon(entityType)}
                <span className="font-medium capitalize">{entityType}</span>
                <span className="text-sm text-gray-500">({stats[entityType].total})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Stats Cards */}
        {currentStats && (
          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total {type}</p>
                  <p className="text-2xl font-semibold text-gray-900">{currentStats.total.toLocaleString()}</p>
                </div>
                <ChartBarIcon className="h-8 w-8 text-gray-400" />
              </div>
            </div>
            {currentStats.newThisWeek !== undefined && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">New This Week</p>
                    <p className="text-2xl font-semibold text-green-600">+{currentStats.newThisWeek}</p>
                  </div>
                  <ArrowPathIcon className="h-8 w-8 text-green-400" />
                </div>
              </div>
            )}
            {currentStats.jurisdiction && (
              <>
                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">By Jurisdiction</p>
                  <div className="space-y-1 text-sm">
                    <p>Federal: <span className="font-semibold">{currentStats.jurisdiction.federal}</span></p>
                    <p>Provincial: <span className="font-semibold">{currentStats.jurisdiction.provincial}</span></p>
                    <p>Municipal: <span className="font-semibold">{currentStats.jurisdiction.municipal}</span></p>
                  </div>
                </div>
              </>
            )}
            {currentStats.lastUpdated && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Last Updated</p>
                    <p className="text-sm text-gray-900">{new Date(currentStats.lastUpdated).toLocaleString()}</p>
                  </div>
                  <InformationCircleIcon className="h-8 w-8 text-blue-400" />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search and Filters */}
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input 
                value={q} 
                onChange={(e) => setQ(e.target.value)} 
                placeholder={`Search ${type}...`}
                onKeyDown={(e) => e.key === 'Enter' && fetchData()}
                className="pl-10 pr-3 py-2 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" 
              />
            </div>
            
            <div className="flex gap-2 items-center">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              {getFilterOptions()}
              
              <select 
                className="border rounded px-2 py-1" 
                value={limit} 
                onChange={(e) => { setOffset(0); setLimit(parseInt(e.target.value)); }}
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
                <option value={100}>100 per page</option>
              </select>
              
              <button 
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center space-x-2" 
                onClick={() => { setOffset(0); fetchData(); }}
              >
                <MagnifyingGlassIcon className="h-4 w-4" />
                <span>Search</span>
              </button>
              
              <button
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 flex items-center space-x-2"
                onClick={() => {
                  setQ('');
                  setFilters({});
                  setOffset(0);
                  fetchData();
                }}
              >
                <ArrowPathIcon className="h-4 w-4" />
                <span>Reset</span>
              </button>
            </div>
          </div>
        </div>

        {/* Actions Bar */}
        {selectedItems.size > 0 && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
            <span className="text-sm text-blue-700">
              {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={exportData}
                className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 flex items-center space-x-1"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Export Selected</span>
              </button>
              <button
                onClick={() => setSelectedItems(new Set())}
                className="text-sm bg-gray-200 text-gray-700 px-3 py-1 rounded hover:bg-gray-300"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <ArrowPathIcon className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Loading {type}...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={items.length > 0 && selectedItems.size === items.length}
                        onChange={selectAll}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </th>
                    {columns().map((col) => (
                      <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {col.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {items.map((item, idx) => (
                    <tr key={item.id || idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedItems.has(item.id)}
                          onChange={() => toggleSelectItem(item.id)}
                          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        />
                      </td>
                      {columns().map((col) => (
                        <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {col === 'status' && item[col] ? (
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              item[col] === 'active' || item[col] === 'passed' ? 'bg-green-100 text-green-800' :
                              item[col] === 'inactive' || item[col] === 'defeated' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {item[col]}
                            </span>
                          ) : col === 'date' && item[col] ? (
                            new Date(item[col]).toLocaleDateString()
                          ) : (
                            String(item?.[col] ?? '')
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={columns().length + 1} className="px-6 py-8 text-center text-gray-500">
                        No {type} found matching your criteria
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {offset + 1} to {Math.min(offset + limit, currentStats.total)} of {currentStats.total} {type}
          </div>
          <div className="flex items-center gap-2">
            <button 
              disabled={offset === 0} 
              onClick={prevPage} 
              className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {Math.floor(offset / limit) + 1} of {Math.ceil(currentStats.total / limit)}
            </span>
            <button 
              disabled={offset + limit >= currentStats.total}
              onClick={nextPage} 
              className="px-3 py-1 rounded bg-gray-200 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
            >
              Next
            </button>
          </div>
        </div>

        {/* Export Options */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={exportData}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            <span>Export All {type}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminEntities;