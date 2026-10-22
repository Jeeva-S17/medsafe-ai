import os
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from typing import Dict, Any
from backend.services.visualization_service import visualization_service
from backend.services.pdf_service import pdf_service
from backend.services.random_forest_service import random_forest_service
from backend.services.shap_service import shap_service
from backend.services.drug_interaction_service import drug_interaction_service
from backend.services.fda_service import fda_service
from backend.services.crewai_service import crewai_service
from backend.services.gemini_service import gemini_service
from backend.database import get_patient, get_patient_vitals_history

router = APIRouter(prefix="/api/report", tags=["Reports & Visualization"])

@router.get("/charts/probabilities/{patient_id}")
def get_probability_chart(patient_id: str):
    p = get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    pred = random_forest_service.predict(p)
    img_bytes = visualization_service.generate_probability_chart(pred["probabilities"], as_bytes=True)
    return Response(content=img_bytes, media_type="image/png")

@router.get("/charts/shap/{patient_id}")
def get_shap_chart(patient_id: str):
    p = get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    shap_res = shap_service.explain(p)
    img_bytes = visualization_service.generate_shap_chart(shap_res["feature_contributions"], as_bytes=True)
    return Response(content=img_bytes, media_type="image/png")

@router.get("/charts/trends/{patient_id}")
def get_trends_chart(patient_id: str):
    vitals = get_patient_vitals_history(patient_id, limit=50)
    img_bytes = visualization_service.generate_vitals_trend_chart(vitals, as_bytes=True)
    return Response(content=img_bytes, media_type="image/png")

@router.get("/pdf/{patient_id}")
def download_pdf_report(patient_id: str):
    p = get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Generate full report context
    pred = random_forest_service.predict(p)
    shap_res = shap_service.explain(p)
    med_safety = drug_interaction_service.evaluate_medications(
        p.get("medications", ""),
        [], # default if no separate ocr is active
        p.get("allergies", "")
    )
    
    fda_data = []
    for m in med_safety.get("all_evaluated_medications", [])[:3]:
        fda_data.append(fda_service.search_fda_medicine(m))

    multi_agents = crewai_service.run_multi_agent_pipeline(p, pred, shap_res, med_safety, fda_data)
    ai_rep = gemini_service.generate_clinical_safety_report(p, pred, shap_res, med_safety, fda_data, multi_agents)

    pdf_path = pdf_service.generate_clinical_report(p, pred, shap_res, med_safety, fda_data, ai_rep)
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path)
    )
