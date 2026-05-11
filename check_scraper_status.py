#!/usr/bin/env python3
"""
Status check script for GitHub Actions.
Reads scraper_status.json and outputs appropriate GitHub Actions annotations.
Exits with error code if status indicates failure.
"""

import json
import sys
import os
from datetime import datetime, timedelta


def load_status():
    """Load scraper status from file."""
    try:
        with open("scraper_status.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("::error file=check_scraper_status.py::scraper_status.json not found - scraper may have failed to run")
        return None
    except json.JSONDecodeError as e:
        print(f"::error file=check_scraper_status.py::Invalid JSON in scraper_status.json: {e}")
        return None


def check_status_stale(status_data):
    """Check if status data is stale (older than 24 hours)."""
    try:
        timestamp = datetime.fromisoformat(status_data["timestamp"])
        return datetime.now() - timestamp > timedelta(hours=24)
    except (KeyError, ValueError):
        return True


def main():
    status_data = load_status()

    if not status_data:
        sys.exit(1)

    status = status_data.get("status", "unknown")
    message = status_data.get("message", "")
    ipo_count = status_data.get("ipo_count", 0)
    error_details = status_data.get("error_details", "")
    workflow_run_id = status_data.get("workflow_run_id", "unknown")

    # Print status summary
    print(f"Scraper Status: {status.upper()}")
    print(f"IPOs Found: {ipo_count}")
    print(f"Message: {message}")
    print(f"Workflow Run ID: {workflow_run_id}")

    # Check if data is stale
    if check_status_stale(status_data):
        print("::warning::Scraper status data is stale (older than 24 hours)")

    # Exit with appropriate code based on status
    if status == "error":
        print(f"::error file=scraper.py::Scraper failed: {message}")
        if error_details:
            print(f"::error file=scraper.py::Error details: {error_details}")
        sys.exit(1)

    elif status == "warning":
        print(f"::warning file=scraper.py::{message}")
        # Don't exit with error for warnings, just alert
        sys.exit(0)

    elif status == "running":
        print("::notice::Scraper is currently running")
        sys.exit(0)

    elif status == "success":
        print(f"::notice::Scraper completed successfully with {ipo_count} IPOs found")
        sys.exit(0)

    else:
        print(f"::error file=scraper.py::Unknown status: {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()