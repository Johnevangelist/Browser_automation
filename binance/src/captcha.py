import time
import json
import os

def create_captcha_task(page, sitekey: str, url: str) -> dict:
    """
    Prepare a captcha task payload. 
    This does not call any solver. The batman can hook in their solver here.
    """
    task_id = f"task_{int(time.time()*1000)}"
    payload = {
        "id": task_id,
        "type": "HCaptchaTaskProxyless",
        "websiteKey": sitekey,
        "websiteURL": url,
        "created": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    out_dir = "debug_out"
    os.makedirs(out_dir, exist_ok=True)
    try:
        sfile = os.path.join(out_dir, f"{task_id}.png")
        page.screenshot(path=sfile, full_page=False)
        payload["screenshot"] = sfile
    except Exception:
        pass
    try:
        hfile = os.path.join(out_dir, f"{task_id}.html")
        with open(hfile, "w", encoding="utf-8") as fh:
            fh.write(page.content())
        payload["html"] = hfile
    except Exception:
        pass

    meta_file = os.path.join(out_dir, f"{task_id}.json")
    with open(meta_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    return payload

def inject_token(page, token: str):
    """
    Injects a captcha token into common response fields.
    Call this after the company provides the solved token.
    """
    try:
        page.evaluate(
            "(tok) => { "
            "const el = document.querySelector('textarea[g-recaptcha-response]'); "
            "if(el){ el.value = tok; } "
            "}", token
        )
    except Exception:
        pass
    try:
        page.evaluate(
            "(tok) => { "
            "const el = document.querySelector('[data-sitekey]'); "
            "if(el){ el.setAttribute('data-response', tok); } "
            "}", token
        )
    except Exception:
        pass
