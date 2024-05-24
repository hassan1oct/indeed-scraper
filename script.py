import subprocess
import time
import os

def run_script(script_path):
    return subprocess.Popen(["python3", script_path])

def wait_for_file(file_path, timeout=600):
    start_time = time.time()
    while not os.path.exists(file_path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timeout waiting for file {file_path}")
        time.sleep(1)

def main():
    # Define paths for the scripts and the CSV files they generate
    script_paths = [
        "indeedScraper.py",
        "companyDetails.py",
        "employeeDetails.py",
        "emails.py"
    ]

    csv_files = [
        "/home/karan/scraper/indeed_company.csv",
        "/home/karan/scraper/company_details.csv",
        "/home/karan/scraper/employee_details.csv",
        "/home/karan/scraper/final.csv"
    ]

    # Ensure the previous output file is not left over
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            os.remove(csv_file)

    # Run scripts sequentially, waiting for each required CSV to be generated
    for i, script_path in enumerate(script_paths):
        process = run_script(script_path)
        wait_for_file(csv_files[i])
        process.wait()

    print("All scripts have been executed successfully.")

if __name__ == "__main__":
    main()
