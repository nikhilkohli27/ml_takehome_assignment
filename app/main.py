import pickle
import pandas as pd
import numpy as np
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# --- 1. SETUP & DATABASE (THE ORM WAY) ---
app = FastAPI(title="No-Show Prediction API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
DB_PATH = os.path.join(BASE_DIR, "appointments.db")

# SQLAlchemy Setup
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Table (Model)
class AppointmentDB(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_age = Column(Integer)
    gender = Column(String)
    neighbourhood = Column(String)
    scheduled_day = Column(String)
    appointment_day = Column(String)
    lead_time = Column(Integer)
    prediction = Column(String)
    probability = Column(Float)
    risk_level = Column(String)
    created_at = Column(DateTime, default=datetime.now)

# Create Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. LOAD ML MODEL ---
try:
    with open(MODEL_PATH, "rb") as f:
        artifacts = pickle.load(f)
        model = artifacts["model"]
        encoders = artifacts["encoders"]
        model_features = artifacts.get("features", ['Age', 'OnGovtWelfareBenefits', 'Hypertension', 'Diabetes', 'Alcoholism', 'Handicapped', 'SMS_received', 'LeadTime', 'IsWeekend', 'DayOfWeek', 'ScheduledHour', 'Gender', 'Neighbourhood'])
except FileNotFoundError:
    raise RuntimeError(f"Model file not found at {MODEL_PATH}")

# --- 3. INPUT SCHEMA ---
class PatientData(BaseModel):
    Gender: str
    ScheduledDay: str 
    AppointmentDay: str
    Age: int
    Neighbourhood: str
    OnGovtWelfareBenefits: int = 0
    Hypertension: int = 0
    Diabetes: int = 0
    Alcoholism: int = 0
    Handicapped: int = 0
    SMS_received: int = 0

# --- 4. PREPROCESSING ---
def preprocess_input(data: PatientData) -> pd.DataFrame:
    input_dict = data.dict()
    df = pd.DataFrame([input_dict])
    
    # Dates
    df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay'])
    df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay'])
    
    # Feature Engineering
    df['LeadTime'] = (df['AppointmentDay'].dt.date - df['ScheduledDay'].dt.date).apply(lambda x: x.days)
    df['LeadTime'] = df['LeadTime'].apply(lambda x: max(x, 0))
    
    df['IsWeekend'] = df['AppointmentDay'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df['DayOfWeek'] = df['AppointmentDay'].dt.dayofweek
    df['ScheduledHour'] = df['ScheduledDay'].dt.hour
    
    # Encoders
    for col, le in encoders.items():
        try:
            df[col] = df[col].map(lambda s: le.transform([s])[0] if s in le.classes_ else 0)
        except:
            df[col] = 0
            
    # Align Columns
    for col in model_features:
        if col not in df.columns:
            df[col] = 0
            
    return df[model_features]

# --- 5. ENDPOINTS ---
@app.post("/predict")
def predict_no_show(patient: PatientData, db: Session = Depends(get_db)):
    try:
        # 1. Prediction Logic
        X_input = preprocess_input(patient)
        prediction_class = model.predict(X_input)[0]
        probability = model.predict_proba(X_input)[0, 1]
        
        # Risk Logic
        if probability > 0.50: risk = "High"
        elif probability > 0.20: risk = "Medium"
        else: risk = "Low"
            
        pred_label = "No-Show" if prediction_class == 1 else "Show"
        
        # 2. Save to DB using ORM (Requirement Met!)
        lead_time = (pd.to_datetime(patient.AppointmentDay).date() - pd.to_datetime(patient.ScheduledDay).date()).days
        
        new_appointment = AppointmentDB(
            patient_age=patient.Age,
            gender=patient.Gender,
            neighbourhood=patient.Neighbourhood,
            scheduled_day=patient.ScheduledDay,
            appointment_day=patient.AppointmentDay,
            lead_time=lead_time,
            prediction=pred_label,
            probability=float(probability),
            risk_level=risk
        )
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)
        
        return {
            "prediction": pred_label,
            "no_show_probability": round(float(probability), 4),
            "risk_level": risk,
            "db_id": new_appointment.id  # Proof it was saved
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))