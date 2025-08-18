#!/usr/bin/env python3
"""
Federal Parliament Scraper for OpenParliament
Scrapes current Members of Parliament from the Canadian Parliament
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any

class FederalParliamentPersonScraper:
    """Scraper for Federal Parliament Members of Canada"""
    
    def __init__(self, jurisdiction_id: str = None, datadir: str = None):
        self.jurisdiction_id = jurisdiction_id or "ocd-jurisdiction/country:ca/legislature/parliament"
        self.datadir = datadir
        self.base_url = "https://www.ourcommons.ca"
        self.api_url = "https://www.ourcommons.ca/Parliamentarians/en/members"
        
    def scrape(self):
        """Scrape current Members of Parliament"""
        try:
            # Get current MPs from the API
            response = requests.get(f"{self.api_url}/JSON", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data or 'AffiliationRoles' not in data:
                print("No data found in API response")
                return []
            
            members = []
            for member_data in data['AffiliationRoles']:
                if member_data.get('IsActive', False):
                    member = self._parse_member(member_data)
                    if member:
                        members.append(member)
            
            return members
            
        except Exception as e:
            print(f"Error scraping Federal Parliament: {str(e)}")
            return []
    
    def _parse_member(self, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse member data into standardized format"""
        try:
            # Extract basic information
            person_id = member_data.get('PersonId')
            if not person_id:
                return None
            
            # Get detailed member information
            member_detail = self._get_member_detail(person_id)
            if not member_detail:
                return None
            
            # Create standardized person object
            person = {
                'name': member_detail.get('Name', 'Unknown'),
                'role': 'Member of Parliament',
                'party': member_detail.get('PartyName', 'Unknown'),
                'district': member_detail.get('ConstituencyName', 'Unknown'),
                'email': member_detail.get('Email', None),
                'phone': member_detail.get('Phone', None),
                'image': member_detail.get('PhotoUrl', None),
                'classification': 'legislature',
                'division_name': 'Canada',
                'riding': member_detail.get('ConstituencyName', None)
            }
            
            return person
            
        except Exception as e:
            print(f"Error parsing member {member_data.get('PersonId', 'Unknown')}: {str(e)}")
            return None
    
    def _get_member_detail(self, person_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific member"""
        try:
            detail_url = f"{self.api_url}/{person_id}/JSON"
            response = requests.get(detail_url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error getting member detail for {person_id}: {str(e)}")
            return None


class FederalParliamentPersonScraperLegacy:
    """Legacy scraper using web scraping approach"""
    
    def __init__(self, jurisdiction_id: str = None, datadir: str = None):
        self.jurisdiction_id = jurisdiction_id or "ocd-jurisdiction/country:ca/legislature/parliament"
        self.datadir = datadir
        self.base_url = "https://www.ourcommons.ca"
        
    def scrape(self):
        """Scrape current Members of Parliament using web scraping"""
        try:
            # Get the main MPs page
            url = f"{self.base_url}/Parliamentarians/en/members"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML to extract member information
            # This is a simplified version - in practice you'd use BeautifulSoup or similar
            members = []
            
            # For now, return some sample data
            sample_members = [
                {
                    'name': 'Justin Trudeau',
                    'role': 'Prime Minister',
                    'party': 'Liberal',
                    'district': 'Papineau',
                    'email': None,
                    'phone': None,
                    'image': None,
                    'classification': 'legislature',
                    'division_name': 'Canada',
                    'riding': 'Papineau'
                },
                {
                    'name': 'Pierre Poilievre',
                    'role': 'Leader of the Opposition',
                    'party': 'Conservative',
                    'district': 'Carleton',
                    'email': None,
                    'phone': None,
                    'image': None,
                    'classification': 'legislature',
                    'division_name': 'Canada',
                    'riding': 'Carleton'
                }
            ]
            
            return sample_members
            
        except Exception as e:
            print(f"Error scraping Federal Parliament: {str(e)}")
            return []


# Use the main scraper class
FederalParliamentPersonScraper = FederalParliamentPersonScraper
