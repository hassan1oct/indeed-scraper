import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
import joblib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the combined CSV
try:
    data = pd.read_csv('emails.csv')
    logging.info("CSV file loaded successfully.")
except FileNotFoundError:
    logging.error("CSV file not found. Please check the file path.")
    raise
except Exception as e:
    logging.error(f"Error loading CSV file: {e}")
    raise

# Generate email patterns
def generate_email_patterns(name, domain):
    try:
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
    except Exception as e:
        logging.error(f"Error generating email patterns: {e}")
        return []

# Extract features and labels for training
def extract_features_and_labels(df):
    X, y = [], []
    try:
        for index, row in df.iterrows():
            domain = row['Company URL'].split('/')[2] if '//' in row['Company URL'] else row['Company URL']
            patterns = generate_email_patterns(row['Person Name'], domain)
            for pattern in patterns:
                X.append(pattern)
                y.append(1 if pattern == row['Email'] else 0)
        logging.info("Features and labels extracted successfully.")
    except Exception as e:
        logging.error(f"Error extracting features and labels: {e}")
    return X, y

X, y = extract_features_and_labels(data)

# Split the data
try:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logging.info("Data split into training and testing sets successfully.")
except Exception as e:
    logging.error(f"Error splitting data: {e}")
    raise

# Create and train the model pipeline with XGBoost
pipeline = Pipeline([
    ('vectorizer', CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))),
    ('classifier', xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
])

# Hyperparameter tuning
param_grid = {
    'classifier__n_estimators': [100, 200],  # Reduced for debugging
    'classifier__learning_rate': [0.1, 0.05],
    'classifier__max_depth': [3, 4],
    'classifier__subsample': [0.8, 1.0],
    'classifier__colsample_bytree': [0.8, 1.0],
}

try:
    grid_search = GridSearchCV(pipeline, param_grid, cv=3, scoring='f1', n_jobs=-1)  # Reduced cv for debugging
    grid_search.fit(X_train, y_train)
    best_pipeline = grid_search.best_estimator_
    logging.info(f"Best Parameters: {grid_search.best_params_}")
except Exception as e:
    logging.error(f"Error during grid search: {e}")
    raise

# Save the trained model
try:
    joblib.dump(best_pipeline, 'email_model_advanced.pkl')
    logging.info("Advanced model training complete and saved to 'email_model_advanced.pkl'")
except Exception as e:
    logging.error(f"Error saving model: {e}")
    raise

print(f"Best Parameters: {grid_search.best_params_}")
print("Advanced model training complete and saved to 'email_model_advanced.pkl'")
