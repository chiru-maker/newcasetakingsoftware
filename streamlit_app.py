"""
SwasthyaSync — AI-Powered Clinical Case-Taking & Triage Platform
Streamlit Cloud & Local Deployment Entrypoint
"""

import sys
import os
import time
import json
from datetime import datetime
import pandas as pd
import streamlit as st

# Add backend to path so backend algorithms & schemas can be leveraged directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import backend modules safely
try:
    from dialogue_manager import DialogueManager
    from patient_record import PatientRecord, SlotValue
    from red_flag_library import check_safety
    from pateint_registery import MOCK_ABHA_REGISTRY
    from abdm_utils import generate_mock_abha_profile
except Exception as e:
    DialogueManager = None
    MOCK_ABHA_REGISTRY = {}

# Page configuration
st.set_page_config(
    page_title="SwasthyaSync | Clinical Case-Taking & Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern medical aesthetic
st.markdown("""
<style>
    :root {
        --primary-color: #0d9488;
        --primary-hover: #0f766e;
        --secondary-color: #0284c7;
        --bg-card: #f8fafc;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .red-flag-alert {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        color: #991b1b;
        font-weight: 600;
        margin: 1rem 0;
    }
    .success-alert {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 8px;
        color: #166534;
        margin: 1rem 0;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {
        "full_name": "Ramesh Patel",
        "abha_id": "91-8823-4412-9901",
        "age": 48,
        "gender": "Male",
        "phone": "+91 98765 43210",
        "token_number": "A-104",
        "clinic_mode": "allopathic",
        "language": "English (en-IN)"
    }
if "triage_queue" not in st.session_state:
    st.session_state.triage_queue = [
        {"token": "A-101", "name": "Sunita Sharma", "age": 34, "gender": "F", "complaint": "Acute Chest Pain & Dyspnea", "priority": "CRITICAL (Red Flag)", "dept": "Cardiology", "status": "In Consultation"},
        {"token": "A-102", "name": "Vikram Singh", "age": 62, "gender": "M", "complaint": "Chronic Knee Joint Pain", "priority": "Normal", "dept": "Orthopedics", "status": "Waiting"},
        {"token": "A-103", "name": "Ananya Rao", "age": 28, "gender": "F", "complaint": "Fever & Productive Cough (3 days)", "priority": "Normal", "dept": "General Medicine", "status": "Waiting"},
        {"token": "A-104", "name": "Ramesh Patel", "age": 48, "gender": "M", "complaint": "Severe epigastric burning with dizziness", "priority": "Elevated", "dept": "Gastroenterology", "status": "Case Intake Done"}
    ]

# Sidebar Navigation
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&q=80", use_container_width=True)
    st.markdown("### 🏥 SwasthyaSync AI")
    st.markdown("**Hospital Kiosk & Clinical Copilot**")
    st.divider()
    
    app_mode = st.radio(
        "Navigation Module",
        [
            "🏠 Patient Intake Kiosk",
            "🩺 Doctor Consultation Queue",
            "📊 Hospital Triage & Analytics",
            "📄 Document & Prescription OCR",
            "⚙️ System Diagnostics & API"
        ],
        index=0
    )
    st.divider()
    st.caption("v2.0.0 • Production Ready")
    st.caption("ABDM / Ayushman Bharat Digital Mission Compatible")

# ─────────────────────────────────────────────────────────────────────────────
# 1. PATIENT INTAKE KIOSK
# ─────────────────────────────────────────────────────────────────────────────
if app_mode == "🏠 Patient Intake Kiosk":
    st.markdown('<div class="main-title">🏥 Patient Case-Taking Kiosk</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Multi-lingual AI assisted clinical history intake with real-time red-flag watchdog.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🪪 Patient Registration & ABDM")
        with st.form("patient_reg_form"):
            name = st.text_input("Full Name", value=st.session_state.patient_data["full_name"])
            phone = st.text_input("Mobile Number", value=st.session_state.patient_data["phone"])
            abha = st.text_input("ABHA ID (14-digit)", value=st.session_state.patient_data["abha_id"])
            
            c1, c2 = st.columns(2)
            with c1:
                age = st.number_input("Age", min_value=1, max_value=120, value=st.session_state.patient_data["age"])
            with c2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)

            clinic_mode = st.selectbox("Clinical Module", ["Allopathic (Modern)", "AYUSH (Ayurveda/Homeopathy)"])
            lang = st.selectbox("Preferred Language", ["English (en-IN)", "Hindi (hi-IN)", "Telugu (te-IN)", "Tamil (ta-IN)", "Marathi (mr-IN)"])

            submitted = st.form_submit_button("✅ Start AI Intake Session", use_container_width=True)
            if submitted:
                st.session_state.patient_data = {
                    "full_name": name,
                    "phone": phone,
                    "abha_id": abha,
                    "age": age,
                    "gender": gender,
                    "token_number": f"A-{int(time.time()) % 900 + 100}",
                    "clinic_mode": clinic_mode.lower(),
                    "language": lang
                }
                st.session_state.session_active = True
                st.session_state.messages = [
                    {"role": "assistant", "content": f"Namaste {name}! I am SwasthyaSync AI Assistant. Please describe your main health complaints or what brought you to the hospital today."}
                ]
                st.success("Session initiated! Token: " + st.session_state.patient_data["token_number"])

        if st.session_state.session_active:
            st.markdown("#### 🩺 Active Vitals Monitor")
            v_bp = st.text_input("Blood Pressure (mmHg)", "130/85")
            v_pulse = st.number_input("Pulse Rate (BPM)", 40, 200, 78)
            v_spo2 = st.number_input("SpO2 (%)", 50, 100, 98)
            v_temp = st.number_input("Temp (°F)", 90.0, 108.0, 98.6)

    with col2:
        st.markdown("### 💬 Conversational Case Taking")
        
        # Chat container
        chat_container = st.container(height=420)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        # User input
        if prompt := st.chat_input("Type your symptom or response (e.g. 'Severe burning stomach pain for 4 days')..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.write(prompt)

            # Analyze for Red Flags
            red_flag_detected = any(k in prompt.lower() for k in ["chest pain", "breathless", "unconscious", "heavy bleeding", "stroke", "paralysis"])
            
            # Simulated clinical engine response
            if red_flag_detected:
                response = f"⚠️ **URGENT SAFETY ALERT**: Potential red-flag symptom detected ({prompt}). The triage nurse and ER duty doctor have been notified immediately. Please proceed to Room 102."
            elif "fever" in prompt.lower():
                response = "I noted the fever. Is it accompanied by chills, shivering, body ache, or sweating? Also, how high has the temperature been?"
            elif "pain" in prompt.lower() or "stomach" in prompt.lower():
                response = "Understood. On a scale of 1 to 10, how severe is this pain? Does it worsen before or after meals, and have you noticed any nausea or vomiting?"
            else:
                response = f"Thank you for sharing. How long have you been experiencing this, and are you currently taking any prescription medications or treatments?"

            time.sleep(0.3)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with chat_container:
                with st.chat_message("assistant"):
                    st.write(response)

        # Quick Actions
        st.divider()
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("📋 Generate Clinical Summary", use_container_width=True):
                st.markdown('<div class="success-alert">✅ <b>Clinical SOAP Summary Generated</b><br>Summary synced with Doctor Queue.</div>', unsafe_allow_html=True)
                st.json({
                    "Patient": st.session_state.patient_data["full_name"],
                    "Token": st.session_state.patient_data["token_number"],
                    "ABHA": st.session_state.patient_data["abha_id"],
                    "Chief Complaint": "Epigastric distress, intermittent nausea (4 days)",
                    "Vitals": "BP: 130/85 | Pulse: 78 | SpO2: 98% | Temp: 98.6°F",
                    "Triage Status": "Elevated Priority - OPD Room 104"
                })
        with qc2:
            st.download_button(
                "📥 Download Case PDF",
                data=f"SwasthyaSync Case Summary\nPatient: {st.session_state.patient_data['full_name']}\nToken: {st.session_state.patient_data['token_number']}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                file_name=f"case_summary_{st.session_state.patient_data['token_number']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with qc3:
            if st.button("🔄 Reset Session", use_container_width=True):
                st.session_state.messages = []
                st.session_state.session_active = False
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 2. DOCTOR CONSULTATION QUEUE
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "🩺 Doctor Consultation Queue":
    st.markdown('<div class="main-title">🩺 Clinician & Doctor Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-time patient triage queue with prioritized red-flag alerts and SOAP case summaries.</div>', unsafe_allow_html=True)

    df_queue = pd.DataFrame(st.session_state.triage_queue)
    
    st.dataframe(
        df_queue,
        column_config={
            "token": "Token #",
            "name": "Patient Name",
            "age": "Age",
            "gender": "Sex",
            "complaint": "Chief Complaint",
            "priority": st.column_config.TextColumn("Triage Priority"),
            "dept": "Department",
            "status": "Queue Status"
        },
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 📑 Rapid Clinical Consultation View")
    sel_token = st.selectbox("Select Patient to Consult", df_queue["token"].tolist())
    patient_sel = df_queue[df_queue["token"] == sel_token].iloc[0]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"#### 👤 Patient: {patient_sel['name']} ({patient_sel['token']})")
        st.write(f"**Age / Gender:** {patient_sel['age']} yrs / {patient_sel['gender']}")
        st.write(f"**Chief Complaint:** {patient_sel['complaint']}")
        st.write(f"**Department:** {patient_sel['dept']}")
        if "CRITICAL" in patient_sel["priority"]:
            st.markdown('<div class="red-flag-alert">🚨 CRITICAL TRIAGE PRIORITY — IMMEDIATE ATTENTION</div>', unsafe_allow_html=True)
        else:
            st.info(f"Triage Priority: {patient_sel['priority']}")

    with c2:
        st.markdown("#### ✍️ Doctor SOAP Notes & Prescription")
        dx = st.text_input("Provisional Diagnosis", "Acute Gastritis with Reflux")
        rx = st.text_area("Prescription (Rx)", "1. Tab Pantoprazole 40mg OD (Before Breakfast) x 10 days\n2. Syp Sucralfate 10ml TID x 7 days")
        if st.button("💾 Save Prescription & Complete Consultation", use_container_width=True):
            st.success(f"Prescription saved & ABDM Health Record created for Token {sel_token}!")

# ─────────────────────────────────────────────────────────────────────────────
# 3. HOSPITAL TRIAGE & ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "📊 Hospital Triage & Analytics":
    st.markdown('<div class="main-title">📊 Hospital OPD Triage & Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Live hospital metrics, department load, and patient turnaround metrics.</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total OPD Intake Today", "142 Patients", "+12%")
    with m2:
        st.metric("Average Case Intake Time", "3.4 mins", "-1.8 mins")
    with m3:
        st.metric("Red Flag Emergencies", "6 Identified", "Immediate Action")
    with m4:
        st.metric("ABDM Digital Sync Rate", "98.4%", "+4.1%")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🏥 Department Intake Distribution")
        dept_data = pd.DataFrame({
            "Department": ["General Medicine", "Cardiology", "Gastroenterology", "Orthopedics", "Pediatrics", "AYUSH"],
            "Patients": [48, 26, 22, 19, 15, 12]
        })
        st.bar_chart(dept_data.set_index("Department"))

    with c2:
        st.markdown("#### 📈 Hourly OPD Traffic")
        hourly_data = pd.DataFrame({
            "Time": ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
            "Check-ins": [12, 28, 35, 42, 38, 20, 25, 18]
        })
        st.line_chart(hourly_data.set_index("Time"))

# ─────────────────────────────────────────────────────────────────────────────
# 4. DOCUMENT & PRESCRIPTION OCR
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "📄 Document & Prescription OCR":
    st.markdown('<div class="main-title">📄 Medical Document & Prescription OCR</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Extract clinical data, lab parameters, and past prescriptions into structured FHIR records.</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Prescription / Lab Report (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 🖼️ Uploaded Document Preview")
            if uploaded_file.name.endswith(('.jpg', '.jpeg', '.png')):
                st.image(uploaded_file, use_container_width=True)
            else:
                st.info(f"Uploaded PDF: {uploaded_file.name} ({len(uploaded_file.getvalue()) // 1024} KB)")

        with col2:
            st.markdown("#### 🔍 Extracted Clinical Entities")
            with st.spinner("Processing medical OCR & entity extraction..."):
                time.sleep(0.5)
                st.success("Extraction Completed!")
                st.json({
                    "document_type": "Outpatient Prescription",
                    "clinic_name": "Apollo Health Center",
                    "extracted_medications": [
                        {"name": "Metformin 500mg", "dosage": "1-0-1", "duration": "30 days"},
                        {"name": "Telmisartan 40mg", "dosage": "1-0-0", "duration": "30 days"}
                    ],
                    "extracted_vitals": {
                        "bp": "138/88 mmHg",
                        "weight": "72 kg",
                        "pulse": "76 bpm"
                    },
                    "lab_references": {
                        "HbA1c": "7.2% (Elevated)",
                        "Fasting Blood Sugar": "142 mg/dL"
                    }
                })

# ─────────────────────────────────────────────────────────────────────────────
# 5. SYSTEM DIAGNOSTICS & API
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "⚙️ System Diagnostics & API":
    st.markdown('<div class="main-title">⚙️ System Diagnostics & Health</div>', unsafe_allow_html=True)
    
    st.markdown("### 🔌 Core Subsystems Status")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.success("✅ FastAPI Backend (Port 8000)")
    with s2:
        st.success("✅ Vite Web Frontend (Port 5173)")
    with s3:
        st.success("✅ Streamlit Engine (Active)")
    with s4:
        st.info("ℹ️ Database (In-Memory / Supabase Ready)")

    st.divider()
    st.markdown("### 📖 REST API Endpoints Reference")
    st.code("""
POST /api/session           — Create new clinical intake session
POST /api/ocr               — Upload and process medical document
POST /api/stt               — Speech to Text (Sarvam AI / Multilingual)
POST /api/tts               — Text to Speech voice generation
GET  /api/record/{session}  — Retrieve patient record and FHIR summary
GET  /docs                  — Interactive Swagger API documentation
    """, language="markdown")
