"""
Federal Parliament Scraper
Collects data from the Parliament of Canada
"""

import requests
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)

class FederalParliamentScraper:
    """Scraper for Federal Parliament of Canada data"""
    
    def __init__(self):
        self.base_url = "https://www.parl.ca"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_bills(self) -> List[Dict]:
        """Scrape bills from Parliament of Canada"""
        logger.info("Starting federal bills scraping")
        
        bills = []
        try:
            # Parliament bills URL
            bills_url = f"{self.base_url}/LegisInfo/en/Bills"
            response = self.session.get(bills_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find bill listings
            bill_elements = soup.find_all('div', class_='bill-item')
            
            for bill_element in bill_elements:
                try:
                    bill_data = self._parse_bill_element(bill_element)
                    if bill_data:
                        bills.append(bill_data)
                except Exception as e:
                    logger.error(f"Error parsing bill element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping federal bills: {e}")
            
        logger.info(f"Scraped {len(bills)} federal bills")
        return bills
    
    def scrape_mps(self) -> List[Dict]:
        """Scrape Members of Parliament data"""
        logger.info("Starting federal MPs scraping")
        
        mps = []
        try:
            # Parliament MPs URL
            mps_url = f"{self.base_url}/Members/en"
            response = self.session.get(mps_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find MP listings
            mp_elements = soup.find_all('div', class_='member-item')
            
            for mp_element in mp_elements:
                try:
                    mp_data = self._parse_mp_element(mp_element)
                    if mp_data:
                        mps.append(mp_data)
                except Exception as e:
                    logger.error(f"Error parsing MP element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping federal MPs: {e}")
            
        logger.info(f"Scraped {len(mps)} federal MPs")
        return mps
    
    def scrape_votes(self) -> List[Dict]:
        """Scrape voting data"""
        logger.info("Starting federal votes scraping")
        
        votes = []
        try:
            # Parliament votes URL
            votes_url = f"{self.base_url}/Votes"
            response = self.session.get(votes_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find vote listings
            vote_elements = soup.find_all('div', class_='vote-item')
            
            for vote_element in vote_elements:
                try:
                    vote_data = self._parse_vote_element(vote_element)
                    if vote_data:
                        votes.append(vote_data)
                except Exception as e:
                    logger.error(f"Error parsing vote element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping federal votes: {e}")
            
        logger.info(f"Scraped {len(votes)} federal votes")
        return votes
    
    def _parse_bill_element(self, element) -> Optional[Dict]:
        """Parse individual bill element"""
        try:
            # Extract bill title
            title_element = element.find('h2') or element.find('h3')
            title = title_element.get_text(strip=True) if title_element else None
            
            # Extract bill description
            desc_element = element.find('p')
            description = desc_element.get_text(strip=True) if desc_element else None
            
            # Extract bill date
            date_element = element.find('span', class_='date')
            introduced_date = None
            if date_element:
                date_text = date_element.get_text(strip=True)
                try:
                    introduced_date = datetime.strptime(date_text, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date format: {date_text}")
            
            # Extract sponsor
            sponsor_element = element.find('span', class_='sponsor')
            sponsor = sponsor_element.get_text(strip=True) if sponsor_element else None
            
            # Extract bill number
            bill_number = None
            if title and 'Bill' in title:
                # Extract bill number from title (e.g., "Bill C-123")
                import re
                match = re.search(r'Bill\s+([A-Z]-\d+)', title)
                if match:
                    bill_number = match.group(1)
            
            if not title:
                return None
                
            return {
                'title': title,
                'description': description,
                'introduced_date': introduced_date,
                'sponsor': sponsor,
                'bill_number': bill_number,
                'jurisdiction': 'federal',
                'status': 'introduced',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing bill element: {e}")
            return None
    
    def _parse_mp_element(self, element) -> Optional[Dict]:
        """Parse individual MP element"""
        try:
            # Extract MP name
            name_element = element.find('h3') or element.find('h4')
            name = name_element.get_text(strip=True) if name_element else None
            
            # Extract party
            party_element = element.find('span', class_='party')
            party = party_element.get_text(strip=True) if party_element else None
            
            # Extract constituency
            constituency_element = element.find('span', class_='constituency')
            constituency = constituency_element.get_text(strip=True) if constituency_element else None
            
            # Extract email
            email_element = element.find('a', href=lambda x: x and 'mailto:' in x)
            email = None
            if email_element:
                email = email_element['href'].replace('mailto:', '')
            
            # Extract phone
            phone_element = element.find('span', class_='phone')
            phone = phone_element.get_text(strip=True) if phone_element else None
            
            if not name:
                return None
                
            return {
                'name': name,
                'party': party,
                'constituency': constituency,
                'email': email,
                'phone': phone,
                'jurisdiction': 'federal',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing MP element: {e}")
            return None
    
    def _parse_vote_element(self, element) -> Optional[Dict]:
        """Parse individual vote element"""
        try:
            # Extract bill number
            bill_element = element.find('span', class_='bill-number')
            bill_number = bill_element.get_text(strip=True) if bill_element else None
            
            # Extract vote date
            date_element = element.find('span', class_='vote-date')
            vote_date = None
            if date_element:
                date_text = date_element.get_text(strip=True)
                try:
                    vote_date = datetime.strptime(date_text, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid vote date format: {date_text}")
            
            # Extract vote type
            type_element = element.find('span', class_='vote-type')
            vote_type = type_element.get_text(strip=True) if type_element else None
            
            # Extract result
            result_element = element.find('span', class_='vote-result')
            result = result_element.get_text(strip=True) if result_element else None
            
            # Extract vote counts
            yea_element = element.find('span', class_='yea-votes')
            yea_votes = int(yea_element.get_text(strip=True)) if yea_element else 0
            
            nay_element = element.find('span', class_='nay-votes')
            nay_votes = int(nay_element.get_text(strip=True)) if nay_element else 0
            
            abstain_element = element.find('span', class_='abstentions')
            abstentions = int(abstain_element.get_text(strip=True)) if abstain_element else 0
            
            if not bill_number or not vote_date:
                return None
                
            return {
                'bill_number': bill_number,
                'vote_date': vote_date,
                'vote_type': vote_type,
                'result': result,
                'yea_votes': yea_votes,
                'nay_votes': nay_votes,
                'abstentions': abstentions,
                'jurisdiction': 'federal',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing vote element: {e}")
            return None
    
    def scrape_all(self) -> Dict[str, List[Dict]]:
        """Scrape all federal parliament data"""
        logger.info("Starting comprehensive federal parliament scraping")
        
        # Add random delay to be respectful
        time.sleep(random.uniform(1, 3))
        
        result = {
            'bills': self.scrape_bills(),
            'mps': self.scrape_mps(),
            'votes': self.scrape_votes()
        }
        
        logger.info(f"Federal scraping completed: {len(result['bills'])} bills, {len(result['mps'])} MPs, {len(result['votes'])} votes")
        return result
    
    def validate_data(self, data: Dict[str, List[Dict]]) -> bool:
        """Validate scraped data"""
        logger.info("Validating federal scraped data")
        
        try:
            # Validate bills
            for bill in data.get('bills', []):
                required_fields = ['title', 'jurisdiction']
                for field in required_fields:
                    if field not in bill or not bill[field]:
                        logger.error(f"Bill missing required field: {field}")
                        return False
            
            # Validate MPs
            for mp in data.get('mps', []):
                required_fields = ['name', 'jurisdiction']
                for field in required_fields:
                    if field not in mp or not mp[field]:
                        logger.error(f"MP missing required field: {field}")
                        return False
            
            # Validate votes
            for vote in data.get('votes', []):
                required_fields = ['bill_number', 'vote_date', 'jurisdiction']
                for field in required_fields:
                    if field not in vote or not vote[field]:
                        logger.error(f"Vote missing required field: {field}")
                        return False
            
            logger.info("Federal data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating federal data: {e}")
            return False
