#!/usr/bin/env python3
"""
Scraper Monitoring Dashboard
===========================

Real-time monitoring dashboard for all scrapers, including:
- Background execution status
- Testing progress
- System resources
- Error tracking

Following AI Agent Guidance System and TDD Process.
"""

import os
import sys
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class ScraperMonitoringDashboard:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.logs_dir = Path(__file__).parent / "logs"
        self.reports_dir = Path(__file__).parent / "reports"
        
        # Load inventory data
        self.inventory_data = self.load_inventory_data()
        
        # Load background execution data
        self.background_data = self.load_background_data()
        
        # System monitoring
        self.system_stats = self.get_system_stats()

    def load_inventory_data(self) -> Dict:
        """Load scraper inventory data."""
        try:
            inventory_file = self.reports_dir / "dashboard_data.json"
            if inventory_file.exists():
                with open(inventory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Error loading inventory data: {e}")
        return {}

    def load_background_data(self) -> Dict:
        """Load background execution data."""
        try:
            # Find the latest status report
            status_files = list(self.logs_dir.glob("status_report_*.json"))
            if status_files:
                latest_file = max(status_files, key=lambda x: x.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Error loading background data: {e}")
        return {}

    def get_system_stats(self) -> Dict:
        """Get current system statistics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available / 1024 / 1024 / 1024,  # GB
                'disk_percent': disk.percent,
                'disk_free': disk.free / 1024 / 1024 / 1024,  # GB
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error getting system stats: {e}")
            return {}

    def display_header(self):
        """Display dashboard header."""
        print("=" * 80)
        print("📊 SCRAPER MONITORING DASHBOARD")
        print("=" * 80)
        print(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def display_system_stats(self):
        """Display system statistics."""
        print("💻 SYSTEM STATISTICS")
        print("-" * 40)
        
        if self.system_stats:
            print(f"CPU Usage:     {self.system_stats.get('cpu_percent', 0):.1f}%")
            print(f"Memory Usage:  {self.system_stats.get('memory_percent', 0):.1f}%")
            print(f"Memory Free:   {self.system_stats.get('memory_available', 0):.1f} GB")
            print(f"Disk Usage:    {self.system_stats.get('disk_percent', 0):.1f}%")
            print(f"Disk Free:     {self.system_stats.get('disk_free', 0):.1f} GB")
        else:
            print("❌ System statistics unavailable")
        print()

    def display_inventory_summary(self):
        """Display scraper inventory summary."""
        print("📋 SCRAPER INVENTORY SUMMARY")
        print("-" * 40)
        
        if self.inventory_data:
            stats = self.inventory_data.get('statistics', {})
            print(f"Total Scrapers:     {stats.get('total_scrapers', 0)}")
            print(f"Tested Scrapers:    {stats.get('tested_scrapers', 0)}")
            print(f"Working Scrapers:   {stats.get('working_scrapers', 0)}")
            print(f"Failed Scrapers:    {stats.get('failed_scrapers', 0)}")
            print(f"Untested Scrapers:  {stats.get('untested_scrapers', 0)}")
            
            # Calculate coverage
            total = stats.get('total_scrapers', 0)
            tested = stats.get('tested_scrapers', 0)
            if total > 0:
                coverage = (tested / total) * 100
                print(f"Testing Coverage:   {coverage:.1f}%")
        else:
            print("❌ Inventory data unavailable")
        print()

    def display_category_breakdown(self):
        """Display category breakdown."""
        print("🏛️ CATEGORY BREAKDOWN")
        print("-" * 40)
        
        if self.inventory_data:
            categories = self.inventory_data.get('categories', {})
            
            for category, data in categories.items():
                total = data.get('total', 0)
                tested = data.get('tested', 0)
                working = data.get('working', 0)
                
                if total > 0:
                    coverage = (tested / total) * 100
                    print(f"{category.title():15} | Total: {total:3d} | Tested: {tested:3d} | Working: {working:3d} | Coverage: {coverage:5.1f}%")
        else:
            print("❌ Category data unavailable")
        print()

    def display_schedule_breakdown(self):
        """Display schedule breakdown."""
        print("📅 SCHEDULE BREAKDOWN")
        print("-" * 40)
        
        if self.inventory_data:
            schedules = self.inventory_data.get('schedules', {})
            
            for schedule_type, count in schedules.items():
                print(f"{schedule_type.replace('_', ' ').title():15} | {count:3d} scrapers")
        else:
            print("❌ Schedule data unavailable")
        print()

    def display_background_execution_status(self):
        """Display background execution status."""
        print("🔄 BACKGROUND EXECUTION STATUS")
        print("-" * 40)
        
        if self.background_data:
            total = self.background_data.get('total_scrapers', 0)
            running = self.background_data.get('running', 0)
            completed = self.background_data.get('completed', 0)
            failed = self.background_data.get('failed', 0)
            scheduled = self.background_data.get('scheduled', 0)
            
            print(f"Total Scrapers:     {total}")
            print(f"Currently Running:  {running}")
            print(f"Completed:          {completed}")
            print(f"Failed:             {failed}")
            print(f"Scheduled:          {scheduled}")
            
            # Calculate success rate
            if total > 0:
                success_rate = (completed / total) * 100
                print(f"Success Rate:       {success_rate:.1f}%")
        else:
            print("❌ Background execution data unavailable")
        print()

    def display_recent_activity(self):
        """Display recent activity."""
        print("📊 RECENT ACTIVITY")
        print("-" * 40)
        
        if self.background_data:
            executions = self.background_data.get('executions', [])
            
            # Show last 10 executions
            # Filter out executions with None start_time and sort
            valid_executions = [e for e in executions if e.get('start_time') is not None]
            recent_executions = sorted(valid_executions, key=lambda x: x.get('start_time', ''), reverse=True)[:10]
            
            for execution in recent_executions:
                name = execution.get('name', 'Unknown')
                status = execution.get('status', 'unknown')
                schedule = execution.get('schedule', 'unknown')
                start_time = execution.get('start_time', '')
                records = execution.get('records_collected', 0)
                
                # Format start time
                if start_time:
                    try:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        start_time = dt.strftime('%H:%M:%S')
                    except:
                        start_time = start_time[:8]
                
                status_icon = {
                    'running': '🔄',
                    'completed': '✅',
                    'failed': '❌',
                    'scheduled': '⏰',
                    'stopped': '⏹️'
                }.get(status, '❓')
                
                print(f"{status_icon} {name:25} | {status:10} | {schedule:8} | {start_time} | {records:3d} records")
        else:
            print("❌ Recent activity data unavailable")
        print()

    def display_error_summary(self):
        """Display error summary."""
        print("🚨 ERROR SUMMARY")
        print("-" * 40)
        
        if self.background_data:
            executions = self.background_data.get('executions', [])
            failed_executions = [e for e in executions if e.get('status') == 'failed']
            
            if failed_executions:
                print(f"Total Failed: {len(failed_executions)}")
                print()
                
                for execution in failed_executions[:5]:  # Show last 5 failures
                    name = execution.get('name', 'Unknown')
                    error = execution.get('last_error', 'Unknown error')
                    error_count = execution.get('error_count', 0)
                    
                    print(f"❌ {name}")
                    print(f"   Error Count: {error_count}")
                    print(f"   Last Error:  {error[:100]}...")
                    print()
            else:
                print("✅ No failed executions")
        else:
            print("❌ Error data unavailable")
        print()

    def display_recommendations(self):
        """Display recommendations."""
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = []
        
        # Check testing coverage
        if self.inventory_data:
            stats = self.inventory_data.get('statistics', {})
            total = stats.get('total_scrapers', 0)
            tested = stats.get('tested_scrapers', 0)
            
            if total > 0:
                coverage = (tested / total) * 100
                if coverage < 80:
                    recommendations.append(f"🔧 Increase testing coverage (currently {coverage:.1f}%)")
                else:
                    recommendations.append(f"✅ Testing coverage is good ({coverage:.1f}%)")
        
        # Check background execution
        if self.background_data:
            total = self.background_data.get('total_scrapers', 0)
            failed = self.background_data.get('failed', 0)
            
            if total > 0 and failed > 0:
                failure_rate = (failed / total) * 100
                if failure_rate > 10:
                    recommendations.append(f"🔧 High failure rate ({failure_rate:.1f}%) - investigate errors")
                else:
                    recommendations.append(f"✅ Background execution is stable")
        
        # Check system resources
        if self.system_stats:
            cpu = self.system_stats.get('cpu_percent', 0)
            memory = self.system_stats.get('memory_percent', 0)
            
            if cpu > 80:
                recommendations.append(f"⚠️  High CPU usage ({cpu:.1f}%) - consider scaling")
            if memory > 80:
                recommendations.append(f"⚠️  High memory usage ({memory:.1f}%) - consider optimization")
        
        if not recommendations:
            recommendations.append("✅ All systems operating normally")
        
        for rec in recommendations:
            print(rec)
        print()

    def display_dashboard(self):
        """Display the complete dashboard."""
        self.display_header()
        self.display_system_stats()
        self.display_inventory_summary()
        self.display_category_breakdown()
        self.display_schedule_breakdown()
        self.display_background_execution_status()
        self.display_recent_activity()
        self.display_error_summary()
        self.display_recommendations()
        
        print("=" * 80)
        print("📊 Dashboard complete - Press Ctrl+C to exit")
        print("=" * 80)

    def run_continuous_monitoring(self, interval: int = 30):
        """Run continuous monitoring with refresh."""
        try:
            while True:
                # Clear screen (works on most terminals)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Refresh data
                self.inventory_data = self.load_inventory_data()
                self.background_data = self.load_background_data()
                self.system_stats = self.get_system_stats()
                
                # Display dashboard
                self.display_dashboard()
                
                # Wait for next refresh
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Scraper Monitoring Dashboard')
    parser.add_argument('--interval', '-i', type=int, default=30, 
                       help='Refresh interval in seconds (default: 30)')
    parser.add_argument('--once', '-o', action='store_true',
                       help='Display dashboard once and exit')
    
    args = parser.parse_args()
    
    dashboard = ScraperMonitoringDashboard()
    
    if args.once:
        dashboard.display_dashboard()
    else:
        dashboard.run_continuous_monitoring(args.interval)

if __name__ == "__main__":
    main()
