# RRB Chennai Notification Bot

A Python bot that scrapes the RRB Chennai notifications page and sends new notices to Telegram.

## How it works
1. Scrapes the latest notifications from the RRB website
2. Compares them with a saved CSV history
3. Sends a Telegram alert for each new notification
4. Runs automatically using Windows Task Scheduler

## Tech used
Python, requests, BeautifulSoup, pandas, python-dotenv, Telegram Bot API, Git

## Setup
1. Install the libraries: `pip install requests beautifulsoup4 pandas python-dotenv`
2. Create a `.env` file with:
