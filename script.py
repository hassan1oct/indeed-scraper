import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import subprocess
import threading
import os
import pandas as pd
from indeedScraper import run_indeed_scraper
from companyDetails import run_company_processing
from employeeDetails import run_employee_processing
from emails import run_email_processing, socketio  # Import socketio from emails.py

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, resources={r"/*": {"origins": "*"}})
socketio.init_app(app)  # Initialize socketio with the Flask app

def run_script(script_path, args=None):
    if args:
        return subprocess.Popen(["python3", script_path] + args)
    else:
        return subprocess.Popen(["python3", script_path])

def wait_for_file(file_path, timeout=600):
    start_time = time.time()
    while not os.path.exists(file_path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timeout waiting for file {file_path}")
        time.sleep(1)

def run_all_scripts(indeed_page):
    # Signal the other scripts to start
    with open("/home/karan/scraper/start_indeed_scraper.txt", "w") as f:
        f.write("start")
    
    # Start the indeed scraper
    run_script("indeedScraper.py", [indeed_page])

    # Wait for the indeed_company.csv file
    wait_for_file("/home/karan/scraper/indeed_company.csv")
    
    # Signal the next script
    with open("/home/karan/scraper/start_company_details.txt", "w") as f:
        f.write("start")

    # Start the company details script
    run_script("companyDetails.py")

    # Wait for the company_details.csv file
    wait_for_file("/home/karan/scraper/company_details.csv")
    
    # Signal the next script
    with open("/home/karan/scraper/start_employee_details.txt", "w") as f:
        f.write("start")

    # Start the employee details script
    run_script("employeeDetails.py")
    
    # Wait for the employee_details.csv file
    wait_for_file("/home/karan/scraper/employee_details.csv")
    
    # Run email processing
    run_email_processing()
    
    print("All scripts have been executed successfully.")

@app.route('/run', methods=['POST'])
def run():
    data = request.get_json()
    indeed_page = data.get('indeed_page')
    
    if not indeed_page:
        return jsonify({"error": "indeed_page is required"}), 400
    
    # Clear existing CSV files
    for csv_file in ["/home/karan/scraper/indeed_company.csv", "/home/karan/scraper/company_details.csv", "/home/karan/scraper/employee_details.csv"]:
        if os.path.exists(csv_file):
            os.remove(csv_file)
    
    # Start the scripts in a separate thread
    threading.Thread(target=run_all_scripts, args=(indeed_page,)).start()
    
    return jsonify({"status": "Script started"}), 202

@app.route('/resume', methods=['POST'])
def resume():
    # Check if indeed_company.csv exists
    if not os.path.exists("/home/karan/scraper/indeed_company.csv"):
        return jsonify({"error": "indeed_company.csv not found. Please enter the link."}), 400
    
    def resume_all_scripts():
        try:
            # Company Details
            company_details_path = "/home/karan/scraper/company_details.csv"
            if not os.path.exists(company_details_path):
                with open("/home/karan/scraper/start_company_details.txt", "w") as f:
                    f.write("start")
                run_script("companyDetails.py")
                wait_for_file(company_details_path)
            
            # Employee Details
            employee_details_path = "/home/karan/scraper/employee_details.csv"
            if not os.path.exists(employee_details_path):
                with open("/home/karan/scraper/start_employee_details.txt", "w") as f:
                    f.write("start")
                run_script("employeeDetails.py")
                wait_for_file(employee_details_path)
            
            # Email Processing
            run_email_processing()
            print("Resumed and completed all scripts successfully.")

            # Delete temporary files after processing
            files_to_delete = [
                "/home/karan/scraper/processed_rows.txt",
                "/home/karan/scraper/processed_email_rows.txt",
                "/home/karan/scraper/indeed_company.csv",
                "/home/karan/scraper/company_details.csv",
                "/home/karan/scraper/employee_details.csv"
            ]
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)

            print("Temporary files deleted.")
        except Exception as e:
            print(f"Error during resuming scripts: {e}")

    threading.Thread(target=resume_all_scripts).start()
    
    return jsonify({"status": "Resume process started"}), 202

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
