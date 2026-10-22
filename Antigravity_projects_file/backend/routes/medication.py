from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from backend.services.drug_interaction_service import drug_interaction_service

router = APIRouter(prefix="/api/medication", tags=["Medication Safety"])

class MedicationCheckRequest(BaseModel):
    patient_id: str
    current_medications: Union[str, List[str]] = ""
    ocr_prescribed_medications: Optional[List[str]] = []
    new_prescriptions: Optional[List[str]] = []
    patient_allergies: Optional[str] = ""
    allergies: Optional[str] = ""
    medical_conditions: Optional[str] = ""
    conditions: Optional[str] = ""

@router.post("/check")
def check_medications(payload: MedicationCheckRequest) -> Dict[str, Any]:
    if isinstance(payload.current_medications, list):
        cur_meds_str = ", ".join(payload.current_medications)
    else:
        cur_meds_str = payload.current_medications or ""
        
    ocr_list = payload.ocr_prescribed_medications or payload.new_prescriptions or []
    allergies = payload.patient_allergies or payload.allergies or ""

    eval_res = drug_interaction_service.evaluate_medications(
        current_meds_str=cur_meds_str,
        ocr_meds_list=ocr_list,
        patient_allergies=allergies
    )
    eval_res["patient_id"] = payload.patient_id
    return eval_res
