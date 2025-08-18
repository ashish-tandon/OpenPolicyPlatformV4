#!/usr/bin/env python3
"""
Quick Scraper Test Runner
=========================

This script provides a simple way to start testing scrapers immediately.
It runs the comprehensive testing framework with sample data to get
the development process started quickly.

Usage:
    python run_scraper_tests.py                    # Test all scrapers with 5 sample records
    python run_scraper_tests.py --category all     # Test all categories
    python run_scraper_tests.py --category parliamentary  # Test only parliamentary
    python run_scraper_tests.py --max-records 10   # Test with 10 sample records
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Quick Scraper Test Runner')
    parser.add_argument('--category', choices=['all', 'parliamentary', 'provincial', 'municipal', 'civic'], 
                       default='all', help='Category to test')
    parser.add_argument('--max-records', type=int, default=5, 
                       help='Maximum sample records per scraper')
    parser.add_argument('--database-url', 
                       default='postgresql://user:pass@localhost/openpolicy',
                       help='Database connection URL')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("🚀 Starting Quick Scraper Tests")
    print("=" * 50)
    print(f"Category: {args.category}")
    print(f"Max Records: {args.max_records}")
    print(f"Database: {args.database_url}")
    print("=" * 50)
    
    # Set environment variable
    os.environ['DATABASE_URL'] = args.database_url
    
    # Check if we're in the right directory
    if not Path('scraper_testing_framework.py').exists():
        print("❌ Error: scraper_testing_framework.py not found")
        print("Please run this script from the backend/OpenPolicyAshBack directory")
        return 1
    
    # Run the testing framework
    try:
        cmd = [
            sys.executable, 'scraper_testing_framework.py',
            '--max-sample-records', str(args.max_records)
        ]
        
        if args.category != 'all':
            cmd.extend(['--category', args.category])
        
        if args.verbose:
            cmd.append('--verbose')
        
        print(f"Running: {' '.join(cmd)}")
        print()
        
        # Run the command
        result = subprocess.run(cmd, capture_output=not args.verbose, text=True)
        
        if result.returncode == 0:
            print("\n✅ Scraper tests completed successfully!")
            
            # Check for report file
            report_files = list(Path('.').glob('scraper_test_report_*.json'))
            if report_files:
                latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
                print(f"📄 Test report saved to: {latest_report}")
            
            return 0
        else:
            print(f"\n❌ Scraper tests failed with return code: {result.returncode}")
            if not args.verbose and result.stderr:
                print("Error output:")
                print(result.stderr)
            return result.returncode
            
    except Exception as e:
        print(f"❌ Error running scraper tests: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
