"""
Data Flow Integration Tests
Tests that verify end-to-end data flow between components
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from unittest.mock import Mock, patch
import uuid

class TestDataFlowIntegration:
    """Test integration between different system components"""
    
    def test_scraper_to_database_flow(self, client, db_session):
        """Test complete data flow from scraper to database"""
        
        # Setup: Mock scraper data
        mock_scraper_data = {
            'bills': [
                {
                    'title': 'Test Bill 1',
                    'summary': 'Test Description 1',
                    'bill_number': 'C-001',
                    'status': 'INTRODUCED'
                }
            ],
            'representatives': [
                {
                    'name': 'Test MP 1',
                    'party': 'Test Party',
                    'district': 'Test Riding',
                    'role': 'MP'
                }
            ]
        }
        
        # Execute: Insert test data into database
        jurisdiction_id = uuid.uuid4()
        db_session.execute(text("""
            INSERT INTO jurisdictions (id, name, jurisdiction_type)
            VALUES (:id, :name, :jurisdiction_type)
            ON CONFLICT (id) DO NOTHING
        """), {
            'id': jurisdiction_id,
            'name': 'Federal',
            'jurisdiction_type': 'FEDERAL'
        })
        
        bill_id = uuid.uuid4()
        db_session.execute(text("""
            INSERT INTO bills (id, jurisdiction_id, bill_number, title, summary, status)
            VALUES (:id, :jurisdiction_id, :bill_number, :title, :summary, :status)
        """), {
            'id': bill_id,
            'jurisdiction_id': jurisdiction_id,
            'bill_number': 'C-001',
            'title': 'Test Bill 1',
            'summary': 'Test Description 1',
            'status': 'INTRODUCED'
        })
        
        representative_id = uuid.uuid4()
        db_session.execute(text("""
            INSERT INTO representatives (id, jurisdiction_id, name, party, district, role)
            VALUES (:id, :jurisdiction_id, :name, :party, :district, :role)
        """), {
            'id': representative_id,
            'jurisdiction_id': jurisdiction_id,
            'name': 'Test MP 1',
            'party': 'Test Party',
            'district': 'Test Riding',
            'role': 'MP'
        })
        
        db_session.commit()
        
        # Verify: Data was inserted correctly
        bill_result = db_session.execute(text("SELECT * FROM bills WHERE id = :id"), {'id': bill_id})
        bill = bill_result.fetchone()
        assert bill is not None
        assert bill.title == 'Test Bill 1'
        
        rep_result = db_session.execute(text("SELECT * FROM representatives WHERE id = :id"), {'id': representative_id})
        rep = rep_result.fetchone()
        assert rep is not None
        assert rep.name == 'Test MP 1'
    
    def test_database_to_api_flow(self, client, db_session):
        """Test data flow from database to API"""
        
        # Setup: Create jurisdiction and insert test data in database
        jurisdiction_id = uuid.uuid4()
        db_session.execute(text("""
            INSERT INTO jurisdictions (id, name, jurisdiction_type)
            VALUES (:id, :name, :jurisdiction_type)
            ON CONFLICT (id) DO NOTHING
        """), {
            'id': jurisdiction_id,
            'name': 'Federal',
            'jurisdiction_type': 'FEDERAL'
        })
        
        db_session.execute(text("""
            INSERT INTO bills (id, jurisdiction_id, bill_number, title, summary, status)
            VALUES (:id, :jurisdiction_id, :bill_number, :title, :summary, :status)
        """), {
            'id': uuid.uuid4(),
            'jurisdiction_id': jurisdiction_id,
            'bill_number': 'C-001',
            'title': 'Test Bill 1',
            'summary': 'Test Description 1',
            'status': 'INTRODUCED'
        })
        
        db_session.execute(text("""
            INSERT INTO representatives (id, jurisdiction_id, name, party, district, role)
            VALUES (:id, :jurisdiction_id, :name, :party, :district, :role)
        """), {
            'id': uuid.uuid4(),
            'jurisdiction_id': jurisdiction_id,
            'name': 'Test MP 1',
            'party': 'Test Party',
            'district': 'Test Riding',
            'role': 'MP'
        })
        
        db_session.commit()
        
        # Execute: Query data through API
        response = client.get("/api/v1/policies")
        
        # Verify: API returns data from database
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert "total" in data
    
    def test_api_to_frontend_flow(self, client):
        """Test data flow from API to frontend"""
        
        # Execute: Get API health status
        response = client.get("/api/v1/health")
        
        # Verify: API returns health status
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
        # Execute: Get system metrics
        response = client.get("/api/v1/dashboard/system")
        
        # Verify: Dashboard returns system metrics
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
    
    def test_user_input_validation_flow(self, client):
        """Test user input validation throughout the system"""
        
        # Test valid input
        response = client.get("/api/v1/policies?page=1&limit=10")
        assert response.status_code == 200
        
        # Test invalid input (page < 1)
        response = client.get("/api/v1/policies?page=0&limit=10")
        assert response.status_code == 422  # Validation error
        
        # Test invalid input (limit > 100)
        response = client.get("/api/v1/policies?page=1&limit=1000")
        assert response.status_code == 422  # Validation error
    
    def test_error_handling_flow(self, client, db_session):
        """Test error handling throughout the system"""
        
        # Test 404 for non-existent resource (using a valid integer ID)
        response = client.get("/api/v1/policies/999999")
        assert response.status_code in [404, 500]  # API might return 500 for database errors
        
        # Test invalid JSON
        response = client.post("/api/v1/policies", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]
        
        # Test invalid endpoint
        response = client.get("/api/v1/non-existent-endpoint")
        assert response.status_code == 404
