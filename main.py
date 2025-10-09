#!/usr/bin/env python3
"""
IPO Scraper Main Application

This module orchestrates the scraping and email notification process for high-rated IPOs.
"""

import sys
import io
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set UTF-8 encoding only once
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from scraper import scrape_ipo_table
from emailer import send_email


def debug_print(message):
    print(f"[MAIN] {message}")


def main():
    """
    Main function that orchestrates the IPO scraping and email notification process.
    """
    debug_print("=" * 50)
    debug_print("IPO Scraper Bot Started")
    debug_print(f"Timestamp: {datetime.now()}")
    debug_print("=" * 50)

    # Step 1: Scrape IPO data
    debug_print("Step 1: Scraping IPO data...")
    ipo_data = scrape_ipo_table()

    if not ipo_data:
        debug_print("No high-rated IPOs found. Process completed.")
        return

    debug_print(f"Found {len(ipo_data)} high-rated IPOs")

    # Step 2: Send email notifications
    debug_print("Step 2: Sending email notifications...")
    email_success = send_email(ipo_data)

    if email_success:
        debug_print("Email process completed successfully")
    else:
        debug_print("Email process failed")

    debug_print("=" * 50)
    debug_print("IPO Scraper Bot Completed")
    debug_print(f"Timestamp: {datetime.now()}")
    debug_print("=" * 50)


if __name__ == "__main__":
    main()