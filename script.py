from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from mail import send_email

# File to track notified IPOs
ARTIFACT_FILE = "notified_ipos.txt"

def load_notified_ipos():
    """Load previously notified IPOs from the artifact file."""
    if os.path.exists(ARTIFACT_FILE):
        with open(ARTIFACT_FILE, "r") as file:
            return set(line.strip() for line in file.readlines())
    return set()

def save_notified_ipos(notified_ipos):
    """Save notified IPOs to the artifact file."""
    with open(ARTIFACT_FILE, "w") as file:
        for ipo in notified_ipos:
            file.write(f"{ipo}\n")

def scrape_ipo_table():
    """Scrape the IPO table and extract qualified IPOs."""
    try:
        # Step 1: Set up WebDriver with headless mode
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

        # Step 2: Fetch the website's HTML content
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        driver.get(url)

        # Step 3: Wait for the table to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )

        # Step 4: Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # Step 5: Locate the main table
        table = soup.find("table", {"id": "report_table"})
        if not table:
            return "Error: Unable to locate the table on the page."

        # Step 6: Parse rows in the table
        rows = table.find_all("tr")
        ipo_list = []  # To store qualified IPOs

        for row in rows[1:]:  # Skip header row
            status_cell = row.find("td", {"data-label": "Status"})
            rating_cell = row.find("td", {"data-label": "Fire Rating"})
            name_cell = row.find("td", {"data-label": "IPO"})
            est_listing_cell = row.find("td", {"data-label": "Est Listing"})
            open_date_cell = row.find("td", {"data-label": "Open"})
            close_date_cell = row.find("td", {"data-label": "Close"})

            if not (status_cell and rating_cell and name_cell and est_listing_cell and open_date_cell and close_date_cell):
                continue

            status_text = status_cell.text.strip()
            if "Upcoming" in status_text:
                continue
            elif "Open" not in status_text:
                break

            rating_title = rating_cell.find("img")["title"]
            if "Rating 4/5" in rating_title or "Rating 5/5" in rating_title:
                ipo_name = name_cell.text.strip()
                est_listing_text = est_listing_cell.text.strip()
                open_date = open_date_cell.text.strip()
                close_date = close_date_cell.text.strip()
                est_listing_percent = est_listing_text.split("(")[-1].replace(")", "").strip()
                size = "Small" if ipo_name.endswith("IPO") else "Big" if "SME" in ipo_name else "Unknown"

                ipo_details = {
                    "Name": ipo_name,
                    "Status": status_text,
                    "Est Listing": est_listing_percent,
                    "Open Date": open_date,
                    "Close Date": close_date,
                    "Size": size,
                }
                ipo_list.append(ipo_details)

        return ipo_list

    except Exception as e:
        return f"Error: {e}"

def notify_new_ipos(ipo_list):
    """Filter and notify about new IPOs."""
    if not ipo_list:
        print("No new IPOs to notify.")
        return

    notified_ipos = load_notified_ipos()
    new_ipos = [ipo for ipo in ipo_list if ipo["Name"] not in notified_ipos]

    if not new_ipos:
        print("No new IPOs to notify.")
        return

    body = "Apply for the following IPOs:\n\n"
    for ipo in new_ipos:
        body += (
            f"Name: {ipo['Name']}\n"
            f"Status: {ipo['Status']}\n"
            f"Est Listing Gain: {ipo['Est Listing']}\n"
            f"Open Date: {ipo['Open Date']}\n"
            f"Close Date: {ipo['Close Date']}\n"
            f"Size: {ipo['Size']}\n\n"
        )

    send_email("New Qualified IPOs", body)

    notified_ipos.update(ipo["Name"] for ipo in new_ipos)
    save_notified_ipos(notified_ipos)

if __name__ == "__main__":
    print("Scraping IPO table...")
    ipo_result = scrape_ipo_table()
    if isinstance(ipo_result, str):  # Error message
        print(ipo_result)
    else:
        notify_new_ipos(ipo_result)
