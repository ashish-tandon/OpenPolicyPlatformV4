"""
Frontend Component Tests
Tests that verify all frontend components work correctly
"""

import pytest
from playwright.sync_api import sync_playwright
import time

class TestFrontendComponents:
    """Test frontend components functionality"""
    
    def test_all_page_components(self):
        """Test that all page components render correctly"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test home page
            page.goto("http://localhost:5173")
            assert page.title() == "OpenPolicy Merge"
            
            # Test bills page
            page.goto("http://localhost:5173/bills")
            assert page.locator("h1").text_content() == "Bills"
            assert page.locator("[data-testid='bills-list']").is_visible()
            
            # Test representatives page
            page.goto("http://localhost:5173/representatives")
            assert page.locator("h1").text_content() == "Representatives"
            assert page.locator("[data-testid='representatives-list']").is_visible()
            
            # Test committees page
            page.goto("http://localhost:5173/committees")
            assert page.locator("h1").text_content() == "Committees"
            assert page.locator("[data-testid='committees-list']").is_visible()
            
            # Test debates page
            page.goto("http://localhost:5173/debates")
            assert page.locator("h1").text_content() == "Debates"
            assert page.locator("[data-testid='debates-list']").is_visible()
            
            # Test search page
            page.goto("http://localhost:5173/search")
            assert page.locator("h1").text_content() == "Search"
            assert page.locator("[data-testid='search-form']").is_visible()
            
            # Test admin login page
            page.goto("http://localhost:5173/admin/login")
            assert page.locator("h1").text_content() == "Admin Login"
            assert page.locator("[data-testid='login-form']").is_visible()
            
            # Test admin dashboard page
            page.goto("http://localhost:5173/admin/dashboard")
            assert page.locator("h1").text_content() == "Admin Dashboard"
            assert page.locator("[data-testid='dashboard-stats']").is_visible()
            
            browser.close()
    
    def test_all_form_components(self):
        """Test that all form components work correctly"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test login form
            page.goto("http://localhost:5173/admin/login")
            
            # Fill login form
            page.fill("[data-testid='username-input']", "testuser")
            page.fill("[data-testid='password-input']", "testpassword123")
            
            # Submit form
            page.click("[data-testid='login-button']")
            
            # Verify form submission
            assert page.locator("[data-testid='login-success']").is_visible()
            
            # Test search form
            page.goto("http://localhost:5173/search")
            
            # Fill search form
            page.fill("[data-testid='search-input']", "test bill")
            page.select_option("[data-testid='jurisdiction-select']", "federal")
            page.click("[data-testid='search-button']")
            
            # Verify search results
            assert page.locator("[data-testid='search-results']").is_visible()
            
            # Test filter form
            page.goto("http://localhost:5173/bills")
            
            # Fill filter form
            page.select_option("[data-testid='status-filter']", "introduced")
            page.select_option("[data-testid='party-filter']", "Liberal")
            page.click("[data-testid='apply-filters-button']")
            
            # Verify filtered results
            assert page.locator("[data-testid='filtered-results']").is_visible()
            
            # Test contact form
            page.goto("http://localhost:5173/contact")
            
            # Fill contact form
            page.fill("[data-testid='name-input']", "Test User")
            page.fill("[data-testid='email-input']", "test@example.com")
            page.fill("[data-testid='message-input']", "Test message")
            page.click("[data-testid='submit-button']")
            
            # Verify form submission
            assert page.locator("[data-testid='contact-success']").is_visible()
            
            browser.close()
    
    def test_all_navigation_components(self):
        """Test that all navigation components work correctly"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test main navigation
            page.goto("http://localhost:5173")
            
            # Test navigation links
            page.click("[data-testid='nav-bills']")
            assert page.url == "http://localhost:5173/bills"
            
            page.click("[data-testid='nav-representatives']")
            assert page.url == "http://localhost:5173/representatives"
            
            page.click("[data-testid='nav-committees']")
            assert page.url == "http://localhost:5173/committees"
            
            page.click("[data-testid='nav-debates']")
            assert page.url == "http://localhost:5173/debates"
            
            page.click("[data-testid='nav-search']")
            assert page.url == "http://localhost:5173/search"
            
            # Test breadcrumb navigation
            page.goto("http://localhost:5173/bills/123")
            assert page.locator("[data-testid='breadcrumb-home']").is_visible()
            assert page.locator("[data-testid='breadcrumb-bills']").is_visible()
            assert page.locator("[data-testid='breadcrumb-current']").is_visible()
            
            # Test pagination
            page.goto("http://localhost:5173/bills")
            assert page.locator("[data-testid='pagination']").is_visible()
            
            # Test next page
            page.click("[data-testid='next-page']")
            assert page.url == "http://localhost:5173/bills?page=2"
            
            # Test previous page
            page.click("[data-testid='prev-page']")
            assert page.url == "http://localhost:5173/bills?page=1"
            
            # Test mobile navigation
            page.set_viewport_size({"width": 375, "height": 667})
            page.click("[data-testid='mobile-menu-toggle']")
            assert page.locator("[data-testid='mobile-menu']").is_visible()
            
            browser.close()
    
    def test_all_data_display_components(self):
        """Test that all data display components work correctly"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test bills table
            page.goto("http://localhost:5173/bills")
            
            # Verify table headers
            assert page.locator("[data-testid='bill-number-header']").text_content() == "Bill Number"
            assert page.locator("[data-testid='title-header']").text_content() == "Title"
            assert page.locator("[data-testid='sponsor-header']").text_content() == "Sponsor"
            assert page.locator("[data-testid='status-header']").text_content() == "Status"
            
            # Verify table data
            assert page.locator("[data-testid='bills-table']").is_visible()
            assert page.locator("[data-testid='bill-row']").count() > 0
            
            # Test representatives grid
            page.goto("http://localhost:5173/representatives")
            
            # Verify grid layout
            assert page.locator("[data-testid='representatives-grid']").is_visible()
            assert page.locator("[data-testid='representative-card']").count() > 0
            
            # Test charts and graphs
            page.goto("http://localhost:5173/admin/dashboard")
            
            # Verify charts
            assert page.locator("[data-testid='bills-chart']").is_visible()
            assert page.locator("[data-testid='votes-chart']").is_visible()
            assert page.locator("[data-testid='activity-chart']").is_visible()
            
            # Test statistics display
            assert page.locator("[data-testid='total-bills']").is_visible()
            assert page.locator("[data-testid='total-representatives']").is_visible()
            assert page.locator("[data-testid='total-committees']").is_visible()
            
            # Test search results display
            page.goto("http://localhost:5173/search")
            page.fill("[data-testid='search-input']", "test")
            page.click("[data-testid='search-button']")
            
            # Verify search results
            assert page.locator("[data-testid='search-results']").is_visible()
            assert page.locator("[data-testid='result-item']").count() > 0
            
            browser.close()
    
    def test_all_interactive_components(self):
        """Test that all interactive components work correctly"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test dropdown menus
            page.goto("http://localhost:5173/bills")
            
            # Test jurisdiction filter dropdown
            page.click("[data-testid='jurisdiction-dropdown']")
            assert page.locator("[data-testid='dropdown-menu']").is_visible()
            page.click("[data-testid='federal-option']")
            assert page.locator("[data-testid='selected-jurisdiction']").text_content() == "Federal"
            
            # Test modal dialogs
            page.click("[data-testid='bill-details-button']")
            assert page.locator("[data-testid='modal-overlay']").is_visible()
            assert page.locator("[data-testid='modal-content']").is_visible()
            
            # Close modal
            page.click("[data-testid='modal-close']")
            assert not page.locator("[data-testid='modal-overlay']").is_visible()
            
            # Test tooltips
            page.hover("[data-testid='help-icon']")
            assert page.locator("[data-testid='tooltip']").is_visible()
            
            # Test accordion components
            page.goto("http://localhost:5173/representatives")
            page.click("[data-testid='accordion-header']")
            assert page.locator("[data-testid='accordion-content']").is_visible()
            
            # Test tabs
            page.goto("http://localhost:5173/bills/123")
            page.click("[data-testid='tab-votes']")
            assert page.locator("[data-testid='votes-tab-content']").is_visible()
            
            page.click("[data-testid='tab-debates']")
            assert page.locator("[data-testid='debates-tab-content']").is_visible()
            
            # Test sorting
            page.goto("http://localhost:5173/bills")
            page.click("[data-testid='sort-title']")
            assert page.locator("[data-testid='sort-indicator']").is_visible()
            
            # Test expandable sections
            page.click("[data-testid='expand-section']")
            assert page.locator("[data-testid='expanded-content']").is_visible()
            
            browser.close()
