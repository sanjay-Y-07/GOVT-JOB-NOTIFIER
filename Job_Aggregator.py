import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time
import os
import textwrap
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from dotenv import load_dotenv

# Suppress SSL warnings for government websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load credentials from .env
load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_RECEIVERS = [e.strip() for e in os.getenv("EMAIL_RECEIVERS", "").split(",") if e.strip()]

# The target list with priority ranking
TARGETS = [
    {"name": "RRB Chennai", "url": "https://www.rrbchennai.gov.in/", "priority": 1},
    {"name": "BHEL Trichy", "url": "https://trichy.bhel.com/", "priority": 2},
    {"name": "BHEL Ranipet", "url": "https://bap.bhel.com/", "priority": 3},
    {"name": "Overall RRB", "url": "https://www.rrbapply.gov.in/", "priority": 4},
    {"name": "Overall BHEL", "url": "https://careers.bhel.in/", "priority": 5}
]

# ---- 1. SCRAPER LOGIC ----
def smart_scrape(source):
    print(f"Scanning {source['name']}...")
    data = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(source['url'], headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        
        keywords = ["cen", ".pdf", "notice", "recruitment", "advertisement", "career", "job", "syllabus", "results"]
        
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            
            if any(k in text.lower() or k in href.lower() for k in keywords) and len(text) > 4:
                full_link = urljoin(source['url'], href)
                data.append({
                    "priority": source['priority'],
                    "source": source['name'],
                    "title": text[:80] + "..." if len(text) > 80 else text,
                    "date_found": time.strftime("%Y-%m-%d"),
                    "link": full_link
                })
    except Exception as e:
        print(f"Failed to scrape {source['name']}: {e}")
        
    return data[:3] # Keep top 3 per site

def gather_data():
    all_jobs = []
    for target in TARGETS:
        all_jobs.extend(smart_scrape(target))
        time.sleep(2)
        
    if not all_jobs:
        return pd.DataFrame()
        
    all_jobs = sorted(all_jobs, key=lambda x: x['priority'])
    df = pd.DataFrame(all_jobs)
    
    csv_file = "all_job_notifications.csv"
    if os.path.exists(csv_file):
        old_df = pd.read_csv(csv_file)
        old_links = old_df['link'].tolist()
        new_jobs = df[~df['link'].isin(old_links)]
        
        if not new_jobs.empty:
            pd.concat([old_df, new_jobs], ignore_index=True).to_csv(csv_file, index=False)
    else:
        df.to_csv(csv_file, index=False)
        
    return df

# ---- 2. PDF GENERATION LOGIC ----
class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Weekly Job Notifications Report", border=False, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, "Priority: RRB Chennai > BHEL Trichy > BHEL Ranipet > Central", border=False, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

def write_safe_text(pdf, text, max_chars=80):
    text = str(text).replace('\n', ' ').replace('\r', ' ').strip()
    text = text.encode('latin-1', 'ignore').decode('latin-1')
    lines = textwrap.wrap(text, width=max_chars, break_long_words=True)
    for line in lines:
        pdf.cell(0, 6, text=line, new_x="LMARGIN", new_y="NEXT")

def generate_pdf(df, output_pdf):
    if df.empty:
        return False

    pdf = PDF()
    pdf.add_page()
    
    for index, row in df.iterrows():
        try:
            pdf.set_font("helvetica", "B", 12)
            write_safe_text(pdf, f"[{row.get('source', 'Unknown')}] {row.get('title', 'No Title')}")
            
            pdf.set_font("helvetica", size=10)
            write_safe_text(pdf, f"Found on: {str(row.get('date_found', 'N/A'))[:50]}")
            
            pdf.set_text_color(0, 0, 255)
            write_safe_text(pdf, f"Link: {row.get('link', 'N/A')}")
            pdf.set_text_color(0, 0, 0) 
            
            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        except Exception:
            continue

    pdf.output(output_pdf)
    return True

# ---- 3. PROFESSIONAL HTML EMAIL LOGIC ----
def send_professional_email(pdf_filename, total_jobs):
    if not (EMAIL_SENDER and EMAIL_APP_PASSWORD and EMAIL_RECEIVERS):
        print("Email settings missing in .env. Skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Weekly Job Opportunities Report: RRB & BHEL Updates"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_SENDER 

    # Professional HTML Email Body tailored for Roshan
    html_content = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto;">
        <h2 style="color: #00466a; border-bottom: 2px solid #00466a; padding-bottom: 10px;">Weekly Job Opportunities Report</h2>
        <p>Dear Roshan,</p>
        <p>Your automated job aggregator has successfully scanned the official government portals for the latest recruitment updates. We found <strong>{total_jobs}</strong> priority notices this week.</p>
        <p><strong>Monitored Portals:</strong></p>
        <ul>
          <li>RRB Chennai</li>
          <li>BHEL Trichy</li>
          <li>BHEL Ranipet</li>
          <li>RRB Central</li>
          <li>BHEL Central</li>
        </ul>
        <p>Please find the detailed report attached as a PDF. The document is sorted by your priority locations and contains direct links to the official notices.</p>
        <br>
        <p>Best regards,<br>
        <strong>Automated Job Aggregation Engine</strong></p>
      </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')

    with open(pdf_filename, 'rb') as f:
        pdf_data = f.read()
        
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=pdf_filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.send_message(msg, to_addrs=EMAIL_RECEIVERS)
        print("Professional email sent successfully with PDF attached!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# ---- 4. MAIN EXECUTION ----
if __name__ == "__main__":
    print("Starting Job Aggregation Engine...")
    jobs_df = gather_data()
    
    if not jobs_df.empty:
        pdf_name = "Weekly_Job_Report.pdf"
        if generate_pdf(jobs_df, pdf_name):
            send_professional_email(pdf_name, len(jobs_df))
    else:
        print("No data available to generate report.")