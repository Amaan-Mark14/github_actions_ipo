from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from mail import send_email

ARTIFACT_FILE = "notified_ipos.txt"

def load_notified_ipos():
    """Load previously notified IPOs from the artifact file."""
    try:
        if os.path.exists(ARTIFACT_FILE):
            with open(ARTIFACT_FILE, "r") as file:
                return set(line.strip() for line in file.readlines())
        return set()
    except Exception as e:
        print(f"Error loading notified IPOs: {e}")
        return set()

def save_notified_ipos(notified_ipos):
    """Save notified IPOs to the artifact file."""
    try:
        with open(ARTIFACT_FILE, "w") as file:
            for ipo in notified_ipos:
                file.write(f"{ipo}\n")
    except Exception as e:
        print(f"Error saving notified IPOs: {e}")

def create_email_body(new_ipos, past_ipos):
    """Create HTML email content with new IPOs and historical data"""
    past_to_show = list(past_ipos)[-5:]  # Show last 5 notified
    
    return f"""
    <html>
    <head>
        <style>
            /* Keep your existing styles */
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h2 {{ color: #007BFF; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f4f4f4; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 10px 15px; margin: 10px 5px 0; 
                     font-size: 14px; color: white; background-color: #007BFF; 
                     text-decoration: none; border-radius: 4px; }}
            .button:hover {{ background-color: #0056b3; }}
            .history {{ margin-top: 30px; color: #666; }}
        </style>
    </head>
    <body>
        {"<h2>🚨 New Qualified IPOs Found!</h2>" if new_ipos else "<h2>✅ No New IPOs Today</h2>"}
        
        {render_ipo_table(new_ipos) if new_ipos else "<p>No new IPOs meeting criteria found today.</p>"}
        
        <div class="history">
            <h3>Recently Notified IPOs (last 5):</h3>
            <ul>
                {''.join([f'<li>{ipo}</li>' for ipo in past_to_show]) if past_to_show else '<li>No historical data</li>'}
            </ul>
        </div>
        
        <p>
            <a href="https://groww.in/ipo" class="button" target="_blank">Apply on Groww</a>
            <a href="https://dhan.co/ipo" class="button" target="_blank">Apply on Dhan</a>
        </p>
        <p>Happy Investing!</p>
    </body>
    </html>
    """

def render_ipo_table(ipos):
    """Generate HTML table for IPOs"""
    table_rows = []
    for ipo in ipos:
        table_rows.append(f"""
            <tr>
                <td>{ipo['Name']}</td>
                <td>{ipo['Status']}</td>
                <td>{ipo['Est Listing']}</td>
                <td>{ipo['Open Date']}</td>
                <td>{ipo['Close Date']}</td>
                <td>{ipo['Size']}</td>
            </tr>
        """)
    
    return f"""
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Est Listing Gain</th>
                <th>Open Date</th>
                <th>Close Date</th>
                <th>Size</th>
            </tr>
        </thead>
        <tbody>
            {''.join(table_rows)}
        </tbody>
    </table>
    """

def notify_new_ipos(ipo_list):
    """Handle notification logic with history tracking"""
    notified_ipos = load_notified_ipos()
    past_ipos = list(notified_ipos)  # Copy for history display
    
    if not ipo_list:
        subject = "No New Qualified IPOs Today"
        new_ipos = []
    else:
        new_ipos = [ipo for ipo in ipo_list if ipo["Name"] not in notified_ipos]
        subject = f"🚨 {len(new_ipos)} New Qualified IPOs Found!" if new_ipos else "✅ No New IPOs Today"
    
    # Build email body with history
    body = create_email_body(new_ipos, past_ipos)
    
    # Send email only if there are new IPOs or it's the first run
    if new_ipos or not past_ipos:
        if send_email(subject, body, html=True):
            # Update notified IPOs only if email sent successfully
            notified_ipos.update(ipo["Name"] for ipo in new_ipos)
            save_notified_ipos(notified_ipos)

# Keep your existing scrape_ipo_table() and __main__ logic