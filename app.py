import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import html

try:
    from llm_engine import analyze_patient
except Exception:
    def analyze_patient(patient_data):
        symptoms = patient_data.get("symptoms", "")
        pain = patient_data.get("pain", 0)
        duration = patient_data.get("duration", "")
        conditions = patient_data.get("conditions", "")
        s = symptoms.lower()
        emergency_terms = [
            "chest pain", "breathing", "shortness of breath", "unconscious",
            "stroke", "seizure", "bleeding", "lung infection"
        ]
        if any(term in s for term in emergency_terms) or pain >= 8:
            level = "High"
            concern = "Possible severe respiratory or cardiac emergency"
            action = "Seek emergency medical care immediately or call local emergency services."
        elif pain >= 5:
            level = "Moderate"
            concern = "Condition may require urgent clinical evaluation"
            action = "Arrange urgent consultation with a doctor as soon as possible."
        else:
            level = "Low"
            concern = "Symptoms may be manageable with standard medical consultation"
            action = "Monitor symptoms and consult a clinician if symptoms persist or worsen."

        note_parts = []
        if conditions and conditions != "None":
            note_parts.append(f"Existing conditions: {conditions}.")
        if duration:
            note_parts.append(f"Duration: {duration}.")
        notes = " ".join(note_parts) if note_parts else "No additional notes provided."

        return f"""
Emergency Triage Assessment for {patient_data.get('name', 'Patient')}

AI-Detected Urgency Level:
{level}

Possible Medical Concern:
{concern}

Symptom Severity Analysis:
Symptoms reported: {symptoms}
Pain score: {pain}/10
Recommended Action: {action}
Precautions: Rest, hydration, and close symptom monitoring are advised.
Warning Signs: Trouble breathing, chest pain, confusion, uncontrolled vomiting, or severe weakness.
AI Confidence Level: Medium

Recommended Next Steps:
{action}

Additional Notes:
{notes}

Disclaimer:
This tool is for informational triage support only and is not a medical diagnosis.
""".strip()

st.set_page_config(page_title="Emergency Triage Assistant", page_icon="🚑", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "form"
if "result" not in st.session_state:
    st.session_state.result = ""
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}

st.sidebar.title("⚙️ Settings")
mode = st.sidebar.radio("Theme", ["Light Mode", "Dark Mode"], index=1)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
<div style="padding:14px;border-radius:16px;background:rgba(37,99,235,0.10);border:1px solid rgba(37,99,235,0.12);">
    <div style="font-weight:700;font-size:1.05rem;margin-bottom:8px;">🚑 Emergency Triage Assistant</div>
    <div style="font-size:0.95rem;line-height:1.7;">AI-powered healthcare support system.</div>
    <div style="margin-top:12px;font-weight:700;">Features</div>
    <ul style="margin-top:8px;line-height:1.8;padding-left:18px;">
        <li>AI symptom analysis</li>
        <li>Emergency detection</li>
        <li>Structured clinical summary</li>
        <li>Downloadable reports</li>
        <li>Light and dark mode</li>
    </ul>
</div>
""",
    unsafe_allow_html=True,
)

if mode == "Dark Mode":
    bg = "#06101f"
    card = "#0b1526"
    card_alt = "#111c31"
    soft_card = "#0f1a2d"
    text = "#f8fafc"
    muted = "#d6deea"
    faint = "#9aa8bc"
    border = "rgba(148,163,184,0.22)"
    input_bg = "#0b1f3a"
    primary = "#2563eb"
    primary_hover = "#3b82f6"
    success_bg = "rgba(22,163,74,0.16)"
    success_text = "#bbf7d0"
    warning_bg = "rgba(245,158,11,0.16)"
    warning_text = "#fde68a"
    danger_bg = "rgba(220,38,38,0.16)"
    danger_text = "#fecaca"
    info_bg = "rgba(59,130,246,0.14)"
    info_text = "#dbeafe"
else:
    bg = "#f3f7fb"
    card = "#ffffff"
    card_alt = "#f8fbff"
    soft_card = "#eef4ff"
    text = "#0f172a"
    muted = "#475569"
    faint = "#64748b"
    border = "rgba(15,23,42,0.10)"
    input_bg = "#ffffff"
    primary = "#1d4ed8"
    primary_hover = "#1e40af"
    success_bg = "#ecfdf5"
    success_text = "#166534"
    warning_bg = "#fffbeb"
    warning_text = "#92400e"
    danger_bg = "#fef2f2"
    danger_text = "#991b1b"
    info_bg = "#eff6ff"
    info_text = "#1d4ed8"

def save_report(data, result):
    file_name = Path("patient_reports.csv")
    report = {**data, "result": result, "timestamp": datetime.now().isoformat(timespec="seconds")}
    new_df = pd.DataFrame([report])
    if file_name.exists():
        old_df = pd.read_csv(file_name)
        pd.concat([old_df, new_df], ignore_index=True).to_csv(file_name, index=False)
    else:
        new_df.to_csv(file_name, index=False)

def normalize_result(raw_text):
    sections = {"urgency":"","concern":"","severity":"","next_steps":"","notes":"","disclaimer":""}
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    current = None
    for line in lines:
        lower = line.lower()
        if "urgency level" in lower:
            current = "urgency"; continue
        elif "possible medical concern" in lower:
            current = "concern"; continue
        elif "symptom severity analysis" in lower:
            current = "severity"; continue
        elif "recommended next steps" in lower:
            current = "next_steps"; continue
        elif "additional notes" in lower:
            current = "notes"; continue
        elif "disclaimer" in lower:
            current = "disclaimer"; continue
        if current:
            sections[current] += line + " "
    for key in sections:
        sections[key] = sections[key].strip()

    if not sections["urgency"]:
        m = re.search(r"(high|moderate|low)", raw_text, re.IGNORECASE)
        sections["urgency"] = m.group(1).title() if m else "Moderate"
    if not sections["concern"]:
        sections["concern"] = "Clinical review recommended based on the reported symptoms."
    if not sections["severity"]:
        sections["severity"] = raw_text.strip()
    if not sections["next_steps"]:
        sections["next_steps"] = "Consult a licensed medical professional for further evaluation."
    if not sections["notes"]:
        sections["notes"] = "No additional notes available."
    if not sections["disclaimer"]:
        sections["disclaimer"] = "This tool supports triage guidance only and does not replace professional medical diagnosis."
    return sections

def urgency_theme(level):
    level = level.lower().strip()
    if "high" in level:
        return {"label": "High Priority", "badge_class": "priority-high", "strip_class": "strip-high", "icon": "🔴"}
    elif "low" in level:
        return {"label": "Low Priority", "badge_class": "priority-low", "strip_class": "strip-low", "icon": "🟢"}
    return {"label": "Moderate Priority", "badge_class": "priority-moderate", "strip_class": "strip-moderate", "icon": "🟠"}

def safe_text(value):
    return html.escape(str(value if value not in [None, ""] else "-"))

def clean_analysis_text(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\b\d+\.\s*", "\n", text)
    text = re.sub(r"\s*\-\s*", "\n• ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()
    lines = [line.strip("• ").strip() for line in text.split("\n") if line.strip()]
    formatted = []
    for line in lines:
        if ":" in line and len(line.split(":")[0]) < 40:
            head, body = line.split(":", 1)
            formatted.append(f"• {head.strip()}: {body.strip()}")
        else:
            formatted.append(f"• {line}")
    return "\n".join(formatted)

