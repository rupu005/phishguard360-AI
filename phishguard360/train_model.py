import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ---------------------------
# TRAINING DATA
# ---------------------------

phishing_samples = [
    "urgent verify your password",
    "your bank account is suspended click here",
    "lottery winnings claim now",
    "update credit card immediately",
    "your account will be locked click to update",
    "payment failed click here to verify"
]

safe_samples = [
    "team meeting tomorrow schedule",
    "project updates shared please review",
    "invoice attached for your reference",
    "let me know if you need anything",
    "your leave request is approved",
    "weekly report is ready for download"
]

# Combine data
X_data = phishing_samples + safe_samples
y_data = [1] * len(phishing_samples) + [0] * len(safe_samples)   # 1 = phishing, 0 = safe

# ---------------------------
# VECTORIZATION (TF-IDF)
# ---------------------------

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(X_data)

# ---------------------------
# TRAIN MODEL (LOGISTIC REGRESSION)
# ---------------------------

model = LogisticRegression()
model.fit(X, y_data)

# ---------------------------
# SAVE MODEL + VECTORIZER
# ---------------------------

with open("model.pkl", "wb") as f:
    pickle.dump({"vectorizer": vectorizer, "model": model}, f)

print("Model trained successfully!")