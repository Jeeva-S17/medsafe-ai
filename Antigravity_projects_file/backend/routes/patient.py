from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.models.schemas import PatientInput
from backend.database import get_all_patients, get_patient, save_patient, get_patient_vitals_history, get_patient_clinical_history

router = APIRouter(prefix="/api/patient", tags=["Patient"])

@router.get("/all")
def list_patients() -> List[Dict[str, Any]]:
    return get_all_patients()

@router.get("/{patient_id}")
def get_patient_details(patient_id: str) -> Dict[str, Any]:
    p = get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return p

@router.post("")
def create_or_update_patient(patient: PatientInput) -> Dict[str, Any]:
    patient_dict = patient.model_dump()
    save_patient(patient_dict)
    return {
        "success": True,
        "message": f"Patient '{patient.patient_id}' saved successfully",
        "patient": patient_dict
    }

@router.get("/{patient_id}/vitals")
def get_vitals(patient_id: str, limit: int = 40) -> List[Dict[str, Any]]:
    return get_patient_vitals_history(patient_id, limit=limit)

@router.get("/{patient_id}/history")
def get_history(patient_id: str) -> List[Dict[str, Any]]:
    """Retrieve full chronological previous clinical visits and laboratory findings"""
    return get_patient_clinical_history(patient_id)

