from playwright.sync_api import sync_playwright
from config import Config

proxy = {
    "server": f"http://{Config.PROXY_HOST}:{Config.PROXY_PORT}",
    "username": Config.PROXY_USER,
    "password": Config.PROXY_PASS,
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, proxy=proxy)
    page = browser.new_page()
    page.goto("https://httpbin.org/ip")
    print("Playwright Proxy Test:", page.text_content("body"))
    browser.close()
