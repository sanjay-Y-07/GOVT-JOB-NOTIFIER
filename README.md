# Job Notification Aggregator (RRB and BHEL)

A Python pipeline that checks government recruitment pages every week, finds newly posted notifications, and emails me a PDF summary. It runs entirely on GitHub Actions, so nothing needs to be running on my own machine.

## Why it uses a proxy

My first version worked locally but failed once it ran on GitHub's servers. Some of these government sites block traffic from foreign data centers, and GitHub's runners fall into that category. To get around this, requests go through ScraperAPI, which routes them via Indian proxy servers. After that change, the pages loaded normally from the cloud.

## What it does

- Checks five pages: RRB Chennai, RRB overall, BHEL Trichy, BHEL Ranipet and BHEL overall.
- Parses each page with BeautifulSoup and picks out links containing keywords such as `cen`, `recruitment` and `syllabus`.
- Keeps a CSV file of every notification it has already seen, so each email contains only new postings and not repeats.
- Builds a PDF of the new listings with `fpdf2`.
- Sends the PDF as an email attachment over SMTP, with an HTML message body.

## How a run works

1. A GitHub Actions cron job starts the workflow once a week.
2. The script fetches each of the five pages through ScraperAPI.
3. Extracted links are compared against the saved CSV history.
4. New items are written to a PDF.
5. The email is sent using credentials stored as GitHub secrets, and the runner shuts down.

## Tech stack

- Python 3.10
- requests, BeautifulSoup4, pandas, fpdf2, smtplib
- GitHub Actions (Ubuntu runners)
- ScraperAPI for proxying and geo-unblocking

## Configuration

The ScraperAPI key and email credentials are stored as GitHub secrets and read as environment variables. None of them are committed to the repository.

## Known limitations

- Keyword matching can miss a notice with an unusual title.
- The proxy service has a usage limit on its plan, so it needs to be checked if the page count grows.