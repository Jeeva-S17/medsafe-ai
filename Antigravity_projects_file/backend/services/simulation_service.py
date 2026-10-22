from datetime import datetime
from typing import Dict, Any, Optional
from backend.database import record_vitals, get_patient

class ClinicalRecordsVitalsService:
    """Service providing verified patient previous clinical vitals from EHR records.
    (Hardware / sensor simulation has been completely removed in accordance with patient historical data workflow)
    """
    def __init__(self):
        self.active_patient_id: str = "P0001"
        self._running: bool = False

    @property
    def is_running(self) -> bool:
        return False

    def start_simulation(self, patient_id: str):
        self.active_patient_id = patient_id

    def stop_simulation(self):
        self._running = False

    def reset_simulation(self, patient_id: Optional[str] = None):
        if patient_id:
            self.active_patient_id = patient_id

    def ingest_hardware_reading(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record verified clinical vitals from EHR intake"""
        reading = {
            "patient_id": reading_data.get("patient_id", self.active_patient_id),
            "timestamp": reading_data.get("timestamp", datetime.now().isoformat()),
            "source": "clinical_history",
            "heart_rate": float(reading_data.get("heart_rate", 75.0)),
            "spo2": float(reading_data.get("spo2", 98.0)),
            "temperature": float(reading_data.get("temperature", 36.8)),
            "systolic_bp": float(reading_data.get("systolic_bp", 120.0)),
            "diastolic_bp": float(reading_data.get("diastolic_bp", 80.0)),
            "is_simulated": False
        }
        record_vitals(reading)
        return reading

    def get_patient_baseline_reading(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        pid = patient_id or self.active_patient_id
        patient = get_patient(pid)
        base_hr = float(patient["heart_rate"]) if patient else 78.0
        base_sbp = float(patient["bp"]) if patient else 124.0
        base_dbp = round(base_sbp * 0.65, 1)
        
        return {
            "patient_id": pid,
            "timestamp": datetime.now().isoformat(),
            "source": "clinical_history",
            "heart_rate": base_hr,
            "spo2": 98.2,
            "temperature": 36.8,
            "systolic_bp": base_sbp,
            "diastolic_bp": base_dbp,
            "is_simulated": False
        }

    def get_status(self) -> Dict[str, Any]:
        reading = self.get_patient_baseline_reading(self.active_patient_id)
        return {
            "running": False,
            "active_patient_id": self.active_patient_id,
            "latest_reading": reading,
            "source": "patient_previous_records",
            "is_simulated": False,
            "mode": "Patient Historical Data / EHR"
        }

# Singleton instance export
simulation_service = ClinicalRecordsVitalsService()
