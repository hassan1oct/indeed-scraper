import pandas as pd
import re
import logging
import smtplib
import dns.resolver
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the combined CSV
data = pd.read_csv('emails.csv')

# Generate email patterns
def generate_email_patterns(name, domain):
    name_parts = name.lower().split()
    first = name_parts[0]
    last = name_parts[1] if len(name_parts) > 1 else ''
    patterns = [
        f"{first}@{domain}",
        f"{first}{last}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first[0]}.{last}@{domain}" if last else '',
        f"{first[0]}_{last}@{domain}" if last else '',
        f"{first}.{last[0]}@{domain}" if last else '',
        f"{first[0]}{last[0]}@{domain}" if last else '',
        f"{last}.{first}@{domain}" if last else '',
        f"{last}_{first}@{domain}" if last else '',
        f"{last}{first}@{domain}" if last else '',
        f"{first}{last[0]}@{domain}" if last else '',
        f"{first}-{last}@{domain}",
        f"{first}.{last[0]}@{domain}",
        f"{first[0]}-{last}@{domain}" if last else '',
        f"{first}_{last[0]}@{domain}" if last else '',
        f"{first}-{last[0]}@{domain}" if last else '',
        f"{first}.{last}@mail.{domain}",
        f"{first}.{last}@{domain}.com",
        f"{first}{last}@mail.{domain}",
        f"{first}@mail.{domain}",
        f"{first}_{last}@mail.{domain}",
        f"{first}.{last[0]}@mail.{domain}",
        f"{first[0]}_{last}@mail.{domain}" if last else '',
        f"{first[0]}{last[0]}@mail.{domain}" if last else '',
    ]
    return [p for p in patterns if p]

# Extract features and labels for training
def extract_features_and_labels(df):
    X, y = [], []
    for index, row in df.iterrows():
        domain = re.sub(r'^https?://', '', row['Company URL']).split('/')[0]
        patterns = generate_email_patterns(row['Person Name'], domain)
        for pattern in patterns:
            X.append(pattern)
            y.append(1 if pattern == row['Email'] else 0)
    return X, y

X, y = extract_features_and_labels(data)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the model pipeline with GradientBoostingClassifier
pipeline = Pipeline([
    ('vectorizer', CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))),
    ('classifier', GradientBoostingClassifier(random_state=42))
])

# Hyperparameter tuning
param_grid = {
    'classifier__n_estimators': [100, 200],
    'classifier__learning_rate': [0.1, 0.05],
    'classifier__max_depth': [3, 4, 5]
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='f1')
grid_search.fit(X_train, y_train)
best_pipeline = grid_search.best_estimator_

# Evaluate the model
y_pred = best_pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

print(f"Best Parameters: {grid_search.best_params_}")
print(f"Accuracy: {accuracy:.2f}")
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1 Score: {f1:.2f}")

# Function to get MX records for a domain
def get_mx_records(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange) for r in records]
    except Exception as e:
        logging.error(f"Error fetching MX records for domain {domain}: {str(e)}")
        return []

# Function to verify email using SMTP
def verify_email(email, mx_records):
    for mx in mx_records:
        try:
            server = smtplib.SMTP(mx)
            server.set_debuglevel(0)
            server.helo('example.com')
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            if code == 250:
                return True
        except Exception as e:
            logging.error(f"Exception during SMTP verification: {str(e)}")
    return False

# Function to find and verify email
def find_and_verify_email(name, domain, model):
    patterns = generate_email_patterns(name, domain)
    predicted_email = None
    highest_prob = 0
    for pattern in patterns:
        prob = model.predict_proba([pattern])[0, 1]
        if prob > highest_prob:
            highest_prob = prob
            predicted_email = pattern
    if predicted_email:
        mx_records = get_mx_records(domain)
        if mx_records and verify_email(predicted_email, mx_records):
            return predicted_email
    return None

# Example usage
name = 'hassan shehzad'
domain = 'codesyconsulting.com'
email = find_and_verify_email(name, domain, best_pipeline)
print(f"Verified email for {name} at {domain}: {email}")
