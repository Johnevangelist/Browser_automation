class Config:
    HEADLESS = True
    SHOW_BROWSER_LOGS = False

    PROXY_HOST = "host"
    PROXY_PORT = "port"
    PROXY_USER = "user"
    PROXY_PASS = "password"

    BROWSER_ARGS = [
        "--disable-blink-features=AutomationControlled",
        "--disable-permissions-api",
        "--disable-popup-blocking",
        "--disable-web-security",
        "--no-sandbox",
        "--disable-webauthn",
        "--log-level=3",
        "--disable-logging",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
        "--memory-pressure-off"
    ]

    CONTEXT_OPTIONS = {
        "viewport": {"width": 1920, "height": 1080},
        "permissions": [],
        "service_workers": "block",
        "ignore_https_errors": True,
        "extra_http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        "java_script_enabled": True,
        "locale": "en-US",
        "timezone_id": "America/New_York"
    }

    TIMEOUTS = {
        "navigation": 20000,
        "default": 15000,
        "wait": 5000,
        "result_wait": 10000
    }

    URLS = {
        "target": "https://accounts.binance.com/en/register/business-info",
        "success_redirect": "https://accounts.binance.com/en/register/verification-new-register"
    }

    SELECTORS = {
        "email_input": [
            "input[name='email']",
            "input[type='email']",
            ".bn-formItem input",
            "input[placeholder*='email']"
        ],
        "checkbox": "div.bn-checkbox",
        "submit_button": [
            "button:has-text('Continue')",
            ".bn-button.bn-button__primary",
            "button[type='submit']"
        ],
        "error_modal": "div[role='dialog'], .bn-modal"
    }

    FILES = {
        "emails": "data/emails.txt",
        "valid": "data/valid.txt"
    }
