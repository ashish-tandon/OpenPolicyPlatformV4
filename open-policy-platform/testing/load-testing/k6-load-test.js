import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";

// Custom metrics
const errorRate = new Rate('errors');
const successRate = new Rate('success');

// Test configuration
export const options = {
  // Test stages - ramp up to 10K users
  stages: [
    { duration: '2m', target: 100 },    // Warm up
    { duration: '5m', target: 1000 },   // Ramp to 1K users
    { duration: '10m', target: 5000 },  // Ramp to 5K users
    { duration: '20m', target: 10000 }, // Ramp to 10K users
    { duration: '10m', target: 10000 }, // Stay at 10K users
    { duration: '5m', target: 0 },      // Ramp down
  ],
  
  // Thresholds
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.05'],                  // Error rate under 5%
    errors: ['rate<0.05'],                            // Custom error rate under 5%
    success: ['rate>0.95'],                           // Success rate over 95%
  },
  
  // Additional options
  noConnectionReuse: false,
  userAgent: 'OpenPolicyPlatform-LoadTest/1.0',
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:9000';
const API_TOKEN = __ENV.API_TOKEN || '';

// User scenarios
const scenarios = {
  // Scenario 1: Browse policies
  browsePolicy: (userId) => {
    const params = {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'BrowsePolicies' },
    };
    
    // Homepage
    let res = http.get(`${BASE_URL}/`, params);
    check(res, {
      'homepage status 200': (r) => r.status === 200,
      'homepage response time < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(res.status !== 200);
    successRate.add(res.status === 200);
    sleep(1);
    
    // Search policies
    res = http.get(`${BASE_URL}/api/policies?search=healthcare&limit=20`, params);
    check(res, {
      'policy search status 200': (r) => r.status === 200,
      'policy search has results': (r) => JSON.parse(r.body).results.length > 0,
    });
    sleep(2);
    
    // View policy details
    const policies = JSON.parse(res.body).results;
    if (policies.length > 0) {
      const policyId = policies[Math.floor(Math.random() * policies.length)].id;
      res = http.get(`${BASE_URL}/api/policies/${policyId}`, params);
      check(res, {
        'policy detail status 200': (r) => r.status === 200,
      });
    }
    sleep(1);
  },
  
  // Scenario 2: API interactions
  apiInteraction: (userId) => {
    const params = {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'APIInteraction' },
    };
    
    // Get representatives
    let res = http.get(`${BASE_URL}/api/representatives?limit=50`, params);
    check(res, {
      'representatives API status 200': (r) => r.status === 200,
      'representatives API response time < 1s': (r) => r.timings.duration < 1000,
    });
    errorRate.add(res.status !== 200);
    successRate.add(res.status === 200);
    sleep(0.5);
    
    // Get bills
    res = http.get(`${BASE_URL}/api/bills?status=active&limit=20`, params);
    check(res, {
      'bills API status 200': (r) => r.status === 200,
    });
    sleep(0.5);
    
    // Get analytics data
    res = http.get(`${BASE_URL}/api/analytics/summary`, params);
    check(res, {
      'analytics API status 200': (r) => r.status === 200,
    });
    sleep(1);
  },
  
  // Scenario 3: Dashboard usage
  dashboardUsage: (userId) => {
    const params = {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'Dashboard' },
    };
    
    // Login
    let res = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
      username: `testuser${userId}@example.com`,
      password: 'testpass123'
    }), params);
    
    if (res.status === 200) {
      const token = JSON.parse(res.body).token;
      params.headers['Authorization'] = `Bearer ${token}`;
      
      // Dashboard data
      res = http.get(`${BASE_URL}/api/dashboard/stats`, params);
      check(res, {
        'dashboard stats status 200': (r) => r.status === 200,
      });
      sleep(1);
      
      // Recent activities
      res = http.get(`${BASE_URL}/api/dashboard/activities`, params);
      check(res, {
        'dashboard activities status 200': (r) => r.status === 200,
      });
      sleep(2);
    }
  },
  
  // Scenario 4: Search intensive
  searchIntensive: (userId) => {
    const params = {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'Search' },
    };
    
    const searchTerms = ['healthcare', 'education', 'climate', 'budget', 'tax', 'infrastructure'];
    
    for (let i = 0; i < 3; i++) {
      const term = searchTerms[Math.floor(Math.random() * searchTerms.length)];
      const res = http.get(`${BASE_URL}/api/search?q=${term}&type=all`, params);
      
      check(res, {
        'search status 200': (r) => r.status === 200,
        'search response time < 2s': (r) => r.timings.duration < 2000,
      });
      errorRate.add(res.status !== 200);
      successRate.add(res.status === 200);
      
      sleep(Math.random() * 2 + 1); // Random sleep 1-3 seconds
    }
  },
  
  // Scenario 5: Real-time updates (WebSocket simulation)
  realtimeUpdates: (userId) => {
    const params = {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'Realtime' },
    };
    
    // Poll for updates
    for (let i = 0; i < 10; i++) {
      const res = http.get(`${BASE_URL}/api/notifications/poll?userId=${userId}`, params);
      check(res, {
        'notification poll status 200': (r) => r.status === 200,
      });
      sleep(5); // Poll every 5 seconds
    }
  },
};

// Main test function
export default function () {
  const userId = Math.floor(Math.random() * 100000);
  const scenarioChoice = Math.random();
  
  // Distribute load across scenarios
  if (scenarioChoice < 0.3) {
    scenarios.browsePolicy(userId);
  } else if (scenarioChoice < 0.5) {
    scenarios.apiInteraction(userId);
  } else if (scenarioChoice < 0.7) {
    scenarios.dashboardUsage(userId);
  } else if (scenarioChoice < 0.9) {
    scenarios.searchIntensive(userId);
  } else {
    scenarios.realtimeUpdates(userId);
  }
}

// Generate HTML report
export function handleSummary(data) {
  return {
    "load-test-report.html": htmlReport(data),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
  };
}

// Setup function - create test users
export function setup() {
  console.log('Setting up load test...');
  console.log(`Testing against: ${BASE_URL}`);
  console.log(`Target: 10,000 concurrent users`);
  
  // Create test data if needed
  const setupParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  // You can add setup logic here if needed
  
  return {
    baseUrl: BASE_URL,
    startTime: new Date().toISOString(),
  };
}

// Teardown function
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Started at: ${data.startTime}`);
  console.log(`Ended at: ${new Date().toISOString()}`);
}