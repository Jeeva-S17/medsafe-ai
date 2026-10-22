import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.config import DATABASE_URL

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Patients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        bmi REAL NOT NULL,
        glucose REAL NOT NULL,
        bp REAL NOT NULL,
        cholesterol REAL NOT NULL,
        heart_rate REAL NOT NULL,
        hba1c REAL NOT NULL,
        smoking INTEGER NOT NULL,
        symptoms TEXT,
        allergies TEXT,
        conditions TEXT,
        medications TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Patient Clinical History Table (Historical Visits & Lab Records)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_clinical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        visit_type TEXT NOT NULL,
        physician_name TEXT NOT NULL,
        systolic_bp REAL,
        diastolic_bp REAL,
        heart_rate REAL,
        glucose REAL,
        hba1c REAL,
        cholesterol REAL,
        bmi REAL,
        spo2 REAL,
        temperature REAL,
        clinical_notes TEXT,
        prescribed_medications TEXT,
        lab_findings TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # 3. Vital Readings Table (Stores verified patient historical vitals from clinical visits)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vital_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT NOT NULL,
        heart_rate REAL,
        spo2 REAL,
        temperature REAL,
        systolic_bp REAL,
        diastolic_bp REAL,
        is_simulated INTEGER DEFAULT 0,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)
    
    # 4. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        predicted_disease TEXT NOT NULL,
        confidence REAL NOT NULL,
        probabilities_json TEXT NOT NULL,
        features_json TEXT NOT NULL,
        shap_values_json TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)
    
    # 5. Prescriptions OCR Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_path TEXT,
        ocr_text TEXT,
        detected_medicines_json TEXT,
        confidence_score REAL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)
    
    # 6. Medication Interactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medication_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        medicines_checked TEXT,
        allergy_alerts_json TEXT,
        interactions_json TEXT,
        severity_level TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)
    
    # 7. AI Clinical Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        safety_level TEXT NOT NULL,
        report_json TEXT NOT NULL,
        pdf_path TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # 8. Nearby Pharmacies / Medical Shops Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pharmacies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pharmacy_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        distance_km REAL NOT NULL,
        rating REAL NOT NULL,
        reviews_count INTEGER DEFAULT 140,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        open_hours TEXT NOT NULL,
        delivery_time_mins INTEGER NOT NULL,
        delivery_fee REAL DEFAULT 0.0,
        is_open INTEGER DEFAULT 1
    )
    """)

    # 9. Medicine Catalog Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicine_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        category TEXT NOT NULL,
        disease_indication TEXT NOT NULL,
        price REAL NOT NULL,
        in_stock INTEGER DEFAULT 1,
        prescription_required INTEGER DEFAULT 1,
        safety_info TEXT,
        manufacturer TEXT
    )
    """)

    # 10. Medicine Delivery Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicine_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        patient_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        pharmacy_id TEXT NOT NULL,
        pharmacy_name TEXT NOT NULL,
        medicines_json TEXT NOT NULL,
        subtotal REAL NOT NULL,
        delivery_fee REAL NOT NULL,
        total_amount REAL NOT NULL,
        delivery_address TEXT NOT NULL,
        phone TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        delivery_type TEXT DEFAULT 'express',
        status TEXT DEFAULT 'Placed',
        tracking_partner_name TEXT,
        tracking_partner_phone TEXT,
        estimated_delivery_mins INTEGER DEFAULT 25,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    conn.commit()
    
    # Seed default sample patients
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    if cursor.fetchone()["cnt"] == 0:
        seed_patients(conn)
        
    # Seed patient clinical history
    cursor.execute("SELECT COUNT(*) as cnt FROM patient_clinical_history")
    if cursor.fetchone()["cnt"] == 0:
        seed_patient_history(conn)

    # Seed pharmacies
    cursor.execute("SELECT COUNT(*) as cnt FROM pharmacies")
    if cursor.fetchone()["cnt"] == 0:
        seed_pharmacies(conn)

    # Seed medicine catalog
    cursor.execute("SELECT COUNT(*) as cnt FROM medicine_catalog")
    if cursor.fetchone()["cnt"] == 0:
        seed_medicine_catalog(conn)

    # Seed initial sample vitals if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM vital_readings")
    if cursor.fetchone()["cnt"] == 0:
        seed_initial_vitals(conn)

    conn.close()

def seed_patients(conn):
    sample_patients = [
        (
            "P0001", "Arthur Pendelton", 58, "Male", 29.4, 168.0, 142.0, 235.0, 84.0, 7.8, 1,
            "Frequent urination, excessive thirst, blurred vision, mild fatigue",
            "Penicillin, Sulfa drugs",
            "Type 2 Diabetes Mellitus, Mild Hypertension",
            "Metformin 850mg, Lisinopril 10mg"
        ),
        (
            "P0002", "Elena Rostova", 46, "Female", 24.1, 102.0, 118.0, 190.0, 72.0, 5.4, 0,
            "Intermittent shortness of breath during exertion, wheezing in cold air",
            "Aspirin",
            "Mild Bronchial Asthma",
            "Albuterol inhaler, Fluticasone"
        ),
        (
            "P0003", "Marcus Vance", 64, "Male", 31.8, 145.0, 158.0, 260.0, 92.0, 6.9, 1,
            "Occasional chest tightness, palpitations upon stairs, bilateral ankle edema",
            "None reported",
            "Hypertension, Coronary Artery Disease, Hyperlipidemia",
            "Amlodipine 5mg, Atorvastatin 20mg, Aspirin 81mg"
        ),
        (
            "P0004", "Samuel Sterling", 62, "Male", 28.1, 108.0, 172.0, 215.0, 88.0, 5.6, 1,
            "Frequent morning occipital headaches, ringing in ears, episodic dizziness",
            "Sulfa drugs",
            "Essential Hypertension Stage 2",
            "Lisinopril 20mg, Hydrochlorothiazide 25mg"
        ),
        (
            "P0005", "Catherine Wells", 67, "Female", 29.8, 185.0, 168.0, 250.0, 86.0, 8.4, 0,
            "Persistent lower leg edema, fatigue, foamy urine, decreased appetite",
            "Penicillin",
            "Chronic Kidney Disease Stage 3, Diabetic Nephropathy",
            "Losartan 50mg, Furosemide 40mg, Insulin Glargine"
        ),
        (
            "P0006", "David Chen", 32, "Male", 22.4, 88.0, 115.0, 165.0, 68.0, 5.1, 0,
            "Asymptomatic routine wellness evaluation",
            "None reported",
            "No chronic conditions reported",
            "None"
        )
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO patients (patient_id, name, age, gender, bmi, glucose, bp, cholesterol, heart_rate, hba1c, smoking, symptoms, allergies, conditions, medications)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_patients)
    conn.commit()

def seed_patient_history(conn):
    """Seed comprehensive past clinical visits and laboratory timeline for each patient"""
    history_records = [
        # P0001 (Arthur Pendelton - Type 2 Diabetes & Mild HTN)
        ("P0001", "2025-11-14", "Initial Diagnostic Intake", "Dr. Sarah Mitchell, MD (Endocrinology)", 150.0, 92.0, 88.0, 192.0, 8.6, 248.0, 30.2, 98.0, 36.8, "Patient presented with polyuria, polydipsia, blurred vision. High fasting sugar and HbA1c 8.6%. Initiated Metformin 500mg titration.", "Metformin 500mg BID", "Fasting Glucose: 192 mg/dL; HbA1c: 8.6%; eGFR: 78 mL/min; Microalbuminuria trace"),
        ("P0001", "2026-02-18", "Quarterly Diabetic Follow-up", "Dr. Sarah Mitchell, MD (Endocrinology)", 146.0, 90.0, 86.0, 178.0, 8.1, 240.0, 29.8, 98.5, 36.7, "Improved glycemic compliance. Fasting sugar down to 178 mg/dL, HbA1c 8.1%. Mild hypertension persisted. Titrated Metformin to 850mg, added Lisinopril 10mg.", "Metformin 850mg BID, Lisinopril 10mg OD", "Fasting Glucose: 178 mg/dL; HbA1c: 8.1%; Serum Creatinine: 1.1 mg/dL"),
        ("P0001", "2026-06-20", "Mid-Year Comprehensive Review", "Dr. Sarah Mitchell, MD (Endocrinology)", 144.0, 88.0, 85.0, 172.0, 7.9, 238.0, 29.5, 98.0, 36.9, "Blood pressure stabilizing around 144/88. Glucose steady at 172 mg/dL. Retinal photo shows no diabetic retinopathy. Advised dietary discipline.", "Metformin 850mg BID, Lisinopril 10mg OD", "Fasting Glucose: 172 mg/dL; HbA1c: 7.9%; Total Cholesterol: 238 mg/dL; LDL: 154 mg/dL"),
        ("P0001", "2026-10-10", "Recent Follow-up & Lab Panel", "Dr. Robert Reynolds, MD (Internal Medicine)", 142.0, 86.0, 84.0, 168.0, 7.8, 235.0, 29.4, 98.2, 36.8, "Current baseline check: HbA1c 7.8%, Glucose 168 mg/dL. Patient reports mild afternoon fatigue. Prescriptions reaffirmed. Safe for home medicine delivery replenishment.", "Metformin 850mg BID, Lisinopril 10mg OD", "Fasting Glucose: 168 mg/dL; HbA1c: 7.8%; Serum Cholesterol: 235 mg/dL; SpO2: 98%"),

        # P0002 (Elena Rostova - Bronchial Asthma)
        ("P0002", "2026-01-12", "Pulmonology Consultation", "Dr. Angela Foster, MD (Pulmonology)", 120.0, 78.0, 78.0, 108.0, 5.5, 195.0, 24.3, 96.0, 36.6, "Recurrent nocturnal coughing and episodic expiratory wheezing triggered by winter air. Spirometry confirmed FEV1/FVC ratio 68%.", "Albuterol Inhaler 100mcg PRN, Fluticasone 125mcg BID", "FEV1: 72% predicted; Post-bronchodilator reversibility: +14% (280mL); SpO2: 96%"),
        ("P0002", "2026-05-15", "Asthma Control Review", "Dr. Angela Foster, MD (Pulmonology)", 118.0, 76.0, 74.0, 104.0, 5.4, 192.0, 24.2, 98.0, 36.7, "Significant improvement in daytime symptoms. Using rescue inhaler only 1-2 times weekly. Maintained on inhaled corticosteroid.", "Albuterol Inhaler 100mcg PRN, Fluticasone 125mcg BID", "FEV1: 84% predicted; SpO2: 98%; Normal ECG"),
        ("P0002", "2026-09-28", "Routine Pulmonary Follow-up", "Dr. Angela Foster, MD (Pulmonology)", 118.0, 75.0, 72.0, 102.0, 5.4, 190.0, 24.1, 98.5, 36.8, "Asthma well controlled under GINA step 2 guidelines. Chest clear bilaterally on auscultation. Refill authorized for inhaler.", "Albuterol Inhaler 100mcg, Fluticasone 125mcg", "SpO2: 98.5%; Peak Expiratory Flow: 420 L/min; Normal vitals"),

        # P0003 (Marcus Vance - Coronary Heart Disease & HTN)
        ("P0003", "2025-10-05", "Cardiology Workup", "Dr. Kenneth Cole, MD (Cardiology)", 165.0, 98.0, 96.0, 155.0, 7.2, 280.0, 32.2, 96.5, 36.7, "Patient reported exertional chest tightness (CCS Class II) and ankle swelling. Stress ECHO showed anterolateral hypokinesis. Started dual therapy.", "Amlodipine 5mg OD, Atorvastatin 40mg OD, Aspirin 81mg OD", "Total Cholesterol: 280 mg/dL; LDL: 185 mg/dL; Triglycerides: 240 mg/dL; Troponin negative"),
        ("P0003", "2026-03-12", "Post-Angiogram Clinical Follow-up", "Dr. Kenneth Cole, MD (Cardiology)", 160.0, 94.0, 94.0, 148.0, 7.0, 268.0, 32.0, 97.0, 36.8, "Blood pressure improving. Ankle edema reduced. Lipid profile trending downward on high-intensity statin. Tolerating aspirin well.", "Amlodipine 5mg OD, Atorvastatin 20mg OD, Aspirin 81mg OD", "Total Cholesterol: 268 mg/dL; LDL: 165 mg/dL; EF: 52%"),
        ("P0003", "2026-08-22", "Recent Cardiology Review", "Dr. Kenneth Cole, MD (Cardiology)", 158.0, 92.0, 92.0, 145.0, 6.9, 260.0, 31.8, 97.5, 36.8, "Stable angina without acute episodes. Vitals: BP 158/92, HR 92 bpm. Continue cardioprotective regimen and lipid monitoring.", "Amlodipine 5mg OD, Atorvastatin 20mg OD, Aspirin 81mg OD", "Total Cholesterol: 260 mg/dL; LDL: 158 mg/dL; Serum Creatinine: 1.2 mg/dL"),

        # P0004 (Samuel Sterling - Essential Hypertension)
        ("P0004", "2026-02-10", "Hypertension Clinic Visit", "Dr. David Patel, MD (Cardiovascular)", 182.0, 104.0, 92.0, 114.0, 5.8, 225.0, 28.5, 98.0, 36.7, "Patient complained of morning throbbing headaches and lightheadedness. Stage 2 hypertension confirmed on repeated measurements.", "Lisinopril 20mg OD, Hydrochlorothiazide 25mg OD", "Serum Potassium: 4.2 mEq/L; BUN: 18 mg/dL; ECG: Left ventricular hypertrophy"),
        ("P0004", "2026-06-14", "BP Stabilization Check", "Dr. David Patel, MD (Cardiovascular)", 175.0, 98.0, 90.0, 110.0, 5.7, 218.0, 28.3, 98.2, 36.8, "Headaches subsided. Blood pressure decreased from 182/104 to 175/98 mmHg. Continue sodium-restricted diet and medication adherence.", "Lisinopril 20mg OD, Hydrochlorothiazide 25mg OD", "Electrolytes normal; Potassium: 4.0 mEq/L; eGFR: 84 mL/min"),
        ("P0004", "2026-09-30", "Recent Clinical Evaluation", "Dr. David Patel, MD (Cardiovascular)", 172.0, 96.0, 88.0, 108.0, 5.6, 215.0, 28.1, 98.4, 36.7, "BP 172/96 mmHg. Patient reports good energy levels. Medication refill approved for delivery. Regular home BP monitoring advised.", "Lisinopril 20mg OD, Hydrochlorothiazide 25mg OD", "Serum Cholesterol: 215 mg/dL; Glucose: 108 mg/dL; Normal renal panel"),

        # P0005 (Catherine Wells - Chronic Kidney Disease)
        ("P0005", "2025-12-08", "Nephrology Consultation", "Dr. Patricia Gomez, MD (Nephrology)", 174.0, 100.0, 90.0, 198.0, 8.9, 265.0, 30.2, 97.0, 36.6, "Bilateral lower extremity pitting edema (2+), foamy urine. Lab confirmed proteinuria and elevated serum creatinine 2.1 mg/dL.", "Losartan 50mg OD, Furosemide 40mg OD, Insulin Glargine 14U", "eGFR: 38 mL/min (CKD Stage 3b); Urine Albumin/Creatinine Ratio: 420 mg/g; K+: 4.6 mEq/L"),
        ("P0005", "2026-04-18", "Renal Disease Monitoring", "Dr. Patricia Gomez, MD (Nephrology)", 170.0, 96.0, 88.0, 190.0, 8.6, 255.0, 30.0, 97.2, 36.8, "Edema stabilized with loop diuretic. Blood pressure 170/96. Strict glycemic and potassium monitoring maintained.", "Losartan 50mg OD, Furosemide 40mg OD, Insulin Glargine 16U", "eGFR: 41 mL/min; Serum Creatinine: 1.9 mg/dL; HbA1c: 8.6%"),
        ("P0005", "2026-09-15", "Recent Nephrology Follow-up", "Dr. Patricia Gomez, MD (Nephrology)", 168.0, 94.0, 86.0, 185.0, 8.4, 250.0, 29.8, 97.5, 36.7, "CKD Stage 3 parameters stable. eGFR 42 mL/min. Patient adhering to renal dietary guidelines. Home delivery recommended for continuous medication supply.", "Losartan 50mg OD, Furosemide 40mg OD, Insulin Glargine", "eGFR: 42 mL/min; Glucose: 185 mg/dL; HbA1c: 8.4%; K+: 4.4 mEq/L"),

        # P0006 (David Chen - Normal / Low Risk)
        ("P0006", "2025-10-10", "Annual Occupational Physical", "Dr. Marcus Brody, MD (Family Medicine)", 116.0, 74.0, 70.0, 90.0, 5.2, 168.0, 22.5, 99.0, 36.8, "Routine annual physical examination. Patient is active, non-smoker, runs 5km 3x weekly. All systems normal.", "None", "Fasting Glucose: 90 mg/dL; HbA1c: 5.2%; Total Cholesterol: 168 mg/dL; CBC normal"),
        ("P0006", "2026-08-14", "Routine Wellness Screening", "Dr. Marcus Brody, MD (Family Medicine)", 115.0, 72.0, 68.0, 88.0, 5.1, 165.0, 22.4, 99.2, 36.7, "Excellent physical health. Blood pressure 115/72, resting HR 68 bpm, HbA1c 5.1%. Recommended standard preventive care.", "None", "Fasting Glucose: 88 mg/dL; HbA1c: 5.1%; Lipid Panel: Optimal; SpO2: 99.2%")
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO patient_clinical_history (patient_id, visit_date, visit_type, physician_name, systolic_bp, diastolic_bp, heart_rate, glucose, hba1c, cholesterol, bmi, spo2, temperature, clinical_notes, prescribed_medications, lab_findings)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, history_records)
    conn.commit()

def seed_pharmacies(conn):
    """Seed verified nearby medical stores and pharmacies"""
    pharmacies = [
        ("PHARM_01", "Apollo Pharmacy 24x7", 0.8, 4.9, 342, "No. 14, Main Road, Anna Nagar (Near City Hospital)", "+91 98401 55210", "Open 24 Hours", 25, 0.0, 1),
        ("PHARM_02", "MedPlus Healthcare & Chemist", 1.4, 4.8, 218, "Plot 82, 2nd Avenue, Central Market Complex", "+91 98402 33419", "Open until 11:30 PM", 30, 20.0, 1),
        ("PHARM_03", "Wellness Forever Life Care", 2.2, 4.9, 412, "Shop 4, Greenfield Square, Metro Station Exit 2", "+91 98403 77890", "Open 24 Hours", 35, 0.0, 1),
        ("PHARM_04", "Sri Venkateswara Medicals & Surgical", 2.9, 4.7, 185, "Door 55, High Street, Gandhi Circle", "+91 98404 11200", "Open until 10:30 PM", 40, 15.0, 1),
        ("PHARM_05", "Netmeds Express Fulfillment Hub", 3.5, 4.8, 560, "Industrial Estate, Logistics Block B-4", "+91 98405 88991", "Open 24 Hours", 45, 0.0, 1)
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO pharmacies (pharmacy_id, name, distance_km, rating, reviews_count, address, phone, open_hours, delivery_time_mins, delivery_fee, is_open)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pharmacies)
    conn.commit()

def seed_medicine_catalog(conn):
    """Seed comprehensive medicine catalog linked to clinical indications"""
    catalog = [
        # Diabetes
        ("MED_D01", "Metformin HCl 850mg", "1 tablet twice daily with meals", "Chronic Prescription", "Type 2 Diabetes Mellitus", 65.0, 1, 1, "First-line biguanide for glycemic control. Take with food.", "Sun Pharma Ltd."),
        ("MED_D02", "Metformin HCl 500mg Extended Release", "1 tablet daily evening", "Chronic Prescription", "Type 2 Diabetes Mellitus", 45.0, 1, 1, "Reduces GI irritation, sustained glucose release.", "Cipla Ltd."),
        ("MED_D03", "Empagliflozin (Jardiance) 10mg", "1 tablet once daily morning", "Chronic Prescription", "Type 2 Diabetes & Cardioprotection", 185.0, 1, 1, "SGLT2 inhibitor; promotes urinary glucose excretion.", "Boehringer Ingelheim"),
        ("MED_D04", "Glimepiride 1mg", "1 tablet daily with breakfast", "Chronic Prescription", "Type 2 Diabetes Mellitus", 42.0, 1, 1, "Sulfonylurea; stimulates pancreatic insulin secretion.", "Sanofi India"),
        ("MED_D05", "Accu-Chek Blood Glucose Test Strips (50s)", "As directed for home glucose monitoring", "Medical Supplies", "Diabetes Self-Monitoring", 420.0, 1, 0, "High accuracy blood glucose test strips for glucometer.", "Roche Diabetes Care"),

        # Hypertension & Cardiovascular
        ("MED_H01", "Lisinopril 10mg", "1 tablet once daily morning", "Chronic Prescription", "Hypertension & Kidney Protection", 85.0, 1, 1, "ACE inhibitor; relaxes blood vessels, protects kidneys.", "Lupin Pharmaceuticals"),
        ("MED_H02", "Lisinopril 20mg", "1 tablet once daily morning", "Chronic Prescription", "Stage 2 Essential Hypertension", 95.0, 1, 1, "Potent ACE inhibitor for Stage 2 hypertension control.", "Lupin Pharmaceuticals"),
        ("MED_H03", "Amlodipine Besylate 5mg", "1 tablet once daily morning", "Chronic Prescription", "Hypertension & Angina", 68.0, 1, 1, "Calcium channel blocker; relieves peripheral resistance.", "Dr. Reddy's Labs"),
        ("MED_H04", "Hydrochlorothiazide 25mg", "1 tablet daily morning", "Chronic Prescription", "Hypertension Diuretic", 48.0, 1, 1, "Thiazide diuretic; eliminates excess sodium and fluid.", "Torrent Pharma"),
        ("MED_H05", "Atorvastatin 20mg", "1 tablet at bedtime", "Chronic Prescription", "Coronary Heart Disease & Hyperlipidemia", 125.0, 1, 1, "HMG-CoA reductase inhibitor; lowers LDL cholesterol.", "Pfizer Healthcare"),
        ("MED_H06", "Aspirin 81mg (Low-Dose Cardio)", "1 tablet once daily after meal", "Chronic Prescription", "Cardiovascular Thromboprophylaxis", 35.0, 1, 1, "Antiplatelet therapy for coronary prevention.", "Bayer India"),
        ("MED_H07", "Metoprolol Succinate ER 25mg", "1 tablet once daily", "Chronic Prescription", "Angina, Arrhythmia & Hypertension", 82.0, 1, 1, "Cardioselective beta-1 blocker; regulates heart rate.", "AstraZeneca"),
        ("MED_H08", "Digital Blood Pressure Monitor (Omron)", "For twice daily home BP logging", "Medical Devices", "Hypertension Monitoring", 1350.0, 1, 0, "Clinically validated upper-arm digital BP cuff.", "Omron Healthcare"),

        # Asthma & Respiratory
        ("MED_A01", "Albuterol (Salbutamol) Inhaler 100mcg", "1-2 puffs every 4-6 hours PRN for shortness of breath", "Respiratory Inhaler", "Bronchial Asthma & Wheezing", 165.0, 1, 1, "Fast-acting bronchodilator for immediate bronchospasm relief.", "Cipla Ltd."),
        ("MED_A02", "Fluticasone Propionate Inhaler 125mcg", "1 puff twice daily regular maintenance", "Respiratory Inhaler", "Asthma Maintenance Anti-inflammatory", 330.0, 1, 1, "Inhaled corticosteroid; reduces chronic airway swelling.", "GlaxoSmithKline"),
        ("MED_A03", "Montelukast Sodium 10mg", "1 tablet once daily at bedtime", "Respiratory Oral", "Allergic Asthma & Rhinitis", 115.0, 1, 1, "Leukotriene receptor antagonist; prevents night symptoms.", "Sun Pharma Ltd."),

        # Kidney Care
        ("MED_K01", "Losartan Potassium 50mg", "1 tablet once daily", "Chronic Prescription", "Chronic Kidney Disease & HTN", 85.0, 1, 1, "Angiotensin II receptor blocker; reduces glomerular pressure.", "Zydus Lifesciences"),
        ("MED_K02", "Furosemide 40mg (Lasix)", "1 tablet morning with water", "Chronic Prescription", "Fluid Overload & Peripheral Edema", 42.0, 1, 1, "Loop diuretic for edema and kidney filtration support.", "Sanofi India"),
        ("MED_K03", "Calcium Acetate 667mg", "1 tablet with each main meal", "Renal Supplement", "Phosphate Binder in CKD", 130.0, 1, 1, "Binds dietary phosphate to prevent hyperphosphatemia.", "Alkem Laboratories"),

        # General Supportive & OTC Essentials
        ("MED_G01", "Paracetamol (Dolo) 650mg", "1 tablet every 6 hours PRN for fever or pain", "General OTC", "Analgesic & Antipyretic", 32.0, 1, 0, "Relieves fever, mild to moderate aches and pain.", "Micro Labs Ltd."),
        ("MED_G02", "Vitamin C (Limcee) 500mg Chewable", "1 chewable tablet daily", "Vitamins & Wellness", "Immune Defense", 65.0, 1, 0, "Antioxidant support for immune health and healing.", "Abbott Healthcare"),
        ("MED_G03", "Vitamin D3 60,000 IU Capsule", "1 capsule once weekly with milk", "Vitamins & Wellness", "Bone & Metabolic Support", 110.0, 1, 0, "High potency cholecalciferol for vitamin D deficiency.", "Cadila Pharma"),
        ("MED_G04", "Becozinc Multivitamin with Zinc", "1 capsule daily after breakfast", "Vitamins & Wellness", "Nutritional Recovery", 145.0, 1, 0, "Complete B-complex with zinc and ascorbic acid.", "Dr. Reddy's Labs"),
        ("MED_G05", "Electral ORS Oral Rehydration (Pack of 5)", "Dissolve 1 sachet in 1 liter clean water", "General OTC", "Electrolyte & Fluid Replenishment", 35.0, 1, 0, "WHO formula oral rehydration salts for dehydration.", "FDC Ltd.")
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO medicine_catalog (medicine_id, name, dosage, category, disease_indication, price, in_stock, prescription_required, safety_info, manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, catalog)
    conn.commit()

def seed_initial_vitals(conn):
    """Seed baseline verified previous vitals from clinical intake for each patient"""
    vitals_data = [
        ("P0001", "clinical_record", 84.0, 98.2, 36.8, 142.0, 86.0, 0),
        ("P0001", "clinical_record", 85.0, 98.0, 36.9, 144.0, 88.0, 0),
        ("P0001", "clinical_record", 86.0, 98.5, 36.7, 146.0, 90.0, 0),
        ("P0001", "clinical_record", 88.0, 98.0, 36.8, 150.0, 92.0, 0),
        ("P0002", "clinical_record", 72.0, 98.5, 36.8, 118.0, 75.0, 0),
        ("P0003", "clinical_record", 92.0, 97.5, 36.8, 158.0, 92.0, 0),
        ("P0004", "clinical_record", 88.0, 98.4, 36.7, 172.0, 96.0, 0),
        ("P0005", "clinical_record", 86.0, 97.5, 36.7, 168.0, 94.0, 0),
        ("P0006", "clinical_record", 68.0, 99.2, 36.7, 115.0, 72.0, 0)
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO vital_readings (patient_id, source, heart_rate, spo2, temperature, systolic_bp, diastolic_bp, is_simulated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, vitals_data)
    conn.commit()

# ================= QUERIES & HELPERS =================

def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_patients() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY patient_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_patient(patient_data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO patients (patient_id, name, age, gender, bmi, glucose, bp, cholesterol, heart_rate, hba1c, smoking, symptoms, allergies, conditions, medications, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(patient_id) DO UPDATE SET
        name=excluded.name,
        age=excluded.age,
        gender=excluded.gender,
        bmi=excluded.bmi,
        glucose=excluded.glucose,
        bp=excluded.bp,
        cholesterol=excluded.cholesterol,
        heart_rate=excluded.heart_rate,
        hba1c=excluded.hba1c,
        smoking=excluded.smoking,
        symptoms=excluded.symptoms,
        allergies=excluded.allergies,
        conditions=excluded.conditions,
        medications=excluded.medications,
        updated_at=CURRENT_TIMESTAMP
    """, (
        patient_data["patient_id"],
        patient_data.get("name", "Unnamed Patient"),
        patient_data["age"],
        patient_data["gender"],
        patient_data["bmi"],
        patient_data["glucose"],
        patient_data["bp"],
        patient_data["cholesterol"],
        patient_data["heart_rate"],
        patient_data["hba1c"],
        1 if patient_data.get("smoking") in [1, True, "1", "yes", "Yes"] else 0,
        patient_data.get("symptoms", ""),
        patient_data.get("allergies", ""),
        patient_data.get("conditions", ""),
        patient_data.get("medications", "")
    ))
    conn.commit()
    conn.close()

def record_vitals(reading: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO vital_readings (patient_id, source, heart_rate, spo2, temperature, systolic_bp, diastolic_bp, is_simulated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        reading["patient_id"],
        reading.get("source", "clinical_record"),
        reading.get("heart_rate"),
        reading.get("spo2"),
        reading.get("temperature"),
        reading.get("systolic_bp"),
        reading.get("diastolic_bp"),
        1 if reading.get("is_simulated", False) else 0
    ))
    conn.commit()
    conn.close()

def get_patient_vitals_history(patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM vital_readings WHERE patient_id = ? ORDER BY id DESC LIMIT ?
    """, (patient_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def get_patient_clinical_history(patient_id: str) -> List[Dict[str, Any]]:
    """Retrieve full chronological visit history and lab trends for patient"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM patient_clinical_history WHERE patient_id = ? ORDER BY visit_date ASC
    """, (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_nearby_pharmacies() -> List[Dict[str, Any]]:
    """Retrieve verified medical shops nearby sorted by proximity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pharmacies WHERE is_open = 1 ORDER BY distance_km ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_medicines_for_patient(patient_id: str) -> Dict[str, Any]:
    """Retrieve prescribed & recommended medicines matched to patient's previous data"""
    patient = get_patient(patient_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicine_catalog WHERE in_stock = 1")
    all_meds = [dict(r) for r in cursor.fetchall()]
    conn.close()

    prescribed_list = []
    supportive_list = []
    otc_list = []

    patient_conds = (patient.get("conditions", "") + " " + patient.get("medications", "")).lower() if patient else ""

    for med in all_meds:
        cat = med.get("category", "")
        ind = med.get("disease_indication", "").lower()
        name = med.get("name", "").lower()

        # Check if matched to patient's chronic condition or medications
        if any(term in patient_conds for term in ["diabet", "metformin"]) and ("diabet" in ind or "glucose" in name or "metformin" in name):
            prescribed_list.append(med)
        elif any(term in patient_conds for term in ["hypertens", "bp", "lisinopril"]) and ("hypertens" in ind or "lisinopril" in name or "amlodipine" in name):
            prescribed_list.append(med)
        elif any(term in patient_conds for term in ["heart", "coronary", "angina"]) and ("coronary" in ind or "angina" in ind or "aspirin" in name or "atorvastatin" in name):
            prescribed_list.append(med)
        elif any(term in patient_conds for term in ["asthma", "bronchial", "inhaler"]) and ("asthma" in ind or "albuterol" in name or "inhaler" in name):
            prescribed_list.append(med)
        elif any(term in patient_conds for term in ["kidney", "nephro", "ckd"]) and ("kidney" in ind or "ckd" in ind or "losartan" in name or "furosemide" in name):
            prescribed_list.append(med)
        elif "medical" in cat or "device" in cat or "strip" in name or "monitor" in name:
            supportive_list.append(med)
        else:
            otc_list.append(med)

    # Avoid empty list
    if not prescribed_list:
        prescribed_list = [m for m in all_meds if m["prescription_required"] == 1][:3]

    return {
        "patient_id": patient_id,
        "patient_name": patient.get("name", "Patient") if patient else "Patient",
        "allergies": patient.get("allergies", "None") if patient else "None",
        "prescribed_medications": prescribed_list,
        "supportive_supplies": supportive_list[:4],
        "general_otc": otc_list[:5]
    }

def create_medicine_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store new delivery order in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    order_id = f"MED-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    
    partner_names = ["Karthik R. (Hero Electric)", "Senthil Kumar (TVS iQube)", "Arun Prasad (Ather 450X)", "Manoj K. (Honda Activa)"]
    import random
    partner = random.choice(partner_names)
    partner_phone = f"+91 {random.randint(97000, 99999)} {random.randint(10000, 99999)}"

    cursor.execute("""
    INSERT INTO medicine_orders (
        order_id, patient_id, patient_name, pharmacy_id, pharmacy_name,
        medicines_json, subtotal, delivery_fee, total_amount, delivery_address,
        phone, payment_method, delivery_type, status, tracking_partner_name,
        tracking_partner_phone, estimated_delivery_mins
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        order_data["patient_id"],
        order_data.get("patient_name", "Patient"),
        order_data["pharmacy_id"],
        order_data.get("pharmacy_name", "Nearby Pharmacy"),
        json.dumps(order_data.get("items", [])),
        float(order_data.get("subtotal", 0.0)),
        float(order_data.get("delivery_fee", 0.0)),
        float(order_data.get("total_amount", 0.0)),
        order_data.get("delivery_address", "Home Address"),
        order_data.get("phone", "+91 98401 00000"),
        order_data.get("payment_method", "Cash on Delivery"),
        order_data.get("delivery_type", "express"),
        "Order Transmitted",
        partner,
        partner_phone,
        int(order_data.get("estimated_delivery_mins", 25))
    ))
    conn.commit()
    conn.close()

    return get_order_by_id(order_id)

def get_patient_orders(patient_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicine_orders WHERE patient_id = ? ORDER BY id DESC", (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d["items"] = json.loads(d.get("medicines_json", "[]"))
        res.append(d)
    return res

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicine_orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["items"] = json.loads(d.get("medicines_json", "[]"))
    return d

def advance_order_status(order_id: str, next_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Advance order delivery status for live demonstration"""
    stages = [
        "Order Transmitted",
        "Pharmacist Confirmed & Packed",
        "Delivery Partner Dispatched",
        "Out for Doorstep Delivery",
        "Delivered Successfully"
    ]
    current = get_order_by_id(order_id)
    if not current:
        return None
    
    cur_status = current.get("status", stages[0])
    if next_status:
        target = next_status
    else:
        try:
            idx = stages.index(cur_status)
            target = stages[min(idx + 1, len(stages) - 1)]
        except ValueError:
            target = stages[1]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE medicine_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?
    """, (target, order_id))
    conn.commit()
    conn.close()
    return get_order_by_id(order_id)
