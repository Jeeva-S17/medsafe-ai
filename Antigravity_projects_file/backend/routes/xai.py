from fastapi import APIRouter
from typing import Dict, Any
from backend.models.schemas import PatientInput
from backend.services.shap_service import shap_service

router = APIRouter(prefix="/api/xai", tags=["Explainable AI"])

@router.post("/explain")
def get_shap_explanation(patient: PatientInput) -> Dict[str, Any]:
    patient_dict = patient.model_dump()
    result = shap_service.explain(patient_dict)
    result["patient_id"] = patient.patient_id
    return result
