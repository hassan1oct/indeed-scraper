import csv
import time
import pandas as pd
import requests
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import threading
from flask_socketio import SocketIO
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Function to get email from Findymail API using LinkedIn URL
def get_email_from_linkedin(linkedin_url, api_key):
    endpoint = "https://app.findymail.com/api/search/linkedin"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "linkedin_url": linkedin_url
    }
    response = requests.post(endpoint, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get("contact", {}).get("email")
    else:
        logging.error(f"Error fetching email for {linkedin_url}: {response.status_code}, {response.text}")
        return None

# Function to get email from Findymail API using name and domain
def get_email_from_name(name, domain, api_key):
    endpoint = "https://app.findymail.com/api/search/name"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "name": name,
        "domain": domain
    }
    response = requests.post(endpoint, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get("contact", {}).get("email")
    else:
        logging.error(f"Error fetching email for {name} at {domain}: {response.status_code}, {response.text}")
        return None

# Function to get email from Findymail API using domain and role
def get_email_from_domain(domain, role, api_key):
    endpoint = "https://app.findymail.com/api/search/domain"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "domain": domain,
        "roles": [role]
    }
    response = requests.post(endpoint, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        contacts = result.get("contacts")
        if contacts:
            return contacts[0].get("email")
        else:
            return None
    else:
        logging.error(f"Error fetching email for {role} at {domain}: {response.status_code}, {response.text}")
        return None

# Function to verify email using Findymail API
def verify_email(email, api_key):
    endpoint = "https://app.findymail.com/api/verify"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "email": email
    }
    response = requests.post(endpoint, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get("verified", False)
    else:
        logging.error(f"Error verifying email {email}: {response.status_code}, {response.text}")
        return False

def process_email_record(record, api_key):
    linkedin_url = record['Person LinkedIn URL']
    name = record['Person Name']
    domain = record['Company URL'].split("//")[-1].split("/")[0]  # Extract domain from URL
    designation = record['Designation']

    # Try fetching email using LinkedIn URL
    email = get_email_from_linkedin(linkedin_url, api_key)
    
    # If email not found, try fetching email using name and domain
    if not email:
        email = get_email_from_name(name, domain, api_key)
    
    # If email still not found, try fetching email using domain and role
    if not email:
        email = get_email_from_domain(domain, designation, api_key)
    
    if email:
        # Verify the email
        verified = verify_email(email, api_key)
        record['Email'] = email
        record['Verified Email'] = verified
        logging.info(f"Fetched and verified email for {record['Person Name']} ({record['Designation']} at {record['Company Name']}): {email} (Verified: {verified})")
    else:
        logging.info(f"No email found for {record['Person Name']} ({record['Designation']} at {record['Company Name']})")

    # Append the processed record to final.csv immediately
    output_csv_path = '/home/karan/scraper/final.csv'
    file_exists = os.path.isfile(output_csv_path)
    with open(output_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    # Emit the processed record to the frontend
    socketio.emit('new_record', record)
    print(record)
    return record

class EmailProcessor:
    def __init__(self, api_key, num_workers=4):
        self.api_key = api_key
        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    def process_queue(self):
        while True:
            record = self.queue.get()
            if record is None:
                break
            self.executor.submit(process_email_record, record, self.api_key)

    def add_record(self, record):
        self.queue.put(record)

    def stop(self):
        self.queue.put(None)
        self.executor.shutdown(wait=True)

def watch_file(processor, filepath):
    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path == filepath:
                logging.info(f"Detected change in {filepath}. Processing new entries.")
                try:
                    df = pd.read_csv(filepath)
                    for index, row in df.iterrows():
                        if not is_row_processed(row):
                            processor.add_record(row.to_dict())
                            mark_row_as_processed(row)
                except pd.errors.ParserError as e:
                    logging.error(f"Error reading CSV file: {e}")

    observer = Observer()
    event_handler = Handler()
    observer.schedule(event_handler, os.path.dirname(filepath), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def is_row_processed(row):
    processed_file = '/home/karan/scraper/processed_email_rows.txt'
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as file:
            processed_ids = file.read().splitlines()
        return str(row['Person LinkedIn URL']) in processed_ids
    return False

def mark_row_as_processed(row):
    processed_file = '/home/karan/scraper/processed_email_rows.txt'
    with open(processed_file, 'a') as file:
        file.write(str(row['Person LinkedIn URL']) + '\n')

def process_existing_records(processor, filepath):
    try:
        df = pd.read_csv(filepath)
        for index, row in df.iterrows():
            if not is_row_processed(row):
                processor.add_record(row.to_dict())
                mark_row_as_processed(row)
    except pd.errors.ParserError as e:
        logging.error(f"Error reading CSV file: {e}")

def run_email_processing():
    api_key = "VkxpS6yQDkO2HjzAK1eq6QdO0pLGpUWvr90PpWfo"
    email_processor = EmailProcessor(api_key)
    
    # Start a thread to process the queue
    processing_thread = threading.Thread(target=email_processor.process_queue)
    processing_thread.start()

    # Watch the file for changes
    csv_file_path = '/home/karan/scraper/employee_details.csv'
    logging.info(f"Watching file: {csv_file_path}")

    # Process existing records at startup
    logging.info("Processing existing records at startup.")
    process_existing_records(email_processor, csv_file_path)

    watch_file(email_processor, csv_file_path)

    # Wait for processing to complete and stop the processor
    processing_thread.join()
    email_processor.stop()

    logging.info("Processing complete.")
    print("Processing complete.")

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
