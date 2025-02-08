from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from tabulate import tabulate
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil import parser

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

def is_within_three_days(close_date_str):
    try:
        close_date = parser.parse(close_date_str).date()
        today = datetime.now().date()
        return close_date >= today and (close_date - today).days <= 3
    except:
        return False

def is_high_rating(rating):
    return rating in ["4.0/5", "5.0/5"]

def send_email(ipo_data):
    sender_email = os.environ.get('GMAIL_USER')
    password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient_emails = os.environ.get('RECIPIENT_EMAILS').split(',')

    if not all([sender_email, password, recipient_emails]):
        debug_print("Missing email configuration")
        return

    # Create base message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['Subject'] = f"IPO Alerts - {datetime.now().strftime('%Y-%m-%d')}"
    # Don't set To field in headers - we'll use BCC instead

    if not ipo_data:
        body = "No qualifying IPOs found for the next 3 days."
    else:
        headers = ["Name", "Status", "Est Listing", "Open Date", "Close Date", "Rating"]
        table = tabulate(ipo_data, headers=headers, tablefmt="html")
        body = f"""
        <html>
            <body>
                <h2>IPO Alerts - Upcoming Offerings</h2>
                <p>Here are the highly-rated IPOs closing in the next 3 days:</p>
                {table}
                <p>Note: Only showing IPOs with ratings of 4/5 or 5/5</p>
            </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            # Send individual emails with BCC
            for recipient in recipient_emails:
                msg_copy = MIMEMultipart()
                msg_copy['From'] = sender_email
                msg_copy['To'] = sender_email  # Set To as sender
                msg_copy['Subject'] = msg['Subject']
                msg_copy['Bcc'] = recipient
                msg_copy.attach(MIMEText(body, 'html'))
                server.send_message(msg_copy)
                debug_print(f"Email sent to BCC recipient")
        debug_print("All emails sent successfully!")
    except Exception as e:
        debug_print(f"Failed to send email: {e}")

def scrape_ipo_table():
    debug_print("Starting IPO table scraping...")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "report_table"))
        )
        debug_print("Table found!")

        table_element = driver.find_element(By.ID, "report_table")
        rows = table_element.find_elements(By.TAG_NAME, "tr")
        ipo_list = []

        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue

            try:
                name = cells[0].text.strip()
                status = cells[1].text.strip()
                est_listing = extract_listing_number(cells[4].text.strip())
                open_date = cells[8].text.strip()
                close_date = cells[9].text.strip()
                rating = convert_rating_to_fraction(cells[5].text.strip())

                # Filter based on close date and rating
                if is_within_three_days(close_date) and is_high_rating(rating):
                    ipo_list.append([name, status, est_listing, open_date, close_date, rating])
                    debug_print(f"Added qualifying IPO: {name}")

            except Exception as e:
                debug_print(f"Skipping row due to error: {e}")

        return ipo_list

    except Exception as e:
        debug_print(f"Error occurred during IPO scraping: {e}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    ipos = scrape_ipo_table()
    send_email(ipos)