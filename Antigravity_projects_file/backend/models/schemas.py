from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any

class PatientInput(BaseModel):
    patient_id: str = Field(..., description="Unique Patient Identifier e.g. P0001")
    name: Optional[str] = Field("Unnamed Patient", description="Patient Full Name")
    age: int = Field(..., ge=0, le=130, description="Age in years (0-130)")
    gender: str = Field(..., description="Gender (Male, Female, Other)")
    bmi: float = Field(..., ge=10.0, le=80.0, description="Body Mass Index kg/m2 (10-80)")
    glucose: float = Field(..., ge=20.0, le=600.0, description="Fasting Blood Glucose mg/dL (20-600)")
    bp: float = Field(..., ge=40.0, le=260.0, description="Systolic Blood Pressure mmHg (40-260)")
    cholesterol: float = Field(..., ge=50.0, le=600.0, description="Serum Cholesterol mg/dL (50-600)")
    heart_rate: float = Field(..., ge=30.0, le=240.0, description="Heart Rate bpm (30-240)")
    hba1c: float = Field(..., ge=3.0, le=18.0, description="Glycated Hemoglobin % (3.0-18.0)")
    smoking: int = Field(0, ge=0, le=1, description="Smoking status: 0 for No, 1 for Yes")
    symptoms: Optional[str] = Field("", description="Reported clinical symptoms")
    allergies: Optional[str] = Field("", description="Known drug/environmental allergies")
    conditions: Optional[str] = Field("", description="Pre-existing medical conditions")
    medications: Optional[str] = Field("", description="Currently prescribed/active medications")

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        v_clean = v.strip().capitalize()
        if v_clean not in ["Male", "Female", "Other"]:
            raise ValueError("Gender must be 'Male', 'Female', or 'Other'")
        return v_clean

class SensorReading(BaseModel):
    patient_id: str
    timestamp: Optional[str] = None
    source: str = "simulation" # "simulation" or "esp32"
    heart_rate: float
    spo2: float
    temperature: float
    systolic_bp: float
    diastolic_bp: float
    is_simulated: bool = True

class SimulationControl(BaseModel):
    patient_id: str
    interval_seconds: float = 2.0
    action: str = "start" # "start", "stop", "reset"

class PredictionResult(BaseModel):
    predicted_disease: str
    confidence: float
    probabilities: Dict[str, float]
    disclaimer: str = "AI-generated decision support — professional verification required."
    features_evaluated: Dict[str, Any]

class FeatureContribution(BaseModel):
    feature: str
    value: Any
    shap_value: float
    contribution: str # "Increases Risk" or "Decreases Risk"

class XAIResponse(BaseModel):
    patient_id: str
    predicted_disease: str
    base_value: float
    feature_contributions: List[FeatureContribution]
    summary_explanation: str
    disclaimer: str = "These values indicate which input features contributed most to the model output. They do not establish medical causation."

class DetectedMedicine(BaseModel):
    name: str
    strength: Optional[str] = "Unspecified"
    frequency: Optional[str] = "Unspecified"
    duration: Optional[str] = "Unspecified"
    confidence: float = 0.85

class PrescriptionOCRResult(BaseModel):
    patient_id: str
    extracted_text: str
    detected_medicines: List[DetectedMedicine]
    confidence_level: str # "High", "Moderate", "Manual verification required"
    disclaimer: str = "OCR output is extracted raw text and must not be treated as verified prescription instructions."

class DrugInteraction(BaseModel):
    medicine_a: str
    medicine_b: str
    severity: str # "Major", "Moderate", "Minor"
    description: str
    evidence_source: str
    action_note: str = "Professional clinical verification required."

class AllergyAlert(BaseModel):
    medicine: str
    allergen_match: str
    status: str # "Potential allergy concern", "Verification required"
    severity: str = "High"

class MedicationSafetyResponse(BaseModel):
    patient_id: str
    current_medications: List[str]
    ocr_prescribed_medications: List[str]
    allergy_alerts: List[AllergyAlert]
    interactions: List[DrugInteraction]
    safety_summary: str
    disclaimer: str = "Do not start, stop, or change medications without consulting a licensed healthcare provider."

class FDAReactionCount(BaseModel):
    reaction: str
    count: int

class FDAMedicineReport(BaseModel):
    medicine_name: str
    total_adverse_reports: int
    top_reactions: List[FDAReactionCount]
    sample_report_ids: List[str]
    seriousness_summary: Dict[str, int]
    source_url: str
    disclaimer: str = "FDA adverse-event reports are reports of events and do not by themselves establish causality."

class AgentOutput(BaseModel):
    agent_name: str
    role: str
    findings: str
    concerns: List[str]
    recommendations: List[str]

class FinalSafetyReport(BaseModel):
    patient_id: str
    patient_summary: Dict[str, Any]
    predicted_disease: str
    disease_probability: float
    all_probabilities: Dict[str, float]
    safety_level: str # "LOW", "MODERATE", "HIGH", "URGENT"
    key_risk_factors: List[str]
    allergy_findings: List[str]
    medication_findings: List[str]
    drug_interactions: List[str]
    fda_evidence_summary: str
    missing_information: List[str]
    professional_verification_required: bool = True
    agents_breakdown: Optional[List[AgentOutput]] = None
    structured_markdown: str
    disclaimer: str = "AI-generated decision support — professional verification required. MediSafe AI does not provide medical diagnoses or prescribe medications."

class SystemServiceStatus(BaseModel):
    status: str # "Connected", "Available", "Ready", "Running", "Stopped", "Error"
    details: Optional[str] = None

class SystemHealthStatus(BaseModel):
    random_forest: SystemServiceStatus
    shap: SystemServiceStatus
    ocr: SystemServiceStatus
    fda_api: SystemServiceStatus
    gemini: SystemServiceStatus
    crewai: SystemServiceStatus
    database: SystemServiceStatus
    patient_history: Optional[SystemServiceStatus] = None
    pharmacy_delivery: Optional[SystemServiceStatus] = None
    simulation: Optional[SystemServiceStatus] = None
