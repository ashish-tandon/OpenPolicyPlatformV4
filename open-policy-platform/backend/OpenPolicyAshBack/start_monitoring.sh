#!/bin/bash

# Quick Start Script for Scraper Monitoring System
# ===============================================

echo "🚀 Starting Scraper Monitoring System..."
echo "========================================"

# Check if we're in the right directory
if [ ! -f "scraper_monitoring_dashboard.py" ]; then
    echo "❌ Error: Please run this script from the backend/OpenPolicyAshBack directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if background execution is running
echo "🔍 Checking background execution status..."
if pgrep -f "background_scraper_execution.py" > /dev/null; then
    echo "✅ Background execution system is running"
else
    echo "⚠️  Background execution system is not running"
    echo "   To start it, run: python3 background_scraper_execution.py &"
fi

# Start monitoring dashboard
echo "📊 Starting monitoring dashboard..."
echo "   Press Ctrl+C to stop monitoring"
echo ""

python3 scraper_monitoring_dashboard.py
