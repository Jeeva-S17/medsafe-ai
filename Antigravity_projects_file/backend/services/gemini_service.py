import os
import json
from typing import Dict, Any, List
from backend.config import GOOGLE_API_KEY

class GeminiService:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.model = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                for candidate in ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
                    try:
                        self.model = genai.GenerativeModel(candidate)
                        break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Failed to initialize Google Generative AI client: {e}")
                self.model = None

    def generate_clinical_safety_report(
        self,
        patient_data: Dict[str, Any],
        prediction_result: Dict[str, Any],
        shap_data: Dict[str, Any],
        medication_safety: Dict[str, Any],
        fda_data: List[Dict[str, Any]],
        multi_agent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate clinical decision support safety report using Gemini or high-fidelity clinical synthesis"""
        
        # Build strict prompt containing ONLY supplied patient information and verified retrieved evidence
        patient_summary = {
            "patient_id": patient_data.get("patient_id"),
            "name": patient_data.get("name", "Unnamed Patient"),
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "bmi": patient_data.get("bmi"),
            "glucose": patient_data.get("glucose"),
            "bp": patient_data.get("bp"),
            "cholesterol": patient_data.get("cholesterol"),
            "heart_rate": patient_data.get("heart_rate"),
            "hba1c": patient_data.get("hba1c"),
            "smoking": "Yes" if patient_data.get("smoking") in [1, True, "1"] else "No",
            "symptoms": patient_data.get("symptoms", "None reported"),
            "allergies": patient_data.get("allergies", "None reported"),
            "conditions": patient_data.get("conditions", "None reported"),
            "medications": patient_data.get("medications", "None reported")
        }

        predicted_disease = prediction_result.get("predicted_disease", "Unspecified")
        probability = prediction_result.get("confidence", 0.0)
        all_probs = prediction_result.get("probabilities", {})
        risk_factors = prediction_result.get("top_risk_factors", [])

        allergy_status = medication_safety.get("allergy_status", "No allergy reported")
        allergy_alerts = medication_safety.get("allergy_alerts", [])
        current_meds = medication_safety.get("current_medications", [])
        ocr_meds = medication_safety.get("ocr_prescribed_medications", [])
        interactions = medication_safety.get("interactions", [])

        # Determine safety level
        # LOW, MODERATE, HIGH, URGENT
        if any(a.get("severity") == "HIGH" for a in allergy_alerts) or any(i.get("severity") == "Major" for i in interactions) or float(patient_data.get("bp", 0)) >= 180:
            safety_level = "URGENT"
        elif len(interactions) > 0 or probability >= 75.0 or float(patient_data.get("glucose", 0)) >= 160:
            safety_level = "HIGH"
        elif len(risk_factors) > 1 or probability >= 50.0:
            safety_level = "MODERATE"
        else:
            safety_level = "LOW"

        missing_info = []
        if not patient_data.get("allergies") or patient_data.get("allergies").strip().lower() in ["none", ""]:
            missing_info.append("Documentation of comprehensive drug/food allergy history")
        if not patient_data.get("conditions"):
            missing_info.append("Complete past medical and family history")
        if float(patient_data.get("hba1c", 0)) < 4.0:
            missing_info.append("Recent confirmed Glycated Hemoglobin (HbA1c) lab panel")

        # Try generating via Gemini if API key is active
        if self.model:
            try:
                prompt = f"""
You are an expert Clinical Decision Support reasoning assistant for MediSafe AI.
CRITICAL INSTRUCTIONS:
1. This is a clinical decision-support prototype.
2. Do NOT present AI output as a confirmed medical diagnosis.
3. Do NOT allow the system to prescribe, stop, or change medication.
4. Clearly emphasize: "AI-generated decision support — professional verification required."
5. Never invent patient information, allergies, medications, prescription data, or medical history.
6. Use ONLY the supplied patient data and verified clinical facts below.

SUPPLIED PATIENT DATA:
{json.dumps(patient_summary, indent=2)}

RANDOM FOREST MODEL RESULT:
- Predicted Disease: {predicted_disease}
- Model Probability: {probability}%
- Probabilities: {json.dumps(all_probs)}
- Key Risk Factors: {json.dumps(risk_factors)}

MEDICATION & ALLERGY SAFETY:
- Reported Allergies: {patient_data.get('allergies')}
- Allergy Alerts: {json.dumps(allergy_alerts)}
- Current Medications: {json.dumps(current_meds)}
- Prescription OCR Medications: {json.dumps(ocr_meds)}
- Drug Interactions: {json.dumps(interactions)}

OPENFDA DATA:
{json.dumps(fda_data, indent=2)}

ASSESSMENT SAFETY LEVEL: {safety_level}

GENERATE A STRUCTURED CLINICAL DECISION-SUPPORT REPORT in Markdown with the following exact numbered sections:
1. Patient Summary
2. Predicted Disease
3. Disease Probability
4. Important Risk Factors
5. Allergy Check
6. Current Medication Check
7. Prescription Check
8. Possible Medication Interactions
9. Important Missing Information
10. Professional Verification Required
11. Safety Level ({safety_level})

Keep it clinical, objective, and concise. End with the mandatory clinical disclaimer.
"""
                response = self.model.generate_content(prompt)
                markdown_text = response.text
                return self._package_report(
                    patient_summary, predicted_disease, probability, all_probs, safety_level,
                    risk_factors, allergy_status, allergy_alerts, current_meds, ocr_meds,
                    interactions, fda_data, missing_info, multi_agent_data, markdown_text
                )
            except Exception as e:
                print(f"Gemini API call failed: {e}. Utilizing deterministic clinical synthesizer.")

        # High-Fidelity Clinical Decision Support Synthesizer (Fallback/Default)
        markdown_text = self._build_deterministic_markdown(
            patient_summary, predicted_disease, probability, all_probs, safety_level,
            risk_factors, allergy_alerts, current_meds, ocr_meds, interactions,
            fda_data, missing_info
        )

        return self._package_report(
            patient_summary, predicted_disease, probability, all_probs, safety_level,
            risk_factors, allergy_status, allergy_alerts, current_meds, ocr_meds,
            interactions, fda_data, missing_info, multi_agent_data, markdown_text
        )

    def _build_deterministic_markdown(
        self, patient_summary, predicted_disease, probability, all_probs, safety_level,
        risk_factors, allergy_alerts, current_meds, ocr_meds, interactions, fda_data, missing_info
    ) -> str:
        allergy_txt = "No active contraindications flagged against current list."
        if allergy_alerts:
            allergy_txt = "⚠ POTENTIAL ALLERGY CONCERN: " + "; ".join([f"{a['medicine']} matches {a['allergen_match']}" for a in allergy_alerts])

        inter_txt = "No severe drug-drug interactions detected among current/prescribed medications."
        if interactions:
            inter_txt = "\n".join([f"- **{i['medicine_a']} + {i['medicine_b']}** ({i['severity']} Severity): {i['potential_interaction']}" for i in interactions])

        fda_txt = "Adverse event profiles reviewed via OpenFDA FAERS database for active ingredients."
        if fda_data:
            fda_txt = "\n".join([f"- **{f['medicine_name']}**: {f['total_adverse_reports']:,} total post-marketing reports filed." for f in fda_data])

        missing_txt = "\n".join([f"- {m}" for m in missing_info]) if missing_info else "- None identified for baseline decision support."
        rf_txt = "\n".join([f"- {rf}" for rf in risk_factors]) if risk_factors else "- No severe acute outliers identified in primary panel."

        return f"""# MediSafe AI — Clinical Decision Support Report

### 1. Patient Summary
- **Patient Identifier:** {patient_summary['patient_id']} ({patient_summary['name']})
- **Demographics:** {patient_summary['age']} years old, {patient_summary['gender']}, BMI {patient_summary['bmi']} kg/m²
- **Hemodynamics & Metabolic:** BP {patient_summary['bp']} mmHg, HR {patient_summary['heart_rate']} bpm, Glucose {patient_summary['glucose']} mg/dL, HbA1c {patient_summary['hba1c']}%, Cholesterol {patient_summary['cholesterol']} mg/dL
- **Reported Symptoms:** {patient_summary['symptoms']}

### 2. Predicted Disease
**{predicted_disease}**  
*(Classification output generated via trained Random Forest ensemble based strictly on verified baseline clinical features)*

### 3. Disease Probability
- **Model Confidence for {predicted_disease}:** {probability:.2f}%
- **Full Model Differential Spectrum:**
{chr(10).join([f"  - {d}: {p:.2f}%" for d, p in all_probs.items()])}

### 4. Important Risk Factors
{rf_txt}

### 5. Allergy Check
- **Reported Allergies:** {patient_summary['allergies']}
- **Clinical Evaluation:** {allergy_txt}

### 6. Current Medication Check
- **Current Active Regimen:** {', '.join(current_meds) if current_meds else 'None reported'}

### 7. Prescription Check
- **OCR Extracted Medications:** {', '.join(ocr_meds) if ocr_meds else 'None detected from uploaded document'}

### 8. Possible Medication Interactions
{inter_txt}

### 9. OpenFDA Safety Surveillance Evidence
{fda_txt}
*(OpenFDA adverse-event reports are reports of events and do not by themselves establish causality)*

### 10. Important Missing Information
{missing_txt}

### 11. Professional Verification Required
**MANDATORY:** AI-generated decision support — professional verification required. This report provides probabilistic guidance for licensed clinicians and must not be used as an autonomous medical diagnosis or prescription authority.

### Overall Safety Level: **{safety_level}**
"""

    def _package_report(
        self, patient_summary, predicted_disease, probability, all_probs, safety_level,
        risk_factors, allergy_status, allergy_alerts, current_meds, ocr_meds,
        interactions, fda_data, missing_info, multi_agent_data, markdown_text
    ) -> Dict[str, Any]:
        return {
            "patient_id": patient_summary["patient_id"],
            "patient_summary": patient_summary,
            "predicted_disease": predicted_disease,
            "disease_probability": probability,
            "all_probabilities": all_probs,
            "safety_level": safety_level,
            "key_risk_factors": risk_factors,
            "allergy_status": allergy_status,
            "allergy_alerts": allergy_alerts,
            "current_medications": current_meds,
            "ocr_medications": ocr_meds,
            "drug_interactions": interactions,
            "fda_evidence": fda_data,
            "missing_information": missing_info,
            "professional_verification_required": True,
            "multi_agent_breakdown": multi_agent_data.get("agents", []),
            "structured_markdown": markdown_text,
            "disclaimer": "AI-generated decision support — professional verification required. MediSafe AI does not confirm diagnoses or prescribe medications."
        }

gemini_service = GeminiService()
