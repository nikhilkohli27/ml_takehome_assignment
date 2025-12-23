# Patient No-Show Predictor

## Overview
This is an end-to-end Machine Learning application designed to predict the probability of a patient missing their medical appointment. The system aims to help clinics optimize scheduling and reduce revenue loss by identifying high-risk appointments in advance.

**Live Demo:** [(https://loquacious-tartufo-8da098.netlify.app/)]
*(Note: This is a free-tier deployment. The backend may take up to 60 seconds to wake up on the first request.)*

## Architecture
The project is built using a microservices architecture:
* **Frontend:** React (Vite) + TypeScript + Tailwind CSS
* **Backend:** FastAPI (Python)
* **Database:** SQLite (local persistence)
* **Model:** LightGBM (Gradient Boosting)
* **Deployment:** Docker containerized environment

## How to Run

### Option 1: Docker (Recommended)
Building the container ensures the environment matches production specifications exactly.

1. Build the image:
   docker build -t no-show-api .

2. Run the container:
   docker run -p 8000:8000 no-show-api

### Option 2: Local Development
If you prefer running the services individually without Docker:

**Backend:**
1. Install dependencies:
   pip install -r requirements.txt
2. Start the server:
   python -m uvicorn app.main:app --reload

**Frontend:**
1. Navigate to the frontend directory:
   cd frontend
2. Install dependencies:
   npm install
3. Start the development server:
   npm run dev

## Model Performance
* **Algorithm:** LightGBM
* **Metric:** ROC-AUC Score: 0.74
* **Baseline Comparison:** The model outperformed a standard Logistic Regression baseline (AUC 0.66).
* **Key Insight:** The "LeadTime" (days between scheduling and the appointment) was identified as the strongest predictor of a no-show.

## Features & Requirements
* **Exploratory Data Analysis (EDA):** Complete analysis of the dataset structure and correlations.
* **Model Training Pipeline:** Automated preprocessing and model serialization.
* **REST API:** FastAPI endpoint handling real-time inference requests.
* **Database Integration:** SQLite database automatically logs all predictions for future drift analysis.
* **Cloud Deployment:** Configured for deployment on Render (Backend) and Netlify (Frontend).