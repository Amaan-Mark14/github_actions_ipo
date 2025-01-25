import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

ARTIFACT_FILE = 'notified_ipos.txt'
MAX_HISTORY = 10  # Keep more than 5 to have buffer for reminders

def debug_print(message):
    """Helper function for debug messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] DEBUG: {message}")

def load_artifact():
    """Load notified IPOs from artifact file"""
    debug_print("Loading artifact file...")
    notified_ipos = []
    try:
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
        # Load existing IPOs and add new ones
        existing = load_artifact()
        updated = list(set(existing + new_ipos))  # Deduplicate
        
        # Keep only the most recent MAX_HISTORY entries
        if len(updated) > MAX_HISTORY:
            updated = updated[-MAX_HISTORY:]
        
        with open(ARTIFACT_FILE, 'w') as f:
            f.write('\n'.join(updated))
        debug_print(f"Saved {len(new_ipos)} new IPOs to artifact")
    except Exception as e:
        debug_print(f"Error saving artifact: {str(e)}")

def scrape_ipo_table():
    """Scrape the IPO table and extract qualified IPOs with enhanced error handling"""
    debug_print("Starting IPO table scraping...")
    driver = None
    try:
        # WebDriver setup
        debug_print("Initializing WebDriver...")
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

        # Fetch content
        debug_print("Fetching website content...")
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        driver.get(url)

        # Wait for table
        debug_print("Waiting for table to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )

        # Parse content
        debug_print("Parsing page content...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        driver = None

        # Extract table data
        debug_print("Locating IPO table...")
        table = soup.find("table", {"id": "report_table"})
        if not table:
            debug_print("Error: IPO table not found")
            return []

        debug_print("Parsing table rows...")
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
        if driver:
            driver.quit()

def notify_new_ipos(scraped_ipos):
    """Identify new IPOs and prepare notification content"""
    debug_print("Identifying new IPOs...")
    notified = load_artifact()
    
    # Get IPO names from scraped data
    current_ipo_names = [ipo["Name"] for ipo in scraped_ipos]
    
    # Find new IPOs
    new_ipos = [ipo for ipo in scraped_ipos if ipo["Name"] not in notified]
    
    # Get recent history (last 5 notified IPOs)
    old_ipos = notified[-5:]
    
    # Get names of new IPOs for saving
    new_ipo_names = [ipo["Name"] for ipo in new_ipos]
    
    return {
        'new_ipos': new_ipos,
        'old_ipo_names': old_ipos,
        'new_ipo_names': new_ipo_names
    }

def send_email(new_ipos, old_ipo_names, scraped_ipos):
    """Send email via Google SMTP with BCC recipients"""
    debug_print("Preparing email...")
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Daily IPO Update - New Opportunities"
        msg['From'] = os.environ['SMTP_USER']
        
        # Get recipients from secrets
        recipients = os.environ['RECIPIENTS'].split(',')
        msg['Bcc'] = ", ".join(recipients)
        debug_print(f"Preparing email for {len(recipients)} recipients (BCC)")

        # Find old IPO details from scraped data
        old_ipos = [ipo for ipo in scraped_ipos if ipo["Name"] in old_ipo_names]

        # Build HTML content
        html = f"""
        <html>
        <head>
            <style>
                /* Existing styles from your code */
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
                /* ... include all other styles from your original code ... */
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📈 Daily IPO Updates</h1>
                </div>
                <div class="content">
                    {"<p>🚨 New IPO Opportunities:</p>" if new_ipos else "<p>No new IPOs today. Here are recent updates:</p>"}
                    
                    {generate_table(new_ipos, 'New IPOs')}
                    
                    {generate_table(old_ipos, 'Recent IPOs (Reminder)') if old_ipos else ''}
                </div>
                <div class="footer">
                    <p>This is an automated report. Visit the 
                    <a href="https://www.investorgain.com/report/live-ipo-gmp/331/">source website</a> 
                    for more details.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML content
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        debug_print("Connecting to SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
            server.send_message(msg)
        debug_print("Email sent successfully")

    except Exception as e:
        debug_print(f"Email sending failed: {str(e)}")

def generate_table(ipos, title):
    """Generate HTML table for IPO data"""
    if not ipos:
        return ""
    
    rows = []
    for ipo in ipos:
        status_class = "open" if "Open" in ipo["Status"] else "closed"
        rows.append(f"""
            <tr>
                <td>{ipo['Name']}</td>
                <td><span class="status {status_class}">{ipo['Status']}</span></td>
                <td>{ipo['Est Listing']}</td>
                <td>{ipo['Open Date']}</td>
                <td>{ipo['Close Date']}</td>
                <td>{ipo['Size']}</td>
            </tr>
        """)
    
    return f"""
    <h3>{title}</h3>
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
            {''.join(rows)}
        </tbody>
    </table>
    """

def main():
    debug_print("Script execution started")
    
    # Scrape IPO data
    scraped_ipos = scrape_ipo_table()
    if not scraped_ipos:
        debug_print("No IPOs found or scraping failed")
        return
    
    # Process notifications
    notification_data = notify_new_ipos(scraped_ipos)
    
    # Only send email if there are new IPOs or reminders
    if notification_data['new_ipos'] or notification_data['old_ipo_names']:
        send_email(
            notification_data['new_ipos'],
            notification_data['old_ipo_names'],
            scraped_ipos
        )
        if notification_data['new_ipo_names']:
            save_artifact(notification_data['new_ipo_names'])
    else:
        debug_print("No new IPOs or reminders to send")

if __name__ == "__main__":
    main()