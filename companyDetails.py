import time
import pandas as pd
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Initialize Chromedriver
driver_path = ChromeDriverManager().install()
service = ChromeService(driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode for faster execution
options.add_argument("--disable-gpu")  # Disable GPU for faster execution
options.add_argument("--no-sandbox")  # Bypass OS security model
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
driver = webdriver.Chrome(service=service, options=options)

# Load the filtered CSV
filtered_csv_path = '/home/karan/scraper/indeed_company.csv'
df = pd.read_csv(filtered_csv_path)

# Function to get the base URL
def get_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"

# Function to search for company websites on Google
def get_company_website(company_name):
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
        print(f"Error fetching website for {company_name}: {e}")
    return None

# Function to search for LinkedIn URLs on Google and copy the link address
def get_linkedin_url(company_name, location):
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
        print(f"Error fetching LinkedIn URL for {company_name}: {e}")
    return None

# List to store company details
company_details = []

# Iterate through the DataFrame and get the website and LinkedIn URLs
for index, row in df.iterrows():
    company_name = row['Company Name']
    location = row['Location']
    website_url = get_company_website(company_name)
    linkedin_url = get_linkedin_url(company_name, location)
    company_details.append({
        'Company Name': company_name,
        'Job Title': row['Job Title'],
        'Location': location,
        'Website URL': website_url,
        'LinkedIn URL': linkedin_url
    })
    time.sleep(1)  # Add a delay between iterations

# Convert to DataFrame and save to CSV
output_df = pd.DataFrame(company_details)
output_csv_path = '/home/karan/scraper/company_details.csv'
output_df.to_csv(output_csv_path, index=False)

print(f"Company details saved to {output_csv_path}")

# Close the browser
driver.quit()
