from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
import json
import os


def debug_print(message):
    print(f"[DEBUG {datetime.now()}] {message}")


def update_scraper_status(status, message="", ipo_count=0, error_details=""):
    """
    Update scraper status file for GitHub Actions monitoring.

    Args:
        status: "success", "warning", "error"
        message: Human readable message
        ipo_count: Number of IPOs found
        error_details: Error details if status is "error"
    """
    status_data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "message": message,
        "ipo_count": ipo_count,
        "error_details": error_details,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "workflow_run_number": os.getenv("GITHUB_RUN_NUMBER", "local")
    }

    # Update last successful run timestamp
    if status == "success":
        status_data["last_successful_run"] = datetime.now().isoformat()

    status_file = "scraper_status.json"
    try:
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        debug_print(f"Status updated: {status} - {message}")
    except Exception as e:
        debug_print(f"Failed to write status file: {e}")


def extract_listing_number(text):
    match = re.search(r'\((-?\d+(\.\d+)?)%\)', text)
    return match.group(1) + ' %' if match else text


def convert_rating_to_fraction(text):
    fire_count = text.count("🔥")
    if fire_count > 0:
        return f"{fire_count}.0/5"
    return "No Rating"


def is_high_rating(rating):
    return rating in ["4.0/5", "5.0/5"]


def scrape_ipo_table():
    """
    Scrape IPO data from investorgain.com and return high-rated open IPOs.

    Returns:
        list: List of IPO data in format [name, closing_status, status, est_listing, open_date, close_date, rating]
    """
    debug_print("Starting IPO table scraping...")
    update_scraper_status("running", "Scraping started")

    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-accelerated-2d-canvas")
        options.add_argument("--disable-accelerated-jpeg-decoding")
        options.add_argument("--disable-accelerated-mjpeg-decode")
        options.add_argument("--disable-accelerated-video-decode")
        options.add_argument("--disable-gl-drawing-for-tests")
        options.add_argument("--disable-canvas-aa")
        options.add_argument("--disable-3d-apis")
        options.add_argument("--disable-gpu-process-crash-limit")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        url = "https://www.investorgain.com/report/live-ipo-gmp/331/open/"

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)

        try:
            driver.get(url)
        except Exception as e:
            error_msg = f"Page load timeout: {e}"
            debug_print(error_msg)
            update_scraper_status("error", error_msg, error_details=str(e))
            return []

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "reportTable"))
            )
            debug_print("Table found!")

            # Wait for table to be fully loaded with rows (not "No data available")
            WebDriverWait(driver, 30).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#tableBody tr")) > 0 and
                "No data available" not in d.find_element(By.ID, "tableBody").text
            )
            debug_print("Table rows loaded!")
        except Exception as e:
            error_msg = f"Table loading timeout: {e}"
            debug_print(error_msg)
            update_scraper_status("error", error_msg, error_details=str(e))
            return []

        # Re-find elements to avoid stale references
        rows = driver.find_elements(By.CSS_SELECTOR, "#tableBody tr")
        ipo_list = []

        debug_print(f"Found {len(rows)} total rows in table body")

        for i, row in enumerate(rows, 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                continue

            try:
                # 1. Name (column 0) - extract from link inside div.mono-num
                name_div = cells[0].find_element(By.CSS_SELECTOR, "div.mono-num")
                name_link = name_div.find_element(By.TAG_NAME, "a")
                full_name = name_link.text.strip()

                # Extract closing status from name
                closing_status = ""
                name = full_name
                if full_name.endswith(" O"):
                    name = full_name[:-2].strip()
                    closing_status = "O"
                elif full_name.endswith(" CT"):
                    name = full_name[:-3].strip()
                    closing_status = "CT"

                # 2. GMP - extract percentage from column 1 (₹100 (20.62%))
                gmp_text = cells[1].text.strip()
                est_gains = extract_listing_number(gmp_text)  # Gets the percentage

                # 3. Rating (column 2)
                rating_text = cells[2].text.strip()
                rating = convert_rating_to_fraction(rating_text)

                # 4. Close date (column 9) - format "13-Oct"
                close_date = cells[9].text.strip() if len(cells) > 9 else ""

                # Filter based on rating only
                if is_high_rating(rating):
                    ipo_list.append([name, closing_status, est_gains, close_date, rating])
                    debug_print(f"Added: {name} | GMP: {est_gains} | Close: {close_date} | Rating: {rating}")
                else:
                    debug_print(f"Skipped low rating: {name} ({rating})")

            except Exception as e:
                debug_print(f"Skipping row {i} due to error: {e}")
                continue

        debug_print(f"Processed {len(rows)} rows, found {len(ipo_list)} high-rated IPOs")

        # Update status based on results
        if len(ipo_list) > 0:
            update_scraper_status("success", f"Successfully scraped {len(ipo_list)} high-rated IPOs", len(ipo_list))
        else:
            update_scraper_status("warning", "No high-rated IPOs found - scraper may be working but no matching IPOs", 0)

        return ipo_list

    except Exception as e:
        error_msg = f"Error occurred during IPO scraping: {e}"
        debug_print(error_msg)
        update_scraper_status("error", error_msg, error_details=str(e))
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    # For testing purposes
    ipos = scrape_ipo_table()
    print(f"Found {len(ipos)} high-rated IPOs:")
    for ipo in ipos:
        print(f"  - {ipo[0]} ({ipo[1]}) - {ipo[4]}")