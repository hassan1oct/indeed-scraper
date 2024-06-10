import time
import pandas as pd
import logging
import os
import csv
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from multiprocessing import Pool

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

def get_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"

def get_company_website(driver, company_name):
    search_query = f"{company_name} official site"
    google_search_url = f"https://www.google.com/search?q={search_query}"
    driver.get(google_search_url)

    try:
        wait = WebDriverWait(driver, 5)
        results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href]')))
        
        candidate_links = []
        for result in results:
            link = result.get_attribute('href')
            try:
                parent = result.find_element(By.XPATH, '..')
                sponsored = parent.find_elements(By.XPATH, ".//*[contains(text(), 'Sponsored')]")
                if sponsored:
                    continue
            except:
                pass
            if ("google.com" not in link and "linkedin.com" not in link and 
                "adurl" not in link and "ads" not in link and 
                "youtube.com" not in link):
                candidate_links.append(link)
        
        for link in candidate_links:
            if ".com" in link:
                return get_base_url(link)
        
        if candidate_links:
            return get_base_url(candidate_links[0])

    except Exception as e:
        logging.error(f"Error fetching website for {company_name}: {e}")
    return None

def get_linkedin_url(driver, company_name, location):
    if "remote" in location.lower() or "hybrid" in location.lower():
        search_query = f"{company_name} LinkedIn"
    else:
        search_query = f"{company_name} {location} LinkedIn"
    
    google_search_url = f"https://www.google.com/search?q={search_query}"
    driver.get(google_search_url)

    try:
        wait = WebDriverWait(driver, 10)
        results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="linkedin.com/company"]')))
        
        for result in results:
            link = result.get_attribute('href')
            if "adurl" not in link and "jobs" not in link:
                return link
        
    except Exception as e:
        logging.error(f"Error fetching LinkedIn URL for {company_name}: {e}")
    return None

def process_company(company_data):
    driver = create_driver()
    company_name = company_data['Company Name']
    job_title = company_data['Job Title']
    location = company_data['Location']

    website_url = get_company_website(driver, company_name)
    linkedin_url = get_linkedin_url(driver, company_name, location)
    result = {
        'Company Name': company_name,
        'Job Title': job_title,
        'Location': location,
        'Website URL': website_url,
        'LinkedIn URL': linkedin_url
    }
    logging.info(f"Processed company: {company_name}, Website URL: {website_url}, LinkedIn URL: {linkedin_url}")

    # Update the CSV file
    csv_file_path = 'company_details.csv'
    file_exists = os.path.isfile(csv_file_path)
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=result.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)
    
    driver.quit()

def get_already_processed_companies():
    if os.path.exists('company_details.csv'):
        df = pd.read_csv('company_details.csv')
        return set(df['Company Name'].tolist())
    return set()

def run_company_processing():
    # Wait for the start signal
    while not os.path.exists("/home/karan/scraper/start_company_details.txt"):
        time.sleep(1)

    filtered_csv_path = '/home/karan/scraper/indeed_company.csv'
    df = pd.read_csv(filtered_csv_path)

    # Get already processed companies
    processed_companies = get_already_processed_companies()

    # Log the number of processed companies
    logging.info(f"Number of already processed companies: {len(processed_companies)}")

    # Filter out the companies that have already been processed
    companies_to_process = df[~df['Company Name'].isin(processed_companies)]

    # Log the number of companies to be processed
    logging.info(f"Number of companies to process: {len(companies_to_process)}")

    # Create a pool of worker processes
    pool = Pool(processes=4)  # Adjust the number of processes as needed

    # Iterate through the DataFrame and process each company using multiprocessing
    pool.map(process_company, [row for _, row in companies_to_process.iterrows()])

    # Close the pool and wait for all processes to finish
    pool.close()
    pool.join()

    logging.info("All companies have been processed.")
    print("Processing complete.")

if __name__ == "__main__":
    run_company_processing()
