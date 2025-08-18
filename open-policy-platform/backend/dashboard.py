#!/usr/bin/env python3
"""
OpenPolicy Monitoring Dashboard
==============================

A simple web dashboard to visualize:
1. System performance metrics
2. Scraper success rates
3. Data quality metrics
4. Real-time alerts
5. Database health status
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, render_template, jsonify, request
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

from src.database.models import (
    Base, Jurisdiction, Representative, ScrapingRun, DataQualityIssue,
    JurisdictionType, RepresentativeRole
)
from src.database.config import get_engine, get_session

app = Flask(__name__)

def get_database_session():
    """Get database session using connection pooling"""
    return get_session()

def create_dashboard_template():
    """Create dashboard template if it doesn't exist"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    dashboard_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenPolicy Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #333;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-value {
            font-weight: bold;
            font-size: 1.2em;
        }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OpenPolicy Monitoring Dashboard</h1>
            <p>Real-time system monitoring and data quality metrics</p>
            <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
        </div>

        <div class="grid">
            <div class="card">
                <h3>System Status</h3>
                <div id="system-metrics">
                    <div class="metric">
                        <span>CPU Usage:</span>
                        <span class="metric-value" id="cpu-usage">-</span>
                    </div>
                    <div class="metric">
                        <span>Memory Usage:</span>
                        <span class="metric-value" id="memory-usage">-</span>
                    </div>
                    <div class="metric">
                        <span>Disk Usage:</span>
                        <span class="metric-value" id="disk-usage">-</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Scraper Performance</h3>
                <div id="scraper-metrics">
                    <div class="metric">
                        <span>Success Rate:</span>
                        <span class="metric-value" id="success-rate">-</span>
                    </div>
                    <div class="metric">
                        <span>Total Scrapers:</span>
                        <span class="metric-value" id="total-scrapers">-</span>
                    </div>
                    <div class="metric">
                        <span>Records Collected:</span>
                        <span class="metric-value" id="records-collected">-</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Data Quality</h3>
                <div id="data-quality">
                    <div class="metric">
                        <span>Quality Score:</span>
                        <span class="metric-value" id="quality-score">-</span>
                    </div>
                    <div class="metric">
                        <span>Total Records:</span>
                        <span class="metric-value" id="total-records">-</span>
                    </div>
                    <div class="metric">
                        <span>Complete Records:</span>
                        <span class="metric-value" id="complete-records">-</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Database Health</h3>
                <div id="database-health">
                    <div class="metric">
                        <span>Status:</span>
                        <span class="metric-value" id="db-status">-</span>
                    </div>
                    <div class="metric">
                        <span>Representatives:</span>
                        <span class="metric-value" id="db-representatives">-</span>
                    </div>
                    <div class="metric">
                        <span>Jurisdictions:</span>
                        <span class="metric-value" id="db-jurisdictions">-</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>System Performance Trends</h3>
            <div class="chart-container">
                <canvas id="performance-chart"></canvas>
            </div>
        </div>

        <div class="card">
            <h3>Recent Alerts</h3>
            <div id="alerts-list">
                <p>Loading alerts...</p>
            </div>
        </div>
    </div>

    <script>
        let performanceChart;

        async function refreshData() {
            try {
                // Load system metrics
                const systemResponse = await fetch('/api/system-metrics');
                const systemData = await systemResponse.json();

                document.getElementById('cpu-usage').textContent = systemData.cpu_usage.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = systemData.memory_usage.toFixed(1) + '%';
                document.getElementById('disk-usage').textContent = systemData.disk_usage.toFixed(1) + '%';

                // Load scraper metrics
                const scraperResponse = await fetch('/api/scraper-metrics');
                const scraperData = await scraperResponse.json();

                const totalScrapers = Object.keys(scraperData).length;
                const successfulScrapers = Object.values(scraperData).filter(s => s.success_rate > 0).length;
                const successRate = totalScrapers > 0 ? (successfulScrapers / totalScrapers * 100) : 0;
                const totalRecords = Object.values(scraperData).reduce((sum, s) => sum + s.records_collected, 0);

                document.getElementById('success-rate').textContent = successRate.toFixed(1) + '%';
                document.getElementById('total-scrapers').textContent = totalScrapers;
                document.getElementById('records-collected').textContent = totalRecords;

                // Load data quality
                const qualityResponse = await fetch('/api/data-quality');
                const qualityData = await qualityResponse.json();

                document.getElementById('quality-score').textContent = qualityData.quality_score.toFixed(1) + '%';
                document.getElementById('total-records').textContent = qualityData.total_records;
                document.getElementById('complete-records').textContent = qualityData.complete_records;

                // Load database health
                const dbResponse = await fetch('/api/database-health');
                const dbData = await dbResponse.json();

                document.getElementById('db-status').textContent = dbData.status;
                document.getElementById('db-status').className = 'metric-value status-' + dbData.status;
                document.getElementById('db-representatives').textContent = dbData.representative_count;
                document.getElementById('db-jurisdictions').textContent = dbData.jurisdiction_count;

                // Load alerts
                const alertsResponse = await fetch('/api/alerts');
                const alertsData = await alertsResponse.json();

                const alertsList = document.getElementById('alerts-list');
                if (alertsData.length === 0) {
                    alertsList.innerHTML = '<p>No recent alerts</p>';
                } else {
                    alertsList.innerHTML = alertsData.map(alert =>
                        `<div class="metric">
                            <span>${alert.message}</span>
                            <span class="metric-value status-${alert.severity}">${alert.severity}</span>
                        </div>`
                    ).join('');
                }

                // Update performance chart
                updatePerformanceChart(systemData);

            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        function updatePerformanceChart(systemData) {
            const ctx = document.getElementById('performance-chart').getContext('2d');

            if (performanceChart) {
                performanceChart.destroy();
            }

            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [new Date().toLocaleTimeString()],
                    datasets: [{
                        label: 'CPU Usage (%)',
                        data: [systemData.cpu_usage],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }, {
                        label: 'Memory Usage (%)',
                        data: [systemData.memory_usage],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        // Initial load
        refreshData();

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
'''

    template_file = os.path.join(templates_dir, 'dashboard.html')
    if not os.path.exists(template_file):
        with open(template_file, 'w') as f:
            f.write(dashboard_template)
        print(f"✅ Created dashboard template: {template_file}")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Ensure template exists
    create_dashboard_template()
    return render_template('dashboard.html')

@app.route('/api/system-metrics')
def system_metrics():
    """Get system performance metrics"""
    try:
        import psutil

        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100

        # Network I/O
        network_io = psutil.net_io_counters()

        metrics = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'network_io': {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify(metrics)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scraper-metrics')
def scraper_metrics():
    """Get scraper performance metrics"""
    try:
        session = get_database_session()

        # Get recent scraping runs (last 24 hours)
        recent_runs = session.query(ScrapingRun).filter(
            ScrapingRun.start_time >= datetime.utcnow() - timedelta(hours=24)
        ).all()

        scraper_stats = {}

        for run in recent_runs:
            if run.scraper_name not in scraper_stats:
                scraper_stats[run.scraper_name] = {
                    'success_rate': 0.0,
                    'records_collected': 0,
                    'records_inserted': 0,
                    'execution_time': 0.0,
                    'last_run': run.start_time.isoformat(),
                    'error_count': 0
                }

            stats = scraper_stats[run.scraper_name]
            stats['records_collected'] += run.records_processed
            stats['records_inserted'] += run.records_created

            if run.status == 'completed':
                stats['success_rate'] = 100.0
            elif run.status == 'failed':
                stats['error_count'] += 1
                stats['success_rate'] = 0.0

            if run.end_time and run.start_time:
                execution_time = (run.end_time - run.start_time).total_seconds()
                stats['execution_time'] = max(stats['execution_time'], execution_time)

        session.close()

        return jsonify(scraper_stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-quality')
def data_quality():
    """Get data quality metrics"""
    try:
        session = get_database_session()

        # Total records
        total_records = session.query(Representative).count()

        # Complete records (have all required fields)
        complete_records = session.query(Representative).filter(
            Representative.name.isnot(None),
            Representative.role.isnot(None),
            Representative.jurisdiction_id.isnot(None)
        ).count()

        # Missing data count
        missing_data_count = total_records - complete_records

        # Duplicate records (same name and jurisdiction)
        duplicate_records = session.query(Representative).filter(
            Representative.name.isnot(None)
        ).group_by(Representative.name, Representative.jurisdiction_id).having(
            sa.func.count(Representative.id) > 1
        ).count()

        # Invalid records (missing required fields)
        invalid_records = session.query(Representative).filter(
            sa.or_(
                Representative.name.is_(None),
                Representative.role.is_(None),
                Representative.jurisdiction_id.is_(None)
            )
        ).count()

        # Calculate quality score
        if total_records > 0:
            quality_score = (complete_records / total_records) * 100
        else:
            quality_score = 0.0

        metrics = {
            'total_records': total_records,
            'complete_records': complete_records,
            'missing_data_count': missing_data_count,
            'duplicate_records': duplicate_records,
            'invalid_records': invalid_records,
            'quality_score': quality_score
        }

        session.close()

        return jsonify(metrics)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database-health')
def database_health():
    """Get database health status"""
    try:
        session = get_database_session()

        # Test connection
        session.execute(sa.text("SELECT 1"))

        # Check table counts
        representative_count = session.query(Representative).count()
        jurisdiction_count = session.query(Jurisdiction).count()

        # Check for recent errors
        recent_errors = session.query(DataQualityIssue).filter(
            DataQualityIssue.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()

        health_status = 'healthy'
        if representative_count == 0 or jurisdiction_count == 0:
            health_status = 'warning'
        if recent_errors > 10:
            health_status = 'critical'

        status = {
            'status': health_status,
            'representative_count': representative_count,
            'jurisdiction_count': jurisdiction_count,
            'recent_errors': recent_errors,
            'last_check': datetime.utcnow().isoformat()
        }

        session.close()

        return jsonify(status)

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'critical'}), 500

@app.route('/api/alerts')
def alerts():
    """Get recent alerts"""
    try:
        session = get_database_session()

        # Get recent data quality issues
        recent_issues = session.query(DataQualityIssue).filter(
            DataQualityIssue.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(DataQualityIssue.created_at.desc()).limit(10).all()

        alerts = []
        for issue in recent_issues:
            alerts.append({
                'type': 'data_quality',
                'severity': issue.severity,
                'message': issue.description,
                'timestamp': issue.created_at.isoformat()
            })

        session.close()

        return jsonify(alerts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary')
def summary():
    """Get overall system summary"""
    try:
        session = get_database_session()

        # System metrics
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent

        # Scraper metrics
        recent_runs = session.query(ScrapingRun).filter(
            ScrapingRun.start_time >= datetime.utcnow() - timedelta(hours=24)
        ).all()

        total_scrapers = len(set(run.scraper_name for run in recent_runs))
        successful_scrapers = len(set(run.scraper_name for run in recent_runs if run.status == 'completed'))
        success_rate = (successful_scrapers / total_scrapers * 100) if total_scrapers > 0 else 0

        # Data quality
        total_records = session.query(Representative).count()
        complete_records = session.query(Representative).filter(
            Representative.name.isnot(None),
            Representative.role.isnot(None),
            Representative.jurisdiction_id.isnot(None)
        ).count()

        quality_score = (complete_records / total_records * 100) if total_records > 0 else 0

        summary = {
            'system': {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'status': 'healthy' if cpu_usage < 80 and memory_usage < 85 else 'warning'
            },
            'scrapers': {
                'total': total_scrapers,
                'successful': successful_scrapers,
                'success_rate': success_rate,
                'status': 'healthy' if success_rate >= 80 else 'warning'
            },
            'data_quality': {
                'total_records': total_records,
                'complete_records': complete_records,
                'quality_score': quality_score,
                'status': 'healthy' if quality_score >= 85 else 'warning'
            },
            'overall_status': 'healthy'
        }

        # Determine overall status
        if (summary['system']['status'] == 'warning' or
            summary['scrapers']['status'] == 'warning' or
            summary['data_quality']['status'] == 'warning'):
            summary['overall_status'] = 'warning'

        session.close()

        return jsonify(summary)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Create dashboard template
    create_dashboard_template()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
