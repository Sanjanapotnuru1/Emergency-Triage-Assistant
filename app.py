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
    sections = {"urgency": "", "concern": "", "severity": "", "next_steps": "", "notes": "", "disclaimer": ""}
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    current = None
    for line in lines:
        lower = line.lower()
        if "urgency level" in lower:
            current = "urgency"
            continue
        elif "possible medical concern" in lower:
            current = "concern"
            continue
        elif "symptom severity analysis" in lower:
            current = "severity"
            continue
        elif "recommended next steps" in lower:
            current = "next_steps"
            continue
        elif "additional notes" in lower:
            current = "notes"
            continue
        elif "disclaimer" in lower:
            current = "disclaimer"
            continue
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

def expand_section_theory(title, items):
    raw = ", ".join(str(x).strip() for x in items if str(x).strip())
    title_key = title.strip().lower()

    if title_key == "symptoms":
        return "These reported symptoms suggest the patient may be experiencing a clinically important illness pattern. When multiple symptoms occur together, especially breathing difficulty, fever, vomiting, weakness, or neurological complaints, the overall triage concern becomes higher because the combination may reflect systemic stress rather than a minor isolated problem."
    if title_key == "pain score":
        return "This pain score helps estimate current symptom burden and guides urgency. Mid-to-high pain scores generally deserve closer observation, and the score becomes more concerning when it appears alongside breathing problems, fever, repeated vomiting, chest discomfort, or severe fatigue."
    if title_key == "recommended action":
        return "This action is being advised because the present symptom combination may require prompt medical assessment. In triage systems, the recommended action is based not only on one symptom but on the overall pattern, intensity, and associated risk factors."
    if title_key == "precautions":
        return "These precautions are intended to reduce immediate risk while the patient is being monitored or prepared for medical review. Supportive steps such as rest, hydration, avoidance of exertion, and close observation can help prevent worsening while waiting for professional evaluation."
    if title_key == "warning signs":
        return "These warning signs are important because they can indicate clinical deterioration or possible emergency progression. If any of these features appear, intensify, or occur together, urgent in-person medical evaluation should not be delayed."
    if title_key == "confidence":
        return "This confidence level reflects how strongly the symptom pattern matches the triage rules used by the system. It is helpful for guidance, but it does not replace medical examination, diagnostic testing, or clinician judgment."
    if title_key == "duration":
        return "Symptom duration is clinically relevant because persistent problems are less likely to represent a brief self-limited episode. A longer duration can point toward ongoing infection, uncontrolled inflammation, dehydration, cardiovascular strain, or another condition that needs assessment."
    if title_key == "existing conditions":
        return "Pre-existing medical conditions can increase the patient’s risk and may reduce the margin of safety during an acute episode. Chronic illness often changes how aggressively symptoms should be interpreted, even when the current complaint initially appears moderate."
    if title_key == "triage priority":
        return "This priority level summarizes how urgently the overall case should be reviewed. It is based on the combination of symptoms, severity indicators, duration, and associated risk factors rather than any single finding alone."
    if title_key == "clinical concern":
        return "This clinical concern represents the main medical interpretation suggested by the symptom profile. It is not a confirmed diagnosis, but it highlights the most important category of illness or emergency risk that should be considered first."
    if title_key == "blood pressure":
        return "Blood pressure is a key triage indicator because markedly abnormal readings may reflect cardiovascular stress or an active medical emergency. High values become more concerning when they are associated with headache, chest symptoms, breathing difficulty, confusion, or vomiting."
    if title_key == "blood sugar":
        return "Blood sugar readings are important because abnormal levels can rapidly worsen weakness, confusion, dehydration, and overall medical stability. In a patient with diabetes or acute illness, this information can meaningfully affect urgency and next-step recommendations."
    return "This section provides additional clinical context to help interpret the triage finding in a more meaningful and medically readable way."

def split_severity_sections(text):
    text = text.replace("Symptoms reported:", "\nSymptoms reported:")
    text = text.replace("Pain score:", "\nPain score:")
    text = text.replace("Recommended Action:", "\nRecommended Action:")
    text = text.replace("Precautions:", "\nPrecautions:")
    text = text.replace("Warning Signs:", "\nWarning Signs:")
    text = text.replace("AI Confidence Level:", "\nAI Confidence Level:")
    text = text.replace("Doctor consultation:", "\nDoctor consultation:")
    text = text.replace("Emergency Alert Recommendation:", "\nEmergency Alert Recommendation:")

    lines = [line.strip("• ").strip() for line in text.splitlines() if line.strip()]

    section_map = {
        "Symptoms reported": "Symptoms",
        "Pain score": "Pain Score",
        "Recommended Action": "Recommended Action",
        "Doctor consultation": "Doctor Consultation",
        "Precautions": "Precautions",
        "Lifestyle & Wellness Suggestions": "Lifestyle",
        "Warning Signs": "Warning Signs",
        "Emergency Warning Signs": "Warning Signs",
        "AI Confidence Level": "Confidence",
        "Emergency Alert Recommendation": "Emergency Alert"
    }

    grouped = {}
    current_title = None

    for line in lines:
        if ":" in line:
            head, body = line.split(":", 1)
            head = head.strip()
            body = body.strip()
            title = section_map.get(head, head)
            current_title = title
            grouped.setdefault(title, []).append(body if body else "-")
        else:
            if current_title:
                grouped.setdefault(current_title, []).append(line)
            else:
                grouped.setdefault("Assessment", []).append(line)

    return grouped

st.markdown(f"""
<style>
:root {{
    --bg: {bg};
    --card: {card};
    --card-alt: {card_alt};
    --soft-card: {soft_card};
    --text: {text};
    --muted: {muted};
    --faint: {faint};
    --border: {border};
    --input-bg: {input_bg};
    --primary: {primary};
    --primary-hover: {primary_hover};
    --success-bg: {success_bg};
    --success-text: {success_text};
    --warning-bg: {warning_bg};
    --warning-text: {warning_text};
    --danger-bg: {danger_bg};
    --danger-text: {danger_text};
    --info-bg: {info_bg};
    --info-text: {info_text};
}}

.stApp {{
    background: radial-gradient(circle at top right, rgba(37,99,235,0.10), transparent 24%), linear-gradient(180deg, var(--bg), var(--bg));
    color: var(--text);
    font-family: 'Segoe UI', sans-serif;
}}

.block-container {{
    max-width: 1220px;
    padding-top: 1.25rem;
    padding-bottom: 2rem;
}}

section[data-testid="stSidebar"] {{
    background: var(--card);
    border-right: 1px solid var(--border);
}}

section[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}

.hero {{
    background: linear-gradient(135deg, var(--primary), var(--primary-hover));
    border-radius: 24px;
    padding: 2rem 2rem 1.8rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 16px 34px rgba(37,99,235,0.24);
    text-align: center;
}}

.hero-title {{
    font-size: clamp(2rem, 2.8vw, 3rem);
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.35rem;
}}

.hero-subtitle {{
    color: #dbeafe;
    font-size: 1rem;
}}

.info-banner {{
    background: var(--info-bg);
    color: var(--info-text);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.95rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.95rem;
}}

.form-card, .result-card {{
    background: var(--card);
    border-radius: 22px;
    padding: 1.35rem;
    border: 1px solid var(--border);
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.12);
    margin-bottom: 1rem;
}}

.section-title {{
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.35rem;
}}

.section-subtitle {{
    color: var(--muted);
    font-size: 0.96rem;
    margin-bottom: 1rem;
}}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {{
    background: var(--input-bg) !important;
    color: var(--text) !important;
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
}}

.stTextArea textarea {{
    min-height: 130px;
}}

label,
.stMarkdown,
.stSelectbox label,
.stMultiSelect label,
.stFileUploader label {{
    color: var(--text) !important;
    font-weight: 600 !important;
}}

textarea::placeholder,
input::placeholder {{
    color: var(--faint) !important;
    opacity: 1 !important;
}}

div.stButton > button,
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button,
.stForm button[kind="primary"] {{
    width: 100% !important;
    min-height: 50px !important;
    border: 1px solid rgba(96,165,250,0.35) !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    box-shadow: 0 10px 24px rgba(37,99,235,0.28) !important;
}}

div.stButton > button:hover,
div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
.stForm button[kind="primary"]:hover {{
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: #ffffff !important;
    border-color: rgba(147,197,253,0.55) !important;
}}

div.stButton > button span,
div.stDownloadButton > button span,
div[data-testid="stFormSubmitButton"] > button span,
.stForm button[kind="primary"] span {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}

section[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
    background: linear-gradient(180deg, #0f2340, #102a4c) !important;
    border: 1px solid rgba(96,165,250,0.32) !important;
    border-radius: 16px !important;
    padding: 0.85rem !important;
}}

section[data-testid="stFileUploader"] button,
section[data-testid="stBaseButton-secondary"] {{
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    color: #ffffff !important;
    border: 1px solid rgba(96,165,250,0.35) !important;
    border-radius: 12px !important;
    box-shadow: 0 6px 16px rgba(37,99,235,0.22) !important;
}}

section[data-testid="stFileUploader"] button:hover,
section[data-testid="stBaseButton-secondary"]:hover {{
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: #ffffff !important;
}}

section[data-testid="stFileUploader"] button span,
section[data-testid="stBaseButton-secondary"] span {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}

section[data-testid="stFileUploader"] small,
section[data-testid="stFileUploader"] div,
section[data-testid="stFileUploader"] span,
section[data-testid="stFileUploader"] p {{
    color: #dbeafe !important;
}}

button[kind="secondary"],
button[kind="primary"] {{
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    color: #ffffff !important;
    border: 1px solid rgba(96,165,250,0.35) !important;
}}

button[kind="secondary"] span,
button[kind="primary"] span {{
    color: #ffffff !important;
}}

.patient-chip {{
    background: var(--soft-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.8rem;
}}

.patient-chip-title {{
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.3rem;
    font-weight: 700;
}}

.patient-chip-value {{
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
}}

.result-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}}

.result-eyebrow {{
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.82rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}}

.result-title {{
    font-size: clamp(1.8rem, 2.2vw, 2.35rem);
    font-weight: 800;
    color: var(--text);
    margin-bottom: 0.25rem;
}}

.result-subtext {{
    color: var(--muted);
    font-size: 0.97rem;
}}

.priority-badge {{
    padding: 0.8rem 1rem;
    border-radius: 999px;
    font-size: 0.92rem;
    font-weight: 800;
    white-space: nowrap;
}}

.priority-high {{
    background: var(--danger-bg);
    color: var(--danger-text);
    border: 1px solid rgba(239,68,68,0.22);
}}

.priority-moderate {{
    background: var(--warning-bg);
    color: var(--warning-text);
    border: 1px solid rgba(245,158,11,0.20);
}}

.priority-low {{
    background: var(--success-bg);
    color: var(--success-text);
    border: 1px solid rgba(34,197,94,0.20);
}}

.medical-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 10px 24px rgba(2, 6, 23, 0.10);
}}

.medical-card h3 {{
    margin-bottom: 0.8rem;
    font-size: 1.05rem;
    color: var(--text);
}}

.summary-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.85rem;
}}

.summary-card {{
    background: var(--card-alt);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem;
}}

.summary-label {{
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}}

.summary-value {{
    color: var(--text);
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.6;
}}

.status-strip {{
    padding: 1rem;
    border-radius: 14px;
    font-weight: 700;
    line-height: 1.6;
}}

.strip-high {{
    background: var(--danger-bg);
    color: var(--danger-text);
    border: 1px solid rgba(239,68,68,0.22);
}}

.strip-moderate {{
    background: var(--warning-bg);
    color: var(--warning-text);
    border: 1px solid rgba(245,158,11,0.20);
}}

.strip-low {{
    background: var(--success-bg);
    color: var(--success-text);
    border: 1px solid rgba(34,197,94,0.20);
}}

.notes-box {{
    background: var(--card-alt);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    color: var(--text);
    line-height: 1.8;
    white-space: pre-wrap;
}}

.severity-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.85rem;
    align-items: stretch;
}}

.severity-item {{
    background: var(--card-alt);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem;
}}

.severity-item-title {{
    font-size: 0.82rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    margin-bottom: 0.45rem;
}}

.severity-item-body {{
    color: var(--text);
    line-height: 1.8;
    font-size: 0.97rem;
}}

.clean-list {{
    margin: 0;
    padding-left: 1.1rem;
    color: var(--text);
    line-height: 1.8;
}}

.clean-list li {{
    margin-bottom: 0.45rem;
}}

.notice-card {{
    background: linear-gradient(180deg, var(--warning-bg), transparent);
}}

.footer {{
    text-align: center;
    margin-top: 1.5rem;
    color: var(--muted);
    padding: 0.75rem;
    font-size: 0.92rem;
}}

@media (max-width: 768px) {{
    .block-container {{
        padding-inline: 1rem;
    }}

    .hero {{
        padding: 1.3rem;
        border-radius: 18px;
    }}

    .form-card,
    .result-card {{
        padding: 1rem;
    }}

    .result-header {{
        flex-direction: column;
        align-items: stretch;
    }}

    .summary-grid,
    .severity-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">🚑 Emergency Triage Assistant</div>
    <div class="hero-subtitle">AI-powered emergency healthcare assessment platform</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-banner">
    Designed for fast clinical-style symptom screening with structured triage output and improved readability in both light and dark mode.
</div>
""", unsafe_allow_html=True)

if st.session_state.page == "form":
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 Patient Assessment Form</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Enter patient symptoms and background details for structured AI-assisted triage.</div>', unsafe_allow_html=True)
    with st.form("triage_form"):
        symptoms = st.text_area("Symptoms", placeholder="Describe symptoms here...")
        col1, col2 = st.columns(2)
        duration = col1.text_input("Duration of Symptoms")
        pain = col2.slider("Pain Level", 1, 10, 5)
        conditions = st.multiselect("Existing Medical Conditions", ["Diabetes", "Blood Pressure", "Asthma", "Heart Disease", "None"])
        if "Diabetes" in conditions or "Blood Pressure" in conditions:
            st.caption("Please fill in the required readings for the selected chronic conditions.")
        sugar_level = st.text_input("Blood Sugar Level") if "Diabetes" in conditions else ""
        bp_level = st.text_input("Blood Pressure Reading") if "Blood Pressure" in conditions else ""
        st.markdown("### 👤 Patient Information")
        col3, col4 = st.columns(2)
        name = col3.text_input("Patient Name")
        age = col3.number_input("Age", min_value=1, max_value=120, value=25)
        gender = col4.selectbox("Gender", ["Male", "Female", "Other"])
        emergency = col4.text_input("Emergency Contact Number")
        uploaded_file = st.file_uploader("Upload Medical Report", type=["pdf", "png", "jpg", "jpeg"])
        submitted = st.form_submit_button("🔍 Analyze Symptoms")
    st.markdown("</div>", unsafe_allow_html=True)
    if submitted:
        if not symptoms.strip():
            st.error("Please enter symptoms.")
            st.stop()
        if not name.strip():
            st.error("Please enter patient name.")
            st.stop()
        if emergency and (not emergency.isdigit() or len(emergency) < 8):
            st.error("Emergency number should contain only digits and be at least 8 digits long.")
            st.stop()
        if "Blood Pressure" in conditions and not bp_level.strip():
            st.error("Please enter the blood pressure reading because Blood Pressure is selected as an existing condition.")
            st.stop()
        if "Diabetes" in conditions and not sugar_level.strip():
            st.error("Please enter the blood sugar level because Diabetes is selected as an existing condition.")
            st.stop()
        patient_data = {
            "name": name.strip(),
            "age": int(age),
            "gender": gender,
            "symptoms": symptoms.strip(),
            "duration": duration.strip(),
            "pain": int(pain),
            "conditions": ", ".join([c for c in conditions if c != "None"]) or "None",
            "blood_sugar": sugar_level.strip(),
            "blood_pressure": bp_level.strip(),
            "uploaded_file": uploaded_file.name if uploaded_file else "",
        }
        with st.spinner("Analyzing symptoms..."):
            result = analyze_patient(patient_data)
        save_report(patient_data, result)
        st.session_state.result = result
        st.session_state.patient_data = patient_data
        st.session_state.page = "result"
        st.rerun()

elif st.session_state.page == "result":
    parsed = normalize_result(st.session_state.result)
    patient = st.session_state.patient_data
    urgency = urgency_theme(parsed["urgency"])

    patient_name = safe_text(patient.get("name", "-"))
    patient_age = safe_text(patient.get("age", "-"))
    patient_gender = safe_text(patient.get("gender", "-"))
    patient_pain = safe_text(patient.get("pain", "-"))
    patient_duration = safe_text(patient.get("duration", "Not specified") or "Not specified")
    patient_symptoms = safe_text(patient.get("symptoms", "-"))
    patient_conditions = safe_text(patient.get("conditions", "None"))
    patient_bp = safe_text(patient.get("blood_pressure", "") or "Not provided")
    patient_sugar = safe_text(patient.get("blood_sugar", "") or "Not provided")
    generated_date = safe_text(datetime.now().strftime("%d %b %Y"))
    parsed_urgency = safe_text(parsed["urgency"])
    parsed_concern = safe_text(parsed["concern"])
    parsed_notes = safe_text(clean_analysis_text(parsed["notes"]))
    parsed_disclaimer = safe_text(parsed["disclaimer"])

    severity_sections = split_severity_sections(parsed["severity"])
    severity_sections["Duration"] = [patient.get("duration", "Not specified") or "Not specified"]
    severity_sections["Existing Conditions"] = [patient.get("conditions", "None") or "None"]
    severity_sections["Triage Priority"] = [parsed["urgency"]]
    severity_sections["Clinical Concern"] = [parsed["concern"]]

    if patient.get("blood_pressure"):
        severity_sections["Blood Pressure"] = [patient["blood_pressure"]]

    if patient.get("blood_sugar"):
        severity_sections["Blood Sugar"] = [patient["blood_sugar"]]

    card_parts = []
    for title, items in severity_sections.items():
        item_html = "".join(
            f"<div style='margin-bottom:0.45rem;'>• {safe_text(item)}</div>"
            for item in items if str(item).strip()
        )
        theory_text = safe_text(expand_section_theory(title, items))
        card_html = f"""
<div class="severity-item">
    <div class="severity-item-title">{safe_text(title)}</div>
    <div class="severity-item-body">
        {item_html}
        <div style='margin-top:0.8rem; color: var(--muted); line-height:1.75; font-size:0.94rem;'>
            {theory_text}
        </div>
    </div>
</div>
"""
        card_parts.append(card_html)
    severity_cards = "".join(card_parts)

    header_html = f"""
    <div class="result-header">
        <div>
            <div class="result-eyebrow">Clinical Triage Summary</div>
            <div class="result-title">Patient Assessment Result</div>
            <div class="result-subtext">Structured emergency screening output for rapid clinical review</div>
        </div>
        <div class="priority-badge {urgency['badge_class']}">{urgency['icon']} {urgency['label']}</div>
    </div>
    """

    strip_class = urgency["strip_class"]
    urgency_html = f'<div class="medical-card"><h3>Urgency Level</h3><div class="status-strip {strip_class}">{parsed_urgency}</div></div>'
    severity_html = f'<div class="medical-card"><h3>Symptom Severity Analysis</h3><div class="severity-grid">{severity_cards}</div></div>'
    summary_html = f'<div class="medical-card"><h3>Clinical Summary</h3><div class="summary-grid"><div class="summary-card"><div class="summary-label">Possible Concern</div><div class="summary-value">{parsed_concern}</div></div><div class="summary-card"><div class="summary-label">Duration</div><div class="summary-value">{patient_duration}</div></div></div></div>'
    notes_html = f'<div class="medical-card"><h3>Additional Notes</h3><div class="notes-box">{parsed_notes}</div></div>'
    overview_html = f'<div class="medical-card"><h3>Patient Overview</h3><ul class="clean-list"><li><strong>Symptoms:</strong> {patient_symptoms}</li><li><strong>Existing conditions:</strong> {patient_conditions}</li><li><strong>Blood pressure:</strong> {patient_bp}</li><li><strong>Blood sugar:</strong> {patient_sugar}</li></ul></div>'

    next_steps_items = [item.strip() for item in re.split(r"[.;]\s+", parsed["next_steps"]) if item.strip()]
    if not next_steps_items:
        next_steps_items = [parsed["next_steps"]]
    steps_html_items = "".join(f"<li>{safe_text(item)}</li>" for item in next_steps_items)
    steps_html = f'<div class="medical-card"><h3>Recommended Next Steps</h3><ul class="clean-list">{steps_html_items}</ul></div>'
    notice_html = f'<div class="medical-card notice-card"><h3>Important Notice</h3><div class="notes-box">{parsed_disclaimer}</div></div>'

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown(header_html, unsafe_allow_html=True)

    top1, top2, top3, top4 = st.columns(4)
    top1.markdown(f'<div class="patient-chip"><div class="patient-chip-title">Patient</div><div class="patient-chip-value">{patient_name}</div></div>', unsafe_allow_html=True)
    top2.markdown(f'<div class="patient-chip"><div class="patient-chip-title">Age / Gender</div><div class="patient-chip-value">{patient_age} / {patient_gender}</div></div>', unsafe_allow_html=True)
    top3.markdown(f'<div class="patient-chip"><div class="patient-chip-title">Pain Score</div><div class="patient-chip-value">{patient_pain}/10</div></div>', unsafe_allow_html=True)
    top4.markdown(f'<div class="patient-chip"><div class="patient-chip-title">Generated</div><div class="patient-chip-value">{generated_date}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.35, 0.95], gap="large")
    with left:
        st.markdown(urgency_html, unsafe_allow_html=True)
        st.markdown(severity_html, unsafe_allow_html=True)
        st.markdown(summary_html, unsafe_allow_html=True)
        st.markdown(notes_html, unsafe_allow_html=True)
    with right:
        st.markdown(overview_html, unsafe_allow_html=True)
        st.markdown(steps_html, unsafe_allow_html=True)
        st.markdown(notice_html, unsafe_allow_html=True)

    st.download_button("📄 Download Medical Report", st.session_state.result, file_name="medical_report.txt", mime="text/plain")

    if st.button("⬅️ Analyze Another Patient"):
        st.session_state.page = "form"
        st.session_state.result = ""
        st.session_state.patient_data = {}
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>Built with ❤️ using Streamlit + AI</div>", unsafe_allow_html=True)
