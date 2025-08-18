#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - Comprehensive Load Testing Suite

This module provides comprehensive load testing capabilities for the OpenPolicy platform,
including performance testing, stress testing, and scalability validation.
"""

import asyncio
import time
import statistics
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import psutil
import threading
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    """Results from a load test"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    start_time: datetime
    end_time: datetime
    duration: float
    concurrent_users: int
    target_endpoint: str
    status_codes: Dict[int, int]
    errors: List[str]

class LoadTestingSuite:
    """Comprehensive load testing suite for OpenPolicy platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenPolicy-LoadTester/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make a single request and return timing data"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, timeout=30, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'status_code': response.status_code,
                'response_time': response_time,
                'success': 200 <= response.status_code < 400,
                'error': None
            }
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'status_code': 0,
                'response_time': response_time,
                'success': False,
                'error': str(e)
            }
    
    def _calculate_statistics(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate statistical measures for response times"""
        if not response_times:
            return {}
        
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        return {
            'average': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'min': min(response_times),
            'max': max(response_times),
            'p95': sorted_times[int(0.95 * n)] if n > 0 else 0,
            'p99': sorted_times[int(0.99 * n)] if n > 0 else 0
        }
    
    def run_load_test(self, 
                     test_name: str,
                     endpoint: str,
                     concurrent_users: int = 10,
                     total_requests: int = 100,
                     method: str = 'GET',
                     **kwargs) -> LoadTestResult:
        """Run a load test with specified parameters"""
        logger.info(f"🚀 Starting load test: {test_name}")
        logger.info(f"   Endpoint: {endpoint}")
        logger.info(f"   Concurrent users: {concurrent_users}")
        logger.info(f"   Total requests: {total_requests}")
        
        start_time = datetime.now()
        response_times = []
        status_codes = {}
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        def worker():
            """Worker function for making requests"""
            nonlocal successful_requests, failed_requests
            
            while True:
                try:
                    result = self._make_request(endpoint, method, **kwargs)
                    response_times.append(result['response_time'])
                    
                    # Track status codes
                    status_code = result['status_code']
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                    
                    if result['success']:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        if result['error']:
                            errors.append(result['error'])
                    
                except Exception as e:
                    failed_requests += 1
                    errors.append(str(e))
        
        # Create and start worker threads
        threads = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(total_requests):
                future = executor.submit(self._make_request, endpoint, method, **kwargs)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    response_times.append(result['response_time'])
                    
                    status_code = result['status_code']
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                    
                    if result['success']:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        if result['error']:
                            errors.append(result['error'])
                except Exception as e:
                    failed_requests += 1
                    errors.append(str(e))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        stats = self._calculate_statistics(response_times)
        
        # Create result
        result = LoadTestResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=stats.get('average', 0),
            median_response_time=stats.get('median', 0),
            min_response_time=stats.get('min', 0),
            max_response_time=stats.get('max', 0),
            p95_response_time=stats.get('p95', 0),
            p99_response_time=stats.get('p99', 0),
            requests_per_second=successful_requests / duration if duration > 0 else 0,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            concurrent_users=concurrent_users,
            target_endpoint=endpoint,
            status_codes=status_codes,
            errors=errors[:10]  # Limit to first 10 errors
        )
        
        self.results.append(result)
        
        # Log results
        logger.info(f"✅ Load test completed: {test_name}")
        logger.info(f"   Success rate: {successful_requests/total_requests*100:.1f}%")
        logger.info(f"   Average response time: {stats.get('average', 0):.3f}s")
        logger.info(f"   Requests per second: {result.requests_per_second:.1f}")
        logger.info(f"   Error rate: {result.error_rate*100:.1f}%")
        
        return result
    
    def run_performance_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite"""
        logger.info("🎯 Starting comprehensive performance test suite")
        
        test_suite = [
            # Basic health and status endpoints
            {
                'name': 'Health Check Performance',
                'endpoint': '/api/v1/health',
                'concurrent_users': 50,
                'total_requests': 500
            },
            {
                'name': 'System Status Performance',
                'endpoint': '/api/v1/stats',
                'concurrent_users': 30,
                'total_requests': 300
            },
            
            # Data retrieval endpoints
            {
                'name': 'Jurisdictions Performance',
                'endpoint': '/api/v1/jurisdictions',
                'concurrent_users': 20,
                'total_requests': 200
            },
            {
                'name': 'Representatives Performance',
                'endpoint': '/api/v1/representatives?limit=50',
                'concurrent_users': 25,
                'total_requests': 250
            },
            {
                'name': 'Policies Performance',
                'endpoint': '/api/v1/policies?limit=50',
                'concurrent_users': 20,
                'total_requests': 200
            },
            
            # Search endpoints
            {
                'name': 'Search Performance',
                'endpoint': '/api/v1/search?q=parliament',
                'concurrent_users': 15,
                'total_requests': 150
            },
            
            # Admin endpoints
            {
                'name': 'Dashboard Performance',
                'endpoint': '/api/v1/dashboard',
                'concurrent_users': 10,
                'total_requests': 100
            }
        ]
        
        suite_results = {}
        
        for test_config in test_suite:
            try:
                result = self.run_load_test(**test_config)
                suite_results[test_config['name']] = asdict(result)
            except Exception as e:
                logger.error(f"❌ Test failed: {test_config['name']} - {e}")
                suite_results[test_config['name']] = {'error': str(e)}
        
        return suite_results
    
    def run_stress_test(self, 
                       endpoint: str = '/api/v1/health',
                       max_concurrent_users: int = 100,
                       max_requests: int = 1000) -> LoadTestResult:
        """Run stress test to find system limits"""
        logger.info(f"🔥 Starting stress test on {endpoint}")
        logger.info(f"   Max concurrent users: {max_concurrent_users}")
        logger.info(f"   Max requests: {max_requests}")
        
        # Gradually increase load
        concurrent_levels = [10, 25, 50, 75, 100, 150, 200]
        stress_results = []
        
        for concurrent_users in concurrent_levels:
            if concurrent_users > max_concurrent_users:
                break
                
            logger.info(f"   Testing with {concurrent_users} concurrent users...")
            
            try:
                result = self.run_load_test(
                    test_name=f"Stress Test - {concurrent_users} users",
                    endpoint=endpoint,
                    concurrent_users=concurrent_users,
                    total_requests=min(concurrent_users * 10, max_requests)
                )
                stress_results.append(result)
                
                # Check if system is struggling
                if result.error_rate > 0.1:  # 10% error rate
                    logger.warning(f"⚠️ High error rate detected: {result.error_rate*100:.1f}%")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Stress test failed at {concurrent_users} users: {e}")
                break
        
        # Return the most challenging result
        if stress_results:
            return max(stress_results, key=lambda r: r.concurrent_users)
        else:
            raise Exception("No stress test results generated")
    
    def run_scalability_test(self, 
                           endpoint: str = '/api/v1/health',
                           base_concurrent_users: int = 10,
                           scaling_factor: float = 2.0,
                           max_iterations: int = 5) -> List[LoadTestResult]:
        """Run scalability test to measure system scaling"""
        logger.info(f"📈 Starting scalability test on {endpoint}")
        
        scalability_results = []
        current_concurrent_users = base_concurrent_users
        
        for iteration in range(max_iterations):
            logger.info(f"   Iteration {iteration + 1}: {current_concurrent_users} concurrent users")
            
            try:
                result = self.run_load_test(
                    test_name=f"Scalability Test - Iteration {iteration + 1}",
                    endpoint=endpoint,
                    concurrent_users=current_concurrent_users,
                    total_requests=current_concurrent_users * 20
                )
                scalability_results.append(result)
                
                # Check if performance is degrading
                if result.error_rate > 0.05:  # 5% error rate
                    logger.warning(f"⚠️ Performance degradation detected: {result.error_rate*100:.1f}% error rate")
                    break
                
                current_concurrent_users = int(current_concurrent_users * scaling_factor)
                
            except Exception as e:
                logger.error(f"❌ Scalability test failed at iteration {iteration + 1}: {e}")
                break
        
        return scalability_results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive load testing report"""
        logger.info("📊 Generating load testing report")
        
        if not self.results:
            return "No test results available"
        
        report = []
        report.append("# 🎯 OpenPolicy Platform - Load Testing Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_tests = len(self.results)
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        
        report.append("## 📈 Summary Statistics")
        report.append(f"- **Total Tests**: {total_tests}")
        report.append(f"- **Total Requests**: {total_requests:,}")
        report.append(f"- **Successful Requests**: {total_successful:,}")
        report.append(f"- **Failed Requests**: {total_failed:,}")
        report.append(f"- **Overall Success Rate**: {total_successful/total_requests*100:.1f}%")
        report.append("")
        
        # Individual test results
        report.append("## 🧪 Test Results")
        for result in self.results:
            report.append(f"### {result.test_name}")
            report.append(f"- **Endpoint**: {result.target_endpoint}")
            report.append(f"- **Concurrent Users**: {result.concurrent_users}")
            report.append(f"- **Total Requests**: {result.total_requests}")
            report.append(f"- **Success Rate**: {result.successful_requests/result.total_requests*100:.1f}%")
            report.append(f"- **Average Response Time**: {result.average_response_time:.3f}s")
            report.append(f"- **Median Response Time**: {result.median_response_time:.3f}s")
            report.append(f"- **P95 Response Time**: {result.p95_response_time:.3f}s")
            report.append(f"- **P99 Response Time**: {result.p99_response_time:.3f}s")
            report.append(f"- **Requests/Second**: {result.requests_per_second:.1f}")
            report.append(f"- **Error Rate**: {result.error_rate*100:.1f}%")
            report.append(f"- **Duration**: {result.duration:.1f}s")
            report.append("")
        
        # Performance recommendations
        report.append("## 🎯 Performance Recommendations")
        
        # Analyze results for recommendations
        avg_response_times = [r.average_response_time for r in self.results]
        error_rates = [r.error_rate for r in self.results]
        
        if avg_response_times:
            avg_response_time = statistics.mean(avg_response_times)
            if avg_response_time > 1.0:
                report.append("- ⚠️ **High Response Times**: Consider optimizing database queries and adding caching")
            elif avg_response_time > 0.5:
                report.append("- ⚠️ **Moderate Response Times**: Consider implementing response caching")
            else:
                report.append("- ✅ **Good Response Times**: System performing well")
        
        if error_rates:
            avg_error_rate = statistics.mean(error_rates)
            if avg_error_rate > 0.05:
                report.append("- ⚠️ **High Error Rates**: Investigate and fix error sources")
            elif avg_error_rate > 0.01:
                report.append("- ⚠️ **Moderate Error Rates**: Monitor and optimize error handling")
            else:
                report.append("- ✅ **Low Error Rates**: System stable")
        
        report.append("")
        report.append("## 🔧 Optimization Suggestions")
        report.append("1. **Database Optimization**: Review and optimize slow queries")
        report.append("2. **Caching Strategy**: Implement Redis caching for frequently accessed data")
        report.append("3. **Connection Pooling**: Optimize database connection pooling")
        report.append("4. **Load Balancing**: Consider implementing load balancing for high traffic")
        report.append("5. **CDN Integration**: Use CDN for static assets")
        report.append("6. **Monitoring**: Implement real-time performance monitoring")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"📄 Report saved to {output_file}")
        
        return report_text
    
    def save_results(self, output_file: str = "load_test_results.json"):
        """Save test results to JSON file"""
        results_data = [asdict(result) for result in self.results]
        
        # Convert datetime objects to strings
        for result in results_data:
            result['start_time'] = result['start_time'].isoformat()
            result['end_time'] = result['end_time'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")

def main():
    """Main function to run load testing suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenPolicy Platform Load Testing Suite")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for testing")
    parser.add_argument("--test-type", choices=["performance", "stress", "scalability", "all"], 
                       default="all", help="Type of test to run")
    parser.add_argument("--output", default="load_test_report.md", help="Output report file")
    parser.add_argument("--results", default="load_test_results.json", help="Results JSON file")
    
    args = parser.parse_args()
    
    # Initialize load testing suite
    suite = LoadTestingSuite(base_url=args.base_url)
    
    try:
        if args.test_type in ["performance", "all"]:
            logger.info("🎯 Running performance test suite...")
            suite.run_performance_test_suite()
        
        if args.test_type in ["stress", "all"]:
            logger.info("🔥 Running stress test...")
            suite.run_stress_test()
        
        if args.test_type in ["scalability", "all"]:
            logger.info("📈 Running scalability test...")
            suite.run_scalability_test()
        
        # Generate and save report
        report = suite.generate_report(args.output)
        suite.save_results(args.results)
        
        print("\n" + "="*80)
        print("🎯 LOAD TESTING COMPLETE")
        print("="*80)
        print(report)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Load testing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Load testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
