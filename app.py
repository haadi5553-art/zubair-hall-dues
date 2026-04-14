import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os
import numpy as np

try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH = True
except ImportError:
    AUTO_REFRESH = False

st.set_page_config(
    page_title="HOLO-MESS v2.1 | UET",
    layout="wide",
    page_icon="⬡",
    initial_sidebar_state="expanded"
)

# ── Theme toggle ───────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
_t = st.session_state["theme"]

# ══════════════════════════════════════════════════════════════════
# MASTER CSS + THREE.JS + TILT JS
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

:root {{
  --cyan:     #00f5ff;
  --magenta:  #ff00ff;
  --green:    #00ff9d;
  --purple:   #bf5af2;
  --orange:   #ff6b35;
  --yellow:   #ffe600;

  {"" if _t=="dark" else "/*"}
  --bg0:      #00000a;
  --bg1:      #05050f;
  --bg2:      #0a0a1a;
  --glass:    rgba(0,245,255,0.04);
  --glass2:   rgba(255,255,255,0.03);
  --border:   rgba(0,245,255,0.15);
  --border2:  rgba(255,0,255,0.12);
  --text1:    #e0f7ff;
  --text2:    #7ecfde;
  --text3:    #3d7a8a;
  --input-bg: rgba(0,245,255,0.05);
  {"" if _t=="dark" else "*/"}

  {"/*" if _t=="dark" else ""}
  --bg0:      #e8f4ff;
  --bg1:      #d0e8ff;
  --bg2:      #c0dcff;
  --glass:    rgba(255,255,255,0.6);
  --glass2:   rgba(0,180,220,0.08);
  --border:   rgba(0,150,200,0.25);
  --border2:  rgba(120,0,200,0.2);
  --text1:    #060a1a;
  --text2:    #0a3a5c;
  --text3:    #1a6a8a;
  --input-bg: rgba(255,255,255,0.8);
  {"*/" if _t=="dark" else ""}
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"] {{
  font-family: 'Inter', sans-serif !important;
  -webkit-font-smoothing: antialiased;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ── App base ── */
.stApp {{
  background: var(--bg0) !important;
  min-height: 100vh;
}}

/* ── 3D Canvas background ── */
#holo-canvas {{
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
}}

/* ── Content above canvas ── */
.block-container {{
  position: relative;
  z-index: 1;
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1500px !important;
}}

/* ══════════ ANIMATED TOP BAR ══════════ */
.stApp::before {{
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    var(--cyan), var(--magenta), var(--green),
    var(--purple), var(--cyan));
  background-size: 400% 100%;
  animation: topbar 3s linear infinite;
  z-index: 9999;
  box-shadow: 0 0 20px var(--cyan), 0 0 40px var(--magenta);
}}
@keyframes topbar {{
  0%   {{ background-position: 0% 0%; }}
  100% {{ background-position: 400% 0%; }}
}}

/* ══════════ SIDEBAR ══════════ */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #02020e 0%, #070718 100%) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 4px 0 40px rgba(0,245,255,0.08) !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: var(--text1) !important; }}
[data-testid="stSidebar"] label {{
  color: var(--cyan) !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.62rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div {{
  background: rgba(0,245,255,0.05) !important;
  border: 1px solid rgba(0,245,255,0.2) !important;
  border-radius: 8px !important;
  color: var(--text1) !important;
  backdrop-filter: blur(10px);
  transition: all 0.2s;
}}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 12px rgba(0,245,255,0.3) !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input {{
  background: rgba(0,245,255,0.05) !important;
  border: 1px solid rgba(0,245,255,0.2) !important;
  border-radius: 8px !important;
  color: var(--text1) !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 12px rgba(0,245,255,0.3) !important;
}}

/* ══════════ SIDEBAR LOGO ══════════ */
.sidebar-logo {{
  padding: 1.5rem 1.25rem 1.25rem;
  border-bottom: 1px solid rgba(0,245,255,0.1);
  margin-bottom: 1.25rem;
  background: linear-gradient(135deg, rgba(0,245,255,0.05), rgba(255,0,255,0.03));
  position: relative;
  overflow: hidden;
}}
.sidebar-logo::before {{
  content: '';
  position: absolute;
  top: 0; left: -100%; width: 200%; height: 1px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
  animation: scan 3s linear infinite;
}}
@keyframes scan {{
  0%   {{ left: -100%; }}
  100% {{ left: 100%; }}
}}
.sidebar-logo h2 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.9rem !important;
  font-weight: 700 !important;
  color: var(--cyan) !important;
  letter-spacing: 0.05em;
  text-shadow: 0 0 12px rgba(0,245,255,0.6);
  margin: 0 !important;
}}
.sidebar-logo p {{
  font-size: 0.6rem !important;
  color: var(--magenta) !important;
  margin-top: 4px !important;
  font-family: 'Orbitron', sans-serif !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  text-shadow: 0 0 8px rgba(255,0,255,0.5);
}}

/* ══════════ BUTTONS ══════════ */
.stButton > button {{
  background: linear-gradient(135deg,
    rgba(0,245,255,0.12), rgba(191,90,242,0.12)) !important;
  color: var(--cyan) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.72rem !important;
  padding: 0.55rem 1.4rem !important;
  letter-spacing: 0.08em !important;
  transition: all 0.25s ease !important;
  backdrop-filter: blur(10px) !important;
  position: relative !important;
  overflow: hidden !important;
  text-transform: uppercase !important;
}}
.stButton > button::before {{
  content: '';
  position: absolute;
  top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg,
    transparent, rgba(0,245,255,0.15), transparent);
  transition: left 0.4s;
}}
.stButton > button:hover {{
  border-color: var(--cyan) !important;
  color: #fff !important;
  box-shadow: 0 0 20px rgba(0,245,255,0.4),
              inset 0 0 20px rgba(0,245,255,0.05) !important;
  transform: translateY(-2px) !important;
}}
.stButton > button:hover::before {{ left: 100%; }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(135deg,
    rgba(255,0,0,0.15), rgba(255,0,255,0.1)) !important;
  border-color: rgba(255,50,50,0.4) !important;
  color: #ff6b6b !important;
}}
.stButton > button[kind="primary"]:hover {{
  box-shadow: 0 0 20px rgba(255,0,80,0.4) !important;
  color: #fff !important;
}}

/* ══════════ DOWNLOAD BUTTON ══════════ */
[data-testid="stDownloadButton"] > button {{
  background: linear-gradient(135deg,
    rgba(0,255,157,0.1), rgba(0,200,120,0.08)) !important;
  border-color: rgba(0,255,157,0.3) !important;
  color: var(--green) !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
  box-shadow: 0 0 20px rgba(0,255,157,0.4) !important;
}}

/* ══════════ TABS ══════════ */
.stTabs [data-baseweb="tab-list"] {{
  background: rgba(0,245,255,0.03) !important;
  border-radius: 10px !important;
  padding: 5px !important;
  border: 1px solid var(--border) !important;
  gap: 3px !important;
  backdrop-filter: blur(15px) !important;
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: 7px !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.65rem !important;
  color: var(--text2) !important;
  padding: 0.45rem 1rem !important;
  letter-spacing: 0.08em !important;
  transition: all 0.2s !important;
  text-transform: uppercase !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
  color: var(--cyan) !important;
  background: rgba(0,245,255,0.06) !important;
}}
.stTabs [aria-selected="true"] {{
  background: linear-gradient(135deg,
    rgba(0,245,255,0.15), rgba(191,90,242,0.1)) !important;
  color: var(--cyan) !important;
  font-weight: 700 !important;
  border: 1px solid rgba(0,245,255,0.3) !important;
  box-shadow: 0 0 15px rgba(0,245,255,0.2),
              inset 0 0 10px rgba(0,245,255,0.05) !important;
  text-shadow: 0 0 8px rgba(0,245,255,0.6) !important;
}}

/* ══════════ METRICS ══════════ */
[data-testid="metric-container"] {{
  background: linear-gradient(135deg,
    rgba(0,245,255,0.05), rgba(191,90,242,0.04)) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 1.25rem 1.5rem !important;
  backdrop-filter: blur(20px) !important;
  transition: all 0.3s ease !important;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 30px rgba(0,0,0,0.3),
              inset 0 1px 0 rgba(0,245,255,0.1) !important;
}}
[data-testid="metric-container"]::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent, var(--cyan), var(--magenta), transparent);
  opacity: 0.6;
}}
[data-testid="metric-container"]::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 80% 20%,
    rgba(0,245,255,0.06) 0%, transparent 60%);
  pointer-events: none;
}}
[data-testid="metric-container"]:hover {{
  transform: translateY(-4px) !important;
  box-shadow: 0 12px 40px rgba(0,0,0,0.4),
              0 0 30px rgba(0,245,255,0.15) !important;
  border-color: rgba(0,245,255,0.35) !important;
}}
[data-testid="stMetricValue"] {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 1.65rem !important;
  font-weight: 800 !important;
  color: var(--cyan) !important;
  letter-spacing: -0.02em !important;
  text-shadow: 0 0 20px rgba(0,245,255,0.5) !important;
  -webkit-text-fill-color: initial !important;
}}
[data-testid="stMetricLabel"] {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.6rem !important;
  font-weight: 600 !important;
  color: var(--text3) !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
}}
[data-testid="stMetricDelta"] {{
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  color: var(--green) !important;
}}

/* ══════════ HEADINGS ══════════ */
h1 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 1.7rem !important;
  font-weight: 900 !important;
  color: var(--cyan) !important;
  letter-spacing: 0.04em !important;
  text-shadow: 0 0 30px rgba(0,245,255,0.4),
               0 0 60px rgba(0,245,255,0.2) !important;
  -webkit-text-fill-color: initial !important;
  animation: glitch-h1 8s infinite;
}}
@keyframes glitch-h1 {{
  0%, 92%, 100% {{ text-shadow: 0 0 30px rgba(0,245,255,0.4); }}
  93% {{ text-shadow: 3px 0 var(--magenta), -3px 0 var(--cyan); }}
  94% {{ text-shadow: -3px 0 var(--magenta), 3px 0 var(--cyan); }}
  95% {{ text-shadow: 0 0 30px rgba(0,245,255,0.4); }}
}}
h2 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  color: var(--text1) !important;
}}
h3 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  color: var(--text2) !important;
}}

/* ══════════ DATAFRAME ══════════ */
[data-testid="stDataFrame"] {{
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 4px 30px rgba(0,0,0,0.3),
              0 0 20px rgba(0,245,255,0.05) !important;
}}
.dataframe thead th {{
  background: rgba(0,245,255,0.08) !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.6rem !important;
  font-weight: 700 !important;
  color: var(--cyan) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  padding: 12px 14px !important;
  border-bottom: 1px solid var(--border) !important;
  text-shadow: 0 0 8px rgba(0,245,255,0.4) !important;
}}
.dataframe td {{
  font-size: 0.84rem !important;
  color: var(--text1) !important;
  padding: 10px 14px !important;
  border-bottom: 1px solid rgba(0,245,255,0.05) !important;
}}
.dataframe tr:hover td {{
  background: rgba(0,245,255,0.04) !important;
}}

/* ══════════ ALERTS ══════════ */
.stSuccess {{
  background: rgba(0,255,157,0.08) !important;
  border: 1px solid rgba(0,255,157,0.3) !important;
  border-radius: 10px !important;
  color: var(--green) !important;
}}
.stWarning {{
  background: rgba(255,230,0,0.08) !important;
  border: 1px solid rgba(255,230,0,0.3) !important;
  border-radius: 10px !important;
}}
.stInfo {{
  background: rgba(0,245,255,0.06) !important;
  border: 1px solid rgba(0,245,255,0.2) !important;
  border-radius: 10px !important;
}}
.stError {{
  background: rgba(255,50,50,0.08) !important;
  border: 1px solid rgba(255,50,50,0.3) !important;
  border-radius: 10px !important;
}}

/* ══════════ INPUTS ══════════ */
.stSelectbox > div > div {{
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
  background: var(--input-bg) !important;
  color: var(--text1) !important;
  backdrop-filter: blur(10px) !important;
  transition: all 0.2s !important;
}}
.stSelectbox > div > div:focus-within {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 15px rgba(0,245,255,0.25) !important;
}}
.stNumberInput > div > div > input,
.stTextInput > div > div > input {{
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
  background: var(--input-bg) !important;
  color: var(--text1) !important;
  transition: all 0.2s !important;
}}
.stNumberInput > div > div > input:focus,
.stTextInput > div > div > input:focus {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 15px rgba(0,245,255,0.25) !important;
}}
label {{ color: var(--text2) !important; }}

/* ══════════ FILE UPLOADER ══════════ */
[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed rgba(0,245,255,0.3) !important;
  border-radius: 12px !important;
  background: rgba(0,245,255,0.03) !important;
  transition: all 0.3s !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{
  border-color: var(--cyan) !important;
  background: rgba(0,245,255,0.07) !important;
  box-shadow: 0 0 20px rgba(0,245,255,0.15) !important;
}}

/* ══════════ EXPANDER ══════════ */
[data-testid="stExpander"] {{
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  background: rgba(0,245,255,0.03) !important;
  backdrop-filter: blur(10px) !important;
  transition: all 0.2s !important;
}}
[data-testid="stExpander"]:hover {{
  border-color: rgba(0,245,255,0.3) !important;
  box-shadow: 0 0 20px rgba(0,245,255,0.08) !important;
}}
[data-testid="stExpander"] summary {{
  color: var(--cyan) !important;
  font-weight: 600 !important;
}}

/* ══════════ SECTION HEADER ══════════ */
.section-header {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.58rem;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 0.85rem;
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 10px;
  text-shadow: 0 0 10px rgba(0,245,255,0.5);
}}
.section-header::before {{
  content: '';
  display: inline-block;
  width: 20px; height: 1px;
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  box-shadow: 0 0 6px var(--cyan);
}}
.section-header::after {{
  content: '';
  flex: 1; height: 1px;
  background: linear-gradient(90deg, rgba(0,245,255,0.2), transparent);
}}

/* ══════════ PAGE HEADER WRAP ══════════ */
.page-header-wrap {{
  background: linear-gradient(135deg,
    rgba(0,245,255,0.05), rgba(191,90,242,0.04));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.75rem 2rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 40px rgba(0,0,0,0.3),
              inset 0 1px 0 rgba(0,245,255,0.12);
}}
.page-header-wrap::before {{
  content: '';
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: conic-gradient(
    from 0deg at 50% 50%,
    transparent 0deg,
    rgba(0,245,255,0.03) 60deg,
    transparent 120deg
  );
  animation: rotate-glow 10s linear infinite;
  pointer-events: none;
}}
.page-header-wrap::after {{
  content: 'NEURAL LINK ACTIVE';
  position: absolute;
  top: 12px; right: 18px;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.5rem;
  color: var(--green);
  letter-spacing: 0.15em;
  text-shadow: 0 0 8px rgba(0,255,157,0.6);
  animation: blink 2s infinite;
}}
@keyframes rotate-glow {{
  0%   {{ transform: rotate(0deg); }}
  100% {{ transform: rotate(360deg); }}
}}
@keyframes blink {{
  0%, 100% {{ opacity: 1; }}
  50%  {{ opacity: 0.3; }}
}}

/* ══════════ SCROLLBAR ══════════ */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: rgba(0,245,255,0.03); }}
::-webkit-scrollbar-thumb {{
  background: linear-gradient(var(--cyan), var(--magenta));
  border-radius: 3px;
}}

/* ══════════ HR ══════════ */
hr {{
  border: none !important;
  height: 1px !important;
  background: linear-gradient(90deg,
    transparent, var(--border), transparent) !important;
  margin: 1.5rem 0 !important;
}}

/* ══════════ CAPTION ══════════ */
.stCaption {{ color: var(--text3) !important; font-size: 0.72rem !important; }}

/* ══════════ TILT CARD WRAPPER ══════════ */
.tilt-card {{
  transform-style: preserve-3d;
  perspective: 1000px;
  transition: transform 0.1s ease;
}}

/* ══════════ SCAN LINE OVERLAY ══════════ */
.scanlines {{
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,245,255,0.015) 2px,
    rgba(0,245,255,0.015) 4px
  );
  pointer-events: none;
  border-radius: inherit;
}}

/* ══════════ STATUS BADGES GLITCH ══════════ */
.badge-paid    {{ animation: glow-green 2s infinite alternate; }}
.badge-partial {{ animation: glow-blue  2s infinite alternate; }}
.badge-unpaid  {{ animation: glow-red   2s infinite alternate; }}
@keyframes glow-green  {{ from {{ box-shadow: 0 0 6px #00ff9d; }} to {{ box-shadow: 0 0 16px #00ff9d, 0 0 30px rgba(0,255,157,0.3); }} }}
@keyframes glow-blue   {{ from {{ box-shadow: 0 0 6px #00f5ff; }} to {{ box-shadow: 0 0 16px #00f5ff, 0 0 30px rgba(0,245,255,0.3); }} }}
@keyframes glow-red    {{ from {{ box-shadow: 0 0 6px #ff2d55; }} to {{ box-shadow: 0 0 16px #ff2d55, 0 0 30px rgba(255,45,85,0.3); }} }}

/* ══════════ NEON PROGRESS BAR ══════════ */
@keyframes neon-flow {{
  0%   {{ background-position: 0% 50%; }}
  100% {{ background-position: 200% 50%; }}
}}
.neon-bar {{
  background: linear-gradient(90deg,
    #00f5ff, #00ff9d, #bf5af2, #00f5ff);
  background-size: 200% 100%;
  animation: neon-flow 2s linear infinite;
  box-shadow: 0 0 10px currentColor;
}}

/* ══════════ FLOATING ANIMATION ══════════ */
@keyframes float {{
  0%, 100% {{ transform: translateY(0px); }}
  50%       {{ transform: translateY(-6px); }}
}}
</style>

<!-- THREE.JS 3D HOLOGRAPHIC BACKGROUND - deferred for fast load -->
<canvas id="holo-canvas"></canvas>
<script>
window.addEventListener('load', function() {{
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  s.onload = initHoloBackground;
  document.head.appendChild(s);
}});

function initHoloBackground() {{
  const canvas = document.getElementById('holo-canvas');
  if (!canvas) return;

  const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 60;

  // ── Particles ──
  const PARTICLE_COUNT = 90;
  const pGeo = new THREE.BufferGeometry();
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const colors    = new Float32Array(PARTICLE_COUNT * 3);
  const sizes     = new Float32Array(PARTICLE_COUNT);
  const speeds    = new Float32Array(PARTICLE_COUNT);

  const neonColors = [
    new THREE.Color(0x00f5ff),
    new THREE.Color(0xff00ff),
    new THREE.Color(0x00ff9d),
    new THREE.Color(0xbf5af2),
  ];

  for (let i = 0; i < PARTICLE_COUNT; i++) {{
    positions[i * 3]     = (Math.random() - 0.5) * 200;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 120;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 100;
    const c = neonColors[Math.floor(Math.random() * neonColors.length)];
    colors[i * 3]     = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
    sizes[i]  = Math.random() * 2.5 + 0.5;
    speeds[i] = Math.random() * 0.3 + 0.05;
  }}

  pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  pGeo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
  pGeo.setAttribute('size',     new THREE.BufferAttribute(sizes, 1));

  const pMat = new THREE.PointsMaterial({{
    size: 0.8, vertexColors: true, transparent: true, opacity: 0.7,
    sizeAttenuation: true, blending: THREE.AdditiveBlending, depthWrite: false
  }});
  const particles = new THREE.Points(pGeo, pMat);
  scene.add(particles);

  // ── Connection Lines ──
  const lineMat = new THREE.LineBasicMaterial({{
    color: 0x00f5ff, transparent: true, opacity: 0.08,
    blending: THREE.AdditiveBlending, depthWrite: false
  }});

  const lines = [];
  const CONNECTION_DIST = 30;

  function rebuildLines() {{
    lines.forEach(l => scene.remove(l));
    lines.length = 0;
    const pos = pGeo.attributes.position.array;
    for (let i = 0; i < PARTICLE_COUNT; i++) {{
      for (let j = i + 1; j < PARTICLE_COUNT; j++) {{
        const dx = pos[i*3]   - pos[j*3];
        const dy = pos[i*3+1] - pos[j*3+1];
        const dz = pos[i*3+2] - pos[j*3+2];
        const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
        if (dist < CONNECTION_DIST) {{
          const geo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(pos[i*3], pos[i*3+1], pos[i*3+2]),
            new THREE.Vector3(pos[j*3], pos[j*3+1], pos[j*3+2])
          ]);
          const alpha = (1 - dist / CONNECTION_DIST) * 0.12;
          const m = lineMat.clone();
          m.opacity = alpha;
          const line = new THREE.Line(geo, m);
          scene.add(line);
          lines.push(line);
        }}
      }}
    }}
  }}

  // ── Glowing orbs ──
  const orbGeo = new THREE.SphereGeometry(0.4, 8, 8);
  const orbs = [];
  for (let i = 0; i < 12; i++) {{
    const c = neonColors[i % neonColors.length];
    const mat = new THREE.MeshBasicMaterial({{
      color: c, transparent: true, opacity: 0.8,
      blending: THREE.AdditiveBlending
    }});
    const orb = new THREE.Mesh(orbGeo, mat);
    orb.position.set(
      (Math.random() - 0.5) * 140,
      (Math.random() - 0.5) * 80,
      (Math.random() - 0.5) * 60
    );
    orb.userData = {{
      vx: (Math.random() - 0.5) * 0.08,
      vy: (Math.random() - 0.5) * 0.08,
      vz: (Math.random() - 0.5) * 0.04,
      phase: Math.random() * Math.PI * 2
    }};
    scene.add(orb);
    orbs.push(orb);
  }}

  // ── Grid plane ──
  const gridHelper = new THREE.GridHelper(200, 30, 0x00f5ff, 0x0a2a2a);
  gridHelper.material.transparent = true;
  gridHelper.material.opacity = 0.06;
  gridHelper.position.y = -40;
  scene.add(gridHelper);

  let frame = 0;
  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', e => {{
    mouseX = (e.clientX / window.innerWidth  - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  }});

  function animate() {{
    requestAnimationFrame(animate);
    frame++;

    const pos = pGeo.attributes.position.array;
    for (let i = 0; i < PARTICLE_COUNT; i++) {{
      pos[i * 3 + 1] += speeds[i] * 0.08;
      if (pos[i * 3 + 1] > 60) pos[i * 3 + 1] = -60;
    }}
    pGeo.attributes.position.needsUpdate = true;

    if (frame % 20 === 0) rebuildLines();

    orbs.forEach((orb, i) => {{
      orb.position.x += orb.userData.vx;
      orb.position.y += orb.userData.vy;
      orb.position.z += orb.userData.vz;
      if (Math.abs(orb.position.x) > 80) orb.userData.vx *= -1;
      if (Math.abs(orb.position.y) > 45) orb.userData.vy *= -1;
      if (Math.abs(orb.position.z) > 35) orb.userData.vz *= -1;
      const pulse = Math.sin(frame * 0.03 + orb.userData.phase);
      orb.material.opacity = 0.4 + pulse * 0.35;
      const s = 0.8 + pulse * 0.4;
      orb.scale.set(s, s, s);
    }});

    gridHelper.rotation.y += 0.0005;

    camera.position.x += (mouseX * 8 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 5 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    particles.rotation.y += 0.0002;
    particles.rotation.x += 0.0001;

    renderer.render(scene, camera);
  }}

  window.addEventListener('resize', () => {{
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }});

  animate();
}}
</script>

<!-- TILT + SHINE JS -->
<script>
document.addEventListener('DOMContentLoaded', function() {{
  function initTilt(el) {{
    el.addEventListener('mousemove', function(e) {{
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width  - 0.5;
      const y = (e.clientY - rect.top)  / rect.height - 0.5;
      el.style.transform = `perspective(800px) rotateY(${{x * 14}}deg) rotateX(${{-y * 10}}deg) translateZ(8px)`;
      const shine = el.querySelector('.holo-shine');
      if (shine) {{
        shine.style.background = `radial-gradient(circle at ${{(x+0.5)*100}}% ${{(y+0.5)*100}}%, rgba(0,245,255,0.18) 0%, rgba(255,0,255,0.08) 40%, transparent 70%)`;
      }}
    }});
    el.addEventListener('mouseleave', function() {{
      el.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) translateZ(0px)';
      el.style.transition = 'transform 0.5s ease';
      const shine = el.querySelector('.holo-shine');
      if (shine) shine.style.background = 'transparent';
    }});
    el.addEventListener('mouseenter', function() {{
      el.style.transition = 'transform 0.1s ease';
    }});
  }}

  const observer = new MutationObserver(function() {{
    document.querySelectorAll('.holo-tilt:not([data-tilt-init])').forEach(function(el) {{
      el.setAttribute('data-tilt-init', '1');
      initTilt(el);
    }});
  }});
  observer.observe(document.body, {{ childList: true, subtree: true }});
  document.querySelectorAll('.holo-tilt').forEach(initTilt);
}});
</script>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════
def get_gspread_client():
    creds = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds,
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(credentials)

def get_spreadsheet():
    return get_gspread_client().open("Hostel Dues Data")

@st.cache_data(ttl=30, show_spinner=False)
def load_all_sheets_data():
    try:
        sh = get_spreadsheet()
        result = {}
        for ws in sh.worksheets():
            try:
                records = ws.get_all_records()
                result[ws.title] = pd.DataFrame(records) if records else pd.DataFrame()
            except Exception:
                result[ws.title] = pd.DataFrame()
        return result
    except Exception as e:
        st.error(f"Google Sheets connection error: {e}")
        return {}

def invalidate_cache():
    load_all_sheets_data.clear()

def find_sheet_key(all_data, name):
    name_clean = name.strip().lower().replace(" ", "")
    for key in all_data:
        if key.strip().lower().replace(" ", "") == name_clean:
            return key
    return None

def standardize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    col_map = {
        "room no": "RoomNo", "roomno": "RoomNo", "room no.": "RoomNo",
        "room": "RoomNo", "room_no": "RoomNo",
        "name": "Name", "student name": "Name", "student_name": "Name",
        "food dues": "Food_Dues", "food_dues": "Food_Dues", "fooddues": "Food_Dues",
        "service charges": "Service_Charges", "service_charges": "Service_Charges",
        "servicecharges": "Service_Charges",
        "previous": "Previous", "prev": "Previous", "arrears": "Previous",
        "month": "Month",
    }
    df = df.rename(columns=col_map)
    for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
        if col not in df.columns:
            df[col] = "" if col in ["RoomNo", "Name"] else 0
    return df

def get_dues_from_cache(all_data, hall):
    key = find_sheet_key(all_data, hall)
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])
    df = all_data[key].copy()
    df = standardize_columns(df)
    if "Month" not in df.columns:
        df["Month"] = "Unknown"
    df["Month"] = df["Month"].astype(str).str.strip()
    for col in ["Food_Dues", "Service_Charges", "Previous"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
    df["Name"]   = df["Name"].astype(str).str.strip()
    df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]
    return df

def get_payments_from_cache(all_data, hall):
    key = find_sheet_key(all_data, f"{hall}_Payments")
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_File","File_Hash"])
    return all_data[key].copy()

def clean_for_sheets(df):
    df = df.copy().fillna("")
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: int(x)   if isinstance(x, (np.integer,))  else
                      float(x) if isinstance(x, (np.floating,)) else
                      bool(x)  if isinstance(x, (np.bool_,))    else
                      str(x)   if not isinstance(x, (str, int, float, bool)) else x
        )
    return df

def find_or_create_worksheet(name):
    sh = get_spreadsheet()
    clean = name.strip().lower().replace(" ", "")
    for ws in sh.worksheets():
        if ws.title.strip().lower().replace(" ", "") == clean:
            return ws
    return sh.add_worksheet(title=name, rows=5000, cols=20)

def save_dues(df, hall):
    ws = find_or_create_worksheet(hall)
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()

def save_payments(df, hall):
    ws = find_or_create_worksheet(f"{hall}_Payments")
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()

if not os.path.exists("receipts"):
    os.makedirs("receipts")


# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
halls = [
    "SMG Hall", "MBQ Hall", "EIDHI Hall", "ZUBAIR Hall", "MUMTAZ Hall",
    "LIAQUAT Hall", "QUAID AZAM Hall", "IQBAL Hall", "SIR SYED Hall"
]
hall_passwords = {
    "SMG Hall": "smg123", "MBQ Hall": "mbq456", "EIDHI Hall": "eidhi789",
    "ZUBAIR Hall": "zubair012", "MUMTAZ Hall": "mumtaz345",
    "LIAQUAT Hall": "liaquat678", "QUAID AZAM Hall": "quaid901",
    "IQBAL Hall": "iqbal234", "SIR SYED Hall": "syed567",
}
senior_password = "senior@1122"


# ══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ══════════════════════════════════════════════════════════════════
def page_header(title, subtitle=""):
    theme_icon  = "☀️" if st.session_state.get("theme","dark") == "dark" else "🌙"
    theme_label = "LIGHT" if st.session_state.get("theme","dark") == "dark" else "DARK"
    st.markdown(f"""
<div class="page-header-wrap">
  <h1 style="margin:0;padding:0;">{title}</h1>
  {"" if not subtitle else f'<p style="color:var(--text2);margin:8px 0 0;font-size:0.82rem;font-family:Orbitron,sans-serif;letter-spacing:0.05em;">{subtitle}</p>'}
</div>
""", unsafe_allow_html=True)
    _c1, _c2 = st.columns([8, 1])
    with _c2:
        if st.button(f"{theme_icon} {theme_label}", key="theme_toggle_btn"):
            st.session_state["theme"] = "light" if st.session_state.get("theme","dark") == "dark" else "dark"
            st.rerun()

def section_label(text):
    st.markdown(f'<p class="section-header">{text}</p>', unsafe_allow_html=True)

def status_badge(label, cls):
    colors = {
        "paid":    ("rgba(0,255,157,0.15)", "#00ff9d", "badge-paid"),
        "partial": ("rgba(0,245,255,0.12)", "#00f5ff", "badge-partial"),
        "unpaid":  ("rgba(255,45,85,0.15)", "#ff2d55", "badge-unpaid"),
    }
    bg, col, anim = colors.get(cls, ("rgba(255,255,255,0.1)", "#fff", ""))
    return f'<span class="{anim}" style="background:{bg};color:{col};border:1px solid {col}40;padding:4px 12px;border-radius:999px;font-family:Orbitron,sans-serif;font-size:0.6rem;font-weight:700;letter-spacing:0.1em;">{label}</span>'

def student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    if paid_amount >= total:
        accent, glow, badge_bg, badge_cls = "#00ff9d", "rgba(0,255,157,0.15)", "linear-gradient(135deg,#00ff9d,#00cc7a)", "paid"
        badge_txt   = "✓ PAID IN FULL"
        amount_html = f'<span style="color:#00ff9d;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;text-shadow:0 0 10px rgba(0,255,157,0.5);">Rs&nbsp;{int(total):,} — CLEARED</span>'
    elif paid_amount > 0:
        accent, glow, badge_bg, badge_cls = "#00f5ff", "rgba(0,245,255,0.12)", "linear-gradient(135deg,#00f5ff,#0099bb)", "partial"
        badge_txt   = "◑ PARTIAL"
        amount_html = f'<span style="color:#00f5ff;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;text-shadow:0 0 10px rgba(0,245,255,0.5);">Paid: Rs&nbsp;{int(paid_amount):,} · Due: Rs&nbsp;{int(remaining):,}</span>'
    else:
        accent, glow, badge_bg, badge_cls = "#ff2d55", "rgba(255,45,85,0.12)", "linear-gradient(135deg,#ff2d55,#cc0033)", "unpaid"
        badge_txt   = "✗ UNPAID"
        amount_html = f'<span style="color:#ff2d55;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;text-shadow:0 0 10px rgba(255,45,85,0.5);">Rs&nbsp;{int(total):,} — OUTSTANDING</span>'

    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    pct   = int(paid_amount / total * 100) if total else 0
    bar_w = min(100, pct)
    badge_html = status_badge(badge_txt, badge_cls)

    st.markdown(f"""
<div class="holo-tilt" style="
  background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(5,5,20,0.8));
  border: 1px solid {accent}40;
  border-radius: 16px;
  padding: 18px 22px;
  margin-bottom: 10px;
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 30px {glow}, inset 0 1px 0 rgba(255,255,255,0.05);
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  cursor: default;
">
  <div class="scanlines"></div>
  <div class="holo-shine" style="position:absolute;inset:0;pointer-events:none;border-radius:16px;transition:background 0.15s;"></div>
  <!-- Accent corner -->
  <div style="position:absolute;top:0;right:0;width:60px;height:60px;
    background:radial-gradient(circle at top right, {accent}20, transparent 70%);
    pointer-events:none;"></div>

  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;position:relative;z-index:1;">
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="width:48px;height:48px;border-radius:12px;
        background:{badge_bg};
        display:flex;align-items:center;justify-content:center;
        font-family:Orbitron,sans-serif;font-size:14px;font-weight:900;color:#fff;flex-shrink:0;
        box-shadow:0 4px 16px {glow};
        border:1px solid {accent}50;">{initials}</div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#e0f7ff;letter-spacing:0.01em;">{name}</div>
        <div style="font-size:0.72rem;color:var(--text3);margin-top:2px;font-family:Orbitron,sans-serif;letter-spacing:0.06em;">
          ROOM&nbsp;<strong style="color:{accent};text-shadow:0 0 8px {accent}80;">{room}</strong>
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
      {badge_html}
      {amount_html}
    </div>
  </div>

  <!-- Progress bar -->
  <div style="margin-top:14px;position:relative;z-index:1;">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
      <span style="font-family:Orbitron,sans-serif;font-size:0.55rem;color:var(--text3);letter-spacing:0.1em;">PAYMENT PROGRESS</span>
      <span style="font-family:Orbitron,sans-serif;font-size:0.55rem;color:{accent};text-shadow:0 0 6px {accent}80;">{pct}%</span>
    </div>
    <div style="background:rgba(255,255,255,0.05);border-radius:999px;height:4px;overflow:hidden;border:1px solid rgba(255,255,255,0.04);">
      <div class="neon-bar" style="height:4px;width:{bar_w}%;border-radius:999px;transition:width 0.6s ease;"></div>
    </div>
  </div>

  <!-- Breakdown -->
  <div style="margin-top:12px;padding-top:12px;border-top:1px solid {accent}20;
    display:flex;gap:20px;flex-wrap:wrap;position:relative;z-index:1;">
    <span style="font-size:0.75rem;color:var(--text3);">Food&nbsp;<strong style="color:#e0f7ff;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(food):,}</strong></span>
    <span style="font-size:0.75rem;color:var(--text3);">Service&nbsp;<strong style="color:#e0f7ff;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(service):,}</strong></span>
    <span style="font-size:0.75rem;color:var(--text3);">Arrears&nbsp;<strong style="color:#e0f7ff;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(prev):,}</strong></span>
    <span style="font-size:0.75rem;color:var(--text3);">Total&nbsp;<strong style="color:{accent};font-size:0.88rem;font-variant-numeric:tabular-nums;text-shadow:0 0 8px {accent}60;">Rs&nbsp;{int(total):,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

def receipt_card(room, name, amount, date, idx):
    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    amt_fmt  = f"Rs\u00a0{int(float(amount)):,}" if amount else "Rs\u00a00"
    st.markdown(f"""
<div class="holo-tilt" style="
  background:linear-gradient(135deg,rgba(0,0,0,0.5),rgba(0,20,15,0.7));
  border:1px solid rgba(0,255,157,0.2);
  border-radius:14px;padding:14px 18px;margin-bottom:8px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;
  backdrop-filter:blur(15px);
  box-shadow:0 2px 20px rgba(0,255,157,0.08);
  position:relative;overflow:hidden;transform-style:preserve-3d;
">
  <div class="holo-shine" style="position:absolute;inset:0;pointer-events:none;border-radius:14px;"></div>
  <div class="scanlines"></div>
  <div style="display:flex;align-items:center;gap:12px;position:relative;z-index:1;">
    <div style="width:40px;height:40px;border-radius:10px;
      background:linear-gradient(135deg,#00ff9d,#00cc7a);
      display:flex;align-items:center;justify-content:center;
      font-family:Orbitron,sans-serif;font-size:12px;font-weight:800;color:#000;
      box-shadow:0 4px 12px rgba(0,255,157,0.4);">{initials}</div>
    <div>
      <div style="font-size:0.9rem;font-weight:700;color:#e0f7ff;">{name}</div>
      <div style="font-size:0.7rem;color:var(--text3);margin-top:1px;font-family:Orbitron,sans-serif;letter-spacing:0.06em;">
        RM&nbsp;<strong style="color:#00f5ff;">{room}</strong>
        &nbsp;·&nbsp;<span>{date}</span>
      </div>
    </div>
  </div>
  <div style="font-family:Orbitron,sans-serif;font-size:1.1rem;font-weight:900;
    color:#00ff9d;text-shadow:0 0 12px rgba(0,255,157,0.6);
    font-variant-numeric:tabular-nums;position:relative;z-index:1;">{amt_fmt}</div>
</div>
""", unsafe_allow_html=True)

def hall_summary_card(hall_name, total, collected, remaining, pct_int):
    if total == 0:
        accent, glow, badge_bg = "#475569", "rgba(71,85,105,0.1)", "linear-gradient(135deg,#475569,#334155)"
    elif remaining == 0:
        accent, glow, badge_bg = "#00ff9d", "rgba(0,255,157,0.12)", "linear-gradient(135deg,#00ff9d,#00cc7a)"
    elif collected > 0:
        accent, glow, badge_bg = "#00f5ff", "rgba(0,245,255,0.12)", "linear-gradient(135deg,#00f5ff,#0099bb)"
    else:
        accent, glow, badge_bg = "#ff2d55", "rgba(255,45,85,0.12)", "linear-gradient(135deg,#ff2d55,#cc0033)"

    bar_width = min(100, pct_int)
    st.markdown(f"""
<div class="holo-tilt" style="
  background:linear-gradient(135deg,rgba(0,0,0,0.55),rgba(5,5,20,0.75));
  border:1px solid {accent}35;
  border-left:3px solid {accent};
  border-radius:16px;padding:18px 22px;margin-bottom:10px;
  backdrop-filter:blur(20px);
  box-shadow:0 4px 30px {glow}, inset 0 1px 0 rgba(255,255,255,0.04);
  position:relative;overflow:hidden;transform-style:preserve-3d;
">
  <div class="scanlines"></div>
  <div class="holo-shine" style="position:absolute;inset:0;pointer-events:none;border-radius:16px;"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;position:relative;z-index:1;">
    <div>
      <div style="font-family:Orbitron,sans-serif;font-size:0.88rem;font-weight:700;
        color:#e0f7ff;text-shadow:0 0 10px {accent}60;">{hall_name}</div>
      <div style="font-size:0.72rem;color:var(--text3);margin-top:3px;letter-spacing:0.03em;">
        Outstanding:&nbsp;<strong style="color:#e0f7ff;font-variant-numeric:tabular-nums;">Rs&nbsp;{total:,}</strong>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-family:Orbitron,sans-serif;font-size:1.7rem;font-weight:900;
        color:{accent};text-shadow:0 0 16px {accent}80;font-variant-numeric:tabular-nums;">{pct_int}%</div>
      <div style="font-family:Orbitron,sans-serif;font-size:0.5rem;color:var(--text3);font-weight:700;letter-spacing:0.14em;">COLLECTED</div>
    </div>
  </div>
  <div style="background:rgba(255,255,255,0.05);border-radius:999px;height:5px;overflow:hidden;margin-bottom:14px;position:relative;z-index:1;">
    <div class="neon-bar" style="height:5px;width:{bar_width}%;border-radius:999px;transition:width 0.6s ease;"></div>
  </div>
  <div style="display:flex;gap:24px;flex-wrap:wrap;position:relative;z-index:1;">
    <span style="font-size:0.76rem;color:var(--text3);">Collected&nbsp;
      <strong style="color:#00ff9d;font-variant-numeric:tabular-nums;text-shadow:0 0 8px rgba(0,255,157,0.4);">Rs&nbsp;{collected:,}</strong></span>
    <span style="font-size:0.76rem;color:var(--text3);">Remaining&nbsp;
      <strong style="color:#ff2d55;font-variant-numeric:tabular-nums;text-shadow:0 0 8px rgba(255,45,85,0.4);">Rs&nbsp;{remaining:,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div class="sidebar-logo">
  <h2>⬡ HOLO-MESS v2.1</h2>
  <p>● HOLO-SYSTEM ONLINE</p>
</div>
""", unsafe_allow_html=True)

role = st.sidebar.selectbox("Access Level", ["Student", "Hall Admin", "Senior Warden"])

if AUTO_REFRESH:
    refresh_rate = st.sidebar.selectbox("Sync Interval", ["Off", "30 sec", "60 sec", "2 min"], index=2)
    rate_map = {"Off": 0, "30 sec": 30000, "60 sec": 60000, "2 min": 120000}
    if rate_map[refresh_rate] > 0:
        st_autorefresh(interval=rate_map[refresh_rate], key="autorefresh")

st.sidebar.markdown("""
<div style="padding:14px 12px;margin-top:10px;
  border-top:1px solid rgba(0,245,255,0.1);text-align:center;
  background:linear-gradient(135deg,rgba(0,245,255,0.04),rgba(255,0,255,0.02));
  border-radius:0 0 8px 8px;position:relative;overflow:hidden;">
  <div style="font-family:Orbitron,sans-serif;font-size:0.75rem;font-weight:800;
    color:#00f5ff;letter-spacing:0.04em;text-shadow:0 0 10px rgba(0,245,255,0.5);">Abdul Hadi</div>
  <div style="font-family:Orbitron,sans-serif;font-size:0.58rem;color:#bf5af2;
    margin-top:3px;font-weight:600;letter-spacing:0.08em;">2025 (S) · CYS 90</div>
  <div style="font-size:0.58rem;color:#3d7a8a;margin-top:4px;font-style:italic;">
    Designed &amp; Developed</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# STUDENT VIEW
# ══════════════════════════════════════════════════════════════════
if role == "Student":
    hall     = st.sidebar.selectbox("Select Hall", halls)
    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    page_header(f"{hall}", "STUDENT PORTAL · VIEW DUES & SUBMIT RECEIPTS")

    if dues.empty:
        st.warning("⚠ No dues have been uploaded for this hall yet.")
        st.stop()

    month_list     = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Billing Cycle", month_list)
    month_dues     = dues[dues["Month"] == selected_month].sort_values("RoomNo")

    total_due      = month_dues["Total"].sum()
    total_students = len(month_dues)
    paid_count     = 0
    total_collected = 0
    for _, r in month_dues.iterrows():
        if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
            sp = payments[
                (payments["RoomNo"].astype(str).str.strip() == str(r["RoomNo"]).strip()) &
                (payments["Name"].astype(str).str.strip()   == str(r["Name"]).strip()) &
                (payments["Month"] == selected_month)
            ]
            pa = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
            if pa >= r["Total"]: paid_count += 1
            total_collected += pa

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL STUDENTS",  total_students)
    c2.metric("TOTAL DUES",      f"Rs {int(total_due):,}")
    c3.metric("FULLY PAID",      paid_count)
    c4.metric("PENDING",         total_students - paid_count)

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Student Dues — " + selected_month)

    for idx, row in month_dues.iterrows():
        room  = str(row["RoomNo"]).strip()
        name  = str(row["Name"]).strip()
        total = float(row["Total"])

        paid_amount = 0.0
        if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
            sp = payments[
                (payments["RoomNo"].astype(str).str.strip() == room) &
                (payments["Name"].astype(str).str.strip()   == name) &
                (payments["Month"] == selected_month)
            ]
            paid_amount = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()

        student_card(room, name, row["Food_Dues"], row["Service_Charges"], row["Previous"], total, paid_amount)

        with st.expander(f"⬡ Submit Receipt — Room {room} · {name}"):
            uploaded_files = st.file_uploader(
                "Upload receipt image(s) — Amount will be auto-detected",
                accept_multiple_files=True,
                type=["png","jpg","jpeg","webp"],
                key=f"files_{room}_{idx}"
            )

            # ── AI Amount Extraction ─────────────────────────────
            ai_extract_key = f"ai_amt_{room}_{idx}"
            ai_done_key    = f"ai_done_{room}_{idx}"

            if uploaded_files:
                # Auto-extract on first upload (only once per file set)
                file_hashes_now = [hashlib.md5(f.getvalue()).hexdigest() for f in uploaded_files]
                prev_hashes_key = f"prev_hashes_{room}_{idx}"

                if st.session_state.get(prev_hashes_key) != file_hashes_now:
                    st.session_state[prev_hashes_key] = file_hashes_now
                    st.session_state[ai_done_key] = False

                if not st.session_state.get(ai_done_key, False):
                    with st.spinner("🔍 Scanning receipt for amount..."):
                        try:
                            import base64, json, requests as _req

                            total_extracted = 0
                            for f in uploaded_files:
                                img_bytes  = f.getvalue()
                                b64_img    = base64.b64encode(img_bytes).decode("utf-8")
                                ext        = f.name.lower().split(".")[-1]
                                media_type = "image/jpeg" if ext in ["jpg","jpeg"] else f"image/{ext}"

                                payload = {
                                    "model": "claude-opus-4-6",
                                    "max_tokens": 200,
                                    "messages": [{
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "image",
                                                "source": {
                                                    "type": "base64",
                                                    "media_type": media_type,
                                                    "data": b64_img
                                                }
                                            },
                                            {
                                                "type": "text",
                                                "text": (
                                                    "This is a payment receipt image. "
                                                    "Extract ONLY the total paid amount as a plain integer number (no Rs, no commas, no text). "
                                                    "If multiple amounts exist, return the TOTAL/GRAND TOTAL. "
                                                    "Reply with ONLY the number, nothing else. Example: 4500"
                                                )
                                            }
                                        ]
                                    }]
                                }

                                resp = _req.post(
                                    "https://api.anthropic.com/v1/messages",
                                    headers={"Content-Type": "application/json"},
                                    json=payload,
                                    timeout=30
                                )
                                if resp.status_code == 200:
                                    raw = resp.json()["content"][0]["text"].strip()
                                    # Clean: extract first number found
                                    import re as _re
                                    nums = _re.findall(r'\d[\d,]*', raw)
                                    if nums:
                                        val = int(nums[0].replace(",",""))
                                        total_extracted += val

                            if total_extracted > 0:
                                # Cap at total due
                                final_amt = min(total_extracted, int(total))
                                st.session_state[ai_extract_key] = final_amt
                                st.session_state[ai_done_key] = True
                            else:
                                st.session_state[ai_extract_key] = int(total)
                                st.session_state[ai_done_key] = True

                        except Exception as _e:
                            # Fallback: use full total
                            st.session_state[ai_extract_key] = int(total)
                            st.session_state[ai_done_key] = True

                # Show extracted amount (read-only display)
                extracted_amount = st.session_state.get(ai_extract_key, int(total))

                st.markdown(f"""
<div style="background:rgba(0,255,157,0.06);border:1px solid rgba(0,255,157,0.3);
  border-radius:10px;padding:12px 16px;margin:8px 0;display:flex;
  justify-content:space-between;align-items:center;">
  <div>
    <div style="font-family:Orbitron,sans-serif;font-size:0.6rem;color:#3d7a8a;
      letter-spacing:0.12em;margin-bottom:4px;">AI DETECTED AMOUNT</div>
    <div style="font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:900;
      color:#00ff9d;text-shadow:0 0 12px rgba(0,255,157,0.5);">
      Rs&nbsp;{extracted_amount:,}
    </div>
  </div>
  <div style="font-size:1.5rem;">🤖</div>
</div>
""", unsafe_allow_html=True)

                if extracted_amount < int(total):
                    rem_after = int(total) - extracted_amount
                    st.info(f"⚠ Partial payment detected. Remaining after this: Rs {rem_after:,}")

                amount_paid_input = extracted_amount

                if st.button(f"⬆ Transmit Receipt — Room {room}", key=f"submit_{room}_{idx}"):
                    invalidate_cache()
                    fresh_all        = load_all_sheets_data()
                    current_payments = get_payments_from_cache(fresh_all, hall)
                    added, errors    = 0, []

                    for f in uploaded_files:
                        file_bytes = f.getvalue()
                        file_hash  = hashlib.md5(file_bytes).hexdigest()
                        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if not current_payments.empty and "File_Hash" in current_payments.columns:
                            dup = current_payments[
                                (current_payments["RoomNo"].astype(str).str.strip() == room) &
                                (current_payments["Name"].astype(str).str.strip()   == name) &
                                (current_payments["Month"] == selected_month) &
                                (current_payments["File_Hash"] == file_hash)
                            ]
                            if not dup.empty:
                                errors.append(f"Duplicate receipt detected: {f.name}")
                                continue

                        save_path = f"receipts/{uuid.uuid4()}_{f.name}"
                        with open(save_path, "wb") as fp:
                            fp.write(file_bytes)

                        new_row = pd.DataFrame([{
                            "Month": selected_month, "RoomNo": room, "Name": name,
                            "Amount_Paid": amount_paid_input, "Submission_Date": now_str,
                            "Receipt_File": save_path, "File_Hash": file_hash
                        }])
                        current_payments = pd.concat([current_payments, new_row], ignore_index=True)
                        added += 1

                    if added:
                        save_payments(current_payments, hall)
                        rem = int(total) - amount_paid_input
                        if rem > 0:
                            st.success(f"✓ Receipt transmitted. Paid: Rs {amount_paid_input:,} · Remaining: Rs {rem:,}")
                        else:
                            st.success(f"✓ Full payment transmitted. Amount: Rs {amount_paid_input:,}")
                        # Reset AI state for this card
                        st.session_state.pop(ai_extract_key, None)
                        st.session_state.pop(ai_done_key, None)
                        st.session_state.pop(prev_hashes_key, None)
                        st.rerun()
                    for e in errors:
                        st.error(e)


# ══════════════════════════════════════════════════════════════════
# HALL ADMIN
# ══════════════════════════════════════════════════════════════════
elif role == "Hall Admin":
    hall = st.sidebar.selectbox("Select Hall", halls)
    pw   = st.sidebar.text_input("Admin Passkey", type="password")

    if pw != hall_passwords.get(hall, ""):
        st.sidebar.error("⚠ ACCESS DENIED")
        st.stop()

    page_header(f"{hall} — ADMIN PANEL", "MANAGE DUES · TRACK PAYMENTS · REVIEW RECEIPTS")

    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⬆ Upload Dues", "◉ Dashboard", "⚠ Pending", "◎ Receipts", "✕ Manage"
    ])

    # ── Upload Dues ──────────────────────────────────────────────
    with tab1:
        section_label("Upload Monthly Dues")
        years       = list(range(2025, 2032))
        months_list = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
        month       = st.selectbox("Billing Month", months_list,
                                   index=months_list.index(datetime.now().strftime("%Y-%m")))
        uploaded = st.file_uploader("Select Excel or CSV File", type=["csv", "xlsx"])

        if uploaded and st.button("⬆ Upload and Save"):
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df = df.loc[:, ~df.columns.duplicated()]
            df = standardize_columns(df)

            for col in ["Food_Dues", "Service_Charges", "Previous"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
            df["Name"]   = df["Name"].astype(str).str.strip()
            df["Month"]  = month
            df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]

            keep = ["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"]
            df   = df[[c for c in keep if c in df.columns]]

            invalidate_cache()
            fresh        = load_all_sheets_data()
            existing     = get_dues_from_cache(fresh, hall)
            all_payments = get_payments_from_cache(fresh, hall)

            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]

            for c in keep:
                if c not in existing.columns: existing[c] = ""
                if c not in df.columns:       df[c] = ""

            existing, df = existing[keep], df[keep]

            if not existing.empty and "Month" in existing.columns:
                past = sorted([m for m in existing["Month"].unique() if m != month], reverse=True)
                if past:
                    last_m    = past[0]
                    last_dues = existing[existing["Month"] == last_m].copy()
                    carry_map = {}

                    for _, lr in last_dues.iterrows():
                        lr_room = str(lr["RoomNo"]).strip()
                        lr_name = str(lr["Name"]).strip()
                        lr_tot  = float(lr["Total"])
                        lr_paid = 0.0
                        if not all_payments.empty and "Amount_Paid" in all_payments.columns and "Month" in all_payments.columns:
                            sp = all_payments[
                                (all_payments["RoomNo"].astype(str).str.strip() == lr_room) &
                                (all_payments["Name"].astype(str).str.strip()   == lr_name) &
                                (all_payments["Month"] == last_m)
                            ]
                            lr_paid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                        rem = max(0.0, lr_tot - lr_paid)
                        if rem > 0:
                            carry_map[f"{lr_room}||{lr_name}"] = rem

                    if carry_map:
                        carried = 0
                        for i, r2 in df.iterrows():
                            k = f"{str(r2['RoomNo']).strip()}||{str(r2['Name']).strip()}"
                            if k in carry_map:
                                df.at[i,"Previous"] = float(df.at[i,"Previous"]) + carry_map[k]
                                df.at[i,"Total"]    = float(df.at[i,"Food_Dues"]) + float(df.at[i,"Service_Charges"]) + float(df.at[i,"Previous"])
                                carried += 1
                        if carried:
                            st.info(f"{carried} student(s) had arrears carried forward from {last_m} to {month}.")

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)

            if not all_payments.empty and "Month" in all_payments.columns:
                cleaned = all_payments[all_payments["Month"] != month]
                removed = len(all_payments) - len(cleaned)
                save_payments(cleaned, hall)
                if removed:
                    st.info(f"{removed} previous payment record(s) for {month} were cleared.")

            st.success(f"✓ {len(df)} student records uploaded for {month}.")

    # ── Dashboard ────────────────────────────────────────────────
    with tab2:
        if dues.empty:
            st.info("No data available. Upload dues first.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Billing Cycle", month_list, key="dash_month")
            df_d       = dues[dues["Month"] == sel_month].copy()

            col_search, col_spacer = st.columns([2, 3])
            with col_search:
                srch = st.text_input("Search by Room or Name", placeholder="e.g. Room 12 or Ahmed")
            if srch:
                df_d = df_d[df_d["RoomNo"].str.contains(srch, case=False) | df_d["Name"].str.contains(srch, case=False)]

            total_dues = df_d["Total"].sum()
            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                collected = pd.to_numeric(payments[payments["Month"]==sel_month]["Amount_Paid"], errors="coerce").fillna(0).sum()
            else:
                collected = 0
            remaining = total_dues - collected
            pct       = int(collected / total_dues * 100) if total_dues else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("TOTAL DUES",   f"Rs {int(total_dues):,}")
            c2.metric("COLLECTED",    f"Rs {int(collected):,}", f"{pct}% recovered")
            c3.metric("REMAINING",    f"Rs {int(remaining):,}")
            c4.metric("STUDENTS",     len(df_d))

            st.markdown("<br>", unsafe_allow_html=True)

            def paid_for(row):
                if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                    sp = payments[
                        (payments["RoomNo"].astype(str).str.strip() == str(row["RoomNo"]).strip()) &
                        (payments["Name"].astype(str).str.strip()   == str(row["Name"]).strip()) &
                        (payments["Month"] == sel_month)
                    ]
                    return int(pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum())
                return 0

            df_d = df_d.copy()
            df_d["Paid (Rs)"]      = df_d.apply(paid_for, axis=1)
            df_d["Remaining (Rs)"] = (df_d["Total"] - df_d["Paid (Rs)"]).clip(lower=0).astype(int)
            df_d["Status"]         = df_d.apply(
                lambda r: "Paid" if r["Paid (Rs)"] >= r["Total"] else ("Partial" if r["Paid (Rs)"] > 0 else "Unpaid"), axis=1
            )

            # ── Summary stats ────────────────────────────────────────
            paid_cnt    = (df_d["Status"] == "Paid").sum()
            partial_cnt = (df_d["Status"] == "Partial").sum()
            unpaid_cnt  = (df_d["Status"] == "Unpaid").sum()

            section_label("Monthly Summary")
            s1, s2, s3, s4, s5 = st.columns(5)
            s1.metric("PAID STUDENTS",    paid_cnt)
            s2.metric("PARTIAL",          partial_cnt)
            s3.metric("UNPAID",           unpaid_cnt)
            s4.metric("COLLECTION RATE",  f"{pct}%")
            s5.metric("AVG DUE / STUDENT", f"Rs {int(total_dues/len(df_d)):,}" if len(df_d) else "Rs 0")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Charts row ───────────────────────────────────────────
            try:
                import plotly.graph_objects as go
                import plotly.express as px

                ch1, ch2, ch3, ch4 = st.columns(4)

                # Chart 1 — Payment status donut
                with ch1:
                    section_label("Payment Status")
                    fig_s = go.Figure(data=[go.Pie(
                        labels=["Paid","Partial","Unpaid"],
                        values=[paid_cnt, partial_cnt, unpaid_cnt],
                        hole=0.6,
                        marker=dict(
                            colors=["#00ff9d","#00f5ff","#ff2d55"],
                            line=dict(color="rgba(0,0,0,0)", width=0)
                        ),
                        textinfo="percent",
                        textfont=dict(size=11, family="Orbitron", color="#fff"),
                        hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
                    )])
                    fig_s.update_layout(
                        showlegend=False, height=200,
                        margin=dict(t=5,b=5,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(
                            text=f"<b>{len(df_d)}</b>",
                            x=0.5, y=0.5, font_size=18, font_color="#00f5ff",
                            font_family="Orbitron", showarrow=False
                        )]
                    )
                    st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

                # Chart 2 — Collection vs Total bar
                with ch2:
                    section_label("Collection vs Total")
                    fig_cv = go.Figure()
                    fig_cv.add_trace(go.Bar(
                        name="Total", x=["Dues"],
                        y=[int(total_dues)], marker_color="rgba(0,245,255,0.25)",
                        marker_line_width=0,
                        hovertemplate="Total: Rs %{y:,.0f}<extra></extra>"
                    ))
                    fig_cv.add_trace(go.Bar(
                        name="Collected", x=["Dues"],
                        y=[int(collected)], marker_color="#00ff9d",
                        marker_line_width=0,
                        hovertemplate="Collected: Rs %{y:,.0f}<extra></extra>"
                    ))
                    fig_cv.update_layout(
                        barmode="overlay", height=200,
                        margin=dict(t=5,b=5,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis=dict(showgrid=False, tickfont=dict(color="#3d7a8a", size=9)),
                        yaxis=dict(showgrid=True, gridcolor="rgba(0,245,255,0.05)",
                                   tickfont=dict(color="#3d7a8a", size=8), tickformat=",")
                    )
                    st.plotly_chart(fig_cv, use_container_width=True, config={"displayModeBar": False})

                # Chart 3 — Top unpaid students (horizontal bar)
                with ch3:
                    section_label("Top Unpaid")
                    top_unpaid = df_d[df_d["Status"] != "Paid"].nlargest(5, "Remaining (Rs)")
                    if not top_unpaid.empty:
                        fig_u = go.Figure(go.Bar(
                            x=top_unpaid["Remaining (Rs)"].tolist(),
                            y=top_unpaid["Name"].tolist(),
                            orientation="h",
                            marker=dict(
                                color=top_unpaid["Remaining (Rs)"].tolist(),
                                colorscale=[[0,"#ff6b35"],[1,"#ff2d55"]],
                                showscale=False, line=dict(width=0)
                            ),
                            text=[f"Rs {v:,}" for v in top_unpaid["Remaining (Rs)"].tolist()],
                            textposition="outside",
                            textfont=dict(size=9, color="#7ecfde"),
                            hovertemplate="<b>%{y}</b><br>Rs %{x:,.0f}<extra></extra>"
                        ))
                        fig_u.update_layout(
                            height=200, margin=dict(t=5,b=5,l=5,r=60),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(showgrid=False, visible=False),
                            yaxis=dict(showgrid=False, tickfont=dict(color="#7ecfde", size=9))
                        )
                        st.plotly_chart(fig_u, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.success("All students paid!")

                # Chart 4 — Dues breakdown (food vs service vs previous)
                with ch4:
                    section_label("Dues Breakdown")
                    fd_tot  = int(df_d["Food_Dues"].sum())
                    sv_tot  = int(df_d["Service_Charges"].sum())
                    pr_tot  = int(df_d["Previous"].sum())
                    fig_br = go.Figure(data=[go.Pie(
                        labels=["Food","Service","Arrears"],
                        values=[fd_tot, sv_tot, pr_tot],
                        hole=0.55,
                        marker=dict(
                            colors=["#bf5af2","#00f5ff","#ff6b35"],
                            line=dict(color="rgba(0,0,0,0)", width=0)
                        ),
                        textinfo="percent",
                        textfont=dict(size=10, family="Orbitron", color="#fff"),
                        hovertemplate="<b>%{label}</b><br>Rs %{value:,.0f}<extra></extra>"
                    )])
                    fig_br.update_layout(
                        showlegend=False, height=200,
                        margin=dict(t=5,b=5,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_br, use_container_width=True, config={"displayModeBar": False})

            except ImportError:
                pass

            st.markdown("<br>", unsafe_allow_html=True)
            section_label("Student Data Matrix")

            def row_color(row):
                s = row.get("Status","")
                if s == "Paid":
                    return ["background-color:rgba(0,255,157,0.08);color:#00ff9d;font-weight:700"] * len(row)
                elif s == "Partial":
                    return ["background-color:rgba(0,245,255,0.08);color:#00f5ff;font-weight:600"] * len(row)
                return ["background-color:rgba(255,45,85,0.07);color:#ff6b6b;font-weight:500"] * len(row)

            display_cols = ["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)","Status"]
            st.dataframe(
                df_d[display_cols].style.apply(row_color, axis=1),
                use_container_width=True, hide_index=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            section_label("Collection Chart")
            chart_data = df_d.set_index("Name")[["Total","Paid (Rs)"]].head(30)
            st.bar_chart(chart_data)

            st.markdown("---")
            csv = df_d[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇ Download {sel_month} Report (CSV)",
                csv, file_name=f"{hall}_{sel_month}.csv", mime="text/csv"
            )

    # ── Pending ──────────────────────────────────────────────────
    with tab3:
        if dues.empty:
            st.info("No data available.")
        else:
            latest_m  = sorted(dues["Month"].unique(), reverse=True)[0]
            lt_dues   = dues[dues["Month"] == latest_m].copy()
            lt_dues["_key"] = lt_dues["RoomNo"].astype(str).str.strip() + "||" + lt_dues["Name"].astype(str).str.strip()

            if not payments.empty and "Month" in payments.columns:
                mp = payments[payments["Month"] == latest_m].copy()
                mp["_key"] = mp["RoomNo"].astype(str).str.strip() + "||" + mp["Name"].astype(str).str.strip()

                def gpd(row):
                    sp = mp[mp["_key"] == row["_key"]]
                    return pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum() if (not sp.empty and "Amount_Paid" in sp.columns) else 0

                lt_dues["Paid"]      = lt_dues.apply(gpd, axis=1)
                lt_dues["Remaining"] = (lt_dues["Total"] - lt_dues["Paid"]).clip(lower=0)
            else:
                lt_dues["Paid"]      = 0
                lt_dues["Remaining"] = lt_dues["Total"]

            pending    = lt_dues[lt_dues["Remaining"] > 0].drop(columns=["_key"])
            fully_paid = len(lt_dues) - len(pending)

            section_label(f"Pending Payments — {latest_m}")
            c1, c2, c3 = st.columns(3)
            c1.metric("PENDING STUDENTS", len(pending))
            c2.metric("FULLY PAID",       fully_paid)
            c3.metric("PENDING AMOUNT",   f"Rs {int(pending['Remaining'].sum()):,}" if not pending.empty else "Rs 0")

            st.markdown("<br>", unsafe_allow_html=True)
            if pending.empty:
                st.success("✓ All students have paid their dues for this month.")
            else:
                show = ["RoomNo","Name","Total","Paid","Remaining"]
                st.dataframe(pending[[c for c in show if c in pending.columns]],
                             use_container_width=True, hide_index=True)

    # ── Receipts ─────────────────────────────────────────────────
    with tab4:
        if payments.empty:
            st.info("No receipts submitted yet.")
        else:
            section_label(f"All Receipts — {len(payments)} transmissions")

            if "Month" in payments.columns:
                rec_months    = ["All Months"] + sorted(payments["Month"].unique(), reverse=True)
                sel_rec_month = st.selectbox("Filter by Month", rec_months, key="rec_month")
                filtered_pays = payments if sel_rec_month == "All Months" else payments[payments["Month"] == sel_rec_month]
            else:
                filtered_pays = payments

            for i, row in filtered_pays.iterrows():
                receipt_card(row["RoomNo"], row["Name"], row.get("Amount_Paid",""), row.get("Submission_Date",""), i)
                path = str(row.get("Receipt_File",""))
                if path and os.path.exists(path):
                    if path.lower().endswith((".png",".jpg",".jpeg")):
                        st.image(path, width=220)
                    with open(path,"rb") as fp:
                        st.download_button("⬇ Download Receipt", fp,
                                           file_name=os.path.basename(path), key=f"dl_{i}")
                else:
                    st.caption("Receipt image not available on server (cloud restart clears files)")

    # ── Manage Months ────────────────────────────────────────────
    with tab5:
        if dues.empty:
            st.info("No months available.")
        else:
            section_label("Delete a Billing Month")
            month_list   = sorted(dues["Month"].unique(), reverse=True)
            month_to_del = st.selectbox("Select Month to Delete", month_list, key="del_month")

            st.warning(f"⚠ This will permanently delete all dues and receipts for **{month_to_del}**.")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✕ Delete Month", type="primary"):
                    updated_dues = dues[dues["Month"] != month_to_del].copy()
                    updated_payments = payments[payments["Month"] != month_to_del].copy() \
                        if (not payments.empty and "Month" in payments.columns) else payments

                    all_remaining_months = sorted(updated_dues["Month"].unique())
                    next_month = None
                    for m in all_remaining_months:
                        if m > month_to_del:
                            next_month = m
                            break

                    if next_month is not None:
                        nm_mask        = updated_dues["Month"] == next_month
                        nm_df          = updated_dues[nm_mask].copy()
                        del_month_dues = dues[dues["Month"] == month_to_del].copy()

                        for i, row in nm_df.iterrows():
                            key_room = str(row["RoomNo"]).strip()
                            key_name = str(row["Name"]).strip()
                            match = del_month_dues[
                                (del_month_dues["RoomNo"].astype(str).str.strip() == key_room) &
                                (del_month_dues["Name"].astype(str).str.strip()   == key_name)
                            ]
                            if match.empty:
                                continue
                            del_total = float(match.iloc[0]["Total"])
                            del_paid  = 0.0
                            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                                sp = payments[
                                    (payments["RoomNo"].astype(str).str.strip() == key_room) &
                                    (payments["Name"].astype(str).str.strip()   == key_name) &
                                    (payments["Month"] == month_to_del)
                                ]
                                del_paid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                            arrear_carried = max(0.0, del_total - del_paid)
                            current_prev   = float(updated_dues.at[i, "Previous"])
                            new_prev       = max(0.0, current_prev - arrear_carried)
                            updated_dues.at[i, "Previous"] = new_prev
                            updated_dues.at[i, "Total"]    = (
                                float(updated_dues.at[i, "Food_Dues"]) +
                                float(updated_dues.at[i, "Service_Charges"]) +
                                new_prev
                            )

                    save_dues(updated_dues, hall)
                    if not payments.empty and "Month" in payments.columns:
                        save_payments(updated_payments, hall)

                    msg = f"All data for {month_to_del} deleted."
                    if next_month:
                        msg += f" Arrears in {next_month} recalculated."
                    st.success(msg)
                    st.rerun()
            with col2:
                st.info("Deleting a month will also remove carried arrears from the next month's Previous column.")


# ══════════════════════════════════════════════════════════════════
# SENIOR WARDEN
# ══════════════════════════════════════════════════════════════════
elif role == "Senior Warden":
    pw = st.sidebar.text_input("Warden Passkey", type="password")
    if pw != senior_password:
        st.sidebar.error("⚠ ACCESS DENIED")
        st.stop()

    page_header("SENIOR WARDEN COMMAND CENTER", "FINANCIAL OVERVIEW · ALL 9 HALLS · REAL-TIME")

    all_data = load_all_sheets_data()

    all_months = set()
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            for m in hd["Month"].unique():
                if m and m != "Unknown":
                    all_months.add(m)

    month_options = ["All Months (Combined)"] + sorted(all_months, reverse=True)

    if "warden_selected_month" not in st.session_state:
        st.session_state["warden_selected_month"] = "All Months (Combined)"
    if st.session_state["warden_selected_month"] not in month_options:
        st.session_state["warden_selected_month"] = "All Months (Combined)"

    selected_w_month = st.selectbox(
        "Reporting Period", month_options,
        index=month_options.index(st.session_state["warden_selected_month"]),
        key="warden_month_select"
    )
    st.session_state["warden_selected_month"] = selected_w_month

    total_all = collected_all = remaining_all = 0
    summary   = []
    paid_students_all = unpaid_students_all = 0

    for hall in halls:
        hd = get_dues_from_cache(all_data, hall)
        hp = get_payments_from_cache(all_data, hall)

        if not hd.empty and "Month" in hd.columns:
            if selected_w_month != "All Months (Combined)":
                hd_f = hd[hd["Month"] == selected_w_month]
                hp_f = hp[hp["Month"] == selected_w_month] if (not hp.empty and "Month" in hp.columns) else pd.DataFrame()
            else:
                hd_f, hp_f = hd, hp

            if hd_f.empty:
                summary.append({"Hall": hall, "Students": 0, "Total": 0, "Collected": 0, "Remaining": 0, "Pct": 0})
                continue

            total     = int(hd_f["Total"].sum())
            collected = int(pd.to_numeric(hp_f["Amount_Paid"], errors="coerce").fillna(0).sum()) \
                        if (not hp_f.empty and "Amount_Paid" in hp_f.columns) else 0
            remaining      = total - collected
            pct            = int(collected / total * 100) if total else 0
            total_all     += total
            collected_all += collected
            remaining_all += remaining

            for _, row in hd_f.iterrows():
                room, name = str(row["RoomNo"]).strip(), str(row["Name"]).strip()
                if not hp_f.empty and "Amount_Paid" in hp_f.columns:
                    sp = hp_f[(hp_f["RoomNo"].astype(str).str.strip() == room) &
                               (hp_f["Name"].astype(str).str.strip() == name)]
                    pa = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    if pa >= row["Total"]: paid_students_all += 1
                    else: unpaid_students_all += 1
                else:
                    unpaid_students_all += 1

            summary.append({"Hall": hall, "Students": len(hd_f), "Total": total,
                             "Collected": collected, "Remaining": remaining, "Pct": pct})
        else:
            summary.append({"Hall": hall, "Students": 0, "Total": 0, "Collected": 0, "Remaining": 0, "Pct": 0})

    overall_pct = int(collected_all / total_all * 100) if total_all else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GRAND TOTAL DUES",  f"Rs {int(total_all):,}")
    c2.metric("TOTAL COLLECTED",   f"Rs {int(collected_all):,}", f"{overall_pct}% recovered")
    c3.metric("TOTAL REMAINING",   f"Rs {int(remaining_all):,}")
    c4.metric("RECOVERY RATE",     f"{overall_pct}%")

    st.markdown("<br>", unsafe_allow_html=True)

    col_pie, col_bar = st.columns([1, 2])

    with col_pie:
        section_label("Collection Status")
        try:
            import plotly.graph_objects as go
            fig_pie = go.Figure(data=[go.Pie(
                labels=["Collected", "Remaining"],
                values=[collected_all, remaining_all],
                hole=0.58,
                marker=dict(colors=["#00ff9d","#ff2d55"], line=dict(color="rgba(0,0,0,0)", width=0)),
                textinfo="percent",
                textfont=dict(size=12, family="Orbitron", color="#fff"),
                hovertemplate="<b>%{label}</b><br>Rs %{value:,.0f}<extra></extra>"
            )])
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                            font=dict(size=10, family="Orbitron", color="#7ecfde")),
                margin=dict(t=10, b=10, l=10, r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{overall_pct}%</b>",
                    x=0.5, y=0.5, font_size=20, font_family="Orbitron",
                    font_color="#00f5ff", showarrow=False
                )]
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            st.info(f"Collection: Rs {collected_all:,} of Rs {total_all:,}")

    with col_bar:
        section_label("Hall-wise Comparison")
        try:
            import plotly.graph_objects as go
            hall_names     = [s["Hall"].replace(" Hall","") for s in summary]
            collected_vals = [s["Collected"] for s in summary]
            remaining_vals = [s["Remaining"] for s in summary]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Collected", x=hall_names, y=collected_vals,
                marker_color="#00ff9d", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Collected: Rs %{y:,.0f}<extra></extra>"
            ))
            fig_bar.add_trace(go.Bar(
                name="Remaining", x=hall_names, y=remaining_vals,
                marker_color="#ff2d55", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Remaining: Rs %{y:,.0f}<extra></extra>"
            ))
            fig_bar.update_layout(
                barmode="stack", showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=9, family="Orbitron", color="#7ecfde")),
                margin=dict(t=30, b=10, l=10, r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, family="Orbitron", color="#3d7a8a")),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,245,255,0.04)",
                           tickformat=",", tickfont=dict(size=8, family="Orbitron", color="#3d7a8a")),
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            st.bar_chart(pd.DataFrame(summary).set_index("Hall")[["Collected","Remaining"]])

    try:
        import plotly.graph_objects as go
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            section_label("Student Payment Status")
            total_students_all = paid_students_all + unpaid_students_all
            fig_d = go.Figure(data=[go.Pie(
                labels=["Paid", "Pending"],
                values=[paid_students_all, unpaid_students_all],
                hole=0.62,
                marker=dict(colors=["#00f5ff","#ff6b35"], line=dict(color="rgba(0,0,0,0)", width=0)),
                textinfo="percent+value",
                textfont=dict(size=11, family="Orbitron", color="#fff"),
                hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
            )])
            fig_d.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
                            font=dict(size=10, family="Orbitron", color="#7ecfde")),
                margin=dict(t=10, b=10, l=10, r=10), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{total_students_all}</b>",
                    x=0.5, y=0.5, font_size=16, font_family="Orbitron",
                    font_color="#00f5ff", showarrow=False
                )]
            )
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

        with col_d2:
            section_label("Hall Recovery Rates")
            hall_labels = [s["Hall"].replace(" Hall","") for s in summary if s["Total"] > 0]
            hall_pcts   = [s["Pct"] for s in summary if s["Total"] > 0]
            fig_h = go.Figure(go.Bar(
                x=hall_pcts, y=hall_labels, orientation="h",
                marker=dict(
                    color=hall_pcts,
                    colorscale=[[0,"#ff2d55"],[0.5,"#ff6b35"],[1,"#00ff9d"]],
                    showscale=False, line=dict(width=0),
                ),
                text=[f"{p}%" for p in hall_pcts],
                textposition="outside",
                textfont=dict(size=10, family="Orbitron", color="#7ecfde"),
                hovertemplate="<b>%{y}</b><br>Recovery: %{x}%<extra></extra>"
            ))
            fig_h.update_layout(
                margin=dict(t=10, b=10, l=10, r=50), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0,120], showgrid=False, visible=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=9, family="Orbitron", color="#7ecfde")),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Hall-wise Breakdown")
    for row in summary:
        hall_summary_card(row["Hall"], row["Total"], row["Collected"], row["Remaining"], row["Pct"])

    st.markdown("---")
    export_df = pd.DataFrame([{
        "Hall": r["Hall"], "Students": r["Students"],
        "Total Dues (Rs)": r["Total"], "Collected (Rs)": r["Collected"],
        "Remaining (Rs)": r["Remaining"], "Recovery %": f"{r['Pct']}%"
    } for r in summary])
    csv_w = export_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Full Summary (CSV)", csv_w,
                       file_name="all_halls_summary.csv", mime="text/csv")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Month-wise Payments Overview")

    all_pay_rows = []
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        hp = get_payments_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            months_to_show = ([selected_w_month] if selected_w_month != "All Months (Combined)"
                              else sorted(hd["Month"].unique(), reverse=True))
            for mv in months_to_show:
                if mv == "Unknown": continue
                mdf = hd[hd["Month"] == mv]
                if mdf.empty: continue
                tot  = int(mdf["Total"].sum())
                recs, col = 0, 0
                if not hp.empty and "Month" in hp.columns:
                    mp   = hp[hp["Month"] == mv]
                    recs = len(mp)
                    if "Amount_Paid" in mp.columns:
                        col = int(pd.to_numeric(mp["Amount_Paid"], errors="coerce").fillna(0).sum())
                all_pay_rows.append({
                    "Hall": h, "Month": mv, "Students": len(mdf),
                    "Total Dues (Rs)": tot, "Receipts": recs,
                    "Collected (Rs)": col, "Remaining (Rs)": max(0, tot - col),
                    "Recovery %": f"{int(col/tot*100) if tot else 0}%"
                })

    if all_pay_rows:
        apdf = pd.DataFrame(all_pay_rows).sort_values(["Month","Hall"], ascending=[False,True])
        st.dataframe(apdf, use_container_width=True, hide_index=True)
    else:
        st.info("No payment data available yet.")


# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-top:3rem;padding:1.5rem 2rem;
  background:linear-gradient(135deg,rgba(0,245,255,0.04),rgba(191,90,242,0.03));
  border:1px solid rgba(0,245,255,0.1);
  border-radius:16px;
  backdrop-filter:blur(20px);
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;
  box-shadow:0 4px 30px rgba(0,0,0,0.2);
  position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(0,245,255,0.3),transparent);"></div>
  <div>
    <span style="font-family:Orbitron,sans-serif;font-size:0.82rem;font-weight:800;
      color:#00f5ff;text-shadow:0 0 10px rgba(0,245,255,0.4);">UNIVERSITY MESS DUES SYSTEM</span>
    <span style="color:rgba(0,245,255,0.15);margin:0 8px;">|</span>
    <span style="font-size:0.74rem;color:#3d7a8a;">Powered by Streamlit &amp; Google Sheets</span>
  </div>
  <div style="text-align:right;">
    <span style="font-family:Orbitron,sans-serif;font-size:0.78rem;font-weight:800;
      color:#bf5af2;text-shadow:0 0 10px rgba(191,90,242,0.4);">Designed &amp; Developed by Abdul Hadi</span>
    <br>
    <span style="font-family:Orbitron,sans-serif;font-size:0.6rem;color:#3d7a8a;letter-spacing:0.08em;">
      2025 (S) &nbsp;·&nbsp; CYS 90 &nbsp;·&nbsp; UET &nbsp;·&nbsp; HOLO-MESS v2.1
    </span>
  </div>
</div>
""", unsafe_allow_html=True)
