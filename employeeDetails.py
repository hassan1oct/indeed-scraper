import csv
import time
import pandas as pd
import os
import logging
import multiprocessing
from multiprocessing import Lock
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_driver():
    driver_path = ChromeDriverManager().install()
    service = ChromeService(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=service, options=options)

def search_linkedin_profiles(company_name, role_keywords, role_name):
    driver = create_driver()
    for role in role_keywords:
        search_query = f"{company_name} {role} LinkedIn"
        google_search_url = f"https://www.google.com/search?q={search_query}"
        driver.get(google_search_url)

        try:
            wait = WebDriverWait(driver, 10)
            results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href]')))

            for result in results:
                link = result.get_attribute('href')
                try:
                    name_element = result.find_element(By.XPATH, ".//h3")
                    name = name_element.text
                except:
                    continue

                if "linkedin.com/in/" in link:
                    driver.quit()
                    return name, link, role_name

        except Exception as e:
            logging.error(f"Error fetching LinkedIn profiles for {company_name} - {role}: {e}")
    
    driver.quit()
    return None, None, None

def process_company(row, lock):
    company_name = row['Company Name']
    company_website = row['Website URL']
    company_linkedin_url = row['LinkedIn URL']
    job_title = row['Job Title']
    location = row['Location']

    roles = {
        "CTO": ["chief technology officer", "cto"],
        "Hiring Manager": ["hiring manager", "hr manager", "talent acquisition"],
        "Technical Recruiter": ["technical recruiter", "recruiter"]
    }

    company_contacts = []
    collected_contacts = {'CTO': 0, 'Hiring Manager': 0, 'Technical Recruiter': 0}

    for role, keywords in roles.items():
        while collected_contacts[role] < (2 if role == "Hiring Manager" else 1):
            name, linkedin_url, designation = search_linkedin_profiles(company_name, keywords, role)
            if name and linkedin_url:
                formatted_name = name.split(" - ")[0]
                company_contacts.append({
                    'Company Name': company_name,
                    'Job Title': job_title,
                    'Location': location,
                    'Company URL': company_website,
                    'Company LinkedIn URL': company_linkedin_url,
                    'Person Name': formatted_name,
                    'Person LinkedIn URL': linkedin_url,
                    'Designation': designation
                })
                collected_contacts[role] += 1
                logging.info(f"Added {formatted_name} ({designation}) at {company_name}")
                break  # Move to next role if contact found

            # Add a delay between iterations to avoid too fast execution
            time.sleep(2)

    if company_contacts:
        # Convert to DataFrame and save to CSV
        output_csv_path = '/home/karan/scraper/employee_details.csv'
        with lock:
            file_exists = os.path.isfile(output_csv_path)
            with open(output_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=company_contacts[0].keys())
                if not file_exists:
                    writer.writeheader()
                for contact in company_contacts:
                    writer.writerow(contact)
        logging.info(f"Company contacts saved to {output_csv_path}")

def run_employee_processing():
    # Wait for the start signal
    while not os.path.exists("/home/karan/scraper/start_employee_details.txt"):
        time.sleep(1)

    Watcher().run()

class Watcher:
    DIRECTORY_TO_WATCH = "/home/karan/scraper/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            logging.error("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    def process(self, event):
        if event.event_type == 'modified' and 'company_details.csv' in event.src_path:
            # Process the new rows in the CSV
            logging.info(f"Detected change in {event.src_path}. Processing new entries.")
            try:
                df = pd.read_csv(event.src_path)
                lock = Lock()
                for index, row in df.iterrows():
                    if not is_row_processed(row):
                        process = multiprocessing.Process(target=process_company, args=(row, lock))
                        process.start()
                        mark_row_as_processed(row)
            except pd.errors.ParserError as e:
                logging.error(f"Error reading CSV file: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            self.process(event)

def is_row_processed(row):
    processed_file = '/home/karan/scraper/processed_rows.txt'
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as file:
            processed_ids = file.read().splitlines()
        return str(row['Company Name']) in processed_ids
    return False

def mark_row_as_processed(row):
    processed_file = '/home/karan/scraper/processed_rows.txt'
    with open(processed_file, 'a') as file:
        file.write(str(row['Company Name']) + '\n')

if __name__ == '__main__':
    run_employee_processing()
    print("Processing complete.")
    logging.info("Processing complete.")
