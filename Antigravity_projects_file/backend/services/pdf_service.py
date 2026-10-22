import io
import os
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from backend.services.visualization_service import visualization_service
from backend.config import REPORTS_DIR

class PDFService:
    def generate_clinical_report(
        self,
        patient_data: Dict[str, Any],
        prediction: Dict[str, Any],
        shap_data: Dict[str, Any],
        medication_safety: Dict[str, Any],
        fda_data: List[Dict[str, Any]],
        ai_report: Dict[str, Any]
    ) -> str:
        """Generate a clinical-grade multi-page PDF report and return the file path"""
        patient_id = patient_data.get("patient_id", "Unknown")
        filename = f"MediSafe_Clinical_Report_{patient_id}_{int(datetime.now().timestamp())}.pdf"
        file_path = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom typography
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f766e"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica-Oblique",
            spaceAfter=12
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#991b1b"),
            fontName="Helvetica-Bold"
        )

        story = []

        # Header Title
        story.append(Paragraph("MediSafe AI — Clinical Decision Support Report", title_style))
        story.append(Paragraph("AI-Powered Disease Risk Classification & Medication Safety Decision Support", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f766e"), spaceAfter=10))

        # Important Disclaimer Banner
        disclaimer_text = (
            "<b>CLINICAL DECISION SUPPORT NOTICE:</b> This document contains algorithmic evaluations for clinical guidance only. "
            "It does NOT constitute a confirmed medical diagnosis and cannot prescribe, modify, or discontinue medications. "
            "Professional verification by a licensed physician or pharmacist is required."
        )
        disclaimer_table = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[540])
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fee2e2")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#ef4444")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(disclaimer_table)
        story.append(Spacer(1, 10))

        # Section 1: Patient Summary Table
        story.append(Paragraph("1. Patient Profile & Clinical Parameters", section_heading))
        p_table_data = [
            [
                Paragraph("<b>Patient ID:</b>", body_style), Paragraph(str(patient_data.get('patient_id')), body_style),
                Paragraph("<b>Full Name:</b>", body_style), Paragraph(str(patient_data.get('name', 'N/A')), body_style)
            ],
            [
                Paragraph("<b>Age / Gender:</b>", body_style), Paragraph(f"{patient_data.get('age')} yrs / {patient_data.get('gender')}", body_style),
                Paragraph("<b>BMI:</b>", body_style), Paragraph(f"{patient_data.get('bmi')} kg/m²", body_style)
            ],
            [
                Paragraph("<b>Blood Pressure:</b>", body_style), Paragraph(f"{patient_data.get('bp')} mmHg", body_style),
                Paragraph("<b>Heart Rate:</b>", body_style), Paragraph(f"{patient_data.get('heart_rate')} bpm", body_style)
            ],
            [
                Paragraph("<b>Fasting Glucose:</b>", body_style), Paragraph(f"{patient_data.get('glucose')} mg/dL", body_style),
                Paragraph("<b>HbA1c:</b>", body_style), Paragraph(f"{patient_data.get('hba1c')}%", body_style)
            ],
            [
                Paragraph("<b>Cholesterol:</b>", body_style), Paragraph(f"{patient_data.get('cholesterol')} mg/dL", body_style),
                Paragraph("<b>Smoking Status:</b>", body_style), Paragraph("Yes" if patient_data.get('smoking') in [1, True, "1"] else "No", body_style)
            ],
            [
                Paragraph("<b>Reported Symptoms:</b>", body_style), Paragraph(str(patient_data.get('symptoms', 'None reported')), body_style),
                Paragraph("<b>Known Allergies:</b>", body_style), Paragraph(str(patient_data.get('allergies', 'None reported')), body_style)
            ]
        ]
        p_table = Table(p_table_data, colWidths=[100, 170, 100, 170])
        p_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(p_table)
        story.append(Spacer(1, 10))

        # Section 2: Disease Prediction & Probabilities
        story.append(Paragraph("2. Random Forest Disease Classification", section_heading))
        pred_disease = prediction.get("predicted_disease", "N/A")
        pred_conf = prediction.get("confidence", 0.0)
        safety_level = ai_report.get("safety_level", "MODERATE")

        pred_summary = (
            f"<b>Primary Prediction:</b> <font color='#0f766e'><b>{pred_disease}</b></font> "
            f"(Model Calibrated Probability: <b>{pred_conf:.1f}%</b>) &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Assigned Safety Level:</b> <font color='#b91c1c'><b>{safety_level}</b></font>"
        )
        story.append(Paragraph(pred_summary, body_style))
        story.append(Spacer(1, 6))

        # Insert Probability Chart
        try:
            prob_bytes = visualization_service.generate_probability_chart(prediction.get("probabilities", {}), as_bytes=True)
            story.append(RLImage(io.BytesIO(prob_bytes), width=480, height=180))
        except Exception as e:
            print(f"Error rendering probability chart in PDF: {e}")

        story.append(Spacer(1, 10))

        # Section 3: Explainable AI / SHAP
        story.append(Paragraph("3. Explainable AI (SHAP TreeExplainer Analysis)", section_heading))
        shap_expl = shap_data.get("summary_explanation", "Feature attribution computed via TreeExplainer.")
        story.append(Paragraph(shap_expl, body_style))
        story.append(Spacer(1, 6))

        try:
            shap_bytes = visualization_service.generate_shap_chart(shap_data.get("feature_contributions", []), as_bytes=True)
            story.append(RLImage(io.BytesIO(shap_bytes), width=480, height=190))
        except Exception as e:
            print(f"Error rendering SHAP chart in PDF: {e}")

        story.append(Spacer(1, 10))

        # Section 4: Medication Safety & Drug Interactions
        story.append(Paragraph("4. Medication Safety, OCR & Drug-Drug Interactions", section_heading))
        allergies = medication_safety.get("allergy_alerts", [])
        interactions = medication_safety.get("interactions", [])

        med_text = f"<b>Active Regimen:</b> {', '.join(medication_safety.get('current_medications', [])) or 'None reported'}<br/>"
        med_text += f"<b>Prescription OCR Detected:</b> {', '.join(medication_safety.get('ocr_prescribed_medications', [])) or 'None detected'}<br/>"
        if allergies:
            med_text += f"<font color='#dc2626'><b>Allergy Concerns:</b> {len(allergies)} flagged conflict(s)</font><br/>"
        else:
            med_text += "<font color='#16a34a'><b>Allergy Status:</b> No active allergy contraindications flagged.</font><br/>"
        story.append(Paragraph(med_text, body_style))
        story.append(Spacer(1, 6))

        if interactions:
            int_table_data = [[
                Paragraph("<b>Drug Pair</b>", body_style),
                Paragraph("<b>Severity</b>", body_style),
                Paragraph("<b>Clinical Mechanism / Interaction</b>", body_style),
                Paragraph("<b>Evidence</b>", body_style)
            ]]
            for i in interactions:
                int_table_data.append([
                    Paragraph(f"{i.get('medicine_a')} + {i.get('medicine_b')}", body_style),
                    Paragraph(f"<b>{i.get('severity')}</b>", body_style),
                    Paragraph(i.get('potential_interaction', ''), body_style),
                    Paragraph(i.get('evidence_source', 'Clinical Reference'), body_style)
                ])
            int_table = Table(int_table_data, colWidths=[120, 70, 230, 120])
            int_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(int_table)
        else:
            story.append(Paragraph("<i>No severe drug-drug interactions detected between evaluated medications.</i>", body_style))

        story.append(Spacer(1, 10))

        # Section 5: OpenFDA Adverse Surveillance Evidence
        story.append(Paragraph("5. OpenFDA Pharmacovigilance Surveillance Evidence", section_heading))
        if fda_data:
            fda_table_data = [[
                Paragraph("<b>Medicine</b>", body_style),
                Paragraph("<b>Total FAERS Reports</b>", body_style),
                Paragraph("<b>Prevalent Adverse Reactions</b>", body_style)
            ]]
            for f in fda_data:
                rx_str = ", ".join([f"{r['reaction']} ({r['count']:,})" for r in f.get('top_reactions', [])[:3]])
                fda_table_data.append([
                    Paragraph(f.get('medicine_name', ''), body_style),
                    Paragraph(f"{f.get('total_adverse_reports', 0):,}", body_style),
                    Paragraph(rx_str or "Standard reporting profile", body_style)
                ])
            fda_table = Table(fda_table_data, colWidths=[110, 120, 310])
            fda_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(fda_table)
        story.append(Paragraph("<i>FDA adverse-event reports are reports of events and do not by themselves establish causality.</i>", subtitle_style))
        story.append(Spacer(1, 10))

        # Section 6: CrewAI Multi-Agent Synthesis & Gemini Reasoning
        story.append(Paragraph("6. Multi-Agent Synthesis & Clinical Recommendations", section_heading))
        agents = ai_report.get("multi_agent_breakdown", [])
        for ag in agents:
            story.append(Paragraph(f"<b>• {ag.get('agent_name')}:</b> {ag.get('findings')}", body_style))
            story.append(Spacer(1, 3))

        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Mandatory Professional Verification:</b>", section_heading))
        story.append(Paragraph(
            "This report is generated for qualified clinical personnel. No dosage adjustments, additions, "
            "or cancellations should occur based purely on algorithmic outputs. Sign below after comprehensive clinician review.",
            body_style
        ))
        story.append(Spacer(1, 20))

        # Signature Block
        sig_data = [
            [Paragraph("<b>Reviewed by Physician / Pharmacist:</b> ___________________________", body_style),
             Paragraph("<b>Signature:</b> ___________________________", body_style)],
            [Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style),
             Paragraph("<b>License ID:</b> ___________________________", body_style)]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([('PADDING', (0,0), (-1,-1), 4)]))
        story.append(sig_table)

        doc.build(story)
        return str(file_path)

pdf_service = PDFService()
