import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';
import Config from 'react-native-config';
import DeviceInfo from 'react-native-device-info';
import NetInfo from '@react-native-community/netinfo';

// API configuration
const API_BASE_URL = Config.API_BASE_URL || 'https://api.openpolicy.com';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'X-App-Version': DeviceInfo.getVersion(),
      'X-App-Build': DeviceInfo.getBuildNumber(),
      'X-Device-Id': DeviceInfo.getUniqueId(),
      'X-Platform': DeviceInfo.getSystemName(),
    },
  });

  // Request interceptor
  instance.interceptors.request.use(
    async (config) => {
      // Check network connectivity
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        throw new Error('No internet connection');
      }

      // Add auth token
      try {
        const credentials = await Keychain.getInternetCredentials('openpolicy.com');
        if (credentials) {
          config.headers.Authorization = `Bearer ${credentials.password}`;
        }
      } catch (error) {
        console.error('Failed to get auth token:', error);
      }

      // Add tenant header if available
      const tenant = await AsyncStorage.getItem('tenant');
      if (tenant) {
        config.headers['X-Tenant-ID'] = tenant;
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response) => {
      return response;
    },
    async (error) => {
      if (error.response?.status === 401) {
        // Token expired, try to refresh
        try {
          const refreshed = await refreshToken();
          if (refreshed) {
            // Retry original request
            return instance.request(error.config);
          }
        } catch (refreshError) {
          // Refresh failed, redirect to login
          await handleLogout();
        }
      }

      // Handle network errors
      if (!error.response) {
        error.message = 'Network error. Please check your connection.';
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

// Helper functions
const refreshToken = async (): Promise<boolean> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`);
    const { token } = response.data;
    
    // Update stored token
    const credentials = await Keychain.getInternetCredentials('openpolicy.com');
    if (credentials) {
      await Keychain.setInternetCredentials(
        'openpolicy.com',
        credentials.username,
        token
      );
    }
    
    return true;
  } catch (error) {
    return false;
  }
};

const handleLogout = async () => {
  await Keychain.resetInternetCredentials('openpolicy.com');
  await AsyncStorage.multiRemove(['user', 'token', 'tenant']);
  // Navigate to login screen (handled by auth context)
};

// Create API instance
export const api = createApiInstance();

// API methods
export const apiMethods = {
  // Auth
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: () => api.post('/auth/refresh'),
  
  getProfile: () => api.get('/auth/me'),
  
  updateProfile: (data: any) => api.put('/auth/profile', data),
  
  // Policies
  getPolicies: (params?: any) => api.get('/policies', { params }),
  
  getPolicy: (id: string) => api.get(`/policies/${id}`),
  
  searchPolicies: (query: string) => api.get('/policies/search', { params: { q: query } }),
  
  // Representatives
  getRepresentatives: (params?: any) => api.get('/representatives', { params }),
  
  getRepresentative: (id: string) => api.get(`/representatives/${id}`),
  
  // Votes
  getVotes: (params?: any) => api.get('/votes', { params }),
  
  getVote: (id: string) => api.get(`/votes/${id}`),
  
  // Committees
  getCommittees: (params?: any) => api.get('/committees', { params }),
  
  getCommittee: (id: string) => api.get(`/committees/${id}`),
  
  // Dashboard
  getDashboard: () => api.get('/dashboard'),
  
  // Notifications
  getNotifications: () => api.get('/notifications'),
  
  markNotificationRead: (id: string) => api.put(`/notifications/${id}/read`),
  
  updateNotificationSettings: (settings: any) => api.put('/notifications/settings', settings),
  
  // Search
  globalSearch: (query: string) => api.get('/search', { params: { q: query } }),
  
  // Analytics
  trackEvent: (event: any) => api.post('/analytics/event', event),
  
  // Files
  downloadFile: (fileId: string) => api.get(`/files/${fileId}/download`, {
    responseType: 'blob',
  }),
  
  // Offline sync
  syncOfflineData: (data: any) => api.post('/sync', data),
};

// Offline queue for requests
class OfflineQueue {
  private queue: any[] = [];
  
  async add(request: AxiosRequestConfig) {
    this.queue.push({
      ...request,
      timestamp: new Date().toISOString(),
    });
    await this.persist();
  }
  
  async process() {
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) return;
    
    const queue = [...this.queue];
    this.queue = [];
    
    for (const request of queue) {
      try {
        await api.request(request);
      } catch (error) {
        // Re-add to queue if failed
        this.queue.push(request);
      }
    }
    
    await this.persist();
  }
  
  private async persist() {
    await AsyncStorage.setItem('offline_queue', JSON.stringify(this.queue));
  }
  
  async load() {
    const data = await AsyncStorage.getItem('offline_queue');
    if (data) {
      this.queue = JSON.parse(data);
    }
  }
}

export const offlineQueue = new OfflineQueue();

// Initialize offline queue
offlineQueue.load();

// Process queue when network becomes available
NetInfo.addEventListener((state) => {
  if (state.isConnected) {
    offlineQueue.process();
  }
});