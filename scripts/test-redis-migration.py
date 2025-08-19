#!/usr/bin/env python3
"""
Redis Migration Testing Script
OpenPolicyPlatform V4 - Test Redis migration functionality
"""

import os
import sys
import time
import json
import redis
from typing import Dict, Any, Optional

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from redis_migration import RedisMigrationManager
except ImportError:
    print("Error: Could not import RedisMigrationManager. Make sure redis_migration.py is in the config directory.")
    sys.exit(1)

class RedisMigrationTester:
    """Test Redis migration functionality"""
    
    def __init__(self):
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'total_tests': 0,
            'test_details': []
        }
        
        # Test data
        self.test_data = {
            'string_key': 'test_string_value',
            'number_key': '42',
            'json_key': json.dumps({'name': 'test', 'value': 123}),
            'large_key': 'x' * 1000,  # 1KB data
            'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?'
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """Log test results"""
        self.results['total_tests'] += 1
        
        if passed:
            self.results['tests_passed'] += 1
            status = "✅ PASSED"
        else:
            self.results['tests_failed'] += 1
            status = "❌ FAILED"
        
        test_result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'duration': f"{duration:.2f}ms"
        }
        
        self.results['test_details'].append(test_result)
        
        print(f"{status} {test_name} ({duration:.2f}ms)")
        if details:
            print(f"   Details: {details}")
    
    def test_redis_connection(self) -> bool:
        """Test basic Redis connection"""
        test_name = "Redis Connection Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            health = redis_manager.ping()
            
            duration = (time.time() - start_time) * 1000
            
            if health['overall_status'] == 'healthy':
                self.log_test(test_name, True, f"Overall status: {health['overall_status']}", duration)
                return True
            else:
                self.log_test(test_name, False, f"Health check failed: {health}", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def test_basic_operations(self) -> bool:
        """Test basic Redis operations (SET, GET, DELETE)"""
        test_name = "Basic Operations Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            
            # Test SET operation
            success = redis_manager.set("test_basic", "test_value", ex=60)
            if not success:
                self.log_test(test_name, False, "SET operation failed")
                return False
            
            # Test GET operation
            value = redis_manager.get("test_basic")
            if value != "test_value":
                self.log_test(test_name, False, f"GET operation failed. Expected: test_value, Got: {value}")
                return False
            
            # Test DELETE operation
            deleted = redis_manager.delete("test_basic")
            if deleted != 1:
                self.log_test(test_name, False, f"DELETE operation failed. Expected: 1, Got: {deleted}")
                return False
            
            # Verify deletion
            value = redis_manager.get("test_basic")
            if value is not None:
                self.log_test(test_name, False, "Value still exists after deletion")
                return False
            
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, True, "All basic operations successful", duration)
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def test_data_types(self) -> bool:
        """Test different data types and sizes"""
        test_name = "Data Types Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            all_passed = True
            
            for key, value in self.test_data.items():
                # Set value
                success = redis_manager.set(f"test_{key}", value, ex=60)
                if not success:
                    print(f"   Failed to set {key}")
                    all_passed = False
                    continue
                
                # Get value
                retrieved = redis_manager.get(f"test_{key}")
                if retrieved != value:
                    print(f"   Value mismatch for {key}. Expected: {value[:50]}..., Got: {retrieved[:50] if retrieved else None}...")
                    all_passed = False
                    continue
                
                # Clean up
                redis_manager.delete(f"test_{key}")
            
            duration = (time.time() - start_time) * 1000
            
            if all_passed:
                self.log_test(test_name, True, "All data types tested successfully", duration)
                return True
            else:
                self.log_test(test_name, False, "Some data type tests failed", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def test_performance(self) -> bool:
        """Test Redis performance with multiple operations"""
        test_name = "Performance Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            operations = 100
            successful_operations = 0
            
            # Test SET operations
            for i in range(operations):
                success = redis_manager.set(f"perf_test_{i}", f"value_{i}", ex=60)
                if success:
                    successful_operations += 1
            
            # Test GET operations
            for i in range(operations):
                value = redis_manager.get(f"perf_test_{i}")
                if value == f"value_{i}":
                    successful_operations += 1
            
            # Clean up
            for i in range(operations):
                redis_manager.delete(f"perf_test_{i}")
            
            duration = (time.time() - start_time) * 1000
            success_rate = (successful_operations / (operations * 2)) * 100
            
            if success_rate >= 95:  # 95% success rate threshold
                self.log_test(test_name, True, f"Success rate: {success_rate:.1f}% ({successful_operations}/{operations * 2})", duration)
                return True
            else:
                self.log_test(test_name, False, f"Success rate too low: {success_rate:.1f}% ({successful_operations}/{operations * 2})", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def test_migration_modes(self) -> bool:
        """Test different migration modes"""
        test_name = "Migration Modes Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            all_passed = True
            
            # Test local mode
            redis_manager.set_migration_mode("local")
            if redis_manager.migration_mode.value != "local":
                print("   Failed to set local mode")
                all_passed = False
            
            # Test dual mode
            redis_manager.set_migration_mode("dual")
            if redis_manager.migration_mode.value != "dual":
                print("   Failed to set dual mode")
                all_passed = False
            
            # Test azure mode
            redis_manager.set_migration_mode("azure")
            if redis_manager.migration_mode.value != "azure":
                print("   Failed to set azure mode")
                all_passed = False
            
            # Reset to dual mode
            redis_manager.set_migration_mode("dual")
            
            duration = (time.time() - start_time) * 1000
            
            if all_passed:
                self.log_test(test_name, True, "All migration modes tested successfully", duration)
                return True
            else:
                self.log_test(test_name, False, "Some migration mode tests failed", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def test_health_monitoring(self) -> bool:
        """Test health monitoring functionality"""
        test_name = "Health Monitoring Test"
        start_time = time.time()
        
        try:
            redis_manager = RedisMigrationManager()
            
            # Get health status
            health = redis_manager.ping()
            
            # Get statistics
            stats = redis_manager.get_stats()
            
            duration = (time.time() - start_time) * 1000
            
            # Check if health and stats are properly formatted
            if (isinstance(health, dict) and 'overall_status' in health and
                isinstance(stats, dict) and 'migration_mode' in stats):
                
                self.log_test(test_name, True, f"Health: {health['overall_status']}, Mode: {stats['migration_mode']}", duration)
                return True
            else:
                self.log_test(test_name, False, "Health or stats format invalid", duration)
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Redis Migration Tests...")
        print("=" * 50)
        
        tests = [
            self.test_redis_connection,
            self.test_basic_operations,
            self.test_data_types,
            self.test_performance,
            self.test_migration_modes,
            self.test_health_monitoring
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
                self.results['tests_failed'] += 1
                self.results['total_tests'] += 1
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['tests_passed']} ✅")
        print(f"Failed: {self.results['tests_failed']} ❌")
        
        success_rate = (self.results['tests_passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results['tests_failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.results['test_details']:
                if "FAILED" in test['status']:
                    print(f"  - {test['test_name']}: {test['details']}")
        
        print("\n" + "=" * 50)
        
        if self.results['tests_failed'] == 0:
            print("🎉 All tests passed! Redis migration is ready.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        return self.results['tests_failed'] == 0

def main():
    """Main function"""
    print("Redis Migration Testing Script")
    print("OpenPolicyPlatform V4")
    print("=" * 50)
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'REDIS_MIGRATION_MODE',
        'LOCAL_REDIS_URL',
        'AZURE_REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the tests.")
        print("\nExample:")
        print("export REDIS_MIGRATION_MODE=dual")
        print("export LOCAL_REDIS_URL=redis://localhost:6379/0")
        print("export AZURE_REDIS_URL=rediss://:<password>@openpolicy-redis.redis.cache.windows.net:6380")
        return False
    
    print("✅ Environment variables configured")
    
    # Run tests
    tester = RedisMigrationTester()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
