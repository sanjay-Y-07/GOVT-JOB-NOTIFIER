import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
import os
import pandas as pd
import time

load_dotenv()  # reads .env and loads values into environment

TELEGRAM_TOKEN = os.getenv("8211287919:AAF6d2fLp5YxwI899nt60V-INjDHpHskacU")
TELEGRAM_CHAT_ID = os.getenv("6904252716")

# ---- Step 1: Scrape the RRB Chennai page ----

url = "https://rrb.indianrailways.gov.in/getdata?loc=chennai"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table", class_="cnp_list")

base_url = "https://rrb.indianrailways.gov.in"
rows = table.find_all("tr", class_="publicR")

data = []
for row in rows:
    cols = row.find_all("td")
    cen_number = cols[1].get_text(strip=True)
    title = cols[2].get_text(strip=True)
    description = cols[3].get_text(strip=True)
    pub_date = cols[4].get_text(strip=True)

    pdf_link = None
    options = cols[5].find_all("option")
    for opt in options:
        if opt.get("value"):
            pdf_link = urljoin(base_url, opt["value"])
            break

    data.append({
        "cen_number": cen_number,
        "title": title,
        "description": description,
        "publication_date": pub_date,
        "pdf_link": pdf_link
    })

# ---- Step 2: Compare against history and find new entries ----

csv_filename = "rrb_chennai_notifications.csv"

if os.path.exists(csv_filename):
    old_df = pd.read_csv(csv_filename)
    old_links = old_df['pdf_link'].dropna().tolist()
else:
    old_df = pd.DataFrame(columns=["cen_number", "title", "description", "publication_date", "pdf_link"])
    old_links = []

new_entries = [row for row in data if row['pdf_link'] and row['pdf_link'] not in old_links]
print(f"Found {len(new_entries)} new notification(s)")

# ---- Step 3: Append new entries to permanent history CSV ----

if new_entries:
    new_df = pd.DataFrame(new_entries)
    combined_df = pd.concat([old_df, new_df], ignore_index=True)
    combined_df.to_csv(csv_filename, index=False)
    print(f"Added {len(new_entries)} new row(s). Total history: {len(combined_df)} rows")
else:
    print("No new notifications — CSV unchanged")

# ---- Step 4: Send Telegram notifications for new entries ----

def send_telegram_message(text, retries=3):
    """Sends a text message to your Telegram chat via the bot API, with retry on failure."""
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(api_url, data=payload, timeout=15)
            if resp.status_code == 200:
                return True
            else:
                print(f"Telegram error (attempt {attempt}):", resp.status_code, resp.text)
        except requests.exceptions.RequestException as e:
            print(f"Telegram request failed (attempt {attempt}):", e)
        time.sleep(2)
    return False


if new_entries:
    for entry in new_entries:
        message = (
            f"🚨 <b>New RRB Notification</b>\n\n"
            f"<b>{entry['title']}</b>\n"
            f"{entry['description']}\n"
            f"📅 {entry['publication_date']}\n"
            f"🔗 {entry['pdf_link']}"
        )
        send_telegram_message(message)
    print(f"Sent {len(new_entries)} Telegram notification(s)")
else:
    print("No new notifications — nothing sent")