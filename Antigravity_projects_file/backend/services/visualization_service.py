import io
import base64
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Medical aesthetic styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
PRIMARY_TEAL = "#0d9488"
SECONDARY_BLUE = "#0284c7"
DANGER_ROSE = "#e11d48"
AMBER_WARNING = "#d97706"
NEUTRAL_SLATE = "#334155"

class VisualizationService:
    def _fig_to_base64(self, fig: plt.Figure) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=140)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _fig_to_bytes(self, fig: plt.Figure) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=180)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_probability_chart(self, probabilities: Dict[str, float], as_bytes: bool = False):
        """Horizontal bar chart for disease model probabilities"""
        fig, ax = plt.subplots(figsize=(8, 4))
        
        diseases = list(probabilities.keys())[::-1]
        probs = [probabilities[d] for d in diseases]
        
        colors = [PRIMARY_TEAL if p == max(probs) else '#94a3b8' for p in probs]
        bars = ax.barh(diseases, probs, color=colors, height=0.55, edgecolor="#0f172a", alpha=0.9)
        
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(ticker.PercentFormatter())
        ax.set_title("Disease Classification Model Probabilities", fontsize=12, fontweight="bold", pad=12, color=NEUTRAL_SLATE)
        ax.set_xlabel("Calibrated Probability (%)", fontsize=10, color="#64748b")
        
        for bar, p in zip(bars, probs):
            ax.text(p + 1.5, bar.get_y() + bar.get_height()/2, f"{p:.1f}%", va="center", ha="left", fontsize=9, fontweight="bold", color=NEUTRAL_SLATE)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        
        return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

    def generate_shap_chart(self, feature_contributions: List[Dict[str, Any]], as_bytes: bool = False):
        """SHAP Feature Attribution / Contribution waterfall chart"""
        fig, ax = plt.subplots(figsize=(8, 4.5))
        
        # Take top 8 contributors
        top_fc = feature_contributions[:8][::-1]
        features = [f"{fc['feature']} ({fc.get('patient_value', '')})" for fc in top_fc]
        shap_vals = [fc["shap_value"] for fc in top_fc]
        colors = [DANGER_ROSE if v > 0 else SECONDARY_BLUE for v in shap_vals]

        bars = ax.barh(features, shap_vals, color=colors, height=0.55, edgecolor="#1e293b", alpha=0.9)
        ax.axvline(0, color="#64748b", linestyle="--", linewidth=1.2)
        
        ax.set_title("SHAP Feature Attribution (TreeExplainer)", fontsize=12, fontweight="bold", pad=12, color=NEUTRAL_SLATE)
        ax.set_xlabel("SHAP Value (Positive = Increases Risk | Negative = Lowers Risk)", fontsize=9, color="#64748b")
        
        for bar, v in zip(bars, shap_vals):
            offset = 0.015 if v >= 0 else -0.015
            ha = "left" if v >= 0 else "right"
            ax.text(v + offset, bar.get_y() + bar.get_height()/2, f"{v:+.3f}", va="center", ha=ha, fontsize=8, fontweight="bold", color=NEUTRAL_SLATE)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

        return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

    def generate_vitals_trend_chart(self, vitals_history: List[Dict[str, Any]], as_bytes: bool = False):
        """Multi-panel time series trend for patient vitals"""
        if not vitals_history or len(vitals_history) < 2:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.text(0.5, 0.5, "No historical trend data available.\n(Start simulated monitoring to stream vital readings)", 
                    ha="center", va="center", fontsize=11, color="#64748b")
            ax.axis("off")
            return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
        
        ticks = list(range(len(vitals_history)))
        hrs = [v["heart_rate"] for v in vitals_history]
        spo2s = [v["spo2"] for v in vitals_history]
        sbps = [v["systolic_bp"] for v in vitals_history]
        dbps = [v["diastolic_bp"] for v in vitals_history]

        # Top plot: Heart Rate & SpO2
        ax1.plot(ticks, hrs, color=DANGER_ROSE, marker="o", markersize=3.5, linewidth=1.8, label="Heart Rate (bpm)")
        ax1.set_ylabel("Heart Rate (bpm)", color=DANGER_ROSE, fontsize=9)
        ax1.tick_params(axis="y", labelcolor=DANGER_ROSE)
        
        ax1_twin = ax1.twinx()
        ax1_twin.plot(ticks, spo2s, color=SECONDARY_BLUE, marker="s", markersize=3.5, linewidth=1.8, linestyle="--", label="SpO2 (%)")
        ax1_twin.set_ylabel("SpO2 (%)", color=SECONDARY_BLUE, fontsize=9)
        ax1_twin.set_ylim(85, 101)
        ax1_twin.tick_params(axis="y", labelcolor=SECONDARY_BLUE)
        ax1.set_title("Real-Time Patient Hemodynamic & Oxygenation Trends [SIMULATED DATA]", fontsize=11, fontweight="bold", pad=8)

        # Bottom plot: Blood Pressure (Systolic / Diastolic)
        ax2.plot(ticks, sbps, color="#b91c1c", marker="^", markersize=3.5, linewidth=1.8, label="Systolic BP (mmHg)")
        ax2.plot(ticks, dbps, color="#f97316", marker="v", markersize=3.5, linewidth=1.8, label="Diastolic BP (mmHg)")
        ax2.fill_between(ticks, sbps, dbps, color="#fee2e2", alpha=0.5)
        ax2.set_ylabel("Blood Pressure (mmHg)", fontsize=9, color=NEUTRAL_SLATE)
        ax2.set_xlabel("Monitoring Sample Ticks", fontsize=9, color="#64748b")
        ax2.legend(loc="upper left", fontsize=8)

        plt.tight_layout()
        return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

    def generate_fda_reactions_chart(self, fda_medicine_report: Dict[str, Any], as_bytes: bool = False):
        """Chart top adverse events reported for a medication"""
        fig, ax = plt.subplots(figsize=(8, 4))
        reactions = fda_medicine_report.get("top_reactions", [])[:7][::-1]
        
        if not reactions:
            ax.text(0.5, 0.5, "No OpenFDA reaction data available", ha="center", va="center")
            ax.axis("off")
            return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

        rx_names = [r["reaction"] for r in reactions]
        counts = [r["count"] for r in reactions]

        ax.barh(rx_names, counts, color="#f59e0b", height=0.55, edgecolor="#b45309", alpha=0.9)
        ax.set_title(f"Top OpenFDA Adverse Reactions: {fda_medicine_report.get('medicine_name')}", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Reported Incident Count in FAERS", fontsize=9, color="#64748b")

        for i, c in enumerate(counts):
            ax.text(c + max(counts)*0.015, i, f"{c:,}", va="center", fontsize=8, fontweight="bold")

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        return self._fig_to_bytes(fig) if as_bytes else self._fig_to_base64(fig)

visualization_service = VisualizationService()
