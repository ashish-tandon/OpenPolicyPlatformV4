#!/bin/bash

# Daily Scraper Execution Script
# This script runs all active scrapers according to their schedule

set -e

echo "Starting daily scraper execution at $(date)"

# Activate virtual environment
source backend/venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Run scraper execution script
cd backend
python scripts/execute_daily_scrapers.py

echo "Daily scraper execution completed at $(date)"
