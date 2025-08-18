"""
Performance Tests
Tests that verify system performance meets requirements
"""

import pytest
import time
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy import text
import requests

class TestPerformanceMetrics:
    """Test system performance metrics"""
    
    def test_api_response_times(self, client, db_session):
        """Test API response times meet performance requirements"""
        
        # Setup: Insert test data
        for i in range(100):
            db_session.execute(text("""
                INSERT INTO bills_bill (title, description, bill_number, introduced_date, sponsor, jurisdiction)
                VALUES (:title, :description, :bill_number, :introduced_date, :sponsor, :jurisdiction)
            """), {
                "title": f"Test Bill {i}",
                "description": f"Test Description {i}",
                "bill_number": f"C-{i:03d}",
                "introduced_date": "2024-01-01",
                "sponsor": f"Test Sponsor {i}",
                "jurisdiction": "federal"
            })
        db_session.commit()
        
        # Test response times for different endpoints
        endpoints = [
            "/api/policies",
            "/api/representatives",
            "/api/committees",
            "/api/health",
            "/api/policies/search",
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Verify: Response time is within acceptable limits
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            assert response_time < 500, f"Response time {response_time}ms exceeds 500ms limit for {endpoint}"
            
            # Verify: Response time is reasonable (should be much faster)
            assert response_time < 100, f"Response time {response_time}ms is too slow for {endpoint}"
    
    def test_database_query_performance(self, client, db_session):
        """Test database query performance"""
        
        # Setup: Insert large dataset
        for i in range(1000):
            db_session.execute(text("""
                INSERT INTO bills_bill (title, description, bill_number, introduced_date, sponsor, jurisdiction)
                VALUES (:title, :description, :bill_number, :introduced_date, :sponsor, :jurisdiction)
            """), {
                "title": f"Performance Test Bill {i}",
                "description": f"Performance Test Description {i}",
                "bill_number": f"P-{i:04d}",
                "introduced_date": "2024-01-01",
                "sponsor": f"Performance Sponsor {i}",
                "jurisdiction": "federal"
            })
        db_session.commit()
        
        # Test simple query performance
        start_time = time.time()
        result = db_session.execute(text("SELECT COUNT(*) FROM bills_bill"))
        count = result.fetchone()[0]
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        # Verify: Simple query is fast
        assert query_time < 50, f"Simple COUNT query took {query_time}ms"
        assert count >= 1000, f"Expected at least 1000 records, got {count}"
        
        # Test complex query performance
        start_time = time.time()
        result = db_session.execute(text("""
            SELECT b.title, b.bill_number, b.sponsor, b.jurisdiction
            FROM bills_bill b
            WHERE b.jurisdiction = 'federal'
            AND b.introduced_date >= '2024-01-01'
            ORDER BY b.introduced_date DESC
            LIMIT 100
        """))
        bills = result.fetchall()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        # Verify: Complex query is reasonably fast
        assert query_time < 100, f"Complex query took {query_time}ms"
        assert len(bills) <= 100, f"Expected max 100 records, got {len(bills)}"
        
        # Test search query performance
        start_time = time.time()
        result = db_session.execute(text("""
            SELECT title, bill_number, sponsor
            FROM bills_bill
            WHERE title ILIKE '%Performance%'
            OR description ILIKE '%Performance%'
        """))
        search_results = result.fetchall()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        # Verify: Search query is fast
        assert query_time < 200, f"Search query took {query_time}ms"
        assert len(search_results) > 0, "Search should return results"
    
    def test_frontend_loading_times(self):
        """Test frontend loading times"""
        
        # Test main page loading time
        start_time = time.time()
        response = requests.get("http://localhost:5173", timeout=10)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000
        
        # Verify: Main page loads quickly
        assert response.status_code == 200, "Main page failed to load"
        assert load_time < 2000, f"Main page took {load_time}ms to load"
        
        # Test bills page loading time
        start_time = time.time()
        response = requests.get("http://localhost:5173/bills", timeout=10)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000
        
        # Verify: Bills page loads quickly
        assert response.status_code == 200, "Bills page failed to load"
        assert load_time < 2000, f"Bills page took {load_time}ms to load"
        
        # Test representatives page loading time
        start_time = time.time()
        response = requests.get("http://localhost:5173/representatives", timeout=10)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000
        
        # Verify: Representatives page loads quickly
        assert response.status_code == 200, "Representatives page failed to load"
        assert load_time < 2000, f"Representatives page took {load_time}ms to load"
        
        # Test search page loading time
        start_time = time.time()
        response = requests.get("http://localhost:5173/search", timeout=10)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000
        
        # Verify: Search page loads quickly
        assert response.status_code == 200, "Search page failed to load"
        assert load_time < 2000, f"Search page took {load_time}ms to load"
        
        # Test admin dashboard loading time
        start_time = time.time()
        response = requests.get("http://localhost:5173/admin/dashboard", timeout=10)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000
        
        # Verify: Admin dashboard loads quickly
        assert response.status_code == 200, "Admin dashboard failed to load"
        assert load_time < 3000, f"Admin dashboard took {load_time}ms to load"
    
    def test_scraper_performance(self, client, db_session):
        """Test scraper performance"""
        
        # Setup: Mock scraper data
        mock_scraper_data = {
            'bills': [
                {
                    'title': f'Performance Test Bill {i}',
                    'description': f'Performance Test Description {i}',
                    'bill_number': f'P-{i:04d}',
                    'introduced_date': '2024-01-01',
                    'sponsor': f'Performance Sponsor {i}',
                    'jurisdiction': 'federal'
                }
                for i in range(100)
            ],
            'mps': [
                {
                    'name': f'Performance MP {i}',
                    'party': f'Performance Party {i}',
                    'constituency': f'Performance Riding {i}',
                    'jurisdiction': 'federal'
                }
                for i in range(50)
            ]
        }
        
        # Test scraper execution time
        start_time = time.time()
        
        # Simulate scraper execution
        from scrapers.federal_parliament_scraper import FederalParliamentScraper
        scraper = FederalParliamentScraper()
        
        # Mock the scrape_all method
        scraper.scrape_all = lambda: mock_scraper_data
        
        data = scraper.scrape_all()
        
        # Store data in database
        for bill in data['bills']:
            db_session.execute(text("""
                INSERT INTO bills_bill (title, description, bill_number, introduced_date, sponsor, jurisdiction)
                VALUES (:title, :description, :bill_number, :introduced_date, :sponsor, :jurisdiction)
            """), bill)
        
        for mp in data['mps']:
            db_session.execute(text("""
                INSERT INTO politicians_politician (name, party, constituency, jurisdiction)
                VALUES (:name, :party, :constituency, :jurisdiction)
            """), mp)
        
        db_session.commit()
        end_time = time.time()
        
        scraper_time = (end_time - start_time) * 1000
        
        # Verify: Scraper completes within reasonable time
        assert scraper_time < 5000, f"Scraper took {scraper_time}ms to complete"
        
        # Verify: Data was stored correctly
        result = db_session.execute(text("SELECT COUNT(*) FROM bills_bill WHERE title LIKE '%Performance Test%'"))
        bill_count = result.fetchone()[0]
        assert bill_count == 100, f"Expected 100 bills, got {bill_count}"
        
        result = db_session.execute(text("SELECT COUNT(*) FROM politicians_politician WHERE name LIKE '%Performance MP%'"))
        mp_count = result.fetchone()[0]
        assert mp_count == 50, f"Expected 50 MPs, got {mp_count}"
    
    def test_concurrent_user_handling(self, client, db_session):
        """Test system performance under concurrent user load"""
        
        # Setup: Insert test data
        for i in range(100):
            db_session.execute(text("""
                INSERT INTO bills_bill (title, description, bill_number, introduced_date, sponsor, jurisdiction)
                VALUES (:title, :description, :bill_number, :introduced_date, :sponsor, :jurisdiction)
            """), {
                "title": f"Concurrent Test Bill {i}",
                "description": f"Concurrent Test Description {i}",
                "bill_number": f"C-{i:03d}",
                "introduced_date": "2024-01-01",
                "sponsor": f"Concurrent Sponsor {i}",
                "jurisdiction": "federal"
            })
        db_session.commit()
        
        # Test concurrent API requests
        def make_request():
            start_time = time.time()
            response = client.get("/api/policies")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Simulate 10 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify: All requests succeeded
        for result in results:
            assert result["status_code"] == 200, f"Request failed with status {result['status_code']}"
            assert result["response_time"] < 1000, f"Request took {result['response_time']}ms"
        
        # Test concurrent search requests
        def make_search_request():
            start_time = time.time()
            response = client.post("/api/policies/search", json={
                "query": "Concurrent Test",
                "jurisdiction": "federal"
            })
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Simulate 5 concurrent search requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_search_request) for _ in range(5)]
            search_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify: All search requests succeeded
        for result in search_results:
            assert result["status_code"] == 200, f"Search request failed with status {result['status_code']}"
            assert result["response_time"] < 2000, f"Search request took {result['response_time']}ms"
        
        # Test concurrent database operations
        def make_db_operation():
            start_time = time.time()
            result = db_session.execute(text("SELECT COUNT(*) FROM bills_bill"))
            count = result.fetchone()[0]
            end_time = time.time()
            return {
                "count": count,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Simulate 5 concurrent database operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_db_operation) for _ in range(5)]
            db_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify: All database operations succeeded
        for result in db_results:
            assert result["count"] >= 100, f"Expected at least 100 records, got {result['count']}"
            assert result["response_time"] < 500, f"Database operation took {result['response_time']}ms"
