import pickle
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# --- 1. SETUP & LOAD MODEL ---
app = FastAPI(title="No-Show Prediction API")

# Path manipulation to ensure we find the model whether running locally or in Docker
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        artifacts = pickle.load(f)
        model = artifacts["model"]
        encoders = artifacts["encoders"]
        # We try to load the feature list if we saved it, otherwise we define it manually
        model_features = artifacts.get("features", None)
    print("✅ Model loaded successfully.")
except FileNotFoundError:
    raise RuntimeError(f"Model file not found at {MODEL_PATH}")

# --- 2. DATA MODELS (INPUT SCHEMA) ---
class PatientData(BaseModel):
    Gender: str
    ScheduledDay: str 
    AppointmentDay: str
    Age: int
    Neighbourhood: str
    OnGovtWelfareBenefits: int
    Hypertension: int
    Diabetes: int
    Alcoholism: int
    Handicapped: int
    SMS_received: int

# --- 3. PREPROCESSING LOGIC ---
def preprocess_input(data: PatientData) -> pd.DataFrame:
    # Convert Pydantic object to DataFrame (single row)
    input_dict = data.dict()
    df = pd.DataFrame([input_dict])
    
    # 1. Date Conversions
    df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'])
    df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay'])
    
    # 2. Feature Engineering (MUST MATCH TRAINING EXACTLY)
    df['LeadTime'] = (df['AppointmentDay'].dt.date - df['ScheduledDay'].dt.date).apply(lambda x: x.days)
    df['LeadTime'] = df['LeadTime'].apply(lambda x: max(x, 0)) # Clip negatives
    
    df['IsWeekend'] = df['AppointmentDay'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df['DayOfWeek'] = df['AppointmentDay'].dt.dayofweek
    df['ScheduledHour'] = df['ScheduledDay'].dt.hour
    
    # 3. Encoding Categoricals
    for col, le in encoders.items():
        try:
            # Handle unseen labels by assigning to the most frequent class (0)
            # This prevents the API from crashing on new neighborhoods
            df[col] = df[col].map(lambda s: le.transform([s])[0] if s in le.classes_ else 0)
        except Exception:
            df[col] = 0
            
    # 4. Column Selection & Ordering
    # If we didn't save the feature list in the pickle, use this hardcoded list from your training script
    if model_features is None:
        expected_cols = ['Age', 'OnGovtWelfareBenefits', 'Hypertension', 'Diabetes', 
                         'Alcoholism', 'Handicapped', 'SMS_received', 'LeadTime', 
                         'IsWeekend', 'DayOfWeek', 'ScheduledHour', 'Gender', 'Neighbourhood']
    else:
        expected_cols = model_features
    
    # Ensure all columns exist (fill 0 if missing)
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0
            
    return df[expected_cols]

# --- 4. API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "running", "model": "LightGBM"}

@app.post("/predict")
def predict_no_show(patient: PatientData):
    try:
        # Preprocess
        X_input = preprocess_input(patient)
        
        # Predict Class and Probability
        prediction_class = model.predict(X_input)[0]
        probability = model.predict_proba(X_input)[0, 1]
        
        return {
            "prediction": "No-Show" if prediction_class == 1 else "Show",
            "no_show_probability": round(float(probability), 4),
            "risk_level": "High" if probability > 0.7 else "Medium" if probability > 0.3 else "Low"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))