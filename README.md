# Adoraxe — Ashford, CT SearchIQS Land Records Scraper

Python-based scraper for the SearchIQS Ashford, CT Guest Search portal.

## Requirements

- Python 3.9+
- `requests`
- `BeautifulSoup`
- `lxml`
- Google Sheets API credentials for Sheet export
- US-based VPN when running the live scraper, as required by the challenge

## Challenge requirements

1. Open SearchIQS Ashford, CT.
2. Select **Search Records as Guest**.
3. Select **Land Records**.
4. From Date = today minus 80 days.
5. To Date = today.
6. Scrape all available result pages.
7. Extract:
   - Party 1
   - Party 2
   - Type
   - Book-Page
   - Date
   - Description
   - Additional Description
   - Related
8. Export results to a Google Sheet with read access.

## Rules

- Python only.
- HTTP requests + HTML parsing.
- No Selenium, Playwright, Puppeteer, or real-browser automation.
- Dates are calculated at runtime.
- Pagination is handled until the final page.

## Project structure

```text
Adoraxe-Ashford-Scraper/
├── scraper.py
├── requirements.txt
├── README.md
├── .gitignore
├── output/
├── tests/
└── credentials/
```

## Setup

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Current status

The project starts with a discovery-first scaffold. Before adding live SearchIQS selectors, inspect the actual HTML returned by the website so that IDs, postback targets, form fields, and result-table headers are not guessed.
