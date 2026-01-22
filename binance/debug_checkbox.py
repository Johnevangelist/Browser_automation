# debug_checkbox.py
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import Config

OUT_DIR = Path("debug_out")
OUT_DIR.mkdir(exist_ok=True)

proxy = {
    "server": f"http://{Config.PROXY_HOST}:{Config.PROXY_PORT}",
    "username": getattr(Config, "PROXY_USER", ""),
    "password": getattr(Config, "PROXY_PASS", ""),
}

selectors_to_test = [
    "input[type='checkbox']",
    "input[name='agreement']",
    "input[name='terms']",
    "label:has-text('Terms')",
    "label:has-text('Terms of Service')",
    "div[class*='checkbox']",
    ".bn-checkbox",
    "input",
    "input[type='email']",
    "input[name='email']",
    "input#email"
]

def dump_locators(page):
    out = []
    for sel in selectors_to_test:
        try:
            loc = page.locator(sel)
            cnt = loc.count()
        except Exception as e:
            cnt = f"error:{e}"
        out.append((sel, cnt))
    return out

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, proxy=proxy, args=getattr(Config, "BROWSER_ARGS", None) or [])
    context = browser.new_context(viewport={"width":1366,"height":768})
    page = context.new_page()

    print("navigating...")
    page.goto(Config.URLS["target"], wait_until="domcontentloaded", timeout=30000)
    time.sleep(1.2)

    print("taking screenshot...")
    ss_path = OUT_DIR / "debug_checkbox.png"
    page.screenshot(path=str(ss_path), full_page=True)

    print("saving html...")
    html = page.content()
    html_path = OUT_DIR / "debug_page.html"
    html_path.write_text(html, encoding="utf-8")

    print("dumping locator counts:")
    locs = dump_locators(page)
    for sel, cnt in locs:
        print(f"  {sel} -> {cnt}")

    # If any input[type='checkbox'] found, print attributes of first one
    try:
        cb = page.locator("input[type='checkbox']")
        if cb.count() > 0:
            first = cb.nth(0)
            attrs = {}
            for a in ["id","name","type","aria-checked","checked","class","role"]:
                try:
                    attrs[a] = first.get_attribute(a)
                except Exception as e:
                    attrs[a] = f"err:{e}"
            bbox = None
            try:
                bbox = first.bounding_box()
            except:
                bbox = None
            print("\nfirst input[type='checkbox'] attributes:")
            for k,v in attrs.items():
                print(f"  {k}: {v}")
            print("  bounding_box:", bbox)
        else:
            print("\nno input[type='checkbox'] found")
    except Exception as e:
        print("error inspecting checkbox:", e)

    print("\nlisting visible labels near the form (first 20):")
    try:
        labels = page.locator("label").all_inner_texts()
        for i,txt in enumerate(labels[:20]):
            print(f"  label[{i}]: {txt.strip()[:120]}")
    except Exception as e:
        print("label listing error:", e)

    print("\noutput files saved to:", OUT_DIR.resolve())
    browser.close()
