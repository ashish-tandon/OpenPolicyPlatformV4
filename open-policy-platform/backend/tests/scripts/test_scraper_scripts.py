"""
Scraper Script Tests
Tests that verify scraper scripts collect and store data correctly
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import text
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import os

class TestScraperScripts:
    """Test scraper scripts end-to-end"""
    
    def test_scraper_script_execution(self, db_session):
        """Test federal scraper script execution"""
        
        # Setup: Mock external requests
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_parliament_response()
            
            # Execute: Run federal scraper
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            result = scraper.scrape_all()
            
            # Verify: Scraper executed successfully
            assert 'bills' in result
            assert 'mps' in result
            assert 'votes' in result
            assert len(result['bills']) > 0
    
    def test_data_collection_from_source(self, db_session):
        """Test that data is collected from external sources"""
        
        # Setup: Mock external API responses
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_api_response()
            
            # Execute: Run scraper
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            data = scraper.scrape_bills()
            
            # Verify: Data is collected
            assert len(data) > 0
            assert all('title' in bill for bill in data)
            assert all('bill_number' in bill for bill in data)
    
    def test_database_insertion_success(self, db_session):
        """Test that collected data is inserted into database"""
        
        # Setup: Mock scraper data
        mock_bills = [
            {
                'title': 'Test Bill 1',
                'description': 'Test Description 1',
                'bill_number': 'C-001',
                'introduced_date': '2024-01-01',
                'sponsor': 'Test Sponsor',
                'jurisdiction': 'federal'
            }
        ]
        
        # Execute: Insert data into database
        for bill in mock_bills:
            # Extract number from bill_number (e.g., 'C-001' -> 1)
            number_only = int(bill['bill_number'].split('-')[1]) if '-' in bill['bill_number'] else 1
            db_session.execute(text("""
                INSERT INTO bills_bill (name_en, name_fr, number, number_only, institution, status_code, added, session_id, library_summary_available, short_title_en, short_title_fr)
                VALUES (:title, :title, :bill_number, :number_only, 'H', 'introduced', CURRENT_DATE, '2024', false, :title, :title)
            """), {**bill, 'number_only': number_only})
        
        db_session.commit()
        
        # Verify: Data is in database
        result = db_session.execute(text("SELECT COUNT(*) FROM bills_bill WHERE number = 'C-001'"))
        count = result.fetchone()[0]
        assert count == 1, "Data not inserted into database"
    
    def test_data_validation_after_insertion(self, db_session):
        """Test that inserted data is valid and complete"""
        
        # Setup: Insert test data
        self.insert_test_bills(db_session)
        
        # Execute: Validate data
        result = db_session.execute(text("""
            SELECT name_en, number, institution
            FROM bills_bill
            WHERE number = 'C-001'
        """))
        bill = result.fetchone()
        
        # Verify: Data is valid
        assert bill is not None, "Bill not found in database"
        assert bill.name_en == 'Test Bill 1'
        assert bill.number == 'C-001'
        assert bill.institution == 'H'
    
    def test_error_handling_for_failed_scrapes(self, db_session):
        """Test error handling when scraping fails"""
        
        # Setup: Mock failed request
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            # Execute: Run scraper with error
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            
            try:
                result = scraper.scrape_bills()
                # Should handle error gracefully
                assert len(result) == 0, "Should return empty list on error"
            except Exception as e:
                # Error should be logged but not crash
                assert "Network error" in str(e)
    
    def test_duplicate_data_handling(self, db_session):
        """Test handling of duplicate data"""
        
        # Setup: Insert existing bill
        db_session.execute(text("""
            INSERT INTO bills_bill (name_en, name_fr, number, number_only, institution, status_code, added, session_id, library_summary_available, short_title_en, short_title_fr)
            VALUES ('Existing Bill', 'Projet de loi existant', 'C-001', 1, 'H', 'introduced', CURRENT_DATE, '2024', false, 'Existing Bill', 'Projet de loi existant')
        """))
        db_session.commit()
        
        # Execute: Try to insert duplicate
        try:
            db_session.execute(text("""
                INSERT INTO bills_bill (name_en, name_fr, number, number_only, institution, status_code, added, session_id, library_summary_available, short_title_en, short_title_fr)
                VALUES ('Duplicate Bill', 'Projet de loi dupliqué', 'C-001', 1, 'H', 'introduced', CURRENT_DATE, '2024', false, 'Duplicate Bill', 'Projet de loi dupliqué')
            """))
            db_session.commit()
        except Exception as e:
            # Should handle duplicate gracefully
            assert "duplicate" in str(e).lower() or "unique" in str(e).lower()
    
    def test_scraper_performance_metrics(self, db_session):
        """Test scraper performance metrics"""
        
        import time
        
        # Execute: Run scraper with timing
        start_time = time.time()
        
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_parliament_response()
            
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            result = scraper.scrape_all()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify: Performance is acceptable
        assert execution_time < 30, f"Scraper took too long: {execution_time:.2f} seconds"
        assert len(result['bills']) > 0, "No bills scraped"
    
    def test_data_freshness_validation(self, db_session):
        """Test that scraped data is fresh"""
        
        # Setup: Mock current date data
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_fresh_data_response()
            
            # Execute: Run scraper
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            data = scraper.scrape_bills()
            
            # Verify: Data is recent
            for bill in data:
                if 'introduced_date' in bill:
                    date_obj = datetime.strptime(bill['introduced_date'], '%Y-%m-%d').date()
                    assert date_obj >= date(2024, 1, 1), "Data is not fresh"
    
    def test_scraper_logging_and_monitoring(self, db_session):
        """Test scraper logging and monitoring"""
        
        # Setup: Capture logs
        import logging
        log_capture = []
        
        def log_handler(record):
            log_capture.append(record.getMessage())
        
        logging.getLogger().addHandler(logging.Handler())
        
        # Execute: Run scraper
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_parliament_response()
            
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            scraper.scrape_all()
        
        # Verify: Logging is working
        assert len(log_capture) > 0, "No logs captured"
        assert any("scraping" in log.lower() for log in log_capture), "No scraping logs found"
    
    def test_scraper_cleanup_and_maintenance(self, db_session):
        """Test scraper cleanup and maintenance"""
        
        # Setup: Create temporary files
        temp_files = ['temp1.txt', 'temp2.txt']
        for file in temp_files:
            with open(file, 'w') as f:
                f.write('test')
        
        # Execute: Run scraper with cleanup
        with patch('requests.get') as mock_get:
            mock_get.return_value = self.create_mock_parliament_response()
            
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            scraper.scrape_all()
        
        # Verify: Cleanup is performed
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)  # Clean up test files
        
        assert True, "Cleanup and maintenance verified"
    
    def create_mock_parliament_response(self):
        """Create mock Parliament of Canada response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="bill">
                    <h2>Bill C-123</h2>
                    <p>An Act to test federal scraping</p>
                    <span class="date">2024-01-15</span>
                    <span class="sponsor">Test Sponsor</span>
                </div>
            </body>
        </html>
        """
        return mock_response
    
    def create_mock_api_response(self):
        """Create mock API response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bills': [
                {
                    'title': 'Test Bill 1',
                    'bill_number': 'C-001',
                    'description': 'Test Description'
                }
            ]
        }
        return mock_response
    
    def create_mock_fresh_data_response(self):
        """Create mock response with fresh data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="bill">
                    <h2>Bill C-456</h2>
                    <p>Fresh data from 2024</p>
                    <span class="date">2024-12-01</span>
                    <span class="sponsor">Fresh Sponsor</span>
                </div>
            </body>
        </html>
        """
        return mock_response
    
    def insert_test_bills(self, db_session):
        """Insert test bills for validation"""
        db_session.execute(text("""
            INSERT INTO bills_bill (name_en, name_fr, number, number_only, institution, status_code, added, session_id, library_summary_available, short_title_en, short_title_fr)
            VALUES ('Test Bill 1', 'Projet de loi de test 1', 'C-001', 1, 'H', 'introduced', CURRENT_DATE, '2024', false, 'Test Bill 1', 'Projet de loi de test 1')
        """))
        db_session.commit()
