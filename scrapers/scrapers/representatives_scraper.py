"""Representatives Scraper - Gets MPs/Representatives data"""

from datetime import datetime
from typing import Dict, Any
from .base_scraper import BaseScraper


class RepresentativesScraper(BaseScraper):
    """Scraper for representatives/MPs"""
    
    def scrape(self) -> Dict[str, Any]:
        """Scrape representatives data"""
        records_scraped = 0
        
        # Sample representatives data
        representatives = [
            {
                'name': 'Justin Trudeau',
                'email': 'justin.trudeau@parl.gc.ca',
                'phone': '613-995-0253',
                'party': 'Liberal',
                'constituency': 'Papineau',
                'province': 'Quebec',
                'photo_url': 'https://www.parl.ca/members/photos/trudeau-justin.jpg',
                'bio': 'Prime Minister of Canada',
                'active': True
            },
            {
                'name': 'Pierre Poilievre',
                'email': 'pierre.poilievre@parl.gc.ca',
                'phone': '613-992-2772',
                'party': 'Conservative',
                'constituency': 'Carleton',
                'province': 'Ontario',
                'photo_url': 'https://www.parl.ca/members/photos/poilievre-pierre.jpg',
                'bio': 'Leader of the Official Opposition',
                'active': True
            },
            {
                'name': 'Jagmeet Singh',
                'email': 'jagmeet.singh@parl.gc.ca',
                'phone': '613-996-5597',
                'party': 'NDP',
                'constituency': 'Burnaby South',
                'province': 'British Columbia',
                'photo_url': 'https://www.parl.ca/members/photos/singh-jagmeet.jpg',
                'bio': 'Leader of the New Democratic Party',
                'active': True
            }
        ]
        
        for rep in representatives:
            if self.save_representative(rep):
                records_scraped += 1
                
        return {'records_scraped': records_scraped}
        
    def save_representative(self, rep: Dict) -> bool:
        """Save representative to database"""
        return self.upsert_record(
            'representatives',
            rep,
            conflict_columns=['email']
        )