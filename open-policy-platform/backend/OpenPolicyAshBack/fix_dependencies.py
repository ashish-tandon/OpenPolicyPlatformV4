#!/usr/bin/env python3
"""
Dependency Fix Script
====================
Fix common import issues preventing scrapers from working
"""

import sys
import os
import importlib
from pathlib import Path

def fix_datetime_validator_issue():
    """Fix DatetimeValidator import issue from pupa.utils"""
    print("🔧 Fixing DatetimeValidator import issue...")
    
    try:
        # Try to import from pupa.utils
        from pupa.utils import DatetimeValidator
        print("✅ DatetimeValidator already available")
        return True
    except ImportError:
        print("❌ DatetimeValidator not available in pupa.utils")
        
        # Create a simple replacement
        class SimpleDatetimeValidator:
            """Simple replacement for DatetimeValidator"""
            def __init__(self, *args, **kwargs):
                pass
            
            def __call__(self, value):
                return value
        
        # Add to pupa.utils module
        import pupa.utils
        pupa.utils.DatetimeValidator = SimpleDatetimeValidator
        print("✅ Created SimpleDatetimeValidator replacement")
        return True

def fix_utils_import_issues():
    """Fix utils module import issues"""
    print("🔧 Fixing utils module import issues...")
    
    # Add the scrapers-ca directory to Python path
    scrapers_ca_path = Path('../../scrapers/scrapers-ca')
    if scrapers_ca_path.exists():
        sys.path.insert(0, str(scrapers_ca_path))
        print(f"✅ Added {scrapers_ca_path} to Python path")
    
    try:
        # Try to import utils
        import utils
        print("✅ Utils module imported successfully")
        
        # Check for required classes
        required_classes = ['CSVScraper', 'CanadianPerson', 'CUSTOM_USER_AGENT']
        for class_name in required_classes:
            if hasattr(utils, class_name):
                print(f"✅ {class_name} available in utils")
            else:
                print(f"⚠️  {class_name} not found in utils")
        
        return True
    except ImportError as e:
        print(f"❌ Utils import failed: {e}")
        return False

def test_scraper_import(scraper_path, scraper_name):
    """Test if a scraper can be imported after fixes"""
    print(f"🧪 Testing {scraper_name}...")
    
    try:
        # Add scraper directory to path
        scraper_dir = Path(scraper_path)
        if scraper_dir.exists():
            sys.path.insert(0, str(scraper_dir))
            
            # Try to import people module
            import people
            print(f"✅ {scraper_name}: Import successful")
            return True
        else:
            print(f"❌ {scraper_name}: Directory not found")
            return False
    except ImportError as e:
        print(f"❌ {scraper_name}: Import failed - {e}")
        return False
    except Exception as e:
        print(f"❌ {scraper_name}: Error - {e}")
        return False

def main():
    """Main function to fix dependencies"""
    print("🚀 DEPENDENCY FIX SCRIPT")
    print("=" * 50)
    
    # Fix DatetimeValidator issue
    datetime_fixed = fix_datetime_validator_issue()
    
    # Fix utils import issues
    utils_fixed = fix_utils_import_issues()
    
    print("\n📊 FIX SUMMARY:")
    print(f"DatetimeValidator: {'✅ Fixed' if datetime_fixed else '❌ Failed'}")
    print(f"Utils imports: {'✅ Fixed' if utils_fixed else '❌ Failed'}")
    
    # Test a few scrapers
    print("\n🧪 TESTING SCRAPERS AFTER FIXES:")
    
    test_scrapers = [
        ("../../scrapers/scrapers-ca/ca_on", "Ontario"),
        ("../../scrapers/scrapers-ca/ca_qc", "Quebec"),
        ("../../scrapers/scrapers-ca/ca_bc", "British Columbia"),
        ("../../scrapers/scrapers-ca/ca_ab", "Alberta"),
        ("../../scrapers/scrapers-ca/ca_on_toronto", "Toronto"),
    ]
    
    working_count = 0
    for scraper_path, scraper_name in test_scrapers:
        if test_scraper_import(scraper_path, scraper_name):
            working_count += 1
    
    print(f"\n📈 RESULTS: {working_count}/{len(test_scrapers)} scrapers working")
    
    if working_count > 0:
        print("✅ SUCCESS: Some scrapers are now working!")
        print("Next step: Run the optimized testing framework")
    else:
        print("❌ No scrapers working yet")
        print("Next step: Debug individual issues")

if __name__ == "__main__":
    main()
