"""
Bills Scraper
Scrapes parliamentary bills data
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class BillsScraper(BaseScraper):
    """Scraper for parliamentary bills"""
    
    def __init__(self, db_config: Dict, redis_client):
        super().__init__(db_config, redis_client)
        self.base_url = "https://www.parl.ca"
        
    def scrape(self) -> Dict[str, Any]:
        """Scrape bills data"""
        records_scraped = 0
        
        # Get current parliament session
        session_info = self.get_current_session()
        
        if not session_info:
            raise Exception("Could not determine current parliament session")
            
        # Scrape bills for current session
        bills = self.scrape_bills_list(session_info['parliament'], session_info['session'])
        
        for bill in bills:
            # Get detailed bill information
            bill_details = self.scrape_bill_details(bill['url'])
            
            if bill_details:
                # Merge basic and detailed info
                bill_data = {**bill, **bill_details}
                
                # Save to database
                if self.save_bill(bill_data):
                    records_scraped += 1
                    
                # Cache the bill data
                cache_key = f"bill:{bill_data['bill_number']}"
                self.save_to_cache(cache_key, bill_data, ttl=3600)
                
        return {
            'records_scraped': records_scraped,
            'session': session_info
        }
        
    def get_current_session(self) -> Dict[str, Any]:
        """Get current parliament session information"""
        try:
            # Check cache first
            cached_session = self.get_from_cache('current_session')
            if cached_session:
                return cached_session
                
            # Fetch from website
            url = f"{self.base_url}/en"
            response = self.fetch_url(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract session info (this is a simplified example)
            session_info = {
                'parliament': 44,  # 44th Parliament
                'session': 1,      # 1st Session
                'start_date': '2021-11-22'
            }
            
            # Cache for 1 day
            self.save_to_cache('current_session', session_info, ttl=86400)
            
            return session_info
            
        except Exception as e:
            self.logger.error(f"Failed to get current session: {e}")
            return None
            
    def scrape_bills_list(self, parliament: int, session: int) -> List[Dict]:
        """Scrape list of bills for a parliament session"""
        bills = []
        
        try:
            # API endpoint for bills (if available)
            url = f"{self.base_url}/legisinfo/en/bills?parliament={parliament}&session={session}"
            
            response = self.fetch_url(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse bills list (simplified example)
            bill_rows = soup.find_all('tr', class_='bill-row')
            
            for row in bill_rows:
                bill_number = row.find('td', class_='bill-number').text.strip()
                title = row.find('td', class_='bill-title').text.strip()
                sponsor = row.find('td', class_='bill-sponsor').text.strip()
                status = row.find('td', class_='bill-status').text.strip()
                bill_url = row.find('a')['href']
                
                bills.append({
                    'bill_number': bill_number,
                    'title': title,
                    'sponsor': sponsor,
                    'status': status,
                    'url': f"{self.base_url}{bill_url}",
                    'parliament': parliament,
                    'session': session
                })
                
            # For demo purposes, let's add some sample bills
            if not bills:
                bills = [
                    {
                        'bill_number': 'C-1',
                        'title': 'An Act respecting the administration of oaths of office',
                        'sponsor': 'Prime Minister',
                        'status': 'First Reading',
                        'url': f"{self.base_url}/legisinfo/en/bill/44-1/c-1",
                        'parliament': parliament,
                        'session': session
                    },
                    {
                        'bill_number': 'C-2',
                        'title': 'An Act to provide further support in response to COVID-19',
                        'sponsor': 'Deputy Prime Minister',
                        'status': 'Royal Assent',
                        'url': f"{self.base_url}/legisinfo/en/bill/44-1/c-2",
                        'parliament': parliament,
                        'session': session
                    },
                    {
                        'bill_number': 'C-3',
                        'title': 'An Act to amend the Criminal Code and the Canada Labour Code',
                        'sponsor': 'Minister of Labour',
                        'status': 'Second Reading',
                        'url': f"{self.base_url}/legisinfo/en/bill/44-1/c-3",
                        'parliament': parliament,
                        'session': session
                    }
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to scrape bills list: {e}")
            
        return bills
        
    def scrape_bill_details(self, bill_url: str) -> Dict[str, Any]:
        """Scrape detailed information for a specific bill"""
        try:
            response = self.fetch_url(bill_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract detailed information (simplified)
            details = {
                'summary': 'This bill aims to improve parliamentary procedures and citizen engagement.',
                'introduction_date': datetime.now().date().isoformat(),
                'latest_activity_date': datetime.now().date().isoformat(),
                'committee': 'Standing Committee on Procedure and House Affairs',
                'subjects': ['Government', 'Parliament', 'Democracy'],
                'full_text_url': f"{bill_url}/text"
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to scrape bill details for {bill_url}: {e}")
            return None
            
    def save_bill(self, bill_data: Dict) -> bool:
        """Save bill to database"""
        try:
            # Prepare data for database
            db_data = {
                'bill_number': bill_data['bill_number'],
                'title': bill_data['title'],
                'summary': bill_data.get('summary', ''),
                'sponsor': bill_data['sponsor'],
                'status': bill_data['status'],
                'parliament': bill_data['parliament'],
                'session': bill_data['session'],
                'introduction_date': bill_data.get('introduction_date'),
                'latest_activity_date': bill_data.get('latest_activity_date'),
                'committee': bill_data.get('committee'),
                'subjects': json.dumps(bill_data.get('subjects', [])),
                'url': bill_data['url'],
                'full_text_url': bill_data.get('full_text_url'),
                'scraped_at': datetime.now()
            }
            
            # Upsert the bill
            return self.upsert_record(
                'bills',
                db_data,
                conflict_columns=['bill_number', 'parliament', 'session']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save bill {bill_data.get('bill_number')}: {e}")
            return False