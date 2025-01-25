import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

ARTIFACT_FILE = 'notified_ipos.txt'
MAX_HISTORY = 10  # Keep more than 5 to have buffer for reminders

def debug_print(message):
    """Helper function for debug messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] DEBUG: {message}")

def setup_driver():
    """Set up Chrome WebDriver with options"""
    debug_print("Setting up Chrome WebDriver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def load_artifact():
    """Load notified IPOs from artifact file"""
    debug_print("Loading artifact file...")
    notified_ipos = []
    try:
        if not os.path.exists(ARTIFACT_FILE):
            with open(ARTIFACT_FILE, 'w') as f:
                pass  
        if os.path.exists(ARTIFACT_FILE):
            with open(ARTIFACT_FILE, 'r') as f:
                notified_ipos = [line.strip() for line in f.readlines()]
            debug_print(f"Loaded {len(notified_ipos)} IPOs from artifact")
        else:
            debug_print("No artifact file found, starting fresh")
    except Exception as e:
        debug_print(f"Error loading artifact: {str(e)}")
    return notified_ipos

def save_artifact(new_ipos):
    """Save newly notified IPOs to artifact file"""
    debug_print("Saving artifact file...")
    try:
        existing = load_artifact()
        updated = list(set(existing + new_ipos))  # Deduplicate
        if len(updated) > MAX_HISTORY:
            updated = updated[-MAX_HISTORY:]
        with open(ARTIFACT_FILE, 'w') as f:
            f.write('\n'.join(updated))
        debug_print(f"Saved {len(new_ipos)} new IPOs to artifact")
    except Exception as e:
        debug_print(f"Error saving artifact: {str(e)}")

def scrape_ipo_table():
    """Scrape the IPO table and extract qualified IPOs"""
    debug_print("Starting IPO table scraping...")
    driver = setup_driver()
    try:
        debug_print("Fetching website content...")
        driver.get("https://www.investorgain.com/report/live-ipo-gmp/331/")
        
        debug_print("Waiting for table to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )
        
        debug_print("Parsing table data...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", {"id": "report_table"})
        
        if not table:
            debug_print("Error: Table not found")
            return []
            
        rows = table.find_all("tr")
        ipo_list = []

        for row in rows[1:]:  # Skip header
            try:
                cells = {
                    'status': row.find("td", {"data-label": "Status"}),
                    'rating': row.find("td", {"data-label": "Fire Rating"}),
                    'name': row.find("td", {"data-label": "IPO"}),
                    'est_listing': row.find("td", {"data-label": "Est Listing"}),
                    'open': row.find("td", {"data-label": "Open"}),
                    'close': row.find("td", {"data-label": "Close"})
                }

                if any(v is None for v in cells.values()):
                    continue

                status = cells['status'].text.strip()
                if "Upcoming" in status:
                    continue
                if "Open" not in status:
                    break

                rating_img = cells['rating'].find("img")
                if not rating_img or not ("Rating 4/5" in rating_img['title'] or "Rating 5/5" in rating_img['title']):
                    continue

                ipo_name = cells['name'].text.strip()
                est_listing = cells['est_listing'].text.split("(")[-1].replace(")", "").strip()
                size = "Small" if ipo_name.endswith("IPO") else "Big" if "SME" in ipo_name else "Unknown"

                ipo_details = {
                    "Name": ipo_name,
                    "Status": status,
                    "Est Listing": est_listing,
                    "Open Date": cells['open'].text.strip(),
                    "Close Date": cells['close'].text.strip(),
                    "Size": size,
                }
                ipo_list.append(ipo_details)
                debug_print(f"Qualified IPO: {ipo_name}")

            except Exception as e:
                debug_print(f"Error parsing row: {str(e)}")
                continue

        debug_print(f"Found {len(ipo_list)} qualified IPOs")
        return ipo_list

    except Exception as e:
        debug_print(f"Scraping error: {str(e)}")
        return []
    finally:
        driver.quit()

# ... rest of your existing functions (notify_new_ipos, send_email, generate_table, main) remain the same ...