"""
Comprehensive API Test Script
Tests all endpoints from previous projects (OpenParliament, Civic Data, OpenPolicy) and new enhanced APIs
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
    
    def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                     description: str = "", data: Dict = None) -> Dict:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        test_result = {
            "method": method,
            "endpoint": endpoint,
            "url": url,
            "description": description,
            "expected_status": expected_status,
            "actual_status": None,
            "response_time": None,
            "success": False,
            "error": None,
            "response_data": None
        }
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            test_result["response_time"] = round(time.time() - start_time, 3)
            test_result["actual_status"] = response.status_code
            test_result["success"] = response.status_code == expected_status
            
            try:
                test_result["response_data"] = response.json()
            except:
                test_result["response_data"] = response.text[:500]  # First 500 chars
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
        
        self.results["tests"].append(test_result)
        return test_result
    
    def run_basic_tests(self):
        """Test basic API functionality"""
        print("🔍 Testing Basic API Endpoints...")
        
        # Root and health endpoints
        self.test_endpoint("GET", "/", 200, "Root endpoint")
        self.test_endpoint("GET", "/health", 200, "Health check")
        self.test_endpoint("GET", "/docs", 200, "Swagger documentation")
        self.test_endpoint("GET", "/redoc", 200, "ReDoc documentation")
        self.test_endpoint("GET", "/openapi.json", 200, "OpenAPI schema")
    
    def run_legacy_openparliament_tests(self):
        """Test endpoints from OpenParliament project"""
        print("🏛️ Testing Legacy OpenParliament Endpoints...")
        
        # Parliamentary data endpoints
        self.test_endpoint("GET", "/api/v1/parliamentary/sessions", 200, "Parliamentary sessions")
        self.test_endpoint("GET", "/api/v1/parliamentary/hansard", 200, "Hansard records")
        self.test_endpoint("GET", "/api/v1/parliamentary/committees/meetings", 200, "Committee meetings")
        self.test_endpoint("GET", "/api/v1/parliamentary/search/speeches", 200, "Speech search")
        
        # Bills and votes
        self.test_endpoint("GET", "/api/v1/bills", 200, "List bills")
        self.test_endpoint("GET", "/api/v1/votes", 200, "List votes")
        self.test_endpoint("GET", "/api/v1/committees", 200, "List committees")
    
    def run_legacy_civic_data_tests(self):
        """Test endpoints from Civic Data project"""
        print("🏙️ Testing Legacy Civic Data Endpoints...")
        
        # Web endpoints (from Laravel routes)
        self.test_endpoint("GET", "/api/v1/web/bills", 200, "Web bills endpoint")
        self.test_endpoint("GET", "/api/v1/web/debate/debate-get-year", 200, "Debate years")
        self.test_endpoint("GET", "/api/v1/web/committee/committee-topics", 200, "Committee topics")
        self.test_endpoint("GET", "/api/v1/web/politician", 200, "Politicians list")
        
        # App endpoints
        self.test_endpoint("GET", "/api/v1/app/representatives/all", 200, "All representatives")
        self.test_endpoint("GET", "/api/v1/app/representatives/single", 200, "Single representative")
        self.test_endpoint("GET", "/api/v1/app/representatives/activity-link", 200, "Activity links")
    
    def run_legacy_openpolicy_tests(self):
        """Test endpoints from OpenPolicy project"""
        print("📊 Testing Legacy OpenPolicy Endpoints...")
        
        # Core data endpoints
        self.test_endpoint("GET", "/api/v1/jurisdictions", 200, "Jurisdictions")
        self.test_endpoint("GET", "/api/v1/representatives", 200, "Representatives")
        self.test_endpoint("GET", "/api/v1/events", 200, "Events")
        self.test_endpoint("GET", "/api/v1/stats", 200, "Statistics")
        
        # GraphQL endpoint
        self.test_endpoint("POST", "/graphql", 200, "GraphQL endpoint", {"query": "{ __schema { types { name } } }"})
        
        # AI features
        self.test_endpoint("POST", "/api/v1/ai/federal-briefing", 200, "Federal briefing")
    
    def run_enhanced_api_tests(self):
        """Test new enhanced API endpoints"""
        print("🚀 Testing Enhanced API Endpoints...")
        
        # Health and monitoring
        self.test_endpoint("GET", "/api/v1/health", 200, "API health")
        self.test_endpoint("GET", "/api/v1/health/detailed", 200, "Detailed health")
        self.test_endpoint("GET", "/api/v1/health/database", 200, "Database health")
        self.test_endpoint("GET", "/api/v1/health/system", 200, "System health")
        
        # Authentication
        self.test_endpoint("POST", "/api/v1/auth/login", 200, "Login endpoint", {"username": "test", "password": "test"})
        self.test_endpoint("POST", "/api/v1/auth/register", 200, "Register endpoint", {"username": "test", "email": "test@test.com", "password": "test123"})
        self.test_endpoint("GET", "/api/v1/auth/users", 200, "Users list")
        
        # Policies
        self.test_endpoint("GET", "/api/v1/policies", 200, "Policies list")
        self.test_endpoint("GET", "/api/v1/policies/search/advanced", 200, "Advanced policy search")
        self.test_endpoint("GET", "/api/v1/policies/categories", 200, "Policy categories")
        self.test_endpoint("GET", "/api/v1/policies/stats", 200, "Policy statistics")
        
        # Scrapers
        self.test_endpoint("GET", "/api/v1/scrapers", 200, "Scrapers list")
        self.test_endpoint("GET", "/api/v1/scrapers/categories", 200, "Scraper categories")
        self.test_endpoint("POST", "/api/v1/scrapers/run/category/municipal", 200, "Run municipal scrapers")
        self.test_endpoint("GET", "/api/v1/scrapers/performance", 200, "Scraper performance")
        
        # Admin
        self.test_endpoint("GET", "/api/v1/admin/dashboard", 200, "Admin dashboard")
        self.test_endpoint("GET", "/api/v1/admin/system/status", 200, "System status")
        self.test_endpoint("GET", "/api/v1/admin/logs", 200, "System logs")
        self.test_endpoint("GET", "/api/v1/admin/performance", 200, "System performance")
        self.test_endpoint("GET", "/api/v1/admin/alerts", 200, "System alerts")
    
    def run_new_feature_tests(self):
        """Test new features and endpoints"""
        print("🆕 Testing New Feature Endpoints...")
        
        # Scraper Monitoring
        self.test_endpoint("GET", "/api/v1/scraper-monitoring/status", 200, "Scraper monitoring status")
        self.test_endpoint("GET", "/api/v1/scraper-monitoring/health", 200, "Scraper monitoring health")
        self.test_endpoint("GET", "/api/v1/scraper-monitoring/stats", 200, "Scraper monitoring stats")
        self.test_endpoint("POST", "/api/v1/scraper-monitoring/run", 200, "Run scraper monitoring")
        
        # Data Management
        self.test_endpoint("GET", "/api/v1/data-management/tables", 200, "Database tables")
        self.test_endpoint("GET", "/api/v1/data-management/analysis/politicians", 200, "Politician analysis")
        self.test_endpoint("GET", "/api/v1/data-management/analysis/bills", 200, "Bill analysis")
        self.test_endpoint("GET", "/api/v1/data-management/analysis/hansards", 200, "Hansard analysis")
        self.test_endpoint("GET", "/api/v1/data-management/database/size", 200, "Database size")
        
        # Dashboard
        self.test_endpoint("GET", "/api/v1/dashboard/overview", 200, "Dashboard overview")
        self.test_endpoint("GET", "/api/v1/dashboard/system", 200, "Dashboard system metrics")
        self.test_endpoint("GET", "/api/v1/dashboard/scrapers", 200, "Dashboard scraper metrics")
        self.test_endpoint("GET", "/api/v1/dashboard/database", 200, "Dashboard database metrics")
        self.test_endpoint("GET", "/api/v1/dashboard/alerts", 200, "Dashboard alerts")
        self.test_endpoint("GET", "/api/v1/dashboard/recent-activity", 200, "Dashboard recent activity")
        self.test_endpoint("GET", "/api/v1/dashboard/performance", 200, "Dashboard performance")
    
    def run_error_handling_tests(self):
        """Test error handling and edge cases"""
        print("⚠️ Testing Error Handling...")
        
        # 404 tests
        self.test_endpoint("GET", "/api/v1/nonexistent", 404, "Non-existent endpoint")
        self.test_endpoint("GET", "/api/v1/policies/999999", 404, "Non-existent policy")
        
        # Authentication tests
        self.test_endpoint("GET", "/api/v1/admin/dashboard", 401, "Unauthorized admin access")
        
        # Invalid data tests
        self.test_endpoint("POST", "/api/v1/auth/login", 422, "Invalid login data", {})
        self.test_endpoint("POST", "/api/v1/policies", 422, "Invalid policy data", {})
    
    def run_performance_tests(self):
        """Test API performance"""
        print("⚡ Testing Performance...")
        
        # Test response times for key endpoints
        endpoints = [
            ("/health", "Health check"),
            ("/api/v1/health", "API health"),
            ("/api/v1/policies", "Policies list"),
            ("/api/v1/representatives", "Representatives list"),
            ("/api/v1/scrapers", "Scrapers list")
        ]
        
        for endpoint, description in endpoints:
            self.test_endpoint("GET", endpoint, 200, f"Performance test: {description}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive API Testing...")
        print(f"📍 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Run all test suites
        self.run_basic_tests()
        self.run_legacy_openparliament_tests()
        self.run_legacy_civic_data_tests()
        self.run_legacy_openpolicy_tests()
        self.run_enhanced_api_tests()
        self.run_new_feature_tests()
        self.run_error_handling_tests()
        self.run_performance_tests()
        
        # Calculate summary
        self.calculate_summary()
        self.print_summary()
        self.save_results()
    
    def calculate_summary(self):
        """Calculate test summary"""
        total = len(self.results["tests"])
        passed = sum(1 for test in self.results["tests"] if test["success"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(success_rate, 2)
        }
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE API TEST SUMMARY")
        print("=" * 60)
        
        summary = self.results["summary"]
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Timestamp: {self.results['timestamp']}")
        print(f"📈 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📊 Success Rate: {summary['success_rate']}%")
        
        # Print failed tests
        failed_tests = [test for test in self.results["tests"] if not test["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['method']} {test['endpoint']} - {test['description']}")
                print(f"    Expected: {test['expected_status']}, Got: {test['actual_status']}")
                if test['error']:
                    print(f"    Error: {test['error']}")
                print()
        
        # Print performance summary
        response_times = [test['response_time'] for test in self.results["tests"] if test['response_time']]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"⚡ Performance Summary:")
            print(f"  • Average Response Time: {avg_time:.3f}s")
            print(f"  • Maximum Response Time: {max_time:.3f}s")
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {filename}")

def main():
    """Main function to run comprehensive API tests"""
    print("🔍 Open Policy Platform - Comprehensive API Testing")
    print("=" * 60)
    
    # Test API server
    base_url = "http://localhost:8000"
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API server is running at {base_url}")
        else:
            print(f"⚠️ API server responded with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API server is not accessible at {base_url}")
        print(f"   Error: {e}")
        print("\n💡 Please ensure the API server is running:")
        print("   cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # Run comprehensive tests
    tester = ComprehensiveAPITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
