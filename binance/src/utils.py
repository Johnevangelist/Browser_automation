import os
from config import Config
from .logger import Logger

logger = Logger("UTILS")

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def load_emails():
    ensure_data_dir()
    try:
        with open(Config.FILES["emails"], 'r', encoding='utf-8') as f:
            emails = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(emails)} emails")
        return emails
    except FileNotFoundError:
        logger.error(f"File not found: {Config.FILES['emails']}")
        return []
    except Exception as e:
        logger.error(f"Error loading emails: {e}")
        return []

def save_valid_email(email):
    ensure_data_dir()
    try:
        with open(Config.FILES["valid"], 'a', encoding='utf-8') as f:
            f.write(email + '\n')
    except Exception as e:
        logger.error(f"Error saving {email}: {e}")

def clear_output():
    ensure_data_dir()
    try:
        with open(Config.FILES["valid"], 'w') as f:
            pass
    except Exception as e:
        logger.error(f"Error clearing output: {e}")