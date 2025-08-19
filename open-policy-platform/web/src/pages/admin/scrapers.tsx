import React, { useState, useEffect } from 'react';
import { 
  PlayIcon, 
  PauseIcon, 
  ArrowPathIcon, 
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CalendarIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

interface Scraper {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'running' | 'error';
  lastRun: string;
  nextRun?: string;
  schedule: string;
  source: string;
  jurisdiction: string;
  successRate: number;
  recordsCollected: number;
  errors: number;
  runtime?: number;
}

interface ScraperConfig {
  scraperId: string;
  schedule: string;
  enabled: boolean;
  params: Record<string, any>;
}

interface ScraperRun {
  id: string;
  scraperId: string;
  status: 'success' | 'failed' | 'running';
  startTime: string;
  endTime?: string;
  recordsScraped: number;
  errors: number;
  logs?: string[];
}

const AdminScrapers: React.FC = () => {
  const [scrapers, setScrapers] = useState<Scraper[]>([]);
  const [selectedScraper, setSelectedScraper] = useState<Scraper | null>(null);
  const [scraperRuns, setScraperRuns] = useState<ScraperRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [scraperConfig, setScraperConfig] = useState<ScraperConfig | null>(null);

  // Mock data for scrapers
  const mockScrapers: Scraper[] = [
    {
      id: 'federal_parliament',
      name: 'Federal Parliament Scraper',
      description: 'Scrapes bills, votes, and MP data from parliament.gc.ca',
      status: 'active',
      lastRun: new Date(Date.now() - 3600000).toISOString(),
      nextRun: new Date(Date.now() + 3600000).toISOString(),
      schedule: '0 */6 * * *',
      source: 'parliament.gc.ca',
      jurisdiction: 'Federal',
      successRate: 98.5,
      recordsCollected: 15234,
      errors: 2,
      runtime: 245
    },
    {
      id: 'openparliament',
      name: 'OpenParliament API',
      description: 'Syncs historic federal data and votes from OpenParliament',
      status: 'running',
      lastRun: new Date(Date.now() - 7200000).toISOString(),
      schedule: '0 0 * * *',
      source: 'openparliament.ca',
      jurisdiction: 'Federal',
      successRate: 99.8,
      recordsCollected: 98765,
      errors: 0,
      runtime: 180
    },
    {
      id: 'provincial_ontario',
      name: 'Ontario Legislature Scraper',
      description: 'Collects bills and MPP data from Ontario Legislative Assembly',
      status: 'inactive',
      lastRun: new Date(Date.now() - 86400000).toISOString(),
      schedule: '0 2 * * *',
      source: 'ola.org',
      jurisdiction: 'Provincial',
      successRate: 95.2,
      recordsCollected: 5432,
      errors: 5,
      runtime: 120
    },
    {
      id: 'civic_scraper',
      name: 'Municipal Council Scraper',
      description: 'Aggregates municipal council data from various cities',
      status: 'error',
      lastRun: new Date(Date.now() - 172800000).toISOString(),
      schedule: '0 3 * * 1',
      source: 'Multiple Sources',
      jurisdiction: 'Municipal',
      successRate: 87.3,
      recordsCollected: 3210,
      errors: 15,
      runtime: 420
    },
    {
      id: 'opennorth_api',
      name: 'Open North Represent API',
      description: 'Syncs current representative data from Represent API',
      status: 'active',
      lastRun: new Date(Date.now() - 1800000).toISOString(),
      nextRun: new Date(Date.now() + 1800000).toISOString(),
      schedule: '*/30 * * * *',
      source: 'represent.opennorth.ca',
      jurisdiction: 'All',
      successRate: 100,
      recordsCollected: 45678,
      errors: 0,
      runtime: 60
    }
  ];

  useEffect(() => {
    fetchScrapers();
    // Simulate real-time updates
    const interval = setInterval(fetchScrapers, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchScrapers = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/v1/scrapers');
      // const data = await response.json();
      
      // Using mock data for now
      setScrapers(mockScrapers);
      
      // Fetch scraper runs if a scraper is selected
      if (selectedScraper) {
        await fetchScraperRuns(selectedScraper.id);
      }
    } catch (error) {
      console.error('Failed to fetch scrapers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScraperRuns = async (scraperId: string) => {
    try {
      // Mock scraper runs
      const mockRuns: ScraperRun[] = [
        {
          id: '1',
          scraperId,
          status: 'success',
          startTime: new Date(Date.now() - 3600000).toISOString(),
          endTime: new Date(Date.now() - 3300000).toISOString(),
          recordsScraped: 234,
          errors: 0
        },
        {
          id: '2',
          scraperId,
          status: 'failed',
          startTime: new Date(Date.now() - 7200000).toISOString(),
          endTime: new Date(Date.now() - 7000000).toISOString(),
          recordsScraped: 180,
          errors: 5,
          logs: ['Connection timeout', 'Retry failed', 'Rate limit exceeded']
        }
      ];
      setScraperRuns(mockRuns);
    } catch (error) {
      console.error('Failed to fetch scraper runs:', error);
    }
  };

  const runScraper = async (scraperId: string) => {
    try {
      const response = await fetch(`/api/v1/scrapers/${scraperId}/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        // Update scraper status
        setScrapers(prev => prev.map(s => 
          s.id === scraperId ? { ...s, status: 'running' } : s
        ));
        
        // Show success message
        alert('Scraper started successfully');
      }
    } catch (error) {
      console.error('Failed to run scraper:', error);
      alert('Failed to start scraper');
    }
  };

  const stopScraper = async (scraperId: string) => {
    try {
      const response = await fetch(`/api/v1/scrapers/${scraperId}/stop`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        setScrapers(prev => prev.map(s => 
          s.id === scraperId ? { ...s, status: 'inactive' } : s
        ));
      }
    } catch (error) {
      console.error('Failed to stop scraper:', error);
    }
  };

  const updateScraperConfig = async (config: ScraperConfig) => {
    try {
      const response = await fetch(`/api/v1/scrapers/${config.scraperId}/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        setConfigModalOpen(false);
        fetchScrapers();
      }
    } catch (error) {
      console.error('Failed to update scraper config:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'running':
        return <ArrowPathIcon className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-600" />;
      default:
        return <PauseIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatSchedule = (cron: string) => {
    // Simple cron description
    if (cron === '0 */6 * * *') return 'Every 6 hours';
    if (cron === '0 0 * * *') return 'Daily at midnight';
    if (cron === '0 2 * * *') return 'Daily at 2 AM';
    if (cron === '0 3 * * 1') return 'Weekly on Monday at 3 AM';
    if (cron === '*/30 * * * *') return 'Every 30 minutes';
    return cron;
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Scrapers Management</h1>
          <p className="text-sm text-gray-600 mt-1">Monitor and control data collection scrapers</p>
        </div>

        {/* Scrapers Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm font-medium text-gray-500">Total Scrapers</p>
            <p className="text-2xl font-semibold text-gray-900">{scrapers.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm font-medium text-gray-500">Active</p>
            <p className="text-2xl font-semibold text-green-600">
              {scrapers.filter(s => s.status === 'active' || s.status === 'running').length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm font-medium text-gray-500">With Errors</p>
            <p className="text-2xl font-semibold text-red-600">
              {scrapers.filter(s => s.status === 'error').length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm font-medium text-gray-500">Success Rate</p>
            <p className="text-2xl font-semibold text-gray-900">
              {(scrapers.reduce((sum, s) => sum + s.successRate, 0) / scrapers.length).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Scrapers List */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">All Scrapers</h3>
            <div className="space-y-4">
              {scrapers.map((scraper) => (
                <div 
                  key={scraper.id} 
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedScraper(scraper)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(scraper.status)}
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{scraper.name}</h4>
                        <p className="text-xs text-gray-500">{scraper.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(scraper.status)}`}>
                        {scraper.status.toUpperCase()}
                      </span>
                      {scraper.status === 'active' || scraper.status === 'inactive' ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            scraper.status === 'active' ? stopScraper(scraper.id) : runScraper(scraper.id);
                          }}
                          className="p-1 rounded hover:bg-gray-200"
                        >
                          {scraper.status === 'active' ? <PauseIcon className="h-4 w-4" /> : <PlayIcon className="h-4 w-4" />}
                        </button>
                      ) : null}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setScraperConfig({
                            scraperId: scraper.id,
                            schedule: scraper.schedule,
                            enabled: scraper.status === 'active',
                            params: {}
                          });
                          setConfigModalOpen(true);
                        }}
                        className="p-1 rounded hover:bg-gray-200"
                      >
                        <Cog6ToothIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-6 gap-2 text-xs">
                    <div>
                      <p className="text-gray-500">Source</p>
                      <p className="font-medium">{scraper.source}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Jurisdiction</p>
                      <p className="font-medium">{scraper.jurisdiction}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Schedule</p>
                      <p className="font-medium">{formatSchedule(scraper.schedule)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Last Run</p>
                      <p className="font-medium">{new Date(scraper.lastRun).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Success Rate</p>
                      <p className="font-medium text-green-600">{scraper.successRate}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Records</p>
                      <p className="font-medium">{scraper.recordsCollected.toLocaleString()}</p>
                    </div>
                  </div>

                  {scraper.nextRun && (
                    <div className="mt-2 flex items-center text-xs text-gray-500">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      Next run: {new Date(scraper.nextRun).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scraper Details Modal */}
        {selectedScraper && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">{selectedScraper.name}</h3>
                  <button
                    onClick={() => setSelectedScraper(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircleIcon className="h-6 w-6" />
                  </button>
                </div>
              </div>
              
              <div className="px-6 py-4">
                {/* Scraper Info */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Status</p>
                    <div className="flex items-center space-x-2 mt-1">
                      {getStatusIcon(selectedScraper.status)}
                      <span className={`text-sm ${getStatusColor(selectedScraper.status).split(' ')[0]}`}>
                        {selectedScraper.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Schedule</p>
                    <p className="text-sm text-gray-900 mt-1">{formatSchedule(selectedScraper.schedule)}</p>
                    <p className="text-xs text-gray-500">({selectedScraper.schedule})</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Success Rate</p>
                    <p className="text-sm text-gray-900 mt-1">{selectedScraper.successRate}%</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Average Runtime</p>
                    <p className="text-sm text-gray-900 mt-1">{selectedScraper.runtime}s</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3 mb-6">
                  <button
                    onClick={() => runScraper(selectedScraper.id)}
                    disabled={selectedScraper.status === 'running'}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    <PlayIcon className="h-4 w-4" />
                    <span>Run Now</span>
                  </button>
                  <button
                    onClick={() => {
                      setScraperConfig({
                        scraperId: selectedScraper.id,
                        schedule: selectedScraper.schedule,
                        enabled: selectedScraper.status === 'active',
                        params: {}
                      });
                      setConfigModalOpen(true);
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    <Cog6ToothIcon className="h-4 w-4" />
                    <span>Configure</span>
                  </button>
                  {selectedScraper.status === 'running' && (
                    <button
                      onClick={() => stopScraper(selectedScraper.id)}
                      className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      <PauseIcon className="h-4 w-4" />
                      <span>Stop</span>
                    </button>
                  )}
                </div>

                {/* Recent Runs */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Runs</h4>
                  <div className="space-y-2">
                    {scraperRuns.map((run) => (
                      <div key={run.id} className="border rounded p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {run.status === 'success' ? (
                              <CheckCircleIcon className="h-4 w-4 text-green-600" />
                            ) : run.status === 'failed' ? (
                              <XCircleIcon className="h-4 w-4 text-red-600" />
                            ) : (
                              <ArrowPathIcon className="h-4 w-4 text-blue-600 animate-spin" />
                            )}
                            <span className="text-sm font-medium">
                              {new Date(run.startTime).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">
                            {run.recordsScraped} records • {run.errors} errors
                          </div>
                        </div>
                        {run.logs && run.logs.length > 0 && (
                          <div className="mt-2 text-xs text-red-600">
                            {run.logs.map((log, i) => (
                              <p key={i}>• {log}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Configuration Modal */}
        {configModalOpen && scraperConfig && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">Configure Scraper</h3>
              </div>
              <div className="px-6 py-4">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Schedule (Cron Expression)</label>
                    <input
                      type="text"
                      value={scraperConfig.schedule}
                      onChange={(e) => setScraperConfig({ ...scraperConfig, schedule: e.target.value })}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                    <p className="mt-1 text-xs text-gray-500">e.g., "0 */6 * * *" for every 6 hours</p>
                  </div>
                  <div>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={scraperConfig.enabled}
                        onChange={(e) => setScraperConfig({ ...scraperConfig, enabled: e.target.checked })}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-700">Enable automatic scheduling</span>
                    </label>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 border-t flex justify-end space-x-3">
                <button
                  onClick={() => setConfigModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={() => updateScraperConfig(scraperConfig)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Save Configuration
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminScrapers;