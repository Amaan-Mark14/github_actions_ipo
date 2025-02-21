# IPO GMP Notifier

This project is an automated system that scrapes IPO (Initial Public Offering) data from the **InvestorGain** website, filters IPOs based on their **GMP (Grey Market Premium)** and **rating**, and sends email alerts to subscribers. The system is designed to help investors identify potentially lucrative IPOs by focusing on those with high GMP and strong ratings.

---

## What is GMP?

**GMP (Grey Market Premium)** is the premium at which IPO shares are traded in the grey market before they are officially listed on the stock exchange. It is a key indicator of market sentiment and demand for the IPO. A high GMP suggests strong investor interest, which often correlates with positive listing gains. While GMP is not a guaranteed predictor of performance, it is a useful first indicator for identifying IPOs worth investigating further.

---

## About InvestorGain

The project scrapes data from [InvestorGain](https://www.investorgain.com/report/live-ipo-gmp/331/), a website that provides real-time updates on IPO GMP and other related metrics. InvestorGain uses a **fire rating system** to evaluate IPOs:

![website_sample](./images/website_info.png)


- **🔥🔥🔥🔥 (4/5 stars)**: Indicates a GMP of **25% or higher**. These IPOs are considered strong candidates for further investigation.
- **🔥🔥🔥🔥🔥 (5/5 stars)**: Indicates an even higher GMP and demand.

The notifier focuses on IPOs with ratings of **4/5 or 5/5**, ensuring that only high-potential IPOs are flagged for attention.

---

## About the Script

The script is built using **Python** and **Selenium** for web scraping. It automates the process of:

1. **Scraping IPO Data**: The script navigates to the InvestorGain website, extracts IPO details (name, status, estimated listing gains, open/close dates, and rating), and filters the data based on:
   - **Close Date**: Only IPOs closing within the next 3 days are considered.
   - **Rating**: Only IPOs with a rating of 4/5 or 5/5 are selected.

2. **Sending Email Alerts**: The script sends an HTML-formatted email to subscribers with details of the qualifying IPOs. The email includes:
   - IPO name
   - Status (e.g., "Open", "Closed")
   - Estimated listing gains
   - Open and close dates
   - Rating

![email_body](./images/email_body.png)


3. **Encryption**: The script uses **Fernet encryption** to securely store and retrieve email recipient details.

---

## Key Features

- **Selenium Web Scraping**: The script uses Selenium to scrape the IPO table from the InvestorGain website. It handles dynamic content and ensures the table is fully loaded before extraction.
- **Email Notifications**: The script sends personalized email alerts to subscribers using **SMTP** and **Gmail**. The email is formatted with HTML for a clean and professional look.
- **Filtering Logic**: The script filters IPOs based on close date and rating, ensuring only relevant IPOs are flagged.
- **Encryption**: Recipient email addresses are stored in an encrypted JSON file for security.
- **Mobile Friendly** : The email body uses a card-based layout for better compatibility on mobile devices.

---

## Setup Instructions

1. **Install Dependencies**:
   - Install Python 3.x.
   - Install required packages: `pip install -r requirements.txt`.

2. **Configure Environment Variables**:
   - Set `GMAIL_USER` and `GMAIL_APP_PASSWORD` for email functionality.
   - Set `CONFIG_ENCRYPTION_KEY` for decrypting recipient data.

3. **Run the Script**:
   - Execute the script: `python ipo_gmp_notifier.py`.

4. **Automate with GitHub Actions**:
   - Schedule the script to run daily using GitHub Actions.

---

## License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it as needed.
If you find this project useful, consider giving it a star ⭐ on GitHub!