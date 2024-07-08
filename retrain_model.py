import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
import joblib

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
        domain = row['Company URL'].split('/')[2] if '//' in row['Company URL'] else row['Company URL']
        patterns = generate_email_patterns(row['Person Name'], domain)
        for pattern in patterns:
            X.append(pattern)
            y.append(1 if pattern == row['Email'] else 0)
    return X, y

X, y = extract_features_and_labels(data)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the model pipeline with XGBoost
pipeline = Pipeline([
    ('vectorizer', CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))),
    ('classifier', xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
])

# Hyperparameter tuning
param_grid = {
    'classifier__n_estimators': [100, 200, 500],
    'classifier__learning_rate': [0.1, 0.05, 0.01],
    'classifier__max_depth': [3, 4, 5, 6],
    'classifier__subsample': [0.8, 1.0],
    'classifier__colsample_bytree': [0.8, 1.0],
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)
best_pipeline = grid_search.best_estimator_

# Save the trained model
joblib.dump(best_pipeline, 'email_model_advanced.pkl')

print(f"Best Parameters: {grid_search.best_params_}")
print("Advanced model retraining complete and saved to 'email_model_advanced.pkl'")
