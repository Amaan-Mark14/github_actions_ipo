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
MAX_HISTORY = 10

def debug_print(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] DEBUG: {message}")

def setup_driver():
    debug_print("Initializing Firefox WebDriver...")
    options = Options()
    options.add_argument("--headless")
    options.page_load_strategy = 'eager'
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(60)
    return driver

def load_artifact():
    debug_print("Loading artifact...")
    notified = []
    try:
        if os.path.exists(ARTIFACT_FILE):
            with open(ARTIFACT_FILE, 'r') as f:
                notified = [line.strip() for line in f.readlines()]
            debug_print(f"Loaded {len(notified)} IPOs from artifact")
    except Exception as e:
        debug_print(f"Error loading artifact: {str(e)}")
    return notified

def save_artifact(new_ipos):
    debug_print("Updating artifact...")
    try:
        existing = load_artifact()
        updated = list(set(existing + new_ipos))
        if len(updated) > MAX_HISTORY:
            updated = updated[-MAX_HISTORY:]
        with open(ARTIFACT_FILE, 'w') as f:
            f.write('\n'.join(updated))
        debug_print(f"Saved {len(new_ipos)} new IPOs")
    except Exception as e:
        debug_print(f"Error saving artifact: {str(e)}")

def scrape_ipo_table():
    debug_print("Starting scraping...")
    driver = setup_driver()
    try:
        driver.get("https://www.investorgain.com/report/live-ipo-gmp/331/")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", {"id": "report_table"})
        if not table:
            debug_print("Table not found")
            return []
            
        ipo_list = []
        for row in table.find_all("tr")[1:]:
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
                if "Upcoming" in status or "Open" not in status:
                    continue
                    
                rating_img = cells['rating'].find("img")
                if not rating_img or "Rating [45]/5" not in rating_img['title']:
                    continue
                    
                ipo_name = cells['name'].text.strip()
                ipo_list.append({
                    "Name": ipo_name,
                    "Status": status,
                    "Est Listing": cells['est_listing'].text.split("(")[-1].replace(")", "").strip(),
                    "Open Date": cells['open'].text.strip(),
                    "Close Date": cells['close'].text.strip(),
                    "Size": "Small" if ipo_name.endswith("IPO") else "Big" if "SME" in ipo_name else "Unknown"
                })
                
            except Exception as e:
                debug_print(f"Row error: {str(e)}")
                continue
                
        debug_print(f"Found {len(ipo_list)} qualified IPOs")
        return ipo_list
        
    except Exception as e:
        debug_print(f"Scraping failed: {str(e)}")
        return []
    finally:
        driver.quit()

def generate_email_content(new_ipos, old_ipos):
    status_style = lambda s: f"background-color: {'#48bb78' if 'Open' in s else '#f56565'}; color: white; padding: 2px 8px; border-radius: 4px"
    
    rows = []
    for ipo in new_ipos + old_ipos:
        rows.append(f"""
        <tr>
            <td>{ipo['Name']}</td>
            <td><span style="{status_style(ipo['Status'])}">{ipo['Status']}</span></td>
            <td>{ipo['Est Listing']}</td>
            <td>{ipo['Open Date']}</td>
            <td>{ipo['Close Date']}</td>
            <td>{ipo['Size']}</td>
        </tr>
        """)
    
    return f"""
    <html>
    <body>
        <h2>📈 IPO Updates</h2>
        {"<h3>New IPOs</h3>" if new_ipos else "<p>No new IPOs today</p>"}
        {f'<table border="1"><tr><th>Name</th><th>Status</th><th>Est. Listing</th><th>Open</th><th>Close</th><th>Size</th></tr>{"".join(rows)}</table>' if rows else ''}
        <p style="color: #666; margin-top: 20px;">This is an automated report. Visit the <a href="https://www.investorgain.com/report/live-ipo-gmp/331/">source</a> for details.</p>
    </body>
    </html>
    """

def send_email(new_ipos, old_ipo_names, scraped_ipos):
    try:
        old_ipos = [ipo for ipo in scraped_ipos if ipo["Name"] in old_ipo_names]
        if not new_ipos and not old_ipos:
            debug_print("Nothing to send")
            return
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "IPO Daily Report"
        msg['From'] = os.environ['SMTP_USER']
        msg['Bcc'] = os.environ['RECIPIENTS']
        
        html = generate_email_content(new_ipos, old_ipos)
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
            server.send_message(msg)
        debug_print("Email sent successfully")
        
    except Exception as e:
        debug_print(f"Email error: {str(e)}")

def main():
    debug_print("=== Starting Process ===")
    scraped = scrape_ipo_table()
    if not scraped:
        return
        
    notified = load_artifact()
    new_ipos = [ipo for ipo in scraped if ipo["Name"] not in notified]
    old_ipos = notified[-5:]
    
    if new_ipos or old_ipos:
        send_email(new_ipos, old_ipos, scraped)
        if new_ipos:
            save_artifact([ipo["Name"] for ipo in new_ipos])
            
    debug_print("=== Process Completed ===")

if __name__ == "__main__":
    main()