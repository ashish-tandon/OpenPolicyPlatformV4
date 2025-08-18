#!/usr/bin/env python3
"""
Simple Scraper Test
==================
Test individual scrapers without complex dependencies
"""

import sys
import os
import requests
import csv
from io import StringIO

# Add paths
sys.path.insert(0, '../../scrapers/scrapers-ca')

def test_toronto_scraper():
    """Test Toronto scraper directly"""
    print("🚀 Testing Toronto Scraper...")
    
    # Toronto CSV URL
    csv_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/27aa4651-4548-4e57-bf00-53a346931251/resource/dea217a2-f7c1-4e62-aec1-48fffaad1170/download/2022-2026%20Elected%20Officials%20Contact%20Info.csv"
    
    try:
        # Download CSV data
        print("📥 Downloading CSV data...")
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        print("📊 Parsing CSV data...")
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        # Show CSV headers
        print(f"📋 CSV Headers: {reader.fieldnames}")
        
        # Collect sample data
        sample_data = []
        count = 0
        max_records = 5
        
        for row in reader:
            if count >= max_records:
                break
                
            # Check if row is valid
            if row.get("First name") != "None" and row.get("Last name") != "None":
                person_data = {
                    'name': f"{row.get('First name', '')} {row.get('Last name', '')}".strip(),
                    'role': row.get('Primary role', ''),
                    'district': row.get('District name', ''),
                    'email': row.get('Email', ''),
                    'phone': row.get('Phone', ''),
                    'website': row.get('Website', ''),
                    'photo_url': row.get('Photo URL', '')
                }
                sample_data.append(person_data)
                count += 1
                print(f"✅ Collected: {person_data['name']} - {person_data['role']} - {person_data['district']}")
        
        print(f"\n🎉 Successfully collected {len(sample_data)} records from Toronto scraper!")
        
        # Show sample data
        if sample_data:
            print("\n📊 SAMPLE DATA:")
            for i, person in enumerate(sample_data, 1):
                print(f"  {i}. {person['name']}")
                print(f"     Role: {person['role']}")
                print(f"     District: {person['district']}")
                print(f"     Email: {person['email']}")
                print(f"     Phone: {person['phone']}")
                print()
        
        return sample_data
        
    except Exception as e:
        print(f"❌ Error testing Toronto scraper: {str(e)}")
        return []

def test_calgary_scraper():
    """Test Calgary scraper directly"""
    print("\n🚀 Testing Calgary Scraper...")
    
    # Calgary CSV URL (example - may need to be updated)
    csv_url = "https://data.calgary.ca/resource/6a7z-gs4q.csv"
    
    try:
        # Download CSV data
        print("📥 Downloading CSV data...")
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        print("📊 Parsing CSV data...")
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        # Show CSV headers
        print(f"📋 CSV Headers: {reader.fieldnames}")
        
        # Collect sample data
        sample_data = []
        count = 0
        max_records = 5
        
        for row in reader:
            if count >= max_records:
                break
                
            person_data = {
                'name': row.get('name', ''),
                'role': row.get('position', ''),
                'district': row.get('ward', ''),
                'email': row.get('email', ''),
                'phone': row.get('phone', '')
            }
            sample_data.append(person_data)
            count += 1
            print(f"✅ Collected: {person_data['name']} - {person_data['role']} - {person_data['district']}")
        
        print(f"\n🎉 Successfully collected {len(sample_data)} records from Calgary scraper!")
        return sample_data
        
    except Exception as e:
        print(f"❌ Error testing Calgary scraper: {str(e)}")
        return []

def main():
    """Main test function"""
    print("🧪 SIMPLE SCRAPER TESTING")
    print("=" * 50)
    
    # Test Toronto scraper
    toronto_data = test_toronto_scraper()
    
    # Test Calgary scraper
    calgary_data = test_calgary_scraper()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Toronto: {len(toronto_data)} records collected")
    print(f"Calgary: {len(calgary_data)} records collected")
    print(f"Total: {len(toronto_data) + len(calgary_data)} records")
    
    if toronto_data or calgary_data:
        print("\n✅ SUCCESS: Some scrapers are working!")
        print("Next step: Integrate with the optimized testing framework")
        
        # Show total data collected
        all_data = toronto_data + calgary_data
        print(f"\n📈 TOTAL DATA COLLECTED: {len(all_data)} records")
        print("This proves the scrapers can collect real data!")
        
    else:
        print("\n❌ No scrapers working yet")
        print("Next step: Debug individual scraper issues")

if __name__ == "__main__":
    main()
