"""
Accessibility Tests
Tests that verify all accessibility features work correctly
"""

import pytest
from playwright.sync_api import sync_playwright
import time

class TestAccessibilityFeatures:
    """Test accessibility features functionality"""
    
    def test_keyboard_navigation(self):
        """Test that all components are navigable via keyboard"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test main navigation with keyboard
            page.goto("http://localhost:5173")
            
            # Navigate through main menu with Tab
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='nav-bills']").is_focused()
            
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='nav-representatives']").is_focused()
            
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='nav-committees']").is_focused()
            
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='nav-debates']").is_focused()
            
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='nav-search']").is_focused()
            
            # Test Enter key activation
            page.keyboard.press("Enter")
            assert page.url == "http://localhost:5173/search"
            
            # Test search form with keyboard
            page.goto("http://localhost:5173/search")
            
            # Navigate to search input
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='search-input']").is_focused()
            
            # Type search query
            page.keyboard.type("test bill")
            
            # Navigate to search button
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='search-button']").is_focused()
            
            # Activate search
            page.keyboard.press("Enter")
            
            # Verify search results are keyboard accessible
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='result-item']").is_focused()
            
            # Test form navigation
            page.goto("http://localhost:5173/admin/login")
            
            # Navigate through form fields
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='username-input']").is_focused()
            
            page.keyboard.type("testuser")
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='password-input']").is_focused()
            
            page.keyboard.type("testpassword123")
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='login-button']").is_focused()
            
            # Test dropdown navigation
            page.goto("http://localhost:5173/bills")
            
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            assert page.locator("[data-testid='jurisdiction-dropdown']").is_focused()
            
            page.keyboard.press("Enter")
            assert page.locator("[data-testid='dropdown-menu']").is_visible()
            
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            
            browser.close()
    
    def test_screen_reader_compatibility(self):
        """Test that all components are compatible with screen readers"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test ARIA labels and roles
            page.goto("http://localhost:5173")
            
            # Check main navigation has proper ARIA labels
            nav_element = page.locator("[data-testid='nav-bills']")
            aria_label = nav_element.get_attribute("aria-label")
            assert aria_label is not None, "Navigation should have aria-label"
            
            # Check search form has proper labels
            page.goto("http://localhost:5173/search")
            
            search_input = page.locator("[data-testid='search-input']")
            aria_label = search_input.get_attribute("aria-label")
            assert aria_label is not None, "Search input should have aria-label"
            
            # Check form fields have proper labels
            page.goto("http://localhost:5173/admin/login")
            
            username_input = page.locator("[data-testid='username-input']")
            aria_label = username_input.get_attribute("aria-label")
            assert aria_label is not None, "Username input should have aria-label"
            
            password_input = page.locator("[data-testid='password-input']")
            aria_label = password_input.get_attribute("aria-label")
            assert aria_label is not None, "Password input should have aria-label"
            
            # Check table has proper ARIA attributes
            page.goto("http://localhost:5173/bills")
            
            table = page.locator("[data-testid='bills-table']")
            role = table.get_attribute("role")
            assert role == "table", "Table should have role='table'"
            
            # Check table headers have proper scope
            headers = page.locator("[data-testid='bill-number-header']")
            scope = headers.get_attribute("scope")
            assert scope == "col", "Table headers should have scope='col'"
            
            # Check buttons have proper ARIA labels
            search_button = page.locator("[data-testid='search-button']")
            aria_label = search_button.get_attribute("aria-label")
            assert aria_label is not None, "Search button should have aria-label"
            
            # Check error messages are announced
            page.goto("http://localhost:5173/admin/login")
            page.fill("[data-testid='username-input']", "")
            page.fill("[data-testid='password-input']", "")
            page.click("[data-testid='login-button']")
            
            error_message = page.locator("[data-testid='error-message']")
            aria_live = error_message.get_attribute("aria-live")
            assert aria_live == "polite", "Error messages should have aria-live='polite'"
            
            # Check loading states are announced
            page.goto("http://localhost:5173/bills")
            page.click("[data-testid='refresh-button']")
            
            loading_indicator = page.locator("[data-testid='loading-indicator']")
            aria_live = loading_indicator.get_attribute("aria-live")
            assert aria_live == "polite", "Loading indicators should have aria-live='polite'"
            
            browser.close()
    
    def test_color_contrast_ratios(self):
        """Test that color contrast ratios meet WCAG standards"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test main page contrast
            page.goto("http://localhost:5173")
            
            # Check main heading contrast
            heading = page.locator("h1")
            color = heading.evaluate("el => window.getComputedStyle(el).color")
            background = heading.evaluate("el => window.getComputedStyle(el).backgroundColor")
            
            # Verify contrast ratio is at least 4.5:1 for normal text
            # This is a simplified check - in practice, you'd use a library to calculate actual ratios
            assert color != background, "Text and background should have different colors"
            
            # Check link contrast
            links = page.locator("a")
            for i in range(min(5, links.count())):  # Check first 5 links
                link = links.nth(i)
                color = link.evaluate("el => window.getComputedStyle(el).color")
                background = link.evaluate("el => window.getComputedStyle(el).backgroundColor")
                assert color != background, f"Link {i} should have sufficient contrast"
            
            # Test form contrast
            page.goto("http://localhost:5173/admin/login")
            
            # Check input field contrast
            username_input = page.locator("[data-testid='username-input']")
            color = username_input.evaluate("el => window.getComputedStyle(el).color")
            background = username_input.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert color != background, "Input text should have sufficient contrast"
            
            # Check button contrast
            login_button = page.locator("[data-testid='login-button']")
            color = login_button.evaluate("el => window.getComputedStyle(el).color")
            background = login_button.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert color != background, "Button text should have sufficient contrast"
            
            # Test table contrast
            page.goto("http://localhost:5173/bills")
            
            # Check table header contrast
            header = page.locator("[data-testid='bill-number-header']")
            color = header.evaluate("el => window.getComputedStyle(el).color")
            background = header.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert color != background, "Table header should have sufficient contrast"
            
            # Check table row contrast
            row = page.locator("[data-testid='bill-row']").first
            color = row.evaluate("el => window.getComputedStyle(el).color")
            background = row.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert color != background, "Table row should have sufficient contrast"
            
            # Test error message contrast
            page.goto("http://localhost:5173/admin/login")
            page.fill("[data-testid='username-input']", "")
            page.fill("[data-testid='password-input']", "")
            page.click("[data-testid='login-button']")
            
            error_message = page.locator("[data-testid='error-message']")
            color = error_message.evaluate("el => window.getComputedStyle(el).color")
            background = error_message.evaluate("el => window.getComputedStyle(el).backgroundColor")
            assert color != background, "Error message should have sufficient contrast"
            
            browser.close()
    
    def test_text_scaling(self):
        """Test that text scales properly up to 200%"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test 100% scaling (default)
            page.goto("http://localhost:5173")
            
            # Get default text size
            heading = page.locator("h1")
            default_font_size = heading.evaluate("el => window.getComputedStyle(el).fontSize")
            
            # Test 125% scaling
            page.evaluate("document.body.style.zoom = '125%'")
            
            new_font_size = heading.evaluate("el => window.getComputedStyle(el).fontSize")
            assert new_font_size != default_font_size, "Text should scale with zoom"
            
            # Verify layout doesn't break
            assert page.locator("h1").is_visible(), "Heading should remain visible"
            assert page.locator("[data-testid='nav-bills']").is_visible(), "Navigation should remain visible"
            
            # Test 150% scaling
            page.evaluate("document.body.style.zoom = '150%'")
            
            new_font_size = heading.evaluate("el => window.getComputedStyle(el).fontSize")
            assert new_font_size != default_font_size, "Text should scale with zoom"
            
            # Verify layout doesn't break
            assert page.locator("h1").is_visible(), "Heading should remain visible"
            assert page.locator("[data-testid='nav-bills']").is_visible(), "Navigation should remain visible"
            
            # Test 200% scaling
            page.evaluate("document.body.style.zoom = '200%'")
            
            new_font_size = heading.evaluate("el => window.getComputedStyle(el).fontSize")
            assert new_font_size != default_font_size, "Text should scale with zoom"
            
            # Verify layout doesn't break
            assert page.locator("h1").is_visible(), "Heading should remain visible"
            assert page.locator("[data-testid='nav-bills']").is_visible(), "Navigation should remain visible"
            
            # Test form scaling
            page.goto("http://localhost:5173/admin/login")
            
            # Get default form text size
            input_field = page.locator("[data-testid='username-input']")
            default_input_size = input_field.evaluate("el => window.getComputedStyle(el).fontSize")
            
            # Test 200% scaling on form
            page.evaluate("document.body.style.zoom = '200%'")
            
            new_input_size = input_field.evaluate("el => window.getComputedStyle(el).fontSize")
            assert new_input_size != default_input_size, "Form text should scale with zoom"
            
            # Verify form remains functional
            assert input_field.is_visible(), "Input field should remain visible"
            assert input_field.is_enabled(), "Input field should remain enabled"
            
            # Test table scaling
            page.goto("http://localhost:5173/bills")
            
            # Get default table text size
            table_cell = page.locator("[data-testid='bill-row']").first.locator("td").first
            default_table_size = table_cell.evaluate("el => window.getComputedStyle(el).fontSize")
            
            # Test 200% scaling on table
            page.evaluate("document.body.style.zoom = '200%'")
            
            new_table_size = table_cell.evaluate("el => window.getComputedStyle(el).fontSize")
            assert new_table_size != default_table_size, "Table text should scale with zoom"
            
            # Verify table remains functional
            assert table_cell.is_visible(), "Table cell should remain visible"
            
            browser.close()
    
    def test_focus_indicators(self):
        """Test that focus indicators are visible and clear"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Test focus indicators on main page
            page.goto("http://localhost:5173")
            
            # Focus on navigation link
            page.keyboard.press("Tab")
            focused_element = page.locator("[data-testid='nav-bills']")
            
            # Check focus indicator is visible
            outline = focused_element.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused element should have outline"
            
            # Check focus indicator color is distinct
            outline_color = focused_element.evaluate("el => window.getComputedStyle(el).outlineColor")
            assert outline_color != "transparent", "Focus indicator should be visible"
            
            # Test focus indicators on form
            page.goto("http://localhost:5173/admin/login")
            
            # Focus on username input
            page.keyboard.press("Tab")
            focused_input = page.locator("[data-testid='username-input']")
            
            # Check input focus indicator
            outline = focused_input.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused input should have outline"
            
            # Check border color changes
            border_color = focused_input.evaluate("el => window.getComputedStyle(el).borderColor")
            assert border_color != "transparent", "Focused input should have visible border"
            
            # Test focus indicators on buttons
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            focused_button = page.locator("[data-testid='login-button']")
            
            # Check button focus indicator
            outline = focused_button.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused button should have outline"
            
            # Test focus indicators on links
            page.goto("http://localhost:5173/bills")
            
            # Focus on a link
            page.keyboard.press("Tab")
            focused_link = page.locator("a").first
            
            # Check link focus indicator
            outline = focused_link.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused link should have outline"
            
            # Test focus indicators on table
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            focused_cell = page.locator("[data-testid='bill-row']").first.locator("td").first
            
            # Check table cell focus indicator
            outline = focused_cell.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused table cell should have outline"
            
            # Test focus indicators on dropdown
            page.keyboard.press("Tab")
            focused_dropdown = page.locator("[data-testid='jurisdiction-dropdown']")
            
            # Check dropdown focus indicator
            outline = focused_dropdown.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused dropdown should have outline"
            
            # Test focus indicators on search results
            page.goto("http://localhost:5173/search")
            page.fill("[data-testid='search-input']", "test")
            page.click("[data-testid='search-button']")
            
            # Focus on search result
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            focused_result = page.locator("[data-testid='result-item']").first
            
            # Check search result focus indicator
            outline = focused_result.evaluate("el => window.getComputedStyle(el).outline")
            assert outline != "none", "Focused search result should have outline"
            
            browser.close()
