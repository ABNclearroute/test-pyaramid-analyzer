"""End-to-end tests for the login flow using Playwright."""
import pytest
from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://localhost:3000"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.mark.e2e
class TestLoginFlow:
    def test_successful_login(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill("#email", "user@example.com")
        page.fill("#password", "secret123")
        page.click("button[type=submit]")
        page.wait_for_url(f"{BASE_URL}/dashboard")
        assert page.title() == "Dashboard"

    def test_invalid_credentials_shows_error(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill("#email", "wrong@example.com")
        page.fill("#password", "wrongpass")
        page.click("button[type=submit]")
        error = page.locator(".error-message")
        assert error.is_visible()
        assert "Invalid credentials" in error.text_content()

    def test_logout_redirects_to_login(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill("#email", "user@example.com")
        page.fill("#password", "secret123")
        page.click("button[type=submit]")
        page.click("#logout-btn")
        assert page.url == f"{BASE_URL}/login"
