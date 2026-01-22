import time, random
from config import Config
from src.captcha import create_captcha_task
from src.logger import Logger

log = Logger("CHECKER")

class EmailChecker:
    def __init__(self):
        self.reset_state()
        self.max_attempts = 2

    def reset_state(self):
        self.api_received = False
        self.is_valid = False
        self.captcha_detected = False
        self.redirect_detected = False

    def handle_response(self, response):
        try:
            url = response.url
        except:
            url = ""
        if "getCaptcha" in url or "captcha" in url:
            self.captcha_detected = True
        if "bizCheck" in url:
            try:
                data = response.json()
                if data.get("success"):
                    self.is_valid = data.get("data", {}).get("valid", False)
                    self.api_received = True
            except:
                pass

    def navigate_to_page(self, page):
        if Config.URLS["target"] not in page.url:
            page.goto(Config.URLS["target"], wait_until="domcontentloaded", timeout=Config.TIMEOUTS.get("navigation", 20000))
        page.wait_for_timeout(300)

    def _checked_state(self, el):
        try:
            v = el.get_attribute("aria-checked")
            if v == "true":
                return True
        except:
            pass
        try:
            cls = (el.get_attribute("class") or "").lower()
            if "is-checked" in cls or "checked" in cls:
                return True
        except:
            pass
        return False

    def handle_checkbox(self, page, max_wait_ms=5000):
        end = time.time() + max_wait_ms/1000.0
        sel = Config.SELECTORS.get("checkbox", "div.bn-checkbox")
        while time.time() < end:
            try:
                loc = page.locator(sel)
                if loc.count() == 0:
                    page.wait_for_timeout(120)
                    continue
                el = loc.first
                try:
                    box = el.bounding_box()
                    if box:
                        x = box["x"] + 8
                        y = box["y"] + box["height"] / 2
                        page.mouse.move(x, y)
                        page.mouse.click(x, y)
                    else:
                        try:
                            el.click(force=True)
                        except:
                            el.click()
                except:
                    try:
                        el.click(force=True)
                    except:
                        pass
                page.wait_for_timeout(150)
                try:
                    if self._checked_state(el):
                        return True
                except:
                    pass
            except:
                pass
            page.wait_for_timeout(100)
        return False

    def _accept_cookie_if_appears(self, page, check_interval=0.2):
        end = time.time() + 10.0
        while time.time() < end:
            try:
                btn = page.locator("button:has-text('Accept cookies & Continue')")
                if btn.count() > 0 and btn.first.is_visible():
                    try:
                        btn.first.click()
                        page.wait_for_timeout(120)
                        return True
                    except:
                        pass
            except:
                pass
            page.wait_for_timeout(int(check_interval*1000))
        return False

    def fill_email(self, page, email, max_total_time=10.0):
        start = time.time()
        for selector in Config.SELECTORS["email_input"]:
            try:
                input_field = page.wait_for_selector(selector, state="visible", timeout=Config.TIMEOUTS.get("default", 15000))
                if input_field:
                    input_field.fill("")
                    remaining_time = max_total_time - (time.time() - start)
                    remaining_time = max(0.1, remaining_time)
                    per_char = max(0.002, min(0.02, remaining_time / max(1, len(email))))
                    for ch in email:
                        try:
                            page.keyboard.insert_text(ch)
                        except:
                            try:
                                input_field.type(ch, delay=0)
                            except:
                                pass
                        if time.time() - start < 10.0:
                            try:
                                btn = page.locator("button:has-text('Accept cookies & Continue')")
                                if btn.count() > 0 and btn.first.is_visible():
                                    try:
                                        btn.first.click()
                                        page.wait_for_timeout(80)
                                    except:
                                        pass
                            except:
                                pass
                        time.sleep(per_char)
                    return True
            except:
                continue
        return False

    def submit_form(self, page):
        for sel in Config.SELECTORS.get("submit_button", ["button:has-text('Continue')"]):
            try:
                btn = page.query_selector(sel)
                if btn:
                    try:
                        btn.click()
                    except:
                        try:
                            page.eval_on_selector(sel, "(b)=>b && b.click && b.click()")
                        except:
                            pass
                    return True
            except:
                continue
        return False

    def _extract_sitekey(self, page):
        try:
            keys = page.evaluate("() => Array.from(document.querySelectorAll('[data-sitekey]')).map(e=>e.getAttribute('data-sitekey'))")
            if keys and isinstance(keys, list) and len(keys) > 0:
                return keys[0]
        except:
            pass
        try:
            iframes = page.evaluate("() => Array.from(document.querySelectorAll('iframe')).map(f=>f.src).filter(Boolean)")
            for src in (iframes or []):
                if "recaptcha" in src or "hcaptcha" in src:
                    parts = src.split("k=")
                    if len(parts) > 1:
                        return parts[1].split("&")[0]
        except:
            pass
        return ""

    def validate_once(self, email, page):
        try:
            if Config.URLS["target"] not in page.url:
                page.goto(Config.URLS["target"], wait_until="domcontentloaded", timeout=Config.TIMEOUTS.get("navigation", 20000))
            page.wait_for_timeout(300)
            cookie_task = None
            start_time = time.time()
            if not self.handle_checkbox(page, max_wait_ms=5000):
                return False
            if not self.fill_email(page, email, max_total_time=10.0):
                return False
            self._accept_cookie_if_appears(page)
            if not self.submit_form(page):
                return False
            start = time.time() * 1000
            timeout_ms = Config.TIMEOUTS.get("result_wait", 10000)
            while not self.api_received and not self.captcha_detected and (time.time() * 1000 - start) < timeout_ms:
                if Config.URLS.get("success_redirect") and Config.URLS["success_redirect"] in page.url:
                    self.redirect_detected = True
                    break
                page.wait_for_timeout(80)
            if self.captcha_detected:
                sitekey = self._extract_sitekey(page)
                task = create_captcha_task(page, sitekey or "", Config.URLS["target"])
                return 'captcha'
            if self.redirect_detected:
                return False
            if self.api_received:
                return self.is_valid
            return False
        except Exception:
            return False

    def validate(self, email, page):
        self.reset_state()
        page.on("response", self.handle_response)
        try:
            for attempt in range(1, self.max_attempts + 1):
                result = self.validate_once(email, page)
                if result == 'captcha':
                    return 'captcha'
                if result:
                    return True
                try:
                    page.wait_for_timeout(300)
                except:
                    pass
            return False
        finally:
            try:
                page.remove_listener("response", self.handle_response)
            except:
                pass