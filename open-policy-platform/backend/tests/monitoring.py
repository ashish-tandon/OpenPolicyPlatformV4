"""
Test monitoring and metrics collection
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class TestMetrics:
    """Test execution metrics"""
    test_name: str
    duration: float
    status: str
    timestamp: str
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class TestMonitor:
    """Monitor test execution and collect metrics"""
    
    def __init__(self, output_file: str = "test_metrics.json"):
        self.output_file = output_file
        self.metrics: List[TestMetrics] = []
        self.start_time = None
    
    def start_test(self, test_name: str):
        """Start monitoring a test"""
        self.start_time = time.time()
    
    def end_test(self, test_name: str, status: str, memory_usage: float = 0.0, cpu_usage: float = 0.0):
        """End monitoring a test and record metrics"""
        if self.start_time:
            duration = time.time() - self.start_time
            metric = TestMetrics(
                test_name=test_name,
                duration=duration,
                status=status,
                timestamp=datetime.now().isoformat(),
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )
            self.metrics.append(metric)
            self.start_time = None
    
    def save_metrics(self):
        """Save metrics to file"""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test execution summary"""
        if not self.metrics:
            return {}
        
        total_tests = len(self.metrics)
        passed_tests = len([m for m in self.metrics if m.status == "passed"])
        failed_tests = len([m for m in self.metrics if m.status == "failed"])
        total_duration = sum(m.duration for m in self.metrics)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "timestamp": datetime.now().isoformat()
        }

# Global monitor instance
test_monitor = TestMonitor()
