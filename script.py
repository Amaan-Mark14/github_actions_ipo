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

def debug_print(message):
    """Helper function for debug output"""
    print(f"[DEBUG] {message}")

def load_notified_ipos():
    """Load previously notified IPOs from the artifact file."""
    debug_print("Loading notified IPOs...")
    try:
        if os.path.exists(ARTIFACT_FILE):
            with open(ARTIFACT_FILE, "r") as file:
                ipos = set(line.strip() for line in file.readlines())
                debug_print(f"Loaded {len(ipos)} IPOs from artifact file")
                return ipos
        debug_print("No artifact file found, starting fresh")
        return set()
    except Exception as e:
        debug_print(f"Error loading notified IPOs: {e}")
        return set()

def save_notified_ipos(notified_ipos):
    """Save notified IPOs to the artifact file."""
    debug_print("Saving notified IPOs...")
    try:
        with open(ARTIFACT_FILE, "w") as file:
            for ipo in notified_ipos:
                file.write(f"{ipo}\n")
        debug_print(f"Saved {len(notified_ipos)} IPOs to artifact file")
    except Exception as e:
        debug_print(f"Error saving notified IPOs: {e}")

def scrape_ipo_table():
    """Scrape the IPO table and extract qualified IPOs."""
    debug_print("Starting IPO table scraping...")
    try:
        # Step 1: Set up WebDriver with headless mode
        debug_print("Initializing WebDriver...")
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

        # Step 2: Fetch the website's HTML content
        debug_print("Fetching website content...")
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        driver.get(url)

        # Step 3: Wait for the table to load
        debug_print("Waiting for table to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )

        # Step 4: Parse the page with BeautifulSoup
        debug_print("Parsing page content...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # Step 5: Locate the main table
        debug_print("Locating IPO table...")
        table = soup.find("table", {"id": "report_table"})
        if not table:
            debug_print("Error: Unable to locate the table on the page.")
            return "Error: Unable to locate the table on the page."

        # Step 6: Parse rows in the table
        debug_print("Parsing table rows...")
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
                debug_print(f"Found qualified IPO: {ipo_name}")

        debug_print(f"Found {len(ipo_list)} qualified IPOs")
        return ipo_list

    except Exception as e:
        debug_print(f"Error during scraping: {e}")
        return f"Error: {e}"

def notify_new_ipos(ipo_list):
    """Filter and notify about new IPOs."""
    debug_print("Starting notification process...")
    if not ipo_list:
        debug_print("No IPOs found in the list")
        return

    notified_ipos = load_notified_ipos()
    new_ipos = [ipo for ipo in ipo_list if ipo["Name"] not in notified_ipos]
    debug_print(f"Found {len(new_ipos)} new IPOs")

    if not new_ipos:
        debug_print("No new IPOs to notify")
        return

    # Build the HTML email body
    debug_print("Building email content...")
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f7fafc;
                color: #2d3748;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background-color: #4299e1;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }}
            th {{
                background-color: #edf2f7;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.05em;
            }}
            tr:hover {{
                background-color: #f7fafc;
            }}
            .status {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            .status.open {{
                background-color: #48bb78;
                color: white;
            }}
            .status.closed {{
                background-color: #f56565;
                color: white;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background-color: #edf2f7;
                font-size: 14px;
                color: #4a5568;
            }}
            .footer a {{
                color: #4299e1;
                text-decoration: none;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
            .cta-buttons {{
                text-align: center;
                margin: 20px 0;
            }}
            .cta-buttons a {{
                display: inline-block;
                padding: 10px 20px;
                margin: 0 10px;
                background-color: #4299e1;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 500;
            }}
            .cta-buttons a:hover {{
                background-color: #3182ce;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 New IPO Opportunities</h1>
            </div>
            <div class="content">
                <p>Here are the latest IPO opportunities that match your criteria:</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Est. Listing Gain</th>
                            <th>Open Date</th>
                            <th>Close Date</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for ipo in new_ipos:
        status_class = "open" if "Open" in ipo['Status'] else "closed"
        body += f"""
                        <tr>
                            <td>{ipo['Name']}</td>
                            <td><span class="status {status_class}">{ipo['Status']}</span></td>
                            <td>{ipo['Est Listing']}</td>
                            <td>{ipo['Open Date']}</td>
                            <td>{ipo['Close Date']}</td>
                            <td>{ipo['Size']}</td>
                        </tr>
        """

    body += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    # Send email notification
    debug_print("Attempting to send email...")
    if send_email("New Qualified IPOs", body, html=True):
        debug_print("Email sent successfully")
        # Update the notified IPOs
        notified_ipos.update(ipo["Name"] for ipo in new_ipos)
        save_notified_ipos(notified_ipos)
    else:
        debug_print("Failed to send email")

if __name__ == "__main__":
    debug_print("Starting IPO Notifier script")
    print("Scraping IPO table...")
    ipo_result = scrape_ipo_table()
    if isinstance(ipo_result, str):  # Error message
        debug_print(f"Scraping error: {ipo_result}")
        print(ipo_result)
    else:
        debug_print(f"Scraping completed with {len(ipo_result)} IPOs found")
        notify_new_ipos(ipo_result)
    debug_print("Script execution completed")