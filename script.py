import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# Debug print function
def debug_print(message):
    print(f"[DEBUG {datetime.now()}] {message}")

# Load artifact
def load_artifact(artifact_file="notified_ipos.txt"):
    debug_print(f"Loading artifact from {artifact_file}...")
    if not os.path.exists(artifact_file):
        debug_print("Artifact file not found, creating a new one.")
        return {"sent": []}
    with open(artifact_file, "r") as f:
        return json.load(f)

# Save artifact
def save_artifact(data, artifact_file="notified_ipos.txt"):
    debug_print(f"Saving artifact to {artifact_file}...")
    with open(artifact_file, "w") as f:
        json.dump(data, f)

# Scrape IPO table
def scrape_ipo_table():
    debug_print("Starting IPO table scraping...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        debug_print("Fetching website content...")
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )

        debug_print("Parsing page content...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        table = soup.find("table", {"id": "report_table"})
        if not table:
            debug_print("Error: Unable to locate the table on the page.")
            return []

        debug_print("Parsing table rows...")
        rows = table.find_all("tr")
        ipo_list = []

        for row in rows[1:]:
            status_cell = row.find("td", {"data-label": "Status"})
            rating_cell = row.find("td", {"data-label": "Fire Rating"})
            name_cell = row.find("td", {"data-label": "IPO"})
            est_listing_cell = row.find("td", {"data-label": "Est Listing"})
            open_date_cell = row.find("td", {"data-label": "Open"})
            close_date_cell = row.find("td", {"data-label": "Close"})

            if not (status_cell and rating_cell and name_cell and est_listing_cell and open_date_cell and close_date_cell):
                continue

            if "Open" not in status_cell.text.strip():
                continue

            rating_title = rating_cell.find("img")["title"]
            if "Rating 4/5" in rating_title or "Rating 5/5" in rating_title:
                ipo_details = {
                    "Name": name_cell.text.strip(),
                    "Status": status_cell.text.strip(),
                    "Est Listing": est_listing_cell.text.strip(),
                    "Open Date": open_date_cell.text.strip(),
                    "Close Date": close_date_cell.text.strip(),
                }
                ipo_list.append(ipo_details)

        debug_print(f"Found {len(ipo_list)} qualified IPOs")
        return ipo_list

    except Exception as e:
        debug_print(f"Error occurred during IPO scraping: {e}")
        return []

# Notify new IPOs
def notify_new_ipos(artifact, ipos):
    new_ipos = []
    for ipo in ipos:
        if ipo["Name"] not in artifact["sent"]:
            new_ipos.append(ipo)
            artifact["sent"].append(ipo["Name"])
    return new_ipos, artifact["sent"][-5:]

# Send email
def send_email(new_ipos, old_ipos, sender, recipients, smtp_server, smtp_port, smtp_user, smtp_password):
    debug_print("Building email content...")

    new_ipo_table = "".join(
        f"""
        <tr>
            <td>{ipo['Name']}</td>
            <td>{ipo['Status']}</td>
            <td>{ipo['Est Listing']}</td>
            <td>{ipo['Open Date']}</td>
            <td>{ipo['Close Date']}</td>
        </tr>
        """
        for ipo in new_ipos
    )

    old_ipo_table = "".join(
        f"""
        <tr>
            <td>{ipo['Name']}</td>
            <td>{ipo['Status']}</td>
            <td>{ipo['Est Listing']}</td>
            <td>{ipo['Open Date']}</td>
            <td>{ipo['Close Date']}</td>
        </tr>
        """
        for ipo in old_ipos
    )

    body = f"""
    <html>
    <body>
        <h2>New IPO Opportunities</h2>
        <table border="1">
            <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Est. Listing Gain</th>
                <th>Open Date</th>
                <th>Close Date</th>
            </tr>
            {new_ipo_table}
        </table>
        <h2>Old IPO Opportunities</h2>
        <table border="1">
            <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Est. Listing Gain</th>
                <th>Open Date</th>
                <th>Close Date</th>
            </tr>
            {old_ipo_table}
        </table>
    </body>
    </html>
    """

    try:
        debug_print("Connecting to SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            for recipient in recipients:
                msg = MIMEMultipart()
                msg["From"] = sender
                msg["To"] = recipient
                msg["Subject"] = "🚀 IPO Opportunities"
                msg.attach(MIMEText(body, "html"))
                server.sendmail(sender, recipient, msg.as_string())
        debug_print("Emails sent successfully.")
    except Exception as e:
        debug_print(f"Error sending email: {e}")

# Main execution
if __name__ == "__main__":
    artifact = load_artifact()
    ipos = scrape_ipo_table()
    new_ipos, old_ipos = notify_new_ipos(artifact, ipos)
    save_artifact(artifact)
    if new_ipos:
        send_email(
            new_ipos=new_ipos,
            old_ipos=old_ipos,
            sender="your-email@example.com",
            recipients=["recipient@example.com"],
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_user="your-email@example.com",
            smtp_password="your-email-password",
        )
