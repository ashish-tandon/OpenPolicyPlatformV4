#!/bin/bash
# Quick Start Scraper Testing
# ===========================
# This script immediately starts testing scrapers in parallel
# without getting stuck on individual scrapers.
# NOW WITH OPTIMIZED PARALLEL EXECUTION - Dynamic worker scaling (10-20)!

set -e  # Exit on any error

echo "🚀 QUICK START - OPTIMIZED PARALLEL SCRAPER TESTING"
echo "=================================================="
echo ""
echo "This will start testing ALL scrapers with OPTIMIZED parallel execution."
echo "Dynamic worker scaling (10-20) based on scraper size and system resources!"
echo "No more waiting for individual scrapers to finish!"
echo ""

# Check if we're in the right directory
if [ ! -f "scraper_testing_framework.py" ]; then
    echo "❌ Error: scraper_testing_framework.py not found"
    echo "Please run this script from the backend/OpenPolicyAshBack directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Running setup first..."
    ./setup_scraper_testing.sh
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check database connection
echo "🔍 Checking database connection..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Using default..."
    export DATABASE_URL="postgresql://user:pass@localhost/openpolicy"
fi

# Display system information
echo ""
echo "💻 SYSTEM INFORMATION:"
echo "======================"
echo "CPU Cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "Unknown")"
echo "Memory: $(free -h 2>/dev/null | grep Mem | awk '{print $2}' || echo "Unknown")"
echo "Python: $(python3 --version)"
echo ""

# Start optimized parallel testing immediately
echo ""
echo "🎯 STARTING OPTIMIZED PARALLEL SCRAPER TESTING"
echo "=============================================="
echo "Features:"
echo "  ✅ Dynamic worker scaling (10-20 workers)"
echo "  ✅ Size-based optimization (Small/Medium/Large scrapers)"
echo "  ✅ System resource monitoring"
echo "  ✅ 5 sample records per scraper"
echo "  ✅ Size-appropriate timeouts (3-10 minutes)"
echo "  ✅ Automatic error handling"
echo "  ✅ Real-time progress updates"
echo "  ✅ Database insertion testing"
echo "  ✅ Performance metrics tracking"
echo ""

# Run the optimized parallel testing framework
echo "🚀 Starting optimized scraper testing framework..."
python3 scraper_testing_framework.py

echo ""
echo "✅ OPTIMIZED PARALLEL TESTING COMPLETED!"
echo ""
echo "📊 Check the results:"
echo "  - Test report: scraper_test_report_*.json"
echo "  - Logs: scraper_testing.log"
echo "  - Database: Check for inserted sample data"
echo "  - Performance: CPU and memory usage tracked"
echo ""
echo "🔄 Next steps:"
echo "  1. Review test results and fix any issues"
echo "  2. Run full data collection: python3 scraper_testing_framework.py --max-records 100"
echo "  3. Start background monitoring: python3 scraper_monitoring_system.py"
echo "  4. Optimize further based on performance metrics"
echo ""
echo "📚 Documentation:"
echo "  - SCRAPER_DEVELOPMENT_PLAN.md"
echo "  - REQUIREMENTS_MANAGEMENT.md"
echo ""
echo "🎉 All scrapers tested with optimized parallel execution!"
echo "   Dynamic scaling based on scraper size and system resources!"
