import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def debug_print(message):
    print(f"[DEBUG {datetime.now()}] {message}")


def get_recipients():
    """
    Load email recipients from local text file or environment variable.

    Returns:
        list: List of recipient email addresses
    """
    try:
        # First try environment variable (for GitHub Actions)
        env_emails = os.environ.get('EMAIL_RECIPIENTS')
        if env_emails:
            emails = [email.strip() for email in env_emails.split(',') if email.strip()]
            debug_print(f"Using {len(emails)} recipients from environment variable")
            return emails

        # Fall back to local text file
        if os.path.exists('config/recipients.txt'):
            with open('config/recipients.txt', 'r') as f:
                content = f.read().strip()
                # Split by comma (same format as GitHub Secrets)
                emails = [email.strip() for email in content.split(',') if email.strip()]
            debug_print(f"Using {len(emails)} recipients from local text file")
            return emails

        debug_print("No email recipients found")
        return []

    except Exception as e:
        debug_print(f"Error reading recipients: {e}")
        return []


def create_email_html(ipo_data):
    """
    Create HTML email content for IPO alerts.

    Args:
        ipo_data (list): List of IPO data

    Returns:
        str: HTML email content
    """
    if not ipo_data:
        return None

    ipo_cards = "".join(
        f"""
        <div class="ipo-card" style="margin-bottom: 20px; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; background-color: white;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 250px;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0; color: #1a237e; font-size: 18px; font-weight: 600;">{ipo[0]}</h3>
                        {"<span style='background-color: #ff9800; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;'>CT</span>" if ipo[1] == "CT" else "<span style='background-color: #4caf50; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;'>O</span>" if ipo[1] == "O" else ""}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <div style="color: #666; font-size: 13px; margin-bottom: 4px;">Est. Gains (GMP %)</div>
                        <div style="color: {'#2e7d32' if '%' in ipo[2] and float(ipo[2].replace(' %', '')) > 0 else '#c62828' if '%' in ipo[2] and float(ipo[2].replace(' %', '')) < 0 else '#666'}; font-size: 16px; font-weight: 600;">{ipo[2]}</div>
                    </div>
                    <div>
                        <div style="color: #666; font-size: 13px; margin-bottom: 4px;">Rating</div>
                        <div style="background-color: #fff3e0; color: #e65100; padding: 6px 12px; border-radius: 6px; display: inline-block; font-weight: 500;">{ipo[4]}</div>
                    </div>
                </div>

                <div style="flex: 1; margin-left: 20px; min-width: 250px;">
                    <div style="margin-bottom: 16px;">
                        <div style="color: #666; font-size: 13px; margin-bottom: 4px;">Close Date</div>
                        <div style="color: #333; font-size: 15px; font-weight: 500;">{ipo[3]}</div>
                    </div>
                    <div style="margin-top: 12px;">
                        <div style="color: #666; font-size: 13px; margin-bottom: 4px;">Days Remaining</div>
                        <div style="color: #1565c0; font-size: 15px; font-weight: 500;">{(datetime.strptime(f"{ipo[3]}-{datetime.now().year}", '%d-%b-%Y') - datetime.now()).days} days</div>
                    </div>
                </div>
            </div>
        </div>
        """
        for ipo in ipo_data
    )

    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
            </style>
        </head>
        <body style="font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 12px; background-color: #f5f5f5; -webkit-font-smoothing: antialiased;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); padding: 24px;">
                <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #f0f0f0;">
                    <h1 style="color: #1a237e; font-size: 24px; margin: 0; font-weight: 600;">
                        🎯 IPO Alerts
                    </h1>
                    <p style="color: #666; font-size: 15px; margin: 8px 0 0 0;">
                        {datetime.now().strftime('%d %B %Y')}
                    </p>
                </div>

                <p style="color: #424242; font-size: 16px; margin: 0 0 24px 0; line-height: 1.5;">
                    Here are the highly-rated IPOs currently open:
                </p>

                <div style="margin-bottom: 24px;">
                    {ipo_cards}
                </div>

                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 16px; margin-top: 24px;">
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        ℹ️ <strong>Status Labels:</strong> <span style="background-color: #4caf50; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">O</span> = Open, <span style="background-color: #ff9800; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">CT</span> = Closes Today
                    </p>
                    <p style="color: #666; font-size: 14px; margin: 8px 0 0 0;">
                        Only showing IPOs with ratings of 4/5 or 5/5
                    </p>
                </div>

                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #f0f0f0; color: #666; font-size: 13px;">
                    <p style="margin: 0;">To unsubscribe from these alerts, please contact the administrator.</p>
                </div>
            </div>
        </body>
    </html>
    """


def send_email(ipo_data):
    """
    Send email notifications about high-rated IPOs.

    Args:
        ipo_data (list): List of IPO data to include in the email
    """
    sender_email = os.environ.get('GMAIL_USER')
    password = os.environ.get('GMAIL_PASSWORD')
    recipient_emails = get_recipients()

    if not all([sender_email, password, recipient_emails]):
        missing = []
        if not sender_email: missing.append("GMAIL_USER")
        if not password: missing.append("GMAIL_PASSWORD")
        if not recipient_emails: missing.append("EMAIL_RECIPIENTS or config/recipients.txt")
        debug_print(f"Missing email configuration: {', '.join(missing)}")
        return False

    if not ipo_data:
        debug_print("No qualifying IPOs found. Skipping email send.")
        return True

    # Create HTML email content
    html_content = create_email_html(ipo_data)
    if not html_content:
        debug_print("Failed to create email content")
        return False

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['Subject'] = f"🚀 IPO Alerts - {datetime.now().strftime('%d %B %Y')}"

    msg.attach(MIMEText(html_content, 'html'))

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
                msg_copy.attach(MIMEText(html_content, 'html'))
                server.send_message(msg_copy)
                debug_print(f"Email sent to BCC recipient")
        debug_print("All emails sent successfully!")
        return True
    except Exception as e:
        debug_print(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    # For testing purposes
    sample_data = [
        ["Test IPO", "O", "25.5 %", "13-Oct", "4.0/5"]
    ]
    print("Testing email HTML generation...")
    html = create_email_html(sample_data)
    if html:
        print("[SUCCESS] HTML email content generated successfully")
        print(f"Length: {len(html)} characters")
    else:
        print("[FAILED] Failed to generate HTML email content")