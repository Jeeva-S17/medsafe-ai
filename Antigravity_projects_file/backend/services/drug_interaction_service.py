from typing import List, Dict, Any

# Clinical drug-drug interaction matrix based on pharmacology guidelines
INTERACTION_RULES = [
    {
        "pair": {"metformin", "lisinopril"},
        "severity": "Moderate",
        "description": "ACE inhibitors like Lisinopril may increase hypoglycemic sensitivity and enhance blood glucose lowering effect of Metformin. Regular glucose and renal monitoring advised.",
        "evidence_source": "Clinical Pharmacology Database (DrugBank/Lexicomp)",
        "action": "Maintain routine glycemic and renal panel monitoring."
    },
    {
        "pair": {"aspirin", "ibuprofen"},
        "severity": "Major",
        "description": "Concomitant use of Ibuprofen can interfere with the antiplatelet effect of low-dose Aspirin and markedly increase gastrointestinal ulceration and bleeding risk.",
        "evidence_source": "FDA Safety Alert / American Heart Association",
        "action": "Co-administration requires physician review and gastroprotective strategy."
    },
    {
        "pair": {"lisinopril", "spironolactone"},
        "severity": "Major",
        "description": "Concurrent use of an ACE inhibitor with a potassium-sparing diuretic can induce severe hyperkalemia, potentially leading to cardiac arrhythmias.",
        "evidence_source": "Joint British Societies Guidelines / FDA Prescribing Info",
        "action": "Requires serum potassium and creatinine monitoring within 1-2 weeks."
    },
    {
        "pair": {"atorvastatin", "amlodipine"},
        "severity": "Minor",
        "description": "Amlodipine may slightly increase plasma concentrations of Atorvastatin via CYP3A4 inhibition; typically well tolerated with lipid panel monitoring.",
        "evidence_source": "Micromedex Drug Interactions",
        "action": "Standard clinical follow-up; observe for muscle discomfort."
    },
    {
        "pair": {"albuterol", "metoprolol"},
        "severity": "Major",
        "description": "Beta-blockers like Metoprolol can antagonize bronchodilatory effects of beta-2 agonists like Albuterol and precipitate severe bronchospasm in reactive airway disease.",
        "evidence_source": "Global Initiative for Asthma (GINA) Guidelines",
        "action": "Cardioselective beta-blocker selection and close pulmonary monitoring required."
    },
    {
        "pair": {"ciprofloxacin", "theophylline"},
        "severity": "Major",
        "description": "Ciprofloxacin significantly inhibits CYP1A2 hepatic clearance of Theophylline, risking toxicity and seizures.",
        "evidence_source": "FDA Adverse Event Reporting & Labeling",
        "action": "Avoid combination or reduce theophylline dosage with therapeutic drug monitoring."
    },
    {
        "pair": {"aspirin", "lisinopril"},
        "severity": "Moderate",
        "description": "High-dose Aspirin may attenuate the antihypertensive and hemodynamic benefits of ACE inhibitors. Low-dose cardioprotective Aspirin (81mg) is generally permissible under clinical supervision.",
        "evidence_source": "Circulation Cardiology Consensus",
        "action": "Regular blood pressure assessment required."
    }
]

# Common allergen-drug cross sensitivities
ALLERGEN_CROSS_REACTIONS = {
    "penicillin": ["amoxicillin", "ampicillin", "augmentin", "clavanox", "piperacillin"],
    "sulfa": ["sulfamethoxazole", "bactrim", "furosemide", "hydrochlorothiazide", "glimepiride", "celecoxib"],
    "aspirin": ["ibuprofen", "naproxen", "ketorolac", "diclofenac"],
    "nsaid": ["aspirin", "ibuprofen", "naproxen", "celecoxib"],
    "iodine": ["amiodarone", "radiocontrast"]
}

class DrugInteractionService:
    def check_allergies(self, reported_allergies: str, medications: List[str]) -> List[Dict[str, Any]]:
        """Verify medications against reported allergies. NEVER invent allergies."""
        if not reported_allergies or reported_allergies.strip().lower() in ["none", "none reported", "no", "nil"]:
            return []

        alerts = []
        allergy_tokens = [a.strip().lower() for a in reported_allergies.replace(";", ",").split(",") if a.strip()]

        for med in medications:
            med_clean = med.strip().lower()
            for allergen in allergy_tokens:
                # Direct match
                if allergen in med_clean or med_clean in allergen:
                    alerts.append({
                        "medicine": med,
                        "allergen_match": allergen.capitalize(),
                        "status": "Potential allergy concern",
                        "severity": "HIGH",
                        "note": f"Direct name match between patient reported allergy '{allergen}' and prescribed drug '{med}'."
                    })
                    break
                
                # Cross-reactivity match
                cross_drugs = ALLERGEN_CROSS_REACTIONS.get(allergen, [])
                for cd in cross_drugs:
                    if cd in med_clean:
                        alerts.append({
                            "medicine": med,
                            "allergen_match": f"{allergen.capitalize()} (Cross-reactivity with {cd.capitalize()})",
                            "status": "Potential cross-allergy concern",
                            "severity": "HIGH",
                            "note": f"Known pharmacological cross-sensitivity between '{allergen}' and '{med}'."
                        })
                        break

        return alerts

    def check_interactions(self, all_medications: List[str]) -> List[Dict[str, Any]]:
        """Check all pairwise combinations of medications for clinical interactions"""
        interactions = []
        med_names = [m.strip().lower() for m in all_medications if m.strip()]

        for i in range(len(med_names)):
            for j in range(i + 1, len(med_names)):
                m1 = med_names[i]
                m2 = med_names[j]

                for rule in INTERACTION_RULES:
                    pair = rule["pair"]
                    # Check if both items in pair match either directly or as substring
                    match_1 = any(p in m1 for p in pair)
                    match_2 = any(p in m2 for p in pair)
                    
                    if match_1 and match_2:
                        p_list = list(pair)
                        interactions.append({
                            "medicine_a": all_medications[i],
                            "medicine_b": all_medications[j],
                            "severity": rule["severity"],
                            "potential_interaction": rule["description"],
                            "evidence_source": rule["evidence_source"],
                            "professional_action": rule["action"],
                            "professional_verification_status": "Verification Required"
                        })
        return interactions

    def evaluate_medications(self, current_meds_str: str, ocr_meds_list: List[str], patient_allergies: str) -> Dict[str, Any]:
        curr_list = [m.strip() for m in current_meds_str.replace(";", ",").split(",") if m.strip()]
        all_meds = list(set(curr_list + ocr_meds_list))

        allergy_alerts = self.check_allergies(patient_allergies, all_meds)
        interactions = self.check_interactions(all_meds)

        allergy_status = "No allergy reported"
        if patient_allergies and patient_allergies.strip().lower() not in ["none", "none reported", "no"]:
            allergy_status = "Potential allergy concern" if allergy_alerts else "Verification required (no conflict flagged with current list)"

        return {
            "current_medications": curr_list,
            "ocr_prescribed_medications": ocr_meds_list,
            "all_evaluated_medications": all_meds,
            "allergy_status": allergy_status,
            "allergy_alerts": allergy_alerts,
            "interactions": interactions,
            "has_major_concerns": any(i["severity"] == "Major" for i in interactions) or len(allergy_alerts) > 0,
            "disclaimer": "Do NOT start, stop, or change medications without consulting a licensed physician or pharmacist."
        }

drug_interaction_service = DrugInteractionService()
