import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from backend.config import MODELS_DIR

MODEL_PATH = MODELS_DIR / "random_forest_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.joblib"

# The EXACT 10 features specified
FEATURES = [
    "Age",
    "Gender",
    "BMI",
    "Glucose",
    "BP",
    "Cholesterol",
    "Heart_Rate",
    "HbA1c",
    "Smoking",
    "Symptoms"
]

DISEASES = [
    "Type 2 Diabetes Mellitus",
    "Essential Hypertension",
    "Coronary Heart Disease",
    "Bronchial Asthma",
    "Chronic Kidney Disease",
    "Low Risk / Normal Evaluation"
]

class RandomForestService:
    def __init__(self):
        self.model: RandomForestClassifier = None
        self.gender_encoder: LabelEncoder = None
        self.symptom_keywords = {
            "diabetes": ["thirst", "urination", "hunger", "blurred", "fatigue", "sweet", "weight loss"],
            "hypertension": ["headache", "dizziness", "flush", "nosebleed", "pounding", "ringing"],
            "heart": ["chest pain", "tightness", "palpitation", "angina", "shortness of breath", "edema", "ankle"],
            "asthma": ["wheeze", "wheezing", "cough", "breathless", "cold air", "chest constriction"],
            "kidney": ["foamy urine", "flank pain", "swelling", "nausea", "metallic taste", "protein"]
        }
        self.load_or_train_model()

    def _encode_symptoms(self, symptoms_str: str) -> float:
        """Convert symptoms string into clinical symptom score based on keyword match density"""
        if not symptoms_str or not isinstance(symptoms_str, str):
            return 0.0
        text = symptoms_str.lower()
        score = 0.0
        for category, kw_list in self.symptom_keywords.items():
            for kw in kw_list:
                if kw in text:
                    score += 1.0
        return min(score, 10.0)

    def _generate_training_dataset(self, n_samples: int = 1200) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate a clinically coherent synthetic dataset based on established medical guidelines"""
        np.random.seed(42)
        
        ages = np.random.randint(20, 85, n_samples)
        genders = np.random.choice(["Male", "Female"], n_samples)
        bmis = np.random.uniform(18.5, 42.0, n_samples)
        glucoses = np.random.uniform(70.0, 320.0, n_samples)
        bps = np.random.uniform(90.0, 200.0, n_samples)
        cholesterols = np.random.uniform(130.0, 340.0, n_samples)
        heart_rates = np.random.uniform(55.0, 120.0, n_samples)
        hba1cs = np.random.uniform(4.2, 12.5, n_samples)
        smokings = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
        symptom_scores = np.random.uniform(0.0, 8.0, n_samples)
        
        labels = []
        for i in range(n_samples):
            # Clinical scoring rules
            d_score = (glucoses[i] > 140) * 3.5 + (hba1cs[i] > 6.5) * 4.5 + (bmis[i] > 30) * 1.5
            h_score = (bps[i] > 140) * 4.0 + (ages[i] > 55) * 1.5 + (smokings[i] == 1) * 1.5
            c_score = (cholesterols[i] > 240) * 3.0 + (bps[i] > 150) * 2.0 + (heart_rates[i] > 90) * 2.0 + (smokings[i] == 1) * 2.0 + (ages[i] > 60) * 2.0
            a_score = (heart_rates[i] > 95) * 2.0 + (symptom_scores[i] > 4.0) * 3.5
            k_score = (bps[i] > 160) * 2.5 + (hba1cs[i] > 8.0) * 2.5 + (cholesterols[i] > 260) * 2.0
            
            scores = {
                "Type 2 Diabetes Mellitus": d_score,
                "Essential Hypertension": h_score,
                "Coronary Heart Disease": c_score,
                "Bronchial Asthma": a_score,
                "Chronic Kidney Disease": k_score
            }
            max_disease = max(scores, key=scores.get)
            if scores[max_disease] < 4.0:
                labels.append("Low Risk / Normal Evaluation")
            else:
                labels.append(max_disease)

        gender_encoded = [1 if g == "Male" else 0 for g in genders]
        df = pd.DataFrame({
            "Age": ages,
            "Gender": gender_encoded,
            "BMI": bmis,
            "Glucose": glucoses,
            "BP": bps,
            "Cholesterol": cholesterols,
            "Heart_Rate": heart_rates,
            "HbA1c": hba1cs,
            "Smoking": smokings,
            "Symptoms": symptom_scores
        })
        return df, pd.Series(labels)

    def load_or_train_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(METADATA_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                meta = joblib.load(METADATA_PATH)
                self.gender_encoder = meta["gender_encoder"]
                return
            except Exception as e:
                print(f"Warning: Failed to load saved model: {e}. Retraining.")
        
        # Train new model
        X, y = self._generate_training_dataset()
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=4,
            random_state=42,
            class_weight="balanced"
        )
        self.model.fit(X, y)
        
        # Save model
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump({"gender_encoder": None, "features": FEATURES, "classes": list(self.model.classes_)}, METADATA_PATH)

    def prepare_feature_vector(self, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """Construct feature vector from patient data strictly respecting the 10 features"""
        gender_val = 1 if str(patient_data.get("gender", "")).lower().startswith("m") else 0
        symptom_score = self._encode_symptoms(str(patient_data.get("symptoms", "")))
        
        data = {
            "Age": [float(patient_data.get("age", 45))],
            "Gender": [gender_val],
            "BMI": [float(patient_data.get("bmi", 24.5))],
            "Glucose": [float(patient_data.get("glucose", 100.0))],
            "BP": [float(patient_data.get("bp", 120.0))],
            "Cholesterol": [float(patient_data.get("cholesterol", 180.0))],
            "Heart_Rate": [float(patient_data.get("heart_rate", 75.0))],
            "HbA1c": [float(patient_data.get("hba1c", 5.5))],
            "Smoking": [1 if patient_data.get("smoking") in [1, True, "1", "yes", "Yes"] else 0],
            "Symptoms": [symptom_score]
        }
        return pd.DataFrame(data, columns=FEATURES)

    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform disease prediction with probabilities"""
        X = self.prepare_feature_vector(patient_data)
        probs = self.model.predict_proba(X)[0]
        classes = list(self.model.classes_)
        
        # Map class probabilities
        prob_dict = {}
        for cls_name, p in zip(classes, probs):
            prob_dict[cls_name] = round(float(p) * 100, 2)
            
        # Sort by highest probability
        sorted_probs = dict(sorted(prob_dict.items(), key=lambda item: item[1], reverse=True))
        predicted_disease = list(sorted_probs.keys())[0]
        confidence = sorted_probs[predicted_disease]
        
        # Identify top key physiological risk indicators based on clinical thresholds
        risk_factors = []
        if float(patient_data.get("glucose", 0)) >= 140:
            risk_factors.append(f"Elevated Fasting Glucose ({patient_data.get('glucose')} mg/dL)")
        if float(patient_data.get("hba1c", 0)) >= 6.5:
            risk_factors.append(f"Diabetic Range HbA1c ({patient_data.get('hba1c')}%)")
        if float(patient_data.get("bp", 0)) >= 140:
            risk_factors.append(f"Hypertensive Systolic BP ({patient_data.get('bp')} mmHg)")
        if float(patient_data.get("cholesterol", 0)) >= 220:
            risk_factors.append(f"Elevated Serum Cholesterol ({patient_data.get('cholesterol')} mg/dL)")
        if float(patient_data.get("bmi", 0)) >= 30:
            risk_factors.append(f"Class I/II Obesity (BMI {patient_data.get('bmi')})")
        if patient_data.get("smoking") in [1, True, "1"]:
            risk_factors.append("Active Tobacco Smoking History")

        return {
            "predicted_disease": predicted_disease,
            "confidence": confidence,
            "probabilities": sorted_probs,
            "features_evaluated": X.to_dict(orient="records")[0],
            "top_risk_factors": risk_factors,
            "disclaimer": "AI-generated decision support — professional verification required."
        }

# Global singleton
random_forest_service = RandomForestService()
