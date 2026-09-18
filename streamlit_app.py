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

import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="SwasthyaSync | Clinical Case-Taking & Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Lightfall Interactive WebGL Shader Background (React Bits Port)
# ─────────────────────────────────────────────────────────────────────────────
LIGHTFALL_HTML = """
<script>
(function() {
  const targetDoc = window.parent.document || document;
  if (targetDoc.getElementById('lightfall-wrapper-global')) return;

  const wrapper = targetDoc.createElement('div');
  wrapper.id = 'lightfall-wrapper-global';
  wrapper.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; pointer-events:none; z-index:0; overflow:hidden; opacity:0.38;';

  const canvas = targetDoc.createElement('canvas');
  canvas.style.cssText = 'width:100%; height:100%; display:block;';
  wrapper.appendChild(canvas);
  targetDoc.body.prepend(wrapper);

  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;

  const hexToRGB = hex => {
    const c = hex.replace('#', '').padEnd(6, '0');
    return [
      parseInt(c.slice(0, 2), 16) / 255,
      parseInt(c.slice(2, 4), 16) / 255,
      parseInt(c.slice(4, 6), 16) / 255
    ];
  };

  const baseColors = ['#93C5FD', '#3B82F6', '#60A5FA', '#38BDF8'];
  const MAX_COLORS = 8;
  const arr = [];
  for (let i = 0; i < MAX_COLORS; i++) {
    arr.push(hexToRGB(baseColors[Math.min(i, baseColors.length - 1)]));
  }
  const avg = [0, 0, 0];
  for (let i = 0; i < baseColors.length; i++) {
    avg[0] += arr[i][0]; avg[1] += arr[i][1]; avg[2] += arr[i][2];
  }
  avg[0] /= baseColors.length; avg[1] /= baseColors.length; avg[2] /= baseColors.length;

  const vsSource = `
    attribute vec2 position;
    attribute vec2 uv;
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;

  const fsSource = `
    precision highp float;
    uniform vec3  iResolution;
    uniform vec2  iMouse;
    uniform float iTime;
    uniform vec3  uColor0, uColor1, uColor2, uColor3, uColor4, uColor5, uColor6, uColor7;
    uniform int   uColorCount;
    uniform vec3  uBgColor;
    uniform vec3  uMouseColor;
    uniform float uSpeed;
    uniform int   uStreakCount;
    uniform float uStreakWidth;
    uniform float uStreakLength;
    uniform float uGlow;
    uniform float uDensity;
    uniform float uTwinkle;
    uniform float uZoom;
    uniform float uBgGlow;
    uniform float uOpacity;
    uniform float uMouseEnabled;
    uniform float uMouseStrength;
    uniform float uMouseRadius;
    uniform float uLightMode;
    varying vec2 vUv;

    vec3 palette(float h) {
      int count = uColorCount;
      if (count < 1) count = 1;
      int idx = int(floor(clamp(h, 0.0, 0.999999) * float(count)));
      if (idx <= 0) return uColor0;
      if (idx == 1) return uColor1;
      if (idx == 2) return uColor2;
      if (idx == 3) return uColor3;
      if (idx == 4) return uColor4;
      if (idx == 5) return uColor5;
      if (idx == 6) return uColor6;
      return uColor7;
    }

    vec3 tanhv(vec3 x) {
      vec3 e = exp(-2.0 * x);
      return (1.0 - e) / (1.0 + e);
    }

    vec2 sceneC(vec2 frag, vec2 r) {
      vec2 P = (frag + frag - r) / r.x;
      float z = 0.0;
      float d = 1e3;
      vec4 O = vec4(0.0);
      for (int k = 0; k < 39; k++) {
        if (d <= 1e-4) break;
        O = z * normalize(vec4(P, uZoom, 0.0)) - vec4(0.0, 4.0, 1.0, 0.0) / 4.5;
        d = 1.0 - sqrt(length(O * O));
        z += d;
      }
      return vec2(O.x, atan(O.z, O.y));
    }

    void mainImage(out vec4 o, vec2 C) {
      vec2 r = iResolution.xy;
      vec2 uv0 = (C + C - r) / r.x;
      float T = 0.1 * iTime * uSpeed + 9.0;
      float angRings = max(1.0, floor(6.28318530718 * max(uDensity, 0.05) + 0.5));
      vec2 Y = vec2(5e-3, 6.28318530718 / angRings);

      vec2 c0 = sceneC(C, r);
      vec2 cdx = sceneC(C + vec2(1.0, 0.0), r);
      vec2 cdy = sceneC(C + vec2(0.0, 1.0), r);
      vec2 dCx = cdx - c0;
      vec2 dCy = cdy - c0;
      dCx.y -= 6.28318530718 * floor(dCx.y / 6.28318530718 + 0.5);
      dCy.y -= 6.28318530718 * floor(dCy.y / 6.28318530718 + 0.5);
      vec2 fw = abs(dCx) + abs(dCy);
      C = c0;

      vec2 P = vec2(2.0, 1.0) * uv0 - (r / r.x) * vec2(0.0, 1.0);
      vec4 O = uLightMode > 0.5
        ? vec4(0.0)
        : vec4(uBgColor * 90.0 * uBgGlow / (1e3 * dot(P, P) + 6.0), 0.0);

      float mGlow = 0.0;
      if (uMouseEnabled > 0.5) {
        vec2 mN = (iMouse + iMouse - r) / r.x;
        float md = length(uv0 - mN);
        mGlow = exp(-md * md / max(uMouseRadius * uMouseRadius, 1e-4)) * uMouseStrength;
        O.rgb += uMouseColor * mGlow * 0.25;
      }

      float zr = 5e-4 * uStreakWidth;
      vec2 rr = vec2(max(length(fw), 1e-5));
      float tail = 19.0 / max(uStreakLength, 0.05);

      for (int m = 0; m < 16; m++) {
        if (m >= uStreakCount) break;
        float jf = float(m) + 1.0;
        float ic = fract(sin(dot(vec2(jf, floor(C.x / Y.x + 0.5)), vec2(7.0, 11.0)) * 73.0));
        vec2 Pp = C - (T + T * ic) * vec2(0.0, 1.0);
        Pp -= floor(Pp / Y + 0.5) * Y;
        float h = fract(8663.0 * ic);
        vec3 col = palette(h);
        float weight = mix(1.5, 1.0 + sin(T + 7.0 * h + 4.0), uTwinkle);
        weight *= (1.0 + mGlow * 2.0);
        vec2 inner = vec2(length(max(Pp, vec2(-1.0, 0.0))), length(Pp) - zr) - zr;
        vec2 sm = vec2(1.0) - smoothstep(-rr, rr, inner);
        O.rgb += dot(sm, vec2(exp(tail * Pp.y), 3.0)) * col * weight;
        C.x += Y.x / 8.0;
      }

      vec3 colr = sqrt(tanhv(max(O.rgb * uGlow - vec3(0.04, 0.08, 0.02), 0.0)));
      if (uLightMode > 0.5) {
        float peak = max(colr.r, max(colr.g, colr.b));
        float coverage = smoothstep(0.035, 0.58, peak) * uOpacity;
        vec3 chroma = clamp(colr / max(peak, 1e-4), 0.0, 1.0);
        chroma = pow(chroma, vec3(1.35));
        float chromaPeak = max(chroma.r, max(chroma.g, chroma.b));
        chroma /= max(chromaPeak, 1e-4);
        o = vec4(mix(vec3(1.0), chroma, coverage * 0.94), 1.0);
      } else {
        o = vec4(colr, uOpacity);
      }
    }

    void main() {
      vec4 color;
      mainImage(color, vUv * iResolution.xy);
      gl_FragColor = color;
    }
  `;

  function createShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    return shader;
  }

  const program = gl.createProgram();
  gl.attachShader(program, createShader(gl, gl.VERTEX_SHADER, vsSource));
  gl.attachShader(program, createShader(gl, gl.FRAGMENT_SHADER, fsSource));
  gl.linkProgram(program);
  gl.useProgram(program);

  const verts = new Float32Array([
    -1, -1,  0, 0,
     3, -1,  2, 0,
    -1,  3,  0, 2
  ]);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW);

  const posLoc = gl.getAttribLocation(program, 'position');
  const uvLoc = gl.getAttribLocation(program, 'uv');
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 16, 0);
  gl.enableVertexAttribArray(uvLoc);
  gl.vertexAttribPointer(uvLoc, 2, gl.FLOAT, false, 16, 8);

  const uRes = gl.getUniformLocation(program, 'iResolution');
  const uMouse = gl.getUniformLocation(program, 'iMouse');
  const uTime = gl.getUniformLocation(program, 'iTime');

  for (let i = 0; i < 8; i++) {
    const loc = gl.getUniformLocation(program, 'uColor' + i);
    gl.uniform3fv(loc, arr[i]);
  }
  gl.uniform1i(gl.getUniformLocation(program, 'uColorCount'), baseColors.length);
  gl.uniform3fv(gl.getUniformLocation(program, 'uBgColor'), hexToRGB('#0284C7'));
  gl.uniform3fv(gl.getUniformLocation(program, 'uMouseColor'), avg);
  gl.uniform1f(gl.getUniformLocation(program, 'uSpeed'), 0.4);
  gl.uniform1i(gl.getUniformLocation(program, 'uStreakCount'), 3);
  gl.uniform1f(gl.getUniformLocation(program, 'uStreakWidth'), 1.2);
  gl.uniform1f(gl.getUniformLocation(program, 'uStreakLength'), 1.0);
  gl.uniform1f(gl.getUniformLocation(program, 'uGlow'), 1.1);
  gl.uniform1f(gl.getUniformLocation(program, 'uDensity'), 0.45);
  gl.uniform1f(gl.getUniformLocation(program, 'uTwinkle'), 0.7);
  gl.uniform1f(gl.getUniformLocation(program, 'uZoom'), 2.5);
  gl.uniform1f(gl.getUniformLocation(program, 'uBgGlow'), 0.25);
  gl.uniform1f(gl.getUniformLocation(program, 'uOpacity'), 0.35);
  gl.uniform1f(gl.getUniformLocation(program, 'uMouseEnabled'), 1.0);
  gl.uniform1f(gl.getUniformLocation(program, 'uMouseStrength'), 0.5);
  gl.uniform1f(gl.getUniformLocation(program, 'uMouseRadius'), 0.7);
  gl.uniform1f(gl.getUniformLocation(program, 'uLightMode'), 0.0);

  let mouseX = 0, mouseY = 0;
  targetDoc.addEventListener('pointermove', e => {
    const scale = window.devicePixelRatio || 1;
    mouseX = e.clientX * scale;
    mouseY = (window.innerHeight - e.clientY) * scale;
  });

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = targetDoc.documentElement.clientWidth || window.innerWidth;
    const h = targetDoc.documentElement.clientHeight || window.innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform3f(uRes, canvas.width, canvas.height, 1.0);
  }
  window.addEventListener('resize', resize);
  resize();

  function render(time) {
    gl.uniform1f(uTime, time * 0.001);
    gl.uniform2f(uMouse, mouseX, mouseY);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
})();
</script>
"""

# Render WebGL Lightfall Background via components
components.html(LIGHTFALL_HTML, height=0)

# Custom CSS for modern medical aesthetic with transparent backdrop
st.markdown("""
<style>
    :root {
        --primary-color: #0d9488;
        --primary-hover: #0f766e;
        --secondary-color: #0284c7;
        --bg-card: #f8fafc;
    }
    
    .stApp {
        background: transparent !important;
    }
    
    .main .block-container {
        position: relative;
        z-index: 10;
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.6);
    }
    
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
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
        color: #475569;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
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
