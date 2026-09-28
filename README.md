# Adoraxe Ashford Land Records Scraper

## Project Objective
This project is an automated Python web scraper designed to extract land records from the SearchIQS portal for Ashford, CT. It was built as an individual hackathon submission.

**Target Website:** `https://www.searchiqs.com/CTASH/`

## Technologies Used
- **Python 3.x**
- **curl_cffi**: Used to establish an HTTP session with browser-like TLS characteristics when required by the target server.
- **BeautifulSoup4 / lxml**: Used for parsing the live HTML structure.
- **gspread / google-auth**: Used to authenticate and export the final validated data to Google Sheets.

**Restrictions Respected:**
- No Selenium, Playwright, Puppeteer, or any real-browser automation used.
- Pure HTTP requests and HTML parsing.

## How the Scraper Works

1. **Guest Login Flow:**
   The scraper initializes a `curl_cffi` session to fetch the target URL. It dynamically extracts all ASP.NET hidden fields (like `__VIEWSTATE` and `__EVENTVALIDATION`) and submits a POST request mimicking the "Search Records as Guest" button click.

2. **Land Records Selection:**
   It parses the new page, sets the Document Group (`ctl00$ContentPlaceHolder1$cboDocGroup`) to `LR` (Land Records), and simulates the JavaScript `onchange` postback.

3. **Dynamic Date Logic:**
   The script dynamically calculates the date window at runtime using Python's `datetime` module:
   - **From Date:** `today - 80 days`
   - **To Date:** `today`

4. **Search Submission:**
   The final search payload is built dynamically using the current page's hidden inputs, plus the calculated dates, and submitted via POST.

5. **Pagination Handling:**
   The script robustly finds the `Next` button, extracts its `__doPostBack` argument, and submits a POST request to advance the page. It repeats this process automatically until the `Next` link disappears or becomes disabled, preventing infinite loops.

6. **Data Extraction & Validation:**
   The scraper identifies the correct results grid by verifying header names (e.g., "Party 1"). It extracts exactly the 8 required fields:
   `Party 1`, `Party 2`, `Type`, `Book-Page`, `Date`, `Description`, `Additional Description`, `Related`.
   
   The data is then validated:
   - Whitespace and non-breaking spaces are safely stripped.
   - Accidental header rows and empty rows are dropped.

7. **Output (CSV & Google Sheets):**
   - The validated dataset is exported to `output/ashford_land_records.csv` and `output/sample_ashford_land_records.csv`.
   - The scraper authentically connects to Google Cloud and uploads the final dataset to a Google Sheet, configuring it for public read access. It verifies the upload by reading the data back into Python.

## Google Sheet Output
The final uploaded and verified data can be viewed here:
**[Adoraxe Ashford Land Records (Google Sheet)](https://docs.google.com/spreadsheets/d/1ulFAXNZdSpluKjEarBHQhhtxCTNaQ5lu2lVM2aClmDw)**

---

## Installation & Setup

1. **Install Requirements:**
   Run the following command to install all necessary Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Credentials Setup:**
   The script requires a Google Service Account to interact with Google Sheets.
   - Create a `credentials` folder in the project root.
   - Place your Service Account JSON key inside it and name it exactly `service_account.json`.
   - **Security Note:** The `credentials/` folder is explicitly ignored in `.gitignore`. **NEVER commit your service account JSON key to GitHub.** The scraper is designed to look for it locally or via the `GOOGLE_CREDENTIALS_FILE` environment variable.

## How to Run
Once dependencies are installed and the credential file is in place, run:
```bash
python scraper.py
```

### Expected Output Structure
The script will output extensive logging to the terminal, detailing:
- The dynamic dates calculated.
- The HTTP status of the guest login and search submission.
- The number of records extracted per page.
- Validation statistics (e.g., duplicates, invalid records).
- The final Google Sheet verification and URL.

The final CSVs are deposited in the `output/` folder.
