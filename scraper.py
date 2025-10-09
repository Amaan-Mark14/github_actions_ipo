from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re


def debug_print(message):
    print(f"[DEBUG {datetime.now()}] {message}")


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
        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )
        debug_print("Table found!")

        # Wait for table to be fully loaded with rows
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_element(By.ID, "report_table").find_elements(By.TAG_NAME, "tr")) > 1
        )
        debug_print("Table rows loaded!")

        table_element = driver.find_element(By.ID, "report_table")
        rows = table_element.find_elements(By.TAG_NAME, "tr")
        ipo_list = []

        debug_print(f"Found {len(rows)} total rows in table")

        for i, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                continue

            try:
                # 1. Name (column 0)
                full_name = cells[0].text.strip()

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

        debug_print(f"Processed {len(rows)-1} rows, found {len(ipo_list)} high-rated IPOs")
        return ipo_list

    except Exception as e:
        debug_print(f"Error occurred during IPO scraping: {e}")
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    # For testing purposes
    ipos = scrape_ipo_table()
    print(f"Found {len(ipos)} high-rated IPOs:")
    for ipo in ipos:
        print(f"  - {ipo[0]} ({ipo[1]}) - {ipo[4]}")