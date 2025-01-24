import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Environment variables with defaults
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Handle RECIPIENTS with validation
recipients = os.getenv("RECIPIENTS", "")
RECIPIENTS = [email.strip() for email in recipients.split(",") if email.strip()]

def debug_print(message):
    """Helper function for debug output"""
    print(f"[DEBUG] {message}")

def validate_config():
    """Validate required configuration"""
    errors = []
    if not GMAIL_USER:
        errors.append("GMAIL_USER is not set")
    if not GMAIL_PASSWORD:
        errors.append("GMAIL_PASSWORD is not set")
    if not RECIPIENTS:
        errors.append("RECIPIENTS is not set or invalid")
    
    if errors:
        raise EnvironmentError("Email configuration error: " + ", ".join(errors))

def send_email(subject, body, html=False):
    try:
        # Validate configuration before proceeding
        validate_config()

        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER  # Send to yourself (or a dummy address)
        msg["Subject"] = subject

        # Add BCC recipients
        msg["Bcc"] = ", ".join(RECIPIENTS)

        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, [GMAIL_USER] + RECIPIENTS, msg.as_string())

        debug_print("Email sent successfully with BCC!")
        return True

    except Exception as e:
        debug_print(f"Error sending email: {e}")
        return False