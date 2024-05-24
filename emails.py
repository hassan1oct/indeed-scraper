import pandas as pd
import requests

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
        print(f"Error fetching email for {linkedin_url}: {response.status_code}, {response.text}")
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
        print(f"Error fetching email for {name} at {domain}: {response.status_code}, {response.text}")
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
        print(f"Error fetching email for {role} at {domain}: {response.status_code}, {response.text}")
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
        print(f"Error verifying email {email}: {response.status_code}, {response.text}")
        return False

# Load the existing CSV
csv_file_path = '/home/karan/scraper/employee_details.csv'
df = pd.read_csv(csv_file_path)

# Add new columns for Email and Verified Email
df['Email'] = None
df['Verified Email'] = False

# Your Findymail API key
api_key = "VkxpS6yQDkO2HjzAK1eq6QdO0pLGpUWvr90PpWfo"

# Iterate through the DataFrame and fetch emails
for index, row in df.iterrows():
    linkedin_url = row['Person LinkedIn URL']
    name = row['Person Name']
    domain = row['Company URL'].split("//")[-1].split("/")[0]  # Extract domain from URL
    designation = row['Designation']

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
        df.at[index, 'Email'] = email
        df.at[index, 'Verified Email'] = verified
        print(f"Fetched and verified email for {row['Person Name']} ({row['Designation']} at {row['Company Name']}): {email} (Verified: {verified})")
    else:
        print(f"No email found for {row['Person Name']} ({row['Designation']} at {row['Company Name']})")

# Save the updated DataFrame to a new CSV file
output_csv_path = '/home/karan/scraper/final.csv'
df.to_csv(output_csv_path, index=False)

print(f"Updated company contacts saved to {output_csv_path}")
