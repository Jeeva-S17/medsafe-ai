# MediSafe AI — Clinical Decision Support & Medicine Delivery System

> **AI-Powered Disease Risk Classification, Medication Safety Decision Support & Doorstep Medicine Delivery from Nearby Medical Stores (Hardware-Free, Purely Based on Patient Previous Medical Data)**

![MediSafe AI](https://img.shields.io/badge/System-Clinical_Decision_Support-0d9488?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![Scikit-Learn](https://img.shields.io/badge/ML-Random_Forest-F7931E?style=for-the-badge&logo=scikit-learn)
![SHAP](https://img.shields.io/badge/XAI-TreeExplainer-blue?style=for-the-badge)
![CrewAI](https://img.shields.io/badge/Multi--Agent-CrewAI-8b5cf6?style=for-the-badge)
![Delivery](https://img.shields.io/badge/Pharmacy-Express_Delivery-10b981?style=for-the-badge)

---

## Important Clinical Decision Support Disclaimer

* **Prototype Notice:** MediSafe AI is strictly an algorithmic clinical decision-support and medication management prototype.
* **No Autonomous Diagnosis:** AI model outputs reflect calibrated multi-class probabilistic classifications, NOT confirmed medical diagnoses.
* **No Medication Authority:** The system assists in medication reconciliation, allergy checks, and ordering refills based on previous doctor prescriptions.
* **Professional Verification Mandatory:** All outputs require independent review by licensed physicians and pharmacists before clinical action.
* **Data Integrity:** Operates purely on verified historical patient medical records and diagnostic EHR encounters.

---

## Purely Patient Previous Data Driven (Hardware-Free Architecture)

This system operates **100% on the patient's previous medical encounters, historical vitals, and laboratory diagnostics**. There is **NO hardware requirement** (all simulated sensors, mock IoT streaming, and hardware probes have been removed).

### Complete Architecture Flow

```
Patient Previous Medical Data & Historical Encounters
          ↓
   Data Validation
          ↓
Random Forest Classifier (10 Features)
          ↓
Calibrated Probabilities & Disease Rank
          ↓
Explainable AI (SHAP TreeExplainer)
          ↓
┌───────────────────────────────────────────────┐
│ Prescription OCR     |  Patient History & EHR │
│ Medicine Detection   |  Documented Allergies  │
└───────────────────────┬───────────────────────┘
                        ↓
Drug-Drug Interaction & Cross-Allergy Verification
                        ↓
OpenFDA Adverse Event Surveillance (FAERS)
                        ↓
CrewAI Multi-Agent Pipeline (5 Specialized Agents)
                        ↓
Gemini AI Clinical Reasoning Synthesis
                        ↓
Final Structured Clinical Safety Report (LOW / MODERATE / HIGH / URGENT)
                        ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PRESCRIBED MEDICINE SHOWCASE & DOORSTEP PHARMACY DELIVERY              │
│ ├─ Prescribed chronic medications matched to diagnosis & safety        │
│ ├─ 5 Verified Neighborhood Medical Shops (Distance, Ratings, ETA)      │
│ ├─ Interactive cart, checkout & delivery details                       │
│ └─ Live 5-Stage Order Tracking (Dispatched, Partner details & Invoice) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 12 Interactive Web Sections

1. **Dashboard:** Executive clinical overview, active patient banner, previous clinical baseline vitals, probability bars, rapid safety checklist, and quick link to order medicines.
2. **Patient Intake:** Comprehensive intake form validating Age (0-130), BMI, Fasting Glucose, BP, Cholesterol, Heart Rate, HbA1c, Smoking status, Symptoms, Allergies, Pre-existing conditions, and active medications.
3. **Medical History & EHR:** Full longitudinal visit history across previous encounters (dates, physician notes, recorded vitals, lab findings, and prescriptions) with multi-visit trajectory charts.
4. **Medicine Delivery & Nearby Pharmacies (NEW):**
   - **Medicine Showcase:** Prescribed chronic medications matched to patient's previous diagnosis & allergies with clear dosage instructions and prices.
   - **Supportive Care & OTC:** Quick add for glucose test strips, digital BP cuffs, electrolytes, and vitamins.
   - **Nearby Medical Shops:** Real-time selection of 5 verified local pharmacies (Apollo Pharmacy, MedPlus, Wellness Forever, etc.) with live distance, ratings, and delivery estimates.
   - **Checkout & Order Placement:** Recipient details, delivery address, express slot, payment methods (COD, UPI, Card, Insurance).
   - **Live Delivery Tracking:** 5-milestone animated stepper, assigned delivery partner with phone number, interactive status advancement demo, and printable PDF-ready delivery invoice.
5. **Disease Prediction:** Random Forest multi-class prediction strictly evaluated on the 10 verified clinical features.
6. **Explainable AI (SHAP):** Interactive TreeExplainer waterfall and feature attribution ranking showing exact positive/negative contributions and summary explanations.
7. **Prescription OCR:** Drag-and-drop file upload (JPG, PNG, PDF) to extract raw text and detect medication names, strengths, dosages, and regimens.
8. **Medication Safety:** Cross-checks active medications and OCR detected prescriptions against patient allergies and clinical drug-drug interaction matrix.
9. **FDA Safety Information:** Live query interface to the OpenFDA FAERS adverse event database.
10. **CrewAI Multi-Agent System:** Visualizes reasoning steps across all 5 specialized agents.
11. **Final Safety Report:** Synthesized clinical summary with Safety Level classification (`LOW`, `MODERATE`, `HIGH`, `URGENT`), risk factors, and structured markdown.
12. **Visuals & PDF Export / System Status:** Live Matplotlib charts gallery, one-click PDF generation, and verified live connection status for all subsystems.

---

## Quick Start / Run Instructions

### 1. Prerequisites
- Python 3.11 or 3.12 (A pre-configured `.venv` is included)

### 2. Launch the Web Dashboard
In PowerShell:
```powershell
# Run backend server (FastAPI and Unified Web Application)
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in Browser
Navigate to:
```
http://localhost:8000
```

---

## Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the MediSafe AI Web Dashboard |
| `GET` | `/api/patient/{patient_id}/history` | Retrieves patient's previous clinical visits and EHR lab records |
| `GET` | `/api/pharmacy/medicines?patient_id=...` | Retrieves prescribed & supportive medicines matched to patient diagnosis |
| `GET` | `/api/pharmacy/nearby` | Lists verified neighborhood medical shops with distance & delivery estimates |
| `POST` | `/api/pharmacy/order` | Places a new medicine delivery order |
| `GET` | `/api/pharmacy/orders?patient_id=...` | Lists past and active delivery orders for patient |
| `GET` | `/api/pharmacy/orders/{order_id}` | Live tracking details and invoice data for order |
| `POST` | `/api/pharmacy/orders/{order_id}/advance` | Advances order delivery status (interactive demo milestone) |
| `POST` | `/predict` | Evaluates Random Forest disease probabilities |
| `POST` | `/api/xai/explain` | Computes TreeExplainer SHAP feature attributions |
| `POST` | `/api/prescription/upload` | Uploads JPG/PNG/PDF for OCR & entity extraction |
| `POST` | `/api/medication/check` | Checks drug-drug interactions & allergies |
| `GET` | `/api/fda/search?medicine=...` | Queries OpenFDA FAERS adverse-event data |
| `POST` | `/api/analysis/multi-agent` | Runs 5-agent CrewAI pipeline |
| `POST` | `/api/analysis/final-safety-report` | Generates Gemini clinical decision report |
| `GET` | `/api/report/pdf/{patient_id}` | Downloads formal ReportLab PDF report |
| `GET` | `/api/system/status` | Live health checks across all subsystems |

---

## Environment Variables (Optional)

Create a `.env` file in the root directory if you wish to connect directly to external cloud APIs:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
FDA_API_KEY=your_openfda_api_key_here
```
*Note: If no Google API key is configured, MediSafe AI automatically utilizes its internal clinical decision-support reasoning engine so all features remain 100% operational offline.*
