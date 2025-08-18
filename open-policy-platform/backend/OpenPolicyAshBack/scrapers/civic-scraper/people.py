#!/usr/bin/env python3
"""
Basic people scraper for civic-scraper
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from utils import CSVScraper
except ImportError:
    # Fallback for missing utils
    class CSVScraper:
        def __init__(self):
            self.csv_url = None
            self.organization_classification = "legislature"
        
        def scrape(self):
            return []

class CivicPersonScraper(CSVScraper):
    organization_classification = "legislature"
    
    def __init__(self, jurisdiction, datadir):
        self.jurisdiction = jurisdiction
        self.datadir = datadir
        super().__init__()
    
    def scrape(self):
        # Basic implementation - returns empty list for now
        return []
