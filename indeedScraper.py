import sys
import time
import os
import pyautogui
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_indeed_scraper(indeed_page):
    # Wait for the start signal
    # Download Chromedriver
    driver_path = ChromeDriverManager().install()

    # Extension Name
    extension_path = 'OFAOKHIEDIPICHPAOBIBBNAHNKDOIIAH_1_2_0_0.crx'
    options = webdriver.ChromeOptions()
    options.add_extension(extension_path)

    # Driver Open
    s = ChromeService(driver_path)
    driver = webdriver.Chrome(service=s, options=options)

    # Open Indeed page
    driver.get(indeed_page)

    # Give some time for the page to load
    time.sleep(5)

    # Automate the click on the extension icon using pyautogui
    # Coordinates for the extension icon
    extension_icon_coordinates = (1005, 116)  # Replace with the actual coordinates you provided

    pyautogui.moveTo(extension_icon_coordinates[0], extension_icon_coordinates[1], duration=1)
    pyautogui.click()

    time.sleep(2)  # Wait for the extension popup to open

    # Coordinates for the Instant Data Scraper extension
    instant_data_scraper_coordinates = (844, 277)  # Replace with the actual coordinates you provided

    pyautogui.moveTo(instant_data_scraper_coordinates[0], instant_data_scraper_coordinates[1], duration=1)
    pyautogui.click()

    # Wait for 15 seconds before switching to the extension window
    time.sleep(10)

    # Switch to the extension window
    driver.switch_to.window(driver.window_handles[1])

    # Wait for the extension interface to load and locate elements by their XPath or CSS Selectors
    wait = WebDriverWait(driver, 300)

    # Set the minimum delay to 3 seconds
    min_delay_input = wait.until(EC.element_to_be_clickable((By.ID, 'crawlDelay')))
    min_delay_input.clear()
    min_delay_input.send_keys('3')

    locate_next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#nextButton')))
    locate_next_button.click()

    # Switch back to the Indeed window
    driver.switch_to.window(driver.window_handles[0])

    # Locate and click the next arrow at the bottom of the page
    next_arrow = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="pagination-page-next"]')))
    next_arrow.click()

    # Switch back to the extension window
    driver.switch_to.window(driver.window_handles[1])

    # Start crawling
    start_crawling = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#startScraping')))
    start_crawling.click()

    # Wait for a specific amount of time to simulate crawling (adjust the timeout as needed)
    time.sleep(60)  # wait for 60 seconds or adjust based on your requirements

    # Stop crawling
    stop_crawling = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#stopScraping')))
    stop_crawling.click()

    # Download the CSV file
    download_csv = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#csv')))
    download_csv.click()

    # Switch back to the Indeed tab
    driver.switch_to.window(driver.window_handles[0])

    # Close the browser after downloading
    time.sleep(15)  # wait to ensure the download completes
    driver.quit()

    # Move the downloaded CSV file to the desired location
    download_path = '/home/karan/Downloads'
    csv_file = os.path.join(download_path, 'indeed.csv')  # Adjust the file name as necessary
    destination_path = '/home/karan/scraper/indeed_company.csv'
    if os.path.exists(csv_file):
        os.rename(csv_file, destination_path)
    else:
        print("CSV file not found.")

    # Read the CSV file and filter the required columns
    try:
        df = pd.read_csv(destination_path)
        # Selecting the required columns based on the provided class names
        company_name_column = 'css-63koeb' if 'css-63koeb' in df.columns else 'css-92r8pb'

        # Selecting the required columns based on the provided class names
        filtered_df = df[['jcs-JobTitle', company_name_column, 'css-1p0sjhy']]
        # Renaming the columns for better readability
        filtered_df.columns = ['Job Title', 'Company Name', 'Location']
        # Remove rows with null values
        filtered_df = filtered_df.dropna()
        # Save the filtered data to a new CSV file
        filtered_df.to_csv(destination_path, index=False)
        print(f"Filtered data saved to {destination_path}")
    except Exception as e:
        print(f"An error occurred while processing the CSV file: {e}")

if __name__ == "__main__":
    indeed_page = sys.argv[1]
    print(indeed_page)
    run_indeed_scraper(indeed_page)
