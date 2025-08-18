"""
End-to-End Workflow Tests
Tests that verify complete user workflows from start to finish
"""

import pytest
from playwright.sync_api import sync_playwright
import time

class TestEndToEndWorkflows:
    """Test complete end-to-end user workflows"""
    
    def test_user_registration_workflow(self):
        """Test complete user registration workflow"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Start at home page
            page.goto("http://localhost:5173")
            
            # Navigate to registration page
            page.click("[data-testid='register-link']")
            assert page.url == "http://localhost:5173/register"
            
            # Fill registration form
            page.fill("[data-testid='username-input']", "newuser123")
            page.fill("[data-testid='email-input']", "newuser123@example.com")
            page.fill("[data-testid='password-input']", "SecurePass123!@#")
            page.fill("[data-testid='confirm-password-input']", "SecurePass123!@#")
            page.fill("[data-testid='first-name-input']", "New")
            page.fill("[data-testid='last-name-input']", "User")
            
            # Submit registration
            page.click("[data-testid='register-button']")
            
            # Verify registration success
            assert page.locator("[data-testid='registration-success']").is_visible()
            assert page.url == "http://localhost:5173/login"
            
            # Verify user can now login
            page.fill("[data-testid='username-input']", "newuser123")
            page.fill("[data-testid='password-input']", "SecurePass123!@#")
            page.click("[data-testid='login-button']")
            
            # Verify successful login
            assert page.locator("[data-testid='user-dashboard']").is_visible()
            assert page.locator("[data-testid='welcome-message']").text_content() == "Welcome, New User!"
            
            browser.close()
    
    def test_user_login_workflow(self):
        """Test complete user login workflow"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Start at home page
            page.goto("http://localhost:5173")
            
            # Navigate to login page
            page.click("[data-testid='login-link']")
            assert page.url == "http://localhost:5173/login"
            
            # Test invalid login
            page.fill("[data-testid='username-input']", "invaliduser")
            page.fill("[data-testid='password-input']", "wrongpassword")
            page.click("[data-testid='login-button']")
            
            # Verify error message
            assert page.locator("[data-testid='error-message']").is_visible()
            assert "Invalid credentials" in page.locator("[data-testid='error-message']").text_content()
            
            # Test valid login
            page.fill("[data-testid='username-input']", "testuser")
            page.fill("[data-testid='password-input']", "testpassword123")
            page.click("[data-testid='login-button']")
            
            # Verify successful login
            assert page.locator("[data-testid='user-dashboard']").is_visible()
            assert page.url == "http://localhost:5173/dashboard"
            
            # Verify user menu is accessible
            page.click("[data-testid='user-menu']")
            assert page.locator("[data-testid='profile-link']").is_visible()
            assert page.locator("[data-testid='logout-link']").is_visible()
            
            # Test logout
            page.click("[data-testid='logout-link']")
            assert page.url == "http://localhost:5173"
            assert page.locator("[data-testid='login-link']").is_visible()
            
            browser.close()
    
    def test_policy_search_workflow(self):
        """Test complete policy search workflow"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Start at home page
            page.goto("http://localhost:5173")
            
            # Navigate to search page
            page.click("[data-testid='nav-search']")
            assert page.url == "http://localhost:5173/search"
            
            # Perform basic search
            page.fill("[data-testid='search-input']", "environment")
            page.select_option("[data-testid='jurisdiction-select']", "federal")
            page.click("[data-testid='search-button']")
            
            # Verify search results
            assert page.locator("[data-testid='search-results']").is_visible()
            assert page.locator("[data-testid='result-item']").count() > 0
            
            # Test advanced search filters
            page.click("[data-testid='advanced-search-toggle']")
            page.select_option("[data-testid='status-filter']", "introduced")
            page.select_option("[data-testid='party-filter']", "Liberal")
            page.fill("[data-testid='date-from']", "2024-01-01")
            page.fill("[data-testid='date-to']", "2024-12-31")
            page.click("[data-testid='apply-filters-button']")
            
            # Verify filtered results
            assert page.locator("[data-testid='filtered-results']").is_visible()
            
            # Test result sorting
            page.select_option("[data-testid='sort-select']", "date-desc")
            assert page.locator("[data-testid='sort-indicator']").is_visible()
            
            # Test result pagination
            if page.locator("[data-testid='next-page']").is_visible():
                page.click("[data-testid='next-page']")
                assert page.url == "http://localhost:5173/search?page=2"
                
                page.click("[data-testid='prev-page']")
                assert page.url == "http://localhost:5173/search?page=1"
            
            # Test result details
            page.click("[data-testid='result-item']").first
            assert page.locator("[data-testid='bill-details']").is_visible()
            assert page.locator("[data-testid='bill-title']").is_visible()
            assert page.locator("[data-testid='bill-description']").is_visible()
            
            # Test bookmark functionality
            page.click("[data-testid='bookmark-button']")
            assert page.locator("[data-testid='bookmark-success']").is_visible()
            
            # Test share functionality
            page.click("[data-testid='share-button']")
            assert page.locator("[data-testid='share-modal']").is_visible()
            
            browser.close()
    
    def test_representative_search_workflow(self):
        """Test complete representative search workflow"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Start at home page
            page.goto("http://localhost:5173")
            
            # Navigate to representatives page
            page.click("[data-testid='nav-representatives']")
            assert page.url == "http://localhost:5173/representatives"
            
            # Perform representative search
            page.fill("[data-testid='search-input']", "Smith")
            page.select_option("[data-testid='jurisdiction-select']", "federal")
            page.select_option("[data-testid='party-select']", "Liberal")
            page.click("[data-testid='search-button']")
            
            # Verify search results
            assert page.locator("[data-testid='representatives-results']").is_visible()
            assert page.locator("[data-testid='representative-card']").count() > 0
            
            # Test representative filtering
            page.click("[data-testid='filter-toggle']")
            page.select_option("[data-testid='constituency-filter']", "Toronto")
            page.select_option("[data-testid='experience-filter']", "5-10 years")
            page.click("[data-testid='apply-filters-button']")
            
            # Verify filtered results
            assert page.locator("[data-testid='filtered-representatives']").is_visible()
            
            # Test representative details
            page.click("[data-testid='representative-card']").first
            assert page.locator("[data-testid='representative-details']").is_visible()
            assert page.locator("[data-testid='representative-name']").is_visible()
            assert page.locator("[data-testid='representative-party']").is_visible()
            assert page.locator("[data-testid='representative-constituency']").is_visible()
            
            # Test voting history
            page.click("[data-testid='voting-history-tab']")
            assert page.locator("[data-testid='voting-history']").is_visible()
            assert page.locator("[data-testid='vote-record']").count() > 0
            
            # Test sponsored bills
            page.click("[data-testid='sponsored-bills-tab']")
            assert page.locator("[data-testid='sponsored-bills']").is_visible()
            
            # Test contact information
            page.click("[data-testid='contact-tab']")
            assert page.locator("[data-testid='contact-info']").is_visible()
            assert page.locator("[data-testid='email']").is_visible()
            assert page.locator("[data-testid='phone']").is_visible()
            
            # Test contact form
            page.fill("[data-testid='contact-name']", "Test User")
            page.fill("[data-testid='contact-email']", "test@example.com")
            page.fill("[data-testid='contact-message']", "Test message")
            page.click("[data-testid='send-message-button']")
            
            # Verify contact success
            assert page.locator("[data-testid='contact-success']").is_visible()
            
            browser.close()
    
    def test_admin_dashboard_workflow(self):
        """Test complete admin dashboard workflow"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Start at admin login
            page.goto("http://localhost:5173/admin/login")
            
            # Login as admin
            page.fill("[data-testid='username-input']", "admin")
            page.fill("[data-testid='password-input']", "adminpassword123")
            page.click("[data-testid='login-button']")
            
            # Verify admin dashboard
            assert page.url == "http://localhost:5173/admin/dashboard"
            assert page.locator("[data-testid='admin-dashboard']").is_visible()
            
            # Test dashboard statistics
            assert page.locator("[data-testid='total-bills']").is_visible()
            assert page.locator("[data-testid='total-representatives']").is_visible()
            assert page.locator("[data-testid='total-committees']").is_visible()
            assert page.locator("[data-testid='total-users']").is_visible()
            
            # Test scraper management
            page.click("[data-testid='scrapers-tab']")
            assert page.locator("[data-testid='scrapers-panel']").is_visible()
            
            # Test scraper status
            assert page.locator("[data-testid='federal-scraper-status']").is_visible()
            assert page.locator("[data-testid='provincial-scraper-status']").is_visible()
            assert page.locator("[data-testid='municipal-scraper-status']").is_visible()
            
            # Test manual scraper execution
            page.click("[data-testid='run-federal-scraper']")
            assert page.locator("[data-testid='scraper-running']").is_visible()
            
            # Wait for scraper completion
            page.wait_for_selector("[data-testid='scraper-complete']", timeout=30000)
            assert page.locator("[data-testid='scraper-success']").is_visible()
            
            # Test data management
            page.click("[data-testid='data-tab']")
            assert page.locator("[data-testid='data-panel']").is_visible()
            
            # Test data backup
            page.click("[data-testid='create-backup']")
            assert page.locator("[data-testid='backup-success']").is_visible()
            
            # Test data import
            page.click("[data-testid='import-data']")
            assert page.locator("[data-testid='import-modal']").is_visible()
            
            # Test user management
            page.click("[data-testid='users-tab']")
            assert page.locator("[data-testid='users-panel']").is_visible()
            
            # Test user creation
            page.click("[data-testid='create-user']")
            page.fill("[data-testid='new-username']", "newadmin")
            page.fill("[data-testid='new-email']", "newadmin@example.com")
            page.fill("[data-testid='new-password']", "NewAdminPass123!")
            page.select_option("[data-testid='new-role']", "admin")
            page.click("[data-testid='save-user']")
            
            # Verify user creation
            assert page.locator("[data-testid='user-created']").is_visible()
            
            # Test system monitoring
            page.click("[data-testid='monitoring-tab']")
            assert page.locator("[data-testid='monitoring-panel']").is_visible()
            
            # Test system health
            assert page.locator("[data-testid='system-health']").is_visible()
            assert page.locator("[data-testid='database-status']").is_visible()
            assert page.locator("[data-testid='api-status']").is_visible()
            
            # Test logs
            page.click("[data-testid='view-logs']")
            assert page.locator("[data-testid='system-logs']").is_visible()
            
            # Test settings
            page.click("[data-testid='settings-tab']")
            assert page.locator("[data-testid='settings-panel']").is_visible()
            
            # Test configuration changes
            page.fill("[data-testid='api-rate-limit']", "1000")
            page.fill("[data-testid='session-timeout']", "3600")
            page.click("[data-testid='save-settings']")
            
            # Verify settings saved
            assert page.locator("[data-testid='settings-saved']").is_visible()
            
            # Test logout
            page.click("[data-testid='admin-logout']")
            assert page.url == "http://localhost:5173/admin/login"
            
            browser.close()
