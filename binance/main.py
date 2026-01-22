import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
import src.captcha as captcha

from src.logger import Logger
from src.utils import load_emails, save_valid_email, clear_output
from src.browser import BrowserManager
from src.checker import EmailChecker
from config import Config

def process_email(thread_id, email, lock):
    logger = Logger(f"T{thread_id}")
    proxy = {
        "server": f"http://{Config.PROXY_HOST}:{Config.PROXY_PORT}",
        "username": Config.PROXY_USER,
        "password": Config.PROXY_PASS,
    }
    result = None
    try:
        with sync_playwright() as playwright:
            browser = BrowserManager(playwright)
            checker = EmailChecker()
            page = browser.create_session(proxy=proxy)
            result = checker.validate(email, page)
            if result == "captcha":
                with lock:
                    logger.warn(f"Captcha detected for {email}")
            elif result:
                with lock:
                    save_valid_email(email)
                    logger.success(f"Valid: {email}")
            else:
                logger.dim(f"Invalid: {email}")
            browser.cleanup()
    except Exception as e:
        with lock:
            logger.error(f"Error processing {email}: {e}")
    return (email, result)

def main():
    logger = Logger("MAIN")
    logger.header("Binance VM - made by @nonvenmous")
    emails = load_emails()
    if not emails:
        logger.error("No emails found in data/emails.txt")
        return
    clear_output()
    cpu = os.cpu_count() or 1
    thread_count = min(max(1, cpu * 2), 8, len(emails))
    logger.info(f"Processing {len(emails)} emails with {thread_count} threads")
    print("-" * 50)
    lock = threading.Lock()
    all_results = []
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [
            executor.submit(process_email, i, email, lock)
            for i, email in enumerate(emails)
        ]
        for future in as_completed(futures):
            try:
                email, result = future.result()
                all_results.append((email, result))
            except Exception as e:
                logger.error(f"Execution error: {e}")
    print("-" * 50)
    logger.header("Results")
    total_checked = len(all_results)
    valid_found = sum(1 for _, res in all_results if res is True)
    logger.info(f"Total checked: {total_checked}")
    logger.success(f"Valid found: {valid_found}")
    logger.info("Output: data/valid.txt")

if __name__ == "__main__":
    main()
