from fastapi import APIRouter, Query
from typing import Dict, Any
from backend.services.fda_service import fda_service

router = APIRouter(prefix="/api/fda", tags=["FDA Safety Information"])

@router.get("/search")
def search_fda(medicine: str = Query(..., description="Medicine or active ingredient name e.g. Metformin")) -> Dict[str, Any]:
    return fda_service.search_fda_medicine(medicine)
