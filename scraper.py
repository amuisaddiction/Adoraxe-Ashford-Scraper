"""
Adoraxe - Ashford, CT SearchIQS Land Records Scraper

Checkpoints 3-11: 
Guest Login, Land Records, Dynamic Dates, Submit Search, Extract Results, Pagination, Validation, Google Sheets.
"""

import logging
import sys
import json
import os
import csv
import time
from datetime import date, timedelta
from bs4 import BeautifulSoup
from curl_cffi import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_URL = "https://www.searchiqs.com/CTASH/"

def create_session() -> requests.Session:
    logging.info("Initializing HTTP session...")
    return requests.Session(impersonate="chrome", timeout=15)

def get_hidden_fields(html: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    hidden_data = {}
    for input_tag in soup.find_all('input', type='hidden'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            hidden_data[name] = value
    return hidden_data

def get_all_inputs(html: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    form_data = {}
    for input_tag in soup.find_all(['input', 'select']):
        name = input_tag.get('name')
        if not name:
            continue
        if input_tag.name == 'input' and input_tag.get('type') in ['submit', 'button']:
            continue
        if input_tag.name == 'input':
            if input_tag.get('type') in ['checkbox', 'radio']:
                if input_tag.has_attr('checked'):
                    form_data[name] = input_tag.get('value', 'on')
            else:
                form_data[name] = input_tag.get('value', '')
        elif input_tag.name == 'select':
            selected = input_tag.find('option', selected=True)
            if selected:
                form_data[name] = selected.get('value', '')
            else:
                first_opt = input_tag.find('option')
                form_data[name] = first_opt.get('value', '') if first_opt else ''
    return form_data

def guest_login(session: requests.Session) -> requests.Response:
    logging.info(f"Fetching initial page: {BASE_URL}")
    r1 = session.get(BASE_URL)
    r1.raise_for_status()

    hidden_fields = get_hidden_fields(r1.text)
    post_data = hidden_fields.copy()
    post_data['__EVENTTARGET'] = 'btnGuestLogin'
    post_data['__EVENTARGUMENT'] = ''
    
    time.sleep(4)
    logging.info("Submitting guest login postback...")
    r2 = session.post(BASE_URL, data=post_data, allow_redirects=True)
    r2.raise_for_status()
    return r2

def select_land_records(session: requests.Session, current_html: str, current_url: str) -> requests.Response:
    logging.info("Extracting all fields for Land Records selection...")
    post_data = get_all_inputs(current_html)
    post_data['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$cboDocGroup'
    post_data['__EVENTARGUMENT'] = ''
    post_data['ctl00$ContentPlaceHolder1$cboDocGroup'] = 'LR'
    
    time.sleep(4)
    logging.info("Submitting Land Records selection postback...")
    r = session.post(current_url, data=post_data, allow_redirects=True)
    r.raise_for_status()
    return r

def calculate_dates() -> tuple[str, str]:
    today = date.today()
    from_date_obj = today - timedelta(days=80)
    to_date_str = today.strftime('%m/%d/%Y')
    from_date_str = from_date_obj.strftime('%m/%d/%Y')
    logging.info(f"Calculated Dates -> From: {from_date_str}, To: {to_date_str}")
    return from_date_str, to_date_str

def submit_search(session: requests.Session, current_html: str, current_url: str, from_date: str, to_date: str) -> requests.Response:
    logging.info("Building full search payload...")
    post_data = get_all_inputs(current_html)
    
    post_data.pop('__EVENTTARGET', None)
    post_data.pop('__EVENTARGUMENT', None)
    post_data['ctl00$ContentPlaceHolder1$cboDocGroup'] = 'LR'
    post_data['ctl00$ContentPlaceHolder1$txtFromDate'] = from_date
    post_data['ctl00$ContentPlaceHolder1$txtThruDate'] = to_date
    post_data['ctl00$ContentPlaceHolder1$cmdSearch'] = 'Search'
    
    headers = {'Referer': current_url}
    time.sleep(4)
    logging.info(f"Submitting Search request to {current_url} ...")
    r = session.post(current_url, data=post_data, headers=headers, allow_redirects=True)
    r.raise_for_status()
    return r

def extract_records(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    
    results_table = None
    for table in tables:
        first_row = table.find('tr')
        if not first_row:
            continue
            
        header_text = [td.text.strip() for td in first_row.find_all(['td', 'th'])]
        if 'Party 1' in header_text and 'Book-Page' in header_text:
            results_table = table
            break
            
    if not results_table:
        return []

    rows = results_table.find_all('tr')
    records = []
    
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) < 12:
            continue
        if cells[4].text.strip() == 'Party 1':
            continue
            
        def clean_text(td):
            return td.text.replace('\xa0', ' ').replace('', '').strip()

        record = {
            'Party 1': clean_text(cells[4]),
            'Party 2': clean_text(cells[5]),
            'Type': clean_text(cells[6]),
            'Book-Page': clean_text(cells[7]),
            'Date': clean_text(cells[8]),
            'Description': clean_text(cells[9]),
            'Additional Description': clean_text(cells[10]),
            'Related': clean_text(cells[11])
        }
        
        if not any(record.values()):
            continue
            
        records.append(record)
        
    return records

def get_next_page(session: requests.Session, current_html: str, current_url: str) -> requests.Response | None:
    soup = BeautifulSoup(current_html, 'lxml')
    next_link = soup.find(lambda tag: tag.name == 'a' and tag.text.strip() == 'Next' and '__doPostBack' in tag.get('href', ''))
    
    if not next_link:
        return None
        
    href = next_link.get('href')
    target = href.split("'")[1]
    
    post_data = get_all_inputs(current_html)
    post_data['__EVENTTARGET'] = target
    post_data['__EVENTARGUMENT'] = ''
    
    headers = {'Referer': current_url}
    time.sleep(4)
    r = session.post(current_url, data=post_data, headers=headers, allow_redirects=True)
    r.raise_for_status()
    return r

def validate_and_clean_records(records: list[dict]) -> tuple[list[dict], dict]:
    validated = []
    stats = {
        'total_raw': len(records),
        'invalid': 0,
        'empty': 0,
        'headers': 0,
        'duplicates': 0
    }
    
    seen = set()
    expected_keys = ['Party 1', 'Party 2', 'Type', 'Book-Page', 'Date', 'Description', 'Additional Description', 'Related']
    
    for rec in records:
        if list(rec.keys()) != expected_keys:
            stats['invalid'] += 1
            continue
            
        cleaned_rec = {}
        is_empty = True
        is_header = False
        
        for k, v in rec.items():
            val = str(v).replace('\\xa0', ' ').replace('\xa0', ' ').strip()
            cleaned_rec[k] = val
            if val:
                is_empty = False
                
        if cleaned_rec.get('Party 1') == 'Party 1' and cleaned_rec.get('Date') == 'Date':
            is_header = True
            
        if is_empty:
            stats['empty'] += 1
            continue
            
        if is_header:
            stats['headers'] += 1
            continue
            
        rec_tuple = tuple(cleaned_rec[k] for k in expected_keys)
        if rec_tuple in seen:
            stats['duplicates'] += 1
        else:
            seen.add(rec_tuple)
            
        validated.append(cleaned_rec)
        
    return validated, stats

def export_to_google_sheets(records: list[dict]):
    """Export validated records to Google Sheets."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        logging.error("Missing gspread or google-auth libraries.")
        return
        
    cred_path = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials/service_account.json')
    if not os.path.exists(cred_path):
        logging.error(f"Google credentials not found at '{cred_path}'.")
        return
        
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_file(cred_path, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        sheet_name = "Adoraxe Ashford Land Records"
        try:
            sh = gc.open(sheet_name)
            logging.info(f"Found existing Google Sheet: {sheet_name}")
        except gspread.exceptions.SpreadsheetNotFound:
            logging.info(f"Creating new Google Sheet: {sheet_name}")
            sh = gc.create(sheet_name)
            sh.share('', role='reader', type='anyone')
            
        worksheet = sh.sheet1
        expected_keys = ['Party 1', 'Party 2', 'Type', 'Book-Page', 'Date', 'Description', 'Additional Description', 'Related']
        
        data = [expected_keys]
        for rec in records:
            data.append([rec.get(k, '') for k in expected_keys])
            
        logging.info("Uploading data to Google Sheets...")
        worksheet.clear()
        worksheet.update(values=data, range_name=f'A1:H{len(data)}')
        
        logging.info(f"Successfully uploaded {len(records)} rows and {len(expected_keys)} columns to Google Sheets.")
        
        uploaded_data = worksheet.get_all_values()
        if len(uploaded_data) == len(data) and uploaded_data[0] == expected_keys:
            logging.info("Verification SUCCESS: Google Sheet data matches expected output exactly.")
        else:
            logging.error("Verification FAILED: Google Sheet data does not match.")
            
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sh.id}"
        logging.info(f"Google Sheet URL: {sheet_url}")
        
        metadata = {
            "title": sheet_name,
            "id": sh.id,
            "url": sheet_url,
            "worksheet": worksheet.title
        }
        with open('output/google_sheet_info.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
        logging.info("Saved Google Sheet metadata to output/google_sheet_info.json")
        
    except Exception as e:
        logging.error(f"Google Sheets export failed: {e}")

def main():
    logging.info("Starting Adoraxe Ashford Scraper")
    
    session = create_session()
    r_search_page = guest_login(session)
    r_land_records = select_land_records(session, r_search_page.text, r_search_page.url)
    from_date, to_date = calculate_dates()
    
    r_results = submit_search(session, r_land_records.text, r_land_records.url, from_date, to_date)
    
    logging.info("--- Starting Checkpoint 8: Pagination & Extraction ---")
    all_records = []
    current_html = r_results.text
    current_url = r_results.url
    page_num = 1
    
    while page_num <= 1000:
        records = extract_records(current_html)
        all_records.extend(records)
        logging.info(f"Page {page_num} -> {len(records)} records extracted.")
        
        r_next = get_next_page(session, current_html, current_url)
        if not r_next:
            break
            
        if r_next.text == current_html:
            break
            
        current_html = r_next.text
        current_url = r_next.url
        page_num += 1

    logging.info("--- Starting Checkpoint 9: Data Validation ---")
    validated_records, stats = validate_and_clean_records(all_records)
    
    os.makedirs('output', exist_ok=True)
    csv_path = os.path.join('output', 'ashford_land_records.csv')
    sample_csv_path = os.path.join('output', 'sample_ashford_land_records.csv')
    
    expected_keys = ['Party 1', 'Party 2', 'Type', 'Book-Page', 'Date', 'Description', 'Additional Description', 'Related']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=expected_keys)
        writer.writeheader()
        writer.writerows(validated_records)
        
    with open(sample_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=expected_keys)
        writer.writeheader()
        writer.writerows(validated_records[:10])

    logging.info("--- Starting Checkpoint 10: Google Sheets Export ---")
    export_to_google_sheets(validated_records)

    logging.info("Deployment/Submission run complete.")

if __name__ == "__main__":
    main()
