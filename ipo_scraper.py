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
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil import parser
from cryptography.fernet import Fernet


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

def get_recipients():
    try:
        encryption_key = os.environ.get('CONFIG_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("CONFIG_ENCRYPTION_KEY not found in environment")

        fernet = Fernet(encryption_key)
        
        with open('config/recipients.enc.json', 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        config = json.loads(decrypted_data)
        
        # Filter only active recipients
        return [r['email'] for r in config['recipients'] if r['status'] == 'active']
    
    except Exception as e:
        debug_print(f"Error reading recipients: {e}")
        return []

def send_email(ipo_data):
    sender_email = os.environ.get('GMAIL_USER')
    password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient_emails = get_recipients()  
    
    if not all([sender_email, password, recipient_emails]):
        debug_print("Missing email configuration")
        return

    # Create base message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['Subject'] = f"🚀 IPO Alerts - {datetime.now().strftime('%d %B %Y')}"

    if not ipo_data:
        body = "No qualifying IPOs found for the next 3 days."
    else:
        # Create HTML table rows
        table_rows = "".join(
            f"""
            <tr style="border-bottom: 1px solid #dddddd;">
                <td style="padding: 12px; text-align: left;">{ipo[0]}</td>
                <td style="padding: 12px; text-align: center;"><span style="background-color: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 4px;">{ipo[1]}</span></td>
                <td style="padding: 12px; text-align: right;"><span style="color: {'#2e7d32' if float(ipo[2].replace(' %', '')) > 0 else '#c62828'}">{ipo[2]}</span></td>
                <td style="padding: 12px; text-align: center;">{ipo[3]}</td>
                <td style="padding: 12px; text-align: center;">{ipo[4]}</td>
                <td style="padding: 12px; text-align: center;"><span style="background-color: #fff3e0; color: #e65100; padding: 4px 8px; border-radius: 4px;">{ipo[5]}</span></td>
            </tr>
            """
            for ipo in ipo_data
        )

        body = f"""
        <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
                </style>
            </head>
            <body style="font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 800px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 20px;">
                    <h1 style="color: #1a237e; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">
                        🎯 IPO Alerts - Upcoming Offerings
                    </h1>
                    
                    <p style="color: #424242; font-size: 16px; margin-bottom: 20px;">
                        Here are the highly-rated IPOs closing in the next 3 days:
                    </p>
                    
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px;">
                            <thead>
                                <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dddddd;">
                                    <th style="padding: 12px; text-align: left; color: #1a237e;">Company</th>
                                    <th style="padding: 12px; text-align: center; color: #1a237e;">Status</th>
                                    <th style="padding: 12px; text-align: right; color: #1a237e;">Est Listing</th>
                                    <th style="padding: 12px; text-align: center; color: #1a237e;">Open Date</th>
                                    <th style="padding: 12px; text-align: center; color: #1a237e;">Close Date</th>
                                    <th style="padding: 12px; text-align: center; color: #1a237e;">Rating</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                        ℹ️ Note: Only showing IPOs with ratings of 4/5 or 5/5
                    </p>
                    
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px;">
                        <p>To unsubscribe from these alerts, please contact the administrator.</p>
                    </div>
                </div>
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