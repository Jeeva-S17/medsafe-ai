import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.services.crewai_service import crewai_service
from backend.services.gemini_service import gemini_service
from backend.services.random_forest_service import random_forest_service
from backend.services.shap_service import shap_service
from backend.services.drug_interaction_service import drug_interaction_service
from backend.services.fda_service import fda_service
from backend.database import get_db_connection

router = APIRouter(prefix="/api/analysis", tags=["CrewAI & Gemini Analysis"])

class FullAnalysisRequest(BaseModel):
    patient_data: Dict[str, Any]
    ocr_medications: Optional[List[str]] = []
    prediction: Optional[Dict[str, Any]] = None
    shap_data: Optional[Dict[str, Any]] = None
    medication_safety: Optional[Dict[str, Any]] = None
    fda_data: Optional[List[Dict[str, Any]]] = None

@router.post("/multi-agent")
def run_crewai_analysis(payload: FullAnalysisRequest) -> Dict[str, Any]:
    patient = payload.patient_data
    ocr_meds = payload.ocr_medications or []
    
    # Run or reuse prediction & SHAP
    ml_pred = payload.prediction or random_forest_service.predict(patient)
    shap_out = payload.shap_data or shap_service.explain(patient)
    
    # Medication safety
    med_safety = payload.medication_safety or drug_interaction_service.evaluate_medications(
        patient.get("medications", ""),
        ocr_meds,
        patient.get("allergies", "")
    )
    
    # FDA data
    if payload.fda_data:
        fda_data = payload.fda_data
    else:
        fda_data = []
        all_meds = med_safety.get("all_evaluated_medications", [])
        for m in all_meds[:4]:
            fda_data.append(fda_service.search_fda_medicine(m))

    agent_results = crewai_service.run_multi_agent_pipeline(
        patient_data=patient,
        ml_prediction=ml_pred,
        shap_explanation=shap_out,
        medication_safety=med_safety,
        fda_data=fda_data
    )
    return agent_results

@router.post("/final-safety-report")
def generate_final_report(payload: FullAnalysisRequest) -> Dict[str, Any]:
    patient = payload.patient_data
    ocr_meds = payload.ocr_medications or []
    
    ml_pred = payload.prediction or random_forest_service.predict(patient)
    shap_out = payload.shap_data or shap_service.explain(patient)
    med_safety = payload.medication_safety or drug_interaction_service.evaluate_medications(
        patient.get("medications", ""),
        ocr_meds,
        patient.get("allergies", "")
    )
    
    if payload.fda_data:
        fda_data = payload.fda_data
    else:
        fda_data = []
        all_meds = med_safety.get("all_evaluated_medications", [])
        for m in all_meds[:4]:
            fda_data.append(fda_service.search_fda_medicine(m))

    multi_agent_data = crewai_service.run_multi_agent_pipeline(
        patient_data=patient,
        ml_prediction=ml_pred,
        shap_explanation=shap_out,
        medication_safety=med_safety,
        fda_data=fda_data
    )

    final_report = gemini_service.generate_clinical_safety_report(
        patient_data=patient,
        prediction_result=ml_pred,
        shap_data=shap_out,
        medication_safety=med_safety,
        fda_data=fda_data,
        multi_agent_data=multi_agent_data
    )

    # Save to SQLite database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO ai_reports (patient_id, safety_level, report_json)
        VALUES (?, ?, ?)
        """, (
            patient.get("patient_id", "Unknown"),
            final_report["safety_level"],
            json.dumps(final_report)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error persisting AI report: {e}")

    return final_report
