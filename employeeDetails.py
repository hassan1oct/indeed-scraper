import time
import pandas as pd
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
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=service, options=options)

# Function to get Google search results for LinkedIn profiles
def search_linkedin_profiles(company_name, role_keywords, role_name):
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
                    return name, link, role_name

        except Exception as e:
            print(f"Error fetching LinkedIn profiles for {company_name} - {role}: {e}")
    return None, None, None

# Load the company details CSV
csv_file_path = '/home/karan/scraper/company_details.csv'
company_df = pd.read_csv(csv_file_path)

# Define the roles you're looking for
roles = {
    "CTO": ["chief technology officer", "cto"],
    "Hiring Manager": ["hiring manager", "hr manager", "talent acquisition"],
    "Technical Recruiter": ["technical recruiter", "recruiter"]
}

# List to store company contacts
company_contacts = []

# Iterate through the entire DataFrame
for index, row in company_df.iterrows():
    company_name = row['Company Name']
    company_website = row['Website URL']
    company_linkedin_url = row['LinkedIn URL']
    job_title = row['Job Title']
    location = row['Location']
    collected_contacts = {'CTO': 0, 'Hiring Manager': 0, 'Technical Recruiter': 0, 'Recruiter': 0}

    for role, keywords in roles.items():
        while collected_contacts[role] < 2 if role == "Hiring Manager" else 1:
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
                print(f"Added {formatted_name} ({designation}) at {company_name}")
                break  # Move to next role if contact found

            # Add a delay between iterations to avoid too fast execution
            time.sleep(2)

# Convert to DataFrame and save to CSV
output_df = pd.DataFrame(company_contacts)
output_csv_path = '/home/karan/scraper/employee_details.csv'
output_df.to_csv(output_csv_path, index=False)

print(f"Company contacts saved to {output_csv_path}")

# Close the browser
driver.quit()
