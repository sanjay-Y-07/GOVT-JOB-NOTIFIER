# Job Notification Aggregator (RRB and BHEL)

A Python script that checks several government recruitment pages, finds new notifications, and emails me a PDF summary every Sunday morning. I built it to save my brother from checking these sites by hand, and it now runs on its own through GitHub Actions.

## What it does

- Scrapes five pages: RRB Chennai, RRB Central, and the BHEL Trichy, Ranipet and Central career pages.
- Looks for links containing keywords like `CEN`, `Notice` and `.pdf` anywhere on the page, instead of relying on a fixed table layout. These sites change their markup often, and this approach has held up better than selecting specific table rows.
- Cleans messy text and very long URLs with pandas and `textwrap`, so the PDF generator doesn't break on them.
- Compares what it finds against `all_job_notifications.csv` and keeps only listings I haven't seen before.
- Sorts new listings by location priority and builds a PDF report with `fpdf2`.
- Emails the report as an attachment with an HTML body.

## How a run works

1. A GitHub Actions cron job starts the workflow every Sunday at 9:00 AM IST.
2. The script fetches each of the five pages. SSL certificate mismatches on some of these sites are ignored so the fetch doesn't fail.
3. New links are identified by checking against the saved CSV history.
4. The new listings are written to a PDF, ordered by priority.
5. The email is sent using credentials stored as GitHub secrets, and the job shuts down.

Nothing runs on my own machine.

## Tech stack

- Python 3.10
- requests, BeautifulSoup4, pandas
- fpdf2, textwrap
- GitHub Actions, smtplib, email.message

## Running it locally

1. Clone the repository.
2. Install the dependencies:

```bash
   pip install requests beautifulsoup4 pandas fpdf2 python-dotenv
```

3. Create a `.env` file in the project root:

```text
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_APP_PASSWORD=your_16_digit_app_password
   EMAIL_RECEIVERS=target_email@gmail.com
```

   Use a Gmail app password, not your normal account password.

4. Run the main script.

## Known limitations

- The scraper depends on keyword matching, so a notice with an unusual title could be missed.
- Ignoring SSL verification is a workaround for these specific sites and should not be copied to other projects.