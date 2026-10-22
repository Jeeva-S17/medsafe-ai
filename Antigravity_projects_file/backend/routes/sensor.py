from fastapi import APIRouter
from typing import Dict, Any, Optional
from backend.models.schemas import SimulationControl, SensorReading
from backend.services.simulation_service import simulation_service

router = APIRouter(prefix="/api/sensor", tags=["Patient Clinical Records & Vitals"])

@router.post("/start")
def start_simulation(payload: Optional[SimulationControl] = None, patient_id: Optional[str] = None) -> Dict[str, Any]:
    pid = (payload.patient_id if payload else None) or patient_id or "P0001"
    simulation_service.start_simulation(pid)
    reading = simulation_service.get_patient_baseline_reading(pid)
    return {
        "success": True,
        "status": "EHR Historical Data Active",
        "patient_id": pid,
        "message": f"Verified previous clinical records active for {pid}. (Hardware simulation removed)",
        "source": "clinical_history",
        "reading": reading
    }

@router.post("/stop")
def stop_simulation() -> Dict[str, Any]:
    simulation_service.stop_simulation()
    return {
        "success": True,
        "status": "Historical Records Active",
        "message": "Clinical records baseline in static evaluation mode"
    }

@router.post("/reset")
def reset_simulation(payload: Optional[SimulationControl] = None, patient_id: Optional[str] = None) -> Dict[str, Any]:
    pid = (payload.patient_id if payload else None) or patient_id or "P0001"
    simulation_service.reset_simulation(pid)
    reading = simulation_service.get_patient_baseline_reading(pid)
    return {
        "success": True,
        "status": "Baseline Reset",
        "patient_id": pid,
        "reading": reading,
        "message": f"Historical clinical baseline refreshed for {pid}"
    }

@router.get("/status")
def get_sensor_status() -> Dict[str, Any]:
    return simulation_service.get_status()

@router.post("/reading")
def ingest_reading(reading: SensorReading) -> Dict[str, Any]:
    """Accept incoming verified clinical reading for patient profile"""
    saved = simulation_service.ingest_hardware_reading(reading.model_dump())
    return {
        "success": True,
        "reading": saved
    }
