#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - Comprehensive Performance Analysis

This script runs a complete performance analysis including:
1. Load testing to identify bottlenecks
2. Performance optimization based on results
3. Re-testing to validate improvements
4. Comprehensive reporting
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
try:
    from load_testing_suite import LoadTestingSuite
    from performance_optimization import PerformanceOptimizer
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure load_testing_suite.py and performance_optimization.py are in the same directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Comprehensive performance analysis engine"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 database_url: str = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                 redis_url: str = "redis://localhost:6379"):
        self.base_url = base_url
        self.database_url = database_url
        self.redis_url = redis_url
        self.analysis_results: Dict[str, Any] = {}
        
    def run_initial_load_testing(self) -> Dict[str, Any]:
        """Run initial load testing to establish baseline"""
        logger.info("🎯 Phase 1: Running initial load testing...")
        
        try:
            # Initialize load testing suite
            load_tester = LoadTestingSuite(base_url=self.base_url)
            
            # Run comprehensive performance tests
            logger.info("   Running performance test suite...")
            performance_results = load_tester.run_performance_test_suite()
            
            # Run stress tests
            logger.info("   Running stress tests...")
            stress_result = load_tester.run_stress_test()
            
            # Run scalability tests
            logger.info("   Running scalability tests...")
            scalability_results = load_tester.run_scalability_test()
            
            # Generate initial report
            initial_report = load_tester.generate_report("initial_load_test_report.md")
            load_tester.save_results("initial_load_test_results.json")
            
            self.analysis_results['initial_load_testing'] = {
                'performance_results': performance_results,
                'stress_result': stress_result,
                'scalability_results': scalability_results,
                'report': initial_report
            }
            
            logger.info("✅ Initial load testing completed")
            return self.analysis_results['initial_load_testing']
            
        except Exception as e:
            logger.error(f"❌ Initial load testing failed: {e}")
            raise
    
    def run_performance_optimization(self) -> Dict[str, Any]:
        """Run performance optimization based on load testing results"""
        logger.info("🔧 Phase 2: Running performance optimization...")
        
        try:
            # Initialize performance optimizer
            optimizer = PerformanceOptimizer(
                database_url=self.database_url,
                redis_url=self.redis_url,
                api_base_url=self.base_url
            )
            
            # Run comprehensive optimization
            optimization_results = optimizer.run_comprehensive_optimization()
            
            # Generate optimization report
            optimization_report = optimizer.generate_optimization_report("optimization_report.md")
            optimizer.save_results("optimization_results.json")
            
            self.analysis_results['performance_optimization'] = {
                'optimization_results': optimization_results,
                'report': optimization_report
            }
            
            logger.info("✅ Performance optimization completed")
            return self.analysis_results['performance_optimization']
            
        except Exception as e:
            logger.error(f"❌ Performance optimization failed: {e}")
            raise
    
    def run_post_optimization_testing(self) -> Dict[str, Any]:
        """Run load testing after optimization to validate improvements"""
        logger.info("🎯 Phase 3: Running post-optimization testing...")
        
        try:
            # Wait a bit for optimizations to take effect
            logger.info("   Waiting for optimizations to take effect...")
            time.sleep(30)
            
            # Initialize load testing suite
            load_tester = LoadTestingSuite(base_url=self.base_url)
            
            # Run the same tests as before
            logger.info("   Running performance test suite (post-optimization)...")
            performance_results = load_tester.run_performance_test_suite()
            
            # Run stress tests
            logger.info("   Running stress tests (post-optimization)...")
            stress_result = load_tester.run_stress_test()
            
            # Run scalability tests
            logger.info("   Running scalability tests (post-optimization)...")
            scalability_results = load_tester.run_scalability_test()
            
            # Generate post-optimization report
            post_report = load_tester.generate_report("post_optimization_load_test_report.md")
            load_tester.save_results("post_optimization_load_test_results.json")
            
            self.analysis_results['post_optimization_testing'] = {
                'performance_results': performance_results,
                'stress_result': stress_result,
                'scalability_results': scalability_results,
                'report': post_report
            }
            
            logger.info("✅ Post-optimization testing completed")
            return self.analysis_results['post_optimization_testing']
            
        except Exception as e:
            logger.error(f"❌ Post-optimization testing failed: {e}")
            raise
    
    def compare_results(self) -> Dict[str, Any]:
        """Compare pre and post optimization results"""
        logger.info("📊 Phase 4: Comparing results...")
        
        try:
            initial_results = self.analysis_results.get('initial_load_testing', {})
            post_results = self.analysis_results.get('post_optimization_testing', {})
            
            if not initial_results or not post_results:
                logger.warning("⚠️ Missing results for comparison")
                return {}
            
            comparison = {
                'performance_improvements': {},
                'stress_test_improvements': {},
                'scalability_improvements': {},
                'overall_improvement': 0.0
            }
            
            # Compare performance results
            if 'performance_results' in initial_results and 'performance_results' in post_results:
                initial_perf = initial_results['performance_results']
                post_perf = post_results['performance_results']
                
                for test_name in initial_perf:
                    if test_name in post_perf:
                        initial_avg = initial_perf[test_name].get('average_response_time', 0)
                        post_avg = post_perf[test_name].get('average_response_time', 0)
                        
                        if initial_avg > 0:
                            improvement = ((initial_avg - post_avg) / initial_avg) * 100
                            comparison['performance_improvements'][test_name] = {
                                'initial_avg': initial_avg,
                                'post_avg': post_avg,
                                'improvement_percentage': improvement
                            }
            
            # Calculate overall improvement
            improvements = []
            for test_improvements in comparison['performance_improvements'].values():
                improvements.append(test_improvements['improvement_percentage'])
            
            if improvements:
                comparison['overall_improvement'] = sum(improvements) / len(improvements)
            
            self.analysis_results['comparison'] = comparison
            logger.info("✅ Results comparison completed")
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Results comparison failed: {e}")
            raise
    
    def generate_comprehensive_report(self, output_file: str = "comprehensive_performance_analysis.md") -> str:
        """Generate comprehensive performance analysis report"""
        logger.info("📄 Generating comprehensive report...")
        
        report = []
        report.append("# 🎯 OpenPolicy Platform - Comprehensive Performance Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.append("## 📊 Executive Summary")
        
        if 'comparison' in self.analysis_results:
            overall_improvement = self.analysis_results['comparison'].get('overall_improvement', 0)
            report.append(f"- **Overall Performance Improvement**: {overall_improvement:.1f}%")
        
        if 'performance_optimization' in self.analysis_results:
            optimization_results = self.analysis_results['performance_optimization'].get('optimization_results', [])
            successful_optimizations = len([r for r in optimization_results if r.status == 'success'])
            total_optimizations = len(optimization_results)
            report.append(f"- **Optimizations Applied**: {successful_optimizations}/{total_optimizations}")
        
        report.append("")
        
        # Phase Results
        report.append("## 🎯 Phase Results")
        
        # Phase 1: Initial Load Testing
        if 'initial_load_testing' in self.analysis_results:
            report.append("### Phase 1: Initial Load Testing")
            report.append("- **Status**: ✅ Completed")
            report.append("- **Purpose**: Establish performance baseline")
            report.append("- **Results**: See `initial_load_test_report.md`")
            report.append("")
        
        # Phase 2: Performance Optimization
        if 'performance_optimization' in self.analysis_results:
            report.append("### Phase 2: Performance Optimization")
            report.append("- **Status**: ✅ Completed")
            report.append("- **Purpose**: Implement performance improvements")
            report.append("- **Results**: See `optimization_report.md`")
            report.append("")
        
        # Phase 3: Post-Optimization Testing
        if 'post_optimization_testing' in self.analysis_results:
            report.append("### Phase 3: Post-Optimization Testing")
            report.append("- **Status**: ✅ Completed")
            report.append("- **Purpose**: Validate performance improvements")
            report.append("- **Results**: See `post_optimization_load_test_report.md`")
            report.append("")
        
        # Phase 4: Results Comparison
        if 'comparison' in self.analysis_results:
            report.append("### Phase 4: Results Comparison")
            report.append("- **Status**: ✅ Completed")
            report.append("- **Purpose**: Compare pre and post optimization results")
            
            comparison = self.analysis_results['comparison']
            if comparison.get('performance_improvements'):
                report.append("- **Performance Improvements**:")
                for test_name, improvement in comparison['performance_improvements'].items():
                    report.append(f"  - {test_name}: {improvement['improvement_percentage']:.1f}% improvement")
            
            report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        report.append("1. **Monitor Performance**: Continue monitoring system performance")
        report.append("2. **Load Testing**: Schedule regular load testing")
        report.append("3. **Optimization**: Implement additional optimizations as needed")
        report.append("4. **Documentation**: Update system documentation")
        report.append("5. **Training**: Train team on performance monitoring")
        report.append("")
        
        # Next Steps
        report.append("## 🚀 Next Steps")
        report.append("1. **Production Deployment**: Deploy optimizations to production")
        report.append("2. **Monitoring Setup**: Implement real-time performance monitoring")
        report.append("3. **Alerting**: Set up performance alerts")
        report.append("4. **Documentation**: Update runbooks and procedures")
        report.append("5. **Team Training**: Train operations team on new monitoring")
        report.append("")
        
        # Files Generated
        report.append("## 📁 Files Generated")
        report.append("- `initial_load_test_report.md` - Initial load testing results")
        report.append("- `initial_load_test_results.json` - Initial load testing data")
        report.append("- `optimization_report.md` - Performance optimization results")
        report.append("- `optimization_results.json` - Optimization data")
        report.append("- `post_optimization_load_test_report.md` - Post-optimization testing results")
        report.append("- `post_optimization_load_test_results.json` - Post-optimization testing data")
        report.append("- `comprehensive_performance_analysis.md` - This comprehensive report")
        report.append("- `performance_analysis.log` - Analysis execution log")
        report.append("")
        
        report_text = "\n".join(report)
        
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        logger.info(f"📄 Comprehensive report saved to {output_file}")
        return report_text
    
    def save_analysis_results(self, output_file: str = "performance_analysis_results.json"):
        """Save all analysis results to JSON file"""
        try:
            # Convert datetime objects to strings
            results_to_save = {}
            for key, value in self.analysis_results.items():
                if isinstance(value, dict):
                    results_to_save[key] = value
                else:
                    results_to_save[key] = str(value)
            
            with open(output_file, 'w') as f:
                json.dump(results_to_save, f, indent=2)
            
            logger.info(f"💾 Analysis results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save analysis results: {e}")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete performance analysis"""
        logger.info("🎯 Starting comprehensive performance analysis...")
        
        try:
            # Phase 1: Initial Load Testing
            self.run_initial_load_testing()
            
            # Phase 2: Performance Optimization
            self.run_performance_optimization()
            
            # Phase 3: Post-Optimization Testing
            self.run_post_optimization_testing()
            
            # Phase 4: Results Comparison
            self.compare_results()
            
            # Generate comprehensive report
            self.generate_comprehensive_report()
            
            # Save all results
            self.save_analysis_results()
            
            logger.info("✅ Comprehensive performance analysis completed")
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive performance analysis failed: {e}")
            raise

def main():
    """Main function to run performance analysis"""
    parser = argparse.ArgumentParser(description="OpenPolicy Platform Performance Analysis")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--database-url", default="postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                       help="Database connection URL")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis connection URL")
    parser.add_argument("--output", default="comprehensive_performance_analysis.md", help="Output report file")
    parser.add_argument("--results", default="performance_analysis_results.json", help="Results JSON file")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(
        base_url=args.base_url,
        database_url=args.database_url,
        redis_url=args.redis_url
    )
    
    try:
        # Run complete analysis
        results = analyzer.run_complete_analysis()
        
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE PERFORMANCE ANALYSIS COMPLETE")
        print("="*80)
        
        # Print summary
        if 'comparison' in results:
            overall_improvement = results['comparison'].get('overall_improvement', 0)
            print(f"📊 Overall Performance Improvement: {overall_improvement:.1f}%")
        
        if 'performance_optimization' in results:
            optimization_results = results['performance_optimization'].get('optimization_results', [])
            successful_optimizations = len([r for r in optimization_results if r.status == 'success'])
            total_optimizations = len(optimization_results)
            print(f"🔧 Optimizations Applied: {successful_optimizations}/{total_optimizations}")
        
        print(f"📄 Comprehensive report: {args.output}")
        print(f"💾 Results data: {args.results}")
        print("="*80)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Performance analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Performance analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
