import random
import time
from pathlib import Path
from config import Config
from src.logger import Logger

log = Logger("BROWSER")

_STEALTH_JS = r"""
Object.defineProperty(navigator, 'webdriver', { get: () => false });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
window.chrome = window.chrome || { runtime: {} };
const _origPerm = window.navigator.permissions && window.navigator.permissions.query;
if (_origPerm) {
  window.navigator.permissions.query = (p) => {
    if (p && p.name === 'notifications') return Promise.resolve({ state: Notification.permission });
    return _origPerm(p);
  };
}
try {
  const ua = navigator.userAgent;
  if (ua && ua.includes('Headless')) {
    Object.defineProperty(navigator, 'userAgent', { get: () => ua.replace('Headless', '') });
  }
} catch (e) {}
"""

_WEBGL_MASK = r"""
(function() {
  try {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
      if (parameter === 37445) return "Intel Inc.";
      if (parameter === 37446) return "Intel Iris OpenGL Engine";
      return getParameter.call(this, parameter);
    };
  } catch(e) {}
})();
"""

_UAS = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36",
]

_VIEWPORTS = [
    {"width":1366,"height":768},
    {"width":1280,"height":720},
    {"width":1536,"height":864},
    {"width":1920,"height":1080},
    {"width":1440,"height":900},
]

_TIMEZONE_MAP = {
    "in": ("Asia/Kolkata", "en-IN"),
    "us": ("America/New_York", "en-US"),
    "eu": ("Europe/Berlin", "en-GB"),
    "sg": ("Asia/Singapore", "en-SG"),
    "jp": ("Asia/Tokyo", "ja-JP"),
}

def _infer_region_from_proxy_user(user: str):
    if not user:
        return None
    u = user.lower()
    if "region-in" in u or u.endswith("-in") or u.endswith("in"):
        return "in"
    if "region-us" in u or u.endswith("-us") or u.endswith("us"):
        return "us"
    if "region-eu" in u or u.endswith("-eu") or u.endswith("eu"):
        return "eu"
    if "sg" in u:
        return "sg"
    if "jp" in u:
        return "jp"
    return None

def _random_fingerprint(proxy_user: str):
    ua = random.choice(_UAS)
    vp = random.choice(_VIEWPORTS)
    region = _infer_region_from_proxy_user(proxy_user)
    tz, locale = None, None
    if region and region in _TIMEZONE_MAP:
        tz, locale = _TIMEZONE_MAP[region]
    else:
        if random.random() < 0.6:
            tz, locale = ("Asia/Kolkata", "en-IN")
        else:
            tz, locale = ("America/New_York", "en-US")
    return {"user_agent": ua, "viewport": vp, "timezone_id": tz, "locale": locale}

class BrowserManager:
    def __init__(self, playwright):
        self.playwright = playwright
        self._browser = None
        self._contexts = []
        self._pages = []
        self._temp_browsers = []
        self._use_persistent = getattr(Config, "USE_PERSISTENT_PROFILE", False)
        self._profile_dir = getattr(Config, "PROFILE_DIR", "profiles/default")
        self._show_logs = getattr(Config, "SHOW_BROWSER_LOGS", False)
        self._launch()

    def _launch(self):
        if self._browser:
            return
        if self._use_persistent:
            Path(self._profile_dir).mkdir(parents=True, exist_ok=True)
            ctx = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self._profile_dir,
                headless=getattr(Config, "HEADLESS", True),
                args=getattr(Config, "BROWSER_ARGS", []) or [],
                viewport=Config.CONTEXT_OPTIONS.get("viewport")
            )
            self._browser = ctx
            if self._show_logs:
                log.info(f"Launched persistent Chromium context headless={getattr(Config,'HEADLESS',True)}")
            return
        self._browser = self.playwright.chromium.launch(
            headless=getattr(Config, "HEADLESS", True),
            args=getattr(Config, "BROWSER_ARGS", []) or []
        )
        if self._show_logs:
            log.info(f"Launched Chromium headless={getattr(Config,'HEADLESS',True)}")

    def _maybe_dismiss_modal(self, page):
        sel = getattr(Config, "SELECTORS", {}).get("error_modal")
        if not sel:
            return False
        try:
            el = page.query_selector(sel)
            if not el:
                return False
            for btn_sel in ["button", ".bn-modal-confirm", ".bn-button", ".ok", ".confirm", "[role='button']"]:
                try:
                    btn = el.query_selector(btn_sel)
                    if btn:
                        btn.click()
                        time.sleep(0.6)
                        return True
                except Exception:
                    continue
            try:
                el.click()
                time.sleep(0.6)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def create_session(self, proxy: dict = None):
        try:
            if proxy and self._use_persistent:
                log.info("Proxy requested but running in persistent-profile mode -> skipping per-session proxy.")
                proxy = None
            fp = _random_fingerprint(getattr(Config, "PROXY_USER", "") if not proxy else proxy.get("username", ""))
            if proxy and not self._use_persistent:
                if self._show_logs:
                    log.info(f"Launching temporary browser with proxy {proxy.get('server')}")
                temp_browser = self.playwright.chromium.launch(
                    headless=getattr(Config, "HEADLESS", True),
                    args=getattr(Config, "BROWSER_ARGS", []) or [],
                    proxy=proxy
                )
                self._temp_browsers.append(temp_browser)
                raw = getattr(Config, "CONTEXT_OPTIONS", {}) or {}
                ctx_opts = {}
                ctx_opts["viewport"] = fp.get("viewport") or raw.get("viewport")
                ctx_opts["locale"] = fp.get("locale") or raw.get("locale")
                ctx_opts["timezone_id"] = fp.get("timezone_id") or raw.get("timezone_id")
                headers = raw.get("extra_http_headers", {})
                if headers:
                    ctx_opts["extra_http_headers"] = headers
                ua = fp.get("user_agent") or headers.get("User-Agent") or raw.get("user_agent")
                if ua:
                    ctx_opts["user_agent"] = ua
                ctx_opts["ignore_https_errors"] = raw.get("ignore_https_errors", True)
                context = temp_browser.new_context(**ctx_opts)
            else:
                if hasattr(self._browser, "new_page") and not hasattr(self._browser, "new_context"):
                    context = self._browser
                else:
                    raw = getattr(Config, "CONTEXT_OPTIONS", {}) or {}
                    ctx_opts = {}
                    fp_global = _random_fingerprint(getattr(Config, "PROXY_USER", ""))
                    ctx_opts["viewport"] = fp_global.get("viewport") or raw.get("viewport")
                    ctx_opts["locale"] = fp_global.get("locale") or raw.get("locale")
                    ctx_opts["timezone_id"] = fp_global.get("timezone_id") or raw.get("timezone_id")
                    headers = raw.get("extra_http_headers", {})
                    if headers:
                        ctx_opts["extra_http_headers"] = headers
                    ua = fp_global.get("user_agent") or headers.get("User-Agent") or raw.get("user_agent")
                    if ua:
                        ctx_opts["user_agent"] = ua
                    ctx_opts["ignore_https_errors"] = raw.get("ignore_https_errors", True)
                    context = self._browser.new_context(**ctx_opts)
            page = context.new_page()
            timeouts = getattr(Config, "TIMEOUTS", {})
            if timeouts.get("navigation"):
                page.set_default_navigation_timeout(timeouts.get("navigation"))
            if timeouts.get("default"):
                page.set_default_timeout(timeouts.get("default"))
            try:
                page.add_init_script(_STEALTH_JS)
            except Exception:
                pass
            try:
                page.evaluate(_WEBGL_MASK)
            except Exception:
                pass
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except Exception:
                pass
            try:
                self._maybe_dismiss_modal(page)
            except Exception:
                pass
            try:
                def _on_load():
                    try:
                        self._maybe_dismiss_modal(page)
                    except Exception:
                        pass
                page.on("load", lambda: _on_load())
            except Exception:
                pass
            self._contexts.append(context)
            self._pages.append(page)
            return page
        except Exception as e:
            log.error(f"Session creation failed: {e}")
            raise

    def human_type(self, page, selector, text, min_delay=50, max_delay=160):
        try:
            page.click(selector)
        except Exception:
            pass
        for ch in text:
            delay = random.randint(min_delay, max_delay)
            try:
                page.keyboard.type(ch, delay=0)
            except Exception:
                try:
                    page.type(selector, ch, delay=delay)
                except Exception:
                    pass
            time.sleep(delay / 1000.0)

    def human_move_and_click(self, page, selector=None, x=None, y=None):
        try:
            vp = page.viewport_size or {"width": 1280, "height": 720}
            if selector:
                box = page.query_selector(selector)
                if box:
                    b = box.bounding_box()
                    if b:
                        x = int(b["x"] + b["width"] / 2)
                        y = int(b["y"] + b["height"] / 2)
            if x is None or y is None:
                x = int(vp["width"] * 0.5) + random.randint(-100, 100)
                y = int(vp["height"] * 0.5) + random.randint(-80, 80)
            page.mouse.move(random.randint(0, 200), random.randint(0, 200), steps=4)
            page.mouse.move(x + random.randint(-10, 10), y + random.randint(-10, 10), steps=6)
            page.mouse.click(x, y)
        except Exception:
            try:
                if selector:
                    page.click(selector)
            except Exception:
                pass

    def cleanup(self):
        try:
            for p in list(self._pages):
                try:
                    p.close()
                except Exception:
                    pass
            self._pages = []
            for ctx in list(self._contexts):
                try:
                    if self._use_persistent and hasattr(self._browser, "new_page") and not hasattr(self._browser, "new_context"):
                        continue
                    ctx.close()
                except Exception:
                    pass
            self._contexts = []
            for tb in list(self._temp_browsers):
                try:
                    tb.close()
                except Exception:
                    pass
            self._temp_browsers = []
            if self._browser and not (self._use_persistent and hasattr(self._browser, "new_page") and not hasattr(self._browser, "new_context")):
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None
        except Exception as e:
            log.error(f"Cleanup error: {e}")
