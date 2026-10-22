import numpy as np
import shap
from typing import Dict, Any, List
from backend.services.random_forest_service import random_forest_service, FEATURES

class SHAPService:
    def __init__(self):
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        try:
            if random_forest_service.model:
                # TreeExplainer is optimal for Random Forest
                self.explainer = shap.TreeExplainer(random_forest_service.model)
        except Exception as e:
            print(f"Warning: SHAP TreeExplainer initialization failed: {e}")
            self.explainer = None

    def explain(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute SHAP feature attribution values for the predicted class"""
        if not self.explainer:
            self._init_explainer()

        if not self.explainer:
            return {
                "available": False,
                "message": "SHAP TreeExplainer is currently unavailable for this model architecture.",
                "feature_contributions": [],
                "disclaimer": "These values indicate which input features contributed most to the model output. They do not establish medical causation."
            }

        try:
            X = random_forest_service.prepare_feature_vector(patient_data)
            shap_values = self.explainer.shap_values(X)
            
            # Predict to get predicted class index
            probs = random_forest_service.model.predict_proba(X)[0]
            pred_idx = int(np.argmax(probs))
            classes = list(random_forest_service.model.classes_)
            predicted_class = classes[pred_idx]

            # In newer shap versions shap_values may be a 3D array or list of arrays
            if isinstance(shap_values, list):
                class_shap = shap_values[pred_idx][0]
            elif isinstance(shap_values, np.ndarray):
                if len(shap_values.shape) == 3:
                    class_shap = shap_values[0, :, pred_idx]
                else:
                    class_shap = shap_values[0]
            else:
                class_shap = np.zeros(len(FEATURES))

            base_val = 0.0
            if hasattr(self.explainer, 'expected_value'):
                if isinstance(self.explainer.expected_value, (list, np.ndarray)):
                    base_val = float(self.explainer.expected_value[pred_idx])
                else:
                    base_val = float(self.explainer.expected_value)

            feature_contributions = []
            for i, feat in enumerate(FEATURES):
                val = X.iloc[0][feat]
                sv = float(class_shap[i])
                feature_contributions.append({
                    "feature": feat,
                    "patient_value": val if feat != "Gender" else ("Male" if val == 1 else "Female"),
                    "shap_value": round(sv, 4),
                    "impact": "Increases Risk" if sv > 0 else "Decreases Risk",
                    "magnitude": round(abs(sv), 4)
                })

            # Sort by absolute magnitude of contribution
            feature_contributions.sort(key=lambda x: x["magnitude"], reverse=True)

            top_drivers = [f"{fc['feature']} ({fc['impact']})" for fc in feature_contributions[:3]]
            summary_explanation = (
                f"The model's classification toward '{predicted_class}' was most heavily influenced by: "
                + ", ".join(top_drivers)
                + ". Features with positive SHAP values shifted probability toward this classification."
            )

            return {
                "available": True,
                "predicted_disease": predicted_class,
                "base_value": round(base_val, 4),
                "feature_contributions": feature_contributions,
                "summary_explanation": summary_explanation,
                "disclaimer": "These values indicate which input features contributed most to the model output. They do not establish medical causation."
            }

        except Exception as e:
            print(f"Error computing SHAP: {e}")
            return {
                "available": False,
                "message": f"SHAP calculation could not be completed: {str(e)}",
                "feature_contributions": [],
                "disclaimer": "These values indicate which input features contributed most to the model output. They do not establish medical causation."
            }

shap_service = SHAPService()
