import csv
import time
import pandas as pd
import os
import logging
import tldextract
import smtplib
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import threading
from flask_socketio import SocketIO
from flask import Flask
from random import randint
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load the pre-trained model
model = joblib.load('email_model_advanced.pkl')

# Function to generate email patterns
def generate_email_patterns(name, domain):
    name_parts = name.lower().split()
    if len(name_parts) < 2:
        logging.error(f"Name {name} does not have enough parts to generate patterns.")
        return []
    patterns = [
        f"{name_parts[0][0]}{name_parts[1]}@{domain}",           # jdoe@domain.com
        f"{name_parts[0]}@{domain}",                             # joe@domain.com
        f"{name_parts[1]}@{domain}",                             # doe@domain.com
        f"{name_parts[0]}.{name_parts[1]}@{domain}",             # joe.doe@domain.com
        f"{name_parts[0]}_{name_parts[1]}@{domain}",             # joe_doe@domain.com
        f"{name_parts[0]}{name_parts[1]}@{domain}",              # joedoe@domain.com
        f"{name_parts[0][0]}.{name_parts[1]}@{domain}",          # j.doe@domain.com
        f"{name_parts[0][0]}_{name_parts[1]}@{domain}",          # j_doe@domain.com
        f"{name_parts[0][0]}{name_parts[1][0]}@{domain}",        # jd@domain.com
        f"{name_parts[0]}.{name_parts[0][0]}{name_parts[1]}@{domain}",  # joe.j.doe@domain.com
        f"{name_parts[0][0]}{name_parts[0]}.{name_parts[1]}@{domain}",  # j.joe.doe@domain.com
        f"{name_parts[1]}.{name_parts[0]}@{domain}",             # doe.joe@domain.com
        f"{name_parts[1]}_{name_parts[0]}@{domain}",             # doe_joe@domain.com
        f"{name_parts[1]}{name_parts[0]}@{domain}",              # doejoe@domain.com
        f"{name_parts[0][0]}{name_parts[1][0]}@mail.{domain}",   # jd@mail.domain.com
    ]
    return patterns

# Function to get MX records for a domain
def get_mx_records(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange) for r in records]
    except Exception as e:
        logging.error(f"Error fetching MX records for domain {domain}: {str(e)}")
        return []

# Function to verify email using SMTP with persistent connections and retries
def verify_email(email, mx_records, server_pool):
    retries = 3
    backoff_time = 5  # in seconds

    for mx in mx_records:
        for attempt in range(retries):
            if mx not in server_pool:
                try:
                    server = smtplib.SMTP(mx)
                    server.set_debuglevel(0)
                    server.connect(mx)
                    server.helo('example.com')
                    server_pool[mx] = server
                except Exception as e:
                    logging.error(f"Exception during SMTP connection setup: {str(e)}")
                    if attempt < retries - 1:
                        time.sleep(backoff_time * (2 ** attempt))
                    continue

            server = server_pool[mx]
            try:
                server.mail('test@example.com')
                code, message = server.rcpt(email)
                if code == 250:
                    return True
            except smtplib.SMTPServerDisconnected as e:
                logging.error(f"SMTP server disconnected during verification: {str(e)}")
                server_pool.pop(mx, None)  # Remove the server from the pool
            except Exception as e:
                logging.error(f"Exception during SMTP verification: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(backoff_time * (2 ** attempt))
                continue
    return False

# Function to find email with concurrency
def find_email(name, domain):
    # Extract the registered domain
    domain = tldextract.extract(domain).registered_domain
    
    # Generate email patterns
    email_patterns = generate_email_patterns(name, domain)
    
    # Get MX records
    mx_records = get_mx_records(domain)
    
    if not mx_records:
        logging.error(f"No MX records found for domain: {domain}")
        return None
    
    server_pool = {}
    found_email = None
    
    # Use ProcessPoolExecutor for multiprocessing
    with ProcessPoolExecutor(max_workers=8) as executor:
        future_to_email = {executor.submit(verify_email, email, mx_records, server_pool): email for email in email_patterns}
        for future in as_completed(future_to_email):
            email = future_to_email[future]
            try:
                is_valid = future.result()
                if is_valid:
                    found_email = email
                    break
            except Exception as e:
                logging.error(f"Error verifying email {email}: {str(e)}")
    
    # Close all SMTP connections
    for server in server_pool.values():
        server.quit()
    
    if found_email:
        logging.info(f"Found valid email: {found_email}")
        return {"email": found_email, "verified": True}
    else:
        logging.info(f"No valid email found for {name} at {domain}")
        return {"email": None, "verified": False}

def process_email_record(record):
    name = record['Person Name']
    domain = record['Company URL'].split("//")[-1].split("/")[0]  # Extract domain from URL
    
    # Find email using the new logic
    result = find_email(name, domain)
    
    if result["email"]:
        email = result["email"]
        verified = result["verified"]
        record['Email'] = email
        record['Verified Email'] = verified
        logging.info(f"Fetched and verified email for {record['Person Name']} at {domain}: {email} (Verified: {verified})")
        
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

        # Update emails.csv with new data
        update_emails_csv(record)

    else:
        logging.info(f"No email found for {record['Person Name']} at {domain}")

    return record

def update_emails_csv(record):
    # Update emails.csv with the new verified data
    emails_csv_path = '/home/karan/scraper/emails.csv'
    new_record = {
        'Person Name': record['Person Name'],
        'Company URL': record['Company URL'],
        'Email': record['Email']
    }
    file_exists = os.path.isfile(emails_csv_path)
    with open(emails_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=new_record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_record)

class EmailProcessor:
    def __init__(self, num_workers=10):
        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    def process_queue(self):
        while True:
            record = self.queue.get()
            if record is None:
                break
            self.executor.submit(process_email_record, record)

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
            time.sleep(randint(1, 5))  # Adding some randomness to reduce simultaneous access
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
    email_processor = EmailProcessor()
    
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
    socketio.run(app, debug=True, port=5000)
