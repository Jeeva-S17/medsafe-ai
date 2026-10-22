import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.models.schemas import PatientInput, PredictionResult
from backend.services.random_forest_service import random_forest_service
from backend.database import get_db_connection

router = APIRouter(tags=["Prediction"])

def _run_prediction(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    res = random_forest_service.predict(patient_dict)
    
    # Save to database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO predictions (patient_id, predicted_disease, confidence, probabilities_json, features_json)
        VALUES (?, ?, ?, ?, ?)
        """, (
            patient_dict.get("patient_id", "Unknown"),
            res["predicted_disease"],
            res["confidence"],
            json.dumps(res["probabilities"]),
            json.dumps(res["features_evaluated"])
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to record prediction in DB: {e}")

    return res

@router.post("/predict")
def predict_disease(patient: PatientInput) -> Dict[str, Any]:
    """Standard endpoint strictly matching Section 4 specification"""
    return _run_prediction(patient.model_dump())

@router.post("/api/predict")
def predict_disease_api(patient: PatientInput) -> Dict[str, Any]:
    return _run_prediction(patient.model_dump())
