import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os, base64
import numpy as np

try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH = True
except ImportError:
    AUTO_REFRESH = False

st.set_page_config(
    page_title="University Mess Dues System",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
_t = st.session_state["theme"]

# ─────────────────────────────────────────────────────────────────
# SUPREME CSS — MAXIMUM LEVEL
# ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700;800&display=swap');

*, html, body, [class*="css"] {{
  font-family: 'Inter', sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  box-sizing: border-box;
}}

/* ══ THEME VARIABLES ══════════════════════════════════════════ */
:root {{
  {"" if _t=="dark" else "/*"}
  --bg:           #06060e;
  --bg2:          #0a0a16;
  --bg3:          #0f0f1e;
  --glass:        rgba(255,255,255,0.035);
  --glass2:       rgba(255,255,255,0.06);
  --glass3:       rgba(255,255,255,0.09);
  --border:       rgba(255,255,255,0.065);
  --border2:      rgba(255,255,255,0.12);
  --border3:      rgba(255,255,255,0.18);
  --t1:           #f0f4ff;
  --t2:           #94a3b8;
  --t3:           #4b5563;
  --t4:           #1f2937;
  --sidebar:      #050509;
  --inp:          rgba(255,255,255,0.05);
  {"" if _t=="dark" else "*/"}
  {"/*" if _t=="dark" else ""}
  --bg:           #eef0ff;
  --bg2:          #e5e8ff;
  --bg3:          #dce0ff;
  --glass:        rgba(255,255,255,0.72);
  --glass2:       rgba(255,255,255,0.85);
  --glass3:       rgba(255,255,255,0.95);
  --border:       rgba(99,102,241,0.1);
  --border2:      rgba(99,102,241,0.2);
  --border3:      rgba(99,102,241,0.32);
  --t1:           #0d0b2e;
  --t2:           #3730a3;
  --t3:           #6366f1;
  --t4:           #c7d2fe;
  --sidebar:      #06040f;
  --inp:          rgba(255,255,255,0.88);
  {"*/" if _t=="dark" else ""}
  --indigo:       #6366f1;
  --violet:       #8b5cf6;
  --cyan:         #06b6d4;
  --emerald:      #10b981;
  --rose:         #f43f5e;
  --amber:        #f59e0b;
  --r-xs:  8px; --r-sm: 12px; --r-md: 16px;
  --r-lg: 22px; --r-xl: 30px; --r-2xl: 40px;
}}

/* ══ APP BACKGROUND ══════════════════════════════════════════ */
.stApp {{
  background: var(--bg) !important;
  background-image:
    radial-gradient(ellipse 100% 60% at 10% -10%, rgba(99,102,241,0.22) 0%, transparent 50%),
    radial-gradient(ellipse 80% 50% at 90% 110%,  rgba(139,92,246,0.18) 0%, transparent 48%),
    radial-gradient(ellipse 60% 40% at 55% 55%,   rgba(6,182,212,0.06)  0%, transparent 55%) !important;
  background-attachment: fixed !important;
}}
.block-container {{ padding: 0 2.5rem 5rem !important; max-width: 1500px !important; }}

/* ══ ANIMATED AURORA TOP STRIP ════════════════════════════════ */
.stApp::before {{
  content: '';
  position: fixed; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg,
    #6366f1,#818cf8,#8b5cf6,#a78bfa,#06b6d4,
    #10b981,#34d399,#f59e0b,#f43f5e,#6366f1);
  background-size: 500% 100%;
  animation: aurora 8s linear infinite;
  z-index: 99999;
}}
@keyframes aurora {{ 0%{{background-position:0% 0%}} 100%{{background-position:500% 0%}} }}

/* ══ FLOATING ORBS (decorative) ═══════════════════════════════ */
.stApp::after {{
  content: '';
  position: fixed; bottom: -200px; right: -200px;
  width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
  pointer-events: none; z-index: 0;
  animation: orb-float 12s ease-in-out infinite alternate;
}}
@keyframes orb-float {{ 0%{{transform:translate(0,0) scale(1)}} 100%{{transform:translate(-40px,-40px) scale(1.1)}} }}

/* ══ SCROLLBAR ═══════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(99,102,241,0.3); border-radius: 99px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(99,102,241,0.6); }}

/* ══ SIDEBAR ═════════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
  background: var(--sidebar) !important;
  border-right: 1px solid rgba(99,102,241,0.1) !important;
  box-shadow: 8px 0 50px rgba(99,102,241,0.06) !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: #c7d2fe !important; }}
[data-testid="stSidebar"] label {{
  color: rgba(99,102,241,0.75) !important;
  font-size: 0.65rem !important; font-weight: 900 !important;
  letter-spacing: 0.16em !important; text-transform: uppercase !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div {{
  background: rgba(99,102,241,0.07) !important;
  border: 1px solid rgba(99,102,241,0.2) !important;
  border-radius: var(--r-sm) !important; color: #e0e7ff !important;
  font-size: 0.85rem !important; backdrop-filter: blur(12px) !important;
  transition: all 0.2s ease !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.16), 0 0 20px rgba(99,102,241,0.15) !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input {{
  background: rgba(99,102,241,0.07) !important;
  border: 1px solid rgba(99,102,241,0.2) !important;
  border-radius: var(--r-sm) !important; color: #e0e7ff !important;
  transition: all 0.2s ease !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.16), 0 0 20px rgba(99,102,241,0.15) !important;
  outline: none !important;
}}

/* ══ BUTTONS ═════════════════════════════════════════════════ */
.stButton > button {{
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
  color: #fff !important; border: none !important;
  border-radius: var(--r-sm) !important;
  font-weight: 700 !important; font-size: 0.84rem !important;
  padding: 0.6rem 1.6rem !important; letter-spacing: 0.025em !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.4), inset 0 1px 0 rgba(255,255,255,0.15) !important;
  transition: all 0.22s cubic-bezier(.4,0,.2,1) !important;
  position: relative !important; overflow: hidden !important;
}}
.stButton > button::before {{
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 60%);
  border-radius: inherit; opacity: 0; transition: opacity 0.2s;
}}
.stButton > button:hover {{
  transform: translateY(-2px) scale(1.015) !important;
  box-shadow: 0 12px 35px rgba(99,102,241,0.55), inset 0 1px 0 rgba(255,255,255,0.18) !important;
}}
.stButton > button:hover::before {{ opacity: 1; }}
.stButton > button:active {{ transform: translateY(0) scale(0.985) !important; }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, #f43f5e, #be123c) !important;
  box-shadow: 0 4px 20px rgba(244,63,94,0.4), inset 0 1px 0 rgba(255,255,255,0.12) !important;
}}
.stButton > button[kind="primary"]:hover {{
  box-shadow: 0 12px 35px rgba(244,63,94,0.55) !important;
}}
[data-testid="stDownloadButton"] > button {{
  background: linear-gradient(135deg, #10b981, #047857) !important;
  box-shadow: 0 4px 20px rgba(16,185,129,0.36) !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
  box-shadow: 0 12px 32px rgba(16,185,129,0.52) !important;
}}

/* ══ TABS ════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
  background: var(--glass) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--r-md) !important;
  padding: 5px !important; gap: 3px !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: var(--r-xs) !important;
  font-weight: 500 !important; font-size: 0.84rem !important;
  color: var(--t2) !important; padding: 0.5rem 1.15rem !important;
  transition: all 0.18s ease !important; letter-spacing: 0.01em !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
  background: var(--glass2) !important; color: var(--t1) !important;
}}
.stTabs [aria-selected="true"] {{
  background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
  color: #fff !important; font-weight: 700 !important;
  box-shadow: 0 4px 18px rgba(99,102,241,0.45),
              inset 0 1px 0 rgba(255,255,255,0.15) !important;
}}

/* ══ METRIC CARDS ════════════════════════════════════════════ */
[data-testid="metric-container"] {{
  background: var(--glass) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--r-md) !important;
  padding: 1.4rem 1.7rem 1.25rem !important;
  backdrop-filter: blur(24px) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2),
              inset 0 1px 0 rgba(255,255,255,0.07) !important;
  transition: transform 0.28s cubic-bezier(.4,0,.2,1),
              box-shadow 0.28s cubic-bezier(.4,0,.2,1) !important;
  position: relative; overflow: hidden;
}}
[data-testid="metric-container"]::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
  opacity: 0.8;
}}
[data-testid="metric-container"]::after {{
  content: ''; position: absolute; top: -50%; right: -25%;
  width: 140px; height: 140px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%);
  pointer-events: none;
}}
[data-testid="metric-container"]:hover {{
  transform: translateY(-5px) !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.28),
              0 0 40px rgba(99,102,241,0.2) !important;
  border-color: rgba(99,102,241,0.4) !important;
}}
[data-testid="stMetricValue"] {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2.1rem !important; font-weight: 800 !important;
  letter-spacing: -0.05em !important; line-height: 1.1 !important;
  background: linear-gradient(135deg, var(--t1) 30%, #818cf8) !important;
  -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}}
[data-testid="stMetricLabel"] {{
  font-size: 0.67rem !important; font-weight: 800 !important;
  color: var(--t3) !important;
  letter-spacing: 0.14em !important; text-transform: uppercase !important;
}}
[data-testid="stMetricDelta"] {{
  font-size: 0.79rem !important; font-weight: 600 !important;
}}

/* ══ HEADINGS ════════════════════════════════════════════════ */
h1 {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2.1rem !important; font-weight: 800 !important;
  letter-spacing: -0.045em !important; line-height: 1.12 !important;
  background: linear-gradient(135deg, var(--t1) 45%, #818cf8 100%) !important;
  -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}}
h2 {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.3rem !important; font-weight: 700 !important;
  color: var(--t1) !important; letter-spacing: -0.025em !important;
}}
h3 {{ font-size: 0.95rem !important; font-weight: 600 !important; color: var(--t2) !important; }}

/* ══ DATAFRAME ═══════════════════════════════════════════════ */
[data-testid="stDataFrame"] {{
  border-radius: var(--r-md) !important; overflow: hidden !important;
  border: 1px solid var(--border2) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18),
              inset 0 1px 0 rgba(255,255,255,0.05) !important;
  backdrop-filter: blur(16px) !important;
}}
.dataframe thead th {{
  background: rgba(99,102,241,0.12) !important;
  font-size: 0.68rem !important; font-weight: 900 !important;
  color: #a5b4fc !important; text-transform: uppercase !important;
  letter-spacing: 0.12em !important; padding: 14px 18px !important;
  border-bottom: 1px solid rgba(99,102,241,0.2) !important;
}}
.dataframe td {{
  font-size: 0.875rem !important; color: var(--t1) !important;
  padding: 12px 18px !important; border-bottom: 1px solid var(--border) !important;
}}
.dataframe tr:hover td {{ background: var(--glass2) !important; }}
.dataframe tr:last-child td {{ border-bottom: none !important; }}

/* ══ ALERTS ══════════════════════════════════════════════════ */
.stSuccess, .stWarning, .stInfo, .stError {{
  border-radius: var(--r-sm) !important;
  backdrop-filter: blur(14px) !important;
  border-width: 1px !important; border-left-width: 3px !important;
  font-size: 0.875rem !important;
}}

/* ══ FORM INPUTS ═════════════════════════════════════════════ */
.stSelectbox > div > div {{
  border-radius: var(--r-sm) !important; border: 1px solid var(--border2) !important;
  background: var(--inp) !important; color: var(--t1) !important;
  font-size: 0.875rem !important; backdrop-filter: blur(10px) !important;
  transition: all 0.2s ease !important;
}}
.stSelectbox > div > div:focus-within {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.16), 0 0 20px rgba(99,102,241,0.12) !important;
}}
.stNumberInput > div > div > input,
.stTextInput > div > div > input {{
  border-radius: var(--r-sm) !important; border: 1px solid var(--border2) !important;
  background: var(--inp) !important; color: var(--t1) !important;
  font-size: 0.875rem !important; transition: all 0.2s ease !important;
}}
.stNumberInput > div > div > input:focus,
.stTextInput > div > div > input:focus {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.16), 0 0 20px rgba(99,102,241,0.12) !important;
  outline: none !important;
}}

/* ══ FILE UPLOADER ═══════════════════════════════════════════ */
[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed rgba(99,102,241,0.35) !important;
  border-radius: var(--r-md) !important;
  background: rgba(99,102,241,0.04) !important;
  backdrop-filter: blur(10px) !important;
  transition: all 0.25s ease !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{
  border-color: rgba(99,102,241,0.7) !important;
  background: rgba(99,102,241,0.09) !important;
  box-shadow: 0 0 30px rgba(99,102,241,0.12) !important;
}}

/* ══ EXPANDER ════════════════════════════════════════════════ */
[data-testid="stExpander"] {{
  border: 1px solid var(--border2) !important;
  border-radius: var(--r-md) !important;
  background: var(--glass) !important;
  backdrop-filter: blur(16px) !important;
  transition: all 0.25s ease !important; overflow: hidden !important;
}}
[data-testid="stExpander"]:hover {{
  border-color: rgba(99,102,241,0.3) !important;
  box-shadow: 0 6px 30px rgba(99,102,241,0.1) !important;
}}

/* ══ HR ══════════════════════════════════════════════════════ */
hr {{
  border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--border2), transparent) !important;
  margin: 2rem 0 !important;
}}

.stCaption {{ color: var(--t3) !important; font-size: 0.73rem !important; }}

/* ══ SECTION LABEL ═══════════════════════════════════════════ */
.sec-lbl {{
  display: flex; align-items: center; gap: 10px;
  font-size: 0.64rem; font-weight: 900; letter-spacing: 0.18em;
  text-transform: uppercase; margin: 0.25rem 0 1rem;
  background: linear-gradient(135deg, #6366f1, #a78bfa);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.sec-lbl::before {{
  content: ''; display: block; width: 22px; height: 2px; flex-shrink: 0;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 99px; box-shadow: 0 0 8px rgba(99,102,241,0.5);
}}
.sec-lbl::after {{
  content: ''; flex: 1; height: 1px;
  background: linear-gradient(90deg, var(--border2), transparent);
}}

/* ══ PAGE HEADER ═════════════════════════════════════════════ */
.ph {{
  background: var(--glass); border: 1px solid var(--border2);
  border-radius: var(--r-xl); padding: 1.75rem 2.25rem;
  margin-bottom: 2.25rem; backdrop-filter: blur(24px);
  box-shadow: 0 8px 40px rgba(0,0,0,0.2),
              inset 0 1px 0 rgba(255,255,255,0.07);
  position: relative; overflow: hidden;
}}
.ph::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.55),
              rgba(139,92,246,0.45), transparent);
}}
.ph::after {{
  content: ''; position: absolute; top: -80px; right: -60px;
  width: 260px; height: 260px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%);
  pointer-events: none;
}}
.ph-badge {{
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25);
  border-radius: 999px; padding: 4px 14px;
  font-size: 0.72rem; font-weight: 800; letter-spacing: 0.07em; color: #a5b4fc;
  margin-bottom: 10px; backdrop-filter: blur(8px);
}}
.ph-badge::before {{
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: #6366f1; box-shadow: 0 0 8px #6366f1;
  animation: pulse-dot 2s ease-in-out infinite;
}}
@keyframes pulse-dot {{
  0%,100%{{ opacity:1; transform:scale(1); }}
  50%{{ opacity:0.5; transform:scale(0.7); }}
}}

/* ══ STUDENT CARD ════════════════════════════════════════════ */
.sc {{
  position: relative; border-radius: 20px;
  padding: 22px 26px 20px; margin-bottom: 14px;
  backdrop-filter: blur(24px);
  transition: transform 0.28s cubic-bezier(.4,0,.2,1),
              box-shadow 0.28s cubic-bezier(.4,0,.2,1);
  overflow: hidden;
}}
.sc:hover {{ transform: translateY(-3px); }}
.sc-top {{ height: 2px; position: absolute; top: 0; left: 0; right: 0; }}
.sc-avatar {{
  width: 52px; height: 52px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 900; color: #fff; flex-shrink: 0;
}}
.sc-name {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.08rem; font-weight: 700; letter-spacing: -0.015em;
  color: var(--t1);
}}
.sc-room {{ font-size: 0.78rem; color: var(--t3); margin-top: 3px; }}
.sc-badge {{
  display: inline-block; padding: 5px 14px; border-radius: 999px;
  font-size: 0.7rem; font-weight: 800; letter-spacing: 0.07em; color: #fff;
}}
.sc-bar-track {{
  background: rgba(255,255,255,0.07); border-radius: 999px;
  height: 5px; overflow: hidden; margin: 8px 0 18px;
}}
.sc-bar {{
  height: 5px; border-radius: 999px;
  transition: width 0.7s cubic-bezier(.4,0,.2,1);
}}
.sc-stats {{
  display: grid; grid-template-columns: repeat(4,1fr);
  background: rgba(255,255,255,0.035); border-radius: 14px;
  border: 1px solid var(--border); overflow: hidden;
}}
.sc-stat {{
  padding: 11px 16px;
  border-right: 1px solid var(--border);
}}
.sc-stat:last-child {{ border-right: none; }}
.sc-stat-lbl {{
  font-size: 0.6rem; font-weight: 800; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--t3);
}}
.sc-stat-val {{
  font-size: 0.95rem; font-weight: 700; margin-top: 4px;
  color: var(--t1); font-variant-numeric: tabular-nums;
}}

/* ══ RECEIPT CARD ════════════════════════════════════════════ */
.rc {{
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 10px;
  background: var(--glass); border: 1px solid rgba(16,185,129,0.2);
  border-radius: 16px; padding: 14px 20px; margin-bottom: 10px;
  backdrop-filter: blur(18px);
  box-shadow: 0 3px 20px rgba(16,185,129,0.08);
  transition: all 0.22s ease;
}}
.rc:hover {{
  border-color: rgba(16,185,129,0.4);
  box-shadow: 0 8px 32px rgba(16,185,129,0.14);
  transform: translateX(3px);
}}
.rc-avatar {{
  width: 44px; height: 44px; border-radius: 13px;
  background: linear-gradient(135deg,#10b981,#047857);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 900; color: #fff; flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(16,185,129,0.4);
}}
.rc-name {{ font-size: 0.93rem; font-weight: 700; color: var(--t1); }}
.rc-sub {{ font-size: 0.75rem; color: var(--t3); margin-top: 2px; }}
.rc-amt {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.2rem; font-weight: 800;
  background: linear-gradient(135deg,#10b981,#34d399);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; font-variant-numeric: tabular-nums;
}}

/* ══ HALL SUMMARY CARD ═══════════════════════════════════════ */
.hsc {{
  background: var(--glass); border: 1px solid var(--border2);
  border-radius: 20px; padding: 22px 26px; margin-bottom: 12px;
  backdrop-filter: blur(20px);
  transition: transform 0.28s cubic-bezier(.4,0,.2,1),
              box-shadow 0.28s cubic-bezier(.4,0,.2,1);
  position: relative; overflow: hidden;
}}
.hsc:hover {{ transform: translateY(-3px); }}
.hsc::before {{
  content: ''; position: absolute; top: 0; left: 0; bottom: 0;
  width: 3px; border-radius: 20px 0 0 20px;
}}

/* ══ SIDEBAR LOGO ════════════════════════════════════════════ */
.sb-logo {{
  padding: 2rem 1.4rem 1.5rem;
  border-bottom: 1px solid rgba(99,102,241,0.12);
  margin-bottom: 1.4rem; position: relative; overflow: hidden;
}}
.sb-logo::after {{
  content: ''; position: absolute; top: -40px; right: -40px;
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.15), transparent 70%);
  pointer-events: none;
}}
.sb-icon {{
  width: 48px; height: 48px; border-radius: 16px;
  background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.18));
  border: 1px solid rgba(99,102,241,0.35);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; margin-bottom: 14px;
  box-shadow: 0 4px 20px rgba(99,102,241,0.22),
              inset 0 1px 0 rgba(255,255,255,0.1);
}}
.sb-title {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.05rem; font-weight: 800;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; letter-spacing: -0.02em;
}}
.sb-sub {{
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: rgba(99,102,241,0.65) !important;
  margin-top: 4px;
}}
.sb-credit {{
  margin: 10px; padding: 14px;
  border-top: 1px solid rgba(99,102,241,0.12);
  border-radius: var(--r-sm);
  background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(139,92,246,0.05));
  text-align: center;
}}
.sb-credit-name {{
  font-family: 'Space Grotesk', sans-serif; font-size: 0.88rem; font-weight: 800;
  background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; letter-spacing: -0.01em;
}}
.sb-credit-sub {{
  font-size: 0.68rem; font-weight: 600; color: rgba(99,102,241,0.6) !important;
  margin-top: 3px; letter-spacing: 0.05em;
}}
.sb-credit-tag {{
  font-size: 0.61rem; color: rgba(99,102,241,0.38) !important;
  margin-top: 5px; font-style: italic; letter-spacing: 0.03em;
}}

/* ══ FOOTER ══════════════════════════════════════════════════ */
.footer {{
  margin-top: 4rem; padding: 1.75rem 2.25rem;
  background: var(--glass); border: 1px solid var(--border2);
  border-radius: var(--r-xl); backdrop-filter: blur(24px);
  box-shadow: 0 8px 40px rgba(0,0,0,0.15),
              inset 0 1px 0 rgba(255,255,255,0.06);
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 12px;
  position: relative; overflow: hidden;
}}
.footer::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.45),
              rgba(139,92,246,0.4), transparent);
}}
.footer-title {{
  font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 800;
  background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; letter-spacing: -0.01em;
}}
.footer-by {{
  font-family: 'Space Grotesk', sans-serif; font-size: 0.9rem; font-weight: 800;
  background: linear-gradient(135deg, #6366f1, #a5b4fc);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.footer-sub {{ font-size: 0.76rem; color: var(--t3); margin-top: 3px; }}
.footer-meta {{ font-size: 0.72rem; color: var(--t3); margin-top: 4px; letter-spacing: 0.03em; }}
</style>
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
        "room no":"RoomNo","roomno":"RoomNo","room no.":"RoomNo","room":"RoomNo","room_no":"RoomNo",
        "name":"Name","student name":"Name","student_name":"Name",
        "food dues":"Food_Dues","food_dues":"Food_Dues","fooddues":"Food_Dues",
        "service charges":"Service_Charges","service_charges":"Service_Charges","servicecharges":"Service_Charges",
        "previous":"Previous","prev":"Previous","arrears":"Previous","month":"Month",
    }
    df = df.rename(columns=col_map)
    for col in ["RoomNo","Name","Food_Dues","Service_Charges","Previous"]:
        if col not in df.columns:
            df[col] = "" if col in ["RoomNo","Name"] else 0
    return df

def get_dues_from_cache(all_data, hall):
    key = find_sheet_key(all_data, hall)
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])
    df = all_data[key].copy()
    df = standardize_columns(df)
    if "Month" not in df.columns: df["Month"] = "Unknown"
    df["Month"] = df["Month"].astype(str).str.strip()
    for col in ["Food_Dues","Service_Charges","Previous"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
    df["Name"]   = df["Name"].astype(str).str.strip()
    df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]
    return df

def get_payments_from_cache(all_data, hall):
    key = find_sheet_key(all_data, f"{hall}_Payments")
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_B64","Receipt_Ext","File_Hash"])
    return all_data[key].copy()

def clean_for_sheets(df):
    df = df.copy().fillna("")
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: int(x)   if isinstance(x, (np.integer,))  else
                      float(x) if isinstance(x, (np.floating,)) else
                      bool(x)  if isinstance(x, (np.bool_,))    else
                      str(x)   if not isinstance(x, (str,int,float,bool)) else x
        )
    return df

def find_or_create_worksheet(name):
    sh = get_spreadsheet()
    clean = name.strip().lower().replace(" ","")
    for ws in sh.worksheets():
        if ws.title.strip().lower().replace(" ","") == clean:
            return ws
    return sh.add_worksheet(title=name, rows=5000, cols=20)

def save_dues(df, hall):
    ws = find_or_create_worksheet(hall)
    ws.clear(); df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()

def save_payments(df, hall):
    ws = find_or_create_worksheet(f"{hall}_Payments")
    ws.clear(); df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()

if not os.path.exists("receipts"):
    os.makedirs("receipts")


# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
halls = [
    "SMG Hall","MBQ Hall","EIDHI Hall","ZUBAIR Hall","MUMTAZ Hall",
    "LIAQUAT Hall","QUAID AZAM Hall","IQBAL Hall","SIR SYED Hall"
]
hall_passwords = {
    "SMG Hall":"smg123","MBQ Hall":"mbq456","EIDHI Hall":"eidhi789",
    "ZUBAIR Hall":"zubair012","MUMTAZ Hall":"mumtaz345","LIAQUAT Hall":"liaquat678",
    "QUAID AZAM Hall":"quaid901","IQBAL Hall":"iqbal234","SIR SYED Hall":"syed567",
}
senior_password = "senior@1122"


# ══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ══════════════════════════════════════════════════════════════════
def section_label(text):
    st.markdown(f'<div class="sec-lbl">{text}</div>', unsafe_allow_html=True)

def page_header(title, subtitle="", badge=""):
    badge_html = f'<div class="ph-badge">{badge}</div>' if badge else ""
    sub_html   = f'<p style="color:var(--t2);margin:8px 0 0;font-size:0.9rem;font-weight:500;">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<div class="ph">{badge_html}<h1 style="margin:0;padding:0;">{title}</h1>{sub_html}</div>',
                unsafe_allow_html=True)
    _c1,_c2 = st.columns([8,1])
    with _c2:
        icon  = "☀" if _t=="dark" else "◑"
        label = "Light" if _t=="dark" else "Dark"
        if st.button(f"{icon} {label}", key="theme_btn"):
            st.session_state["theme"] = "light" if _t=="dark" else "dark"
            st.rerun()

def student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    pct = int(min(100, paid_amount / total * 100)) if total else 0

    if paid_amount >= total:
        accent="#10b981"; glow="rgba(16,185,129,0.22)"; grad="linear-gradient(135deg,#10b981,#059669)"
        badge_txt="PAID IN FULL"; badge_ic="✓"; border_col="rgba(16,185,129,0.32)"
        bg="rgba(16,185,129,0.05)"
        amt_html=f'<span style="color:#10b981;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Cleared</span>'
    elif paid_amount > 0:
        accent="#6366f1"; glow="rgba(99,102,241,0.22)"; grad="linear-gradient(135deg,#6366f1,#8b5cf6)"
        badge_txt="PARTIAL PAYMENT"; badge_ic="◑"; border_col="rgba(99,102,241,0.32)"
        bg="rgba(99,102,241,0.05)"
        amt_html=f'<span style="color:#818cf8;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;">Paid&nbsp;Rs&nbsp;{int(paid_amount):,} &nbsp;·&nbsp; Due&nbsp;Rs&nbsp;{int(remaining):,}</span>'
    else:
        accent="#f43f5e"; glow="rgba(244,63,94,0.2)"; grad="linear-gradient(135deg,#f43f5e,#be123c)"
        badge_txt="UNPAID"; badge_ic="✗"; border_col="rgba(244,63,94,0.3)"
        bg="rgba(244,63,94,0.04)"
        amt_html=f'<span style="color:#fb7185;font-weight:800;font-size:0.95rem;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Outstanding</span>'

    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"

    st.markdown(f"""
<div class="sc" style="background:{bg};border:1px solid {border_col};
     box-shadow:0 6px 36px {glow},0 1px 4px rgba(0,0,0,0.14);">
  <div class="sc-top" style="background:{grad};
       box-shadow:0 0 20px {glow};"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-top:4px;">
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="sc-avatar" style="background:{grad};box-shadow:0 8px 24px {glow};">{initials}</div>
      <div>
        <div class="sc-name">{name}</div>
        <div class="sc-room">Room&nbsp;<strong style="color:{accent};font-weight:700;">{room}</strong></div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
      <span class="sc-badge" style="background:{grad};box-shadow:0 4px 14px {glow};">
        {badge_ic}&nbsp;&nbsp;{badge_txt}
      </span>
      {amt_html}
    </div>
  </div>
  <div style="margin-top:18px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;">
      <span style="font-size:0.68rem;font-weight:700;color:var(--t3);letter-spacing:0.08em;text-transform:uppercase;">Payment Progress</span>
      <span style="font-size:0.78rem;font-weight:900;color:{accent};">{pct}%</span>
    </div>
    <div class="sc-bar-track">
      <div class="sc-bar" style="width:{pct}%;background:{grad};box-shadow:0 0 12px {glow};"></div>
    </div>
    <div class="sc-stats">
      <div class="sc-stat">
        <div class="sc-stat-lbl">Food Dues</div>
        <div class="sc-stat-val">Rs&nbsp;{int(food):,}</div>
      </div>
      <div class="sc-stat">
        <div class="sc-stat-lbl">Service</div>
        <div class="sc-stat-val">Rs&nbsp;{int(service):,}</div>
      </div>
      <div class="sc-stat">
        <div class="sc-stat-lbl">Previous</div>
        <div class="sc-stat-val">Rs&nbsp;{int(prev):,}</div>
      </div>
      <div class="sc-stat" style="background:rgba(99,102,241,0.07);">
        <div class="sc-stat-lbl" style="color:{accent};">Total Due</div>
        <div class="sc-stat-val" style="color:{accent};font-size:1.02rem;font-weight:900;">Rs&nbsp;{int(total):,}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

def receipt_card(room, name, amount, date, idx):
    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    try: amt_fmt = f"Rs\u00a0{int(float(amount)):,}"
    except: amt_fmt = "Rs\u00a00"
    st.markdown(f"""
<div class="rc">
  <div style="display:flex;align-items:center;gap:14px;">
    <div class="rc-avatar">{initials}</div>
    <div>
      <div class="rc-name">{name}</div>
      <div class="rc-sub">Room&nbsp;<strong style="color:#818cf8;">{room}</strong>&nbsp;&nbsp;·&nbsp;&nbsp;{date}</div>
    </div>
  </div>
  <div class="rc-amt">{amt_fmt}</div>
</div>
""", unsafe_allow_html=True)

def hall_summary_card(hall_name, total, collected, remaining, pct_int):
    if total == 0:
        accent="#64748b"; glow="rgba(100,116,139,0.1)"; grad="linear-gradient(135deg,#64748b,#475569)"
    elif remaining == 0:
        accent="#10b981"; glow="rgba(16,185,129,0.18)"; grad="linear-gradient(135deg,#10b981,#059669)"
    elif collected > 0:
        accent="#6366f1"; glow="rgba(99,102,241,0.18)"; grad="linear-gradient(135deg,#6366f1,#8b5cf6)"
    else:
        accent="#f43f5e"; glow="rgba(244,63,94,0.18)"; grad="linear-gradient(135deg,#f43f5e,#be123c)"

    bar_w = min(100, pct_int)
    st.markdown(f"""
<div class="hsc" style="box-shadow:0 6px 32px {glow};">
  <div style="position:absolute;top:0;left:0;bottom:0;width:3px;
              background:{grad};border-radius:20px 0 0 20px;
              box-shadow:2px 0 12px {glow};"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;gap:12px;padding-left:8px;">
    <div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;
                  color:var(--t1);letter-spacing:-0.02em;">{hall_name}</div>
      <div style="font-size:0.75rem;color:var(--t3);margin-top:4px;">
        Total Outstanding:&nbsp;<strong style="color:var(--t2);font-variant-numeric:tabular-nums;">Rs&nbsp;{total:,}</strong>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:1.9rem;font-weight:900;
                  background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;font-variant-numeric:tabular-nums;line-height:1;">{pct_int}%</div>
      <div style="font-size:0.62rem;color:var(--t3);font-weight:900;letter-spacing:0.12em;margin-top:2px;">COLLECTED</div>
    </div>
  </div>
  <div style="background:rgba(255,255,255,0.06);border-radius:999px;height:7px;
              overflow:hidden;margin-bottom:18px;padding-left:8px;box-shadow:inset 0 1px 3px rgba(0,0,0,0.2);">
    <div style="background:{grad};height:7px;width:{bar_w}%;border-radius:999px;
                box-shadow:0 0 16px {glow};transition:width 0.6s cubic-bezier(.4,0,.2,1);"></div>
  </div>
  <div style="display:flex;gap:28px;flex-wrap:wrap;padding-left:8px;">
    <div>
      <div style="font-size:0.63rem;font-weight:800;color:var(--t3);letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Collected</div>
      <div style="font-size:0.95rem;font-weight:800;color:#10b981;font-variant-numeric:tabular-nums;">Rs&nbsp;{collected:,}</div>
    </div>
    <div>
      <div style="font-size:0.63rem;font-weight:800;color:var(--t3);letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Remaining</div>
      <div style="font-size:0.95rem;font-weight:800;color:#f43f5e;font-variant-numeric:tabular-nums;">Rs&nbsp;{remaining:,}</div>
    </div>
    <div>
      <div style="font-size:0.63rem;font-weight:800;color:var(--t3);letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">Students</div>
      <div style="font-size:0.95rem;font-weight:800;color:var(--t2);font-variant-numeric:tabular-nums;">—</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div class="sb-logo">
  <div class="sb-icon">🏛️</div>
  <div class="sb-title">Mess Dues System</div>
  <div class="sb-sub">University Hostel Management</div>
</div>
""", unsafe_allow_html=True)

role = st.sidebar.selectbox("Role", ["Student", "Hall Admin", "Senior Warden"])

if AUTO_REFRESH:
    refresh_rate = st.sidebar.selectbox("Auto Refresh", ["Off", "30 sec", "60 sec", "2 min"], index=2)
    rate_map = {"Off":0,"30 sec":30000,"60 sec":60000,"2 min":120000}
    if rate_map[refresh_rate] > 0:
        st_autorefresh(interval=rate_map[refresh_rate], key="autorefresh")

st.sidebar.markdown("""
<div class="sb-credit">
  <div class="sb-credit-name">Abdul Hadi</div>
  <div class="sb-credit-sub">2025 (S) &nbsp;·&nbsp; CYS 90</div>
  <div class="sb-credit-tag">Designed &amp; Developed</div>
</div>
""", unsafe_allow_html=True)

if role == "Student":
    hall     = st.sidebar.selectbox("Select Hall", halls)
    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    page_header(hall, "View your mess dues and submit payment receipts", badge="Student Portal")

    if dues.empty:
        st.warning("No dues have been uploaded for this hall yet.")
        st.stop()

    month_list     = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Select Month", month_list)
    month_dues     = dues[dues["Month"] == selected_month].sort_values("RoomNo")

    total_due = month_dues["Total"].sum()
    total_students = len(month_dues)
    paid_count = 0; total_collected = 0
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

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Students", total_students)
    c2.metric("Total Dues",     f"Rs {int(total_due):,}")
    c3.metric("Fully Paid",     paid_count)
    c4.metric("Still Pending",  total_students - paid_count)

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Student Dues")

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

        with st.expander(f"Receipt Upload  |  Room {room}  |  {name}"):
            uploaded_files = st.file_uploader("Upload receipt image(s)", accept_multiple_files=True, key=f"files_{room}_{idx}")
            amount_paid_input = st.number_input("Amount Submitted (Rs)", min_value=1, max_value=int(total), value=int(total), step=1, key=f"amt_{room}_{idx}")

            if uploaded_files:
                if st.button(f"Submit Receipt  |  Room {room}", key=f"submit_{room}_{idx}"):
                    invalidate_cache()
                    fresh_all        = load_all_sheets_data()
                    current_payments = get_payments_from_cache(fresh_all, hall)
                    added, errors    = 0, []
                    for f in uploaded_files:
                        file_bytes = f.getvalue()
                        file_hash  = hashlib.md5(file_bytes).hexdigest()
                        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        file_ext   = os.path.splitext(f.name)[-1].lower().strip(".")

                        if not current_payments.empty and "File_Hash" in current_payments.columns:
                            dup = current_payments[
                                (current_payments["RoomNo"].astype(str).str.strip() == room) &
                                (current_payments["Name"].astype(str).str.strip()   == name) &
                                (current_payments["Month"] == selected_month) &
                                (current_payments["File_Hash"] == file_hash)
                            ]
                            if not dup.empty:
                                errors.append(f"Duplicate receipt: {f.name}")
                                continue

                        import base64
                        b64_data = base64.b64encode(file_bytes).decode("utf-8")

                        new_row = pd.DataFrame([{
                            "Month":selected_month,"RoomNo":room,"Name":name,
                            "Amount_Paid":amount_paid_input,"Submission_Date":now_str,
                            "Receipt_B64":b64_data,"Receipt_Ext":file_ext,
                            "File_Hash":file_hash
                        }])
                        current_payments = pd.concat([current_payments, new_row], ignore_index=True)
                        added += 1
                    if added:
                        save_payments(current_payments, hall)
                        rem = int(total) - amount_paid_input
                        if rem > 0: st.success(f"Receipt submitted. Paid: Rs {amount_paid_input:,} · Remaining: Rs {rem:,}")
                        else:       st.success(f"Full payment submitted. Amount: Rs {amount_paid_input:,}")
                        st.rerun()
                    for e in errors: st.error(e)


# ══════════════════════════════════════════════════════════════════
# HALL ADMIN
# ══════════════════════════════════════════════════════════════════
elif role == "Hall Admin":
    hall = st.sidebar.selectbox("Select Hall", halls)
    pw   = st.sidebar.text_input("Administrator Password", type="password")
    if pw != hall_passwords.get(hall,""):
        st.sidebar.error("Incorrect password")
        st.stop()

    page_header(f"{hall} — Admin Panel", "Manage dues, track payments and review receipts", badge="Admin")

    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    tab1,tab2,tab3,tab4,tab5 = st.tabs(["Upload Dues","Dashboard","Pending","Receipts","Manage Months"])

    with tab1:
        section_label("Upload Monthly Dues")
        years       = list(range(2025, 2032))
        months_list = [f"{y}-{m:02d}" for y in years for m in range(1,13)]
        month       = st.selectbox("Billing Month", months_list, index=months_list.index(datetime.now().strftime("%Y-%m")))
        uploaded    = st.file_uploader("Select Excel or CSV File", type=["csv","xlsx"])

        if uploaded and st.button("Upload and Save"):
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df = df.loc[:,~df.columns.duplicated()]
            df = standardize_columns(df)
            for col in ["Food_Dues","Service_Charges","Previous"]:
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
            if "Month" in existing.columns: existing = existing[existing["Month"] != month]
            for c in keep:
                if c not in existing.columns: existing[c] = ""
                if c not in df.columns:       df[c] = ""
            existing, df = existing[keep], df[keep]

            if not existing.empty and "Month" in existing.columns:
                past = sorted([m for m in existing["Month"].unique() if m != month], reverse=True)
                if past:
                    last_m = past[0]; last_dues = existing[existing["Month"]==last_m].copy(); carry_map = {}
                    for _, lr in last_dues.iterrows():
                        lr_room = str(lr["RoomNo"]).strip(); lr_name = str(lr["Name"]).strip()
                        lr_tot  = float(lr["Total"]); lr_paid = 0.0
                        if not all_payments.empty and "Amount_Paid" in all_payments.columns and "Month" in all_payments.columns:
                            sp = all_payments[
                                (all_payments["RoomNo"].astype(str).str.strip()==lr_room) &
                                (all_payments["Name"].astype(str).str.strip()==lr_name) &
                                (all_payments["Month"]==last_m)
                            ]
                            lr_paid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                        rem = max(0.0, lr_tot - lr_paid)
                        if rem > 0: carry_map[f"{lr_room}||{lr_name}"] = rem
                    if carry_map:
                        carried = 0
                        for i,r2 in df.iterrows():
                            k = f"{str(r2['RoomNo']).strip()}||{str(r2['Name']).strip()}"
                            if k in carry_map:
                                df.at[i,"Previous"] = float(df.at[i,"Previous"]) + carry_map[k]
                                df.at[i,"Total"]    = float(df.at[i,"Food_Dues"]) + float(df.at[i,"Service_Charges"]) + float(df.at[i,"Previous"])
                                carried += 1
                        if carried: st.info(f"{carried} student(s) had arrears carried forward from {last_m} to {month}.")

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)
            if not all_payments.empty and "Month" in all_payments.columns:
                cleaned = all_payments[all_payments["Month"] != month]
                removed = len(all_payments) - len(cleaned)
                save_payments(cleaned, hall)
                if removed: st.info(f"{removed} previous payment record(s) for {month} were cleared.")
            st.success(f"{len(df)} student records uploaded for {month}.")

    with tab2:
        if dues.empty:
            st.info("No data available. Please upload dues first.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Select Month", month_list, key="dash_month")
            df_d       = dues[dues["Month"] == sel_month].copy()
            col_s,_    = st.columns([2,3])
            with col_s:
                srch = st.text_input("Search by Room or Name", placeholder="Room 12 or Ahmed")
            if srch:
                df_d = df_d[df_d["RoomNo"].str.contains(srch,case=False)|df_d["Name"].str.contains(srch,case=False)]

            total_dues = df_d["Total"].sum()
            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                collected = pd.to_numeric(payments[payments["Month"]==sel_month]["Amount_Paid"], errors="coerce").fillna(0).sum()
            else: collected = 0
            remaining = total_dues - collected
            pct = int(collected/total_dues*100) if total_dues else 0

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Dues",  f"Rs {int(total_dues):,}")
            c2.metric("Collected",   f"Rs {int(collected):,}", f"{pct}% recovered")
            c3.metric("Remaining",   f"Rs {int(remaining):,}")
            c4.metric("Students",    len(df_d))
            st.markdown("<br>",unsafe_allow_html=True)

            def paid_for(row):
                if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                    sp = payments[
                        (payments["RoomNo"].astype(str).str.strip()==str(row["RoomNo"]).strip()) &
                        (payments["Name"].astype(str).str.strip()==str(row["Name"]).strip()) &
                        (payments["Month"]==sel_month)
                    ]
                    return int(pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum())
                return 0

            df_d = df_d.copy()
            df_d["Paid (Rs)"]      = df_d.apply(paid_for, axis=1)
            df_d["Remaining (Rs)"] = (df_d["Total"]-df_d["Paid (Rs)"]).clip(lower=0).astype(int)
            df_d["Status"]         = df_d.apply(lambda r: "Paid" if r["Paid (Rs)"]>=r["Total"] else ("Partial" if r["Paid (Rs)"]>0 else "Unpaid"), axis=1)

            def row_color(row):
                s = row.get("Status","")
                if s=="Paid":    return ["background-color:rgba(16,185,129,0.12);color:#10b981;font-weight:700"]*len(row)
                elif s=="Partial": return ["background-color:rgba(99,102,241,0.12);color:#818cf8;font-weight:600"]*len(row)
                return ["background-color:rgba(244,63,94,0.10);color:#fb7185;font-weight:500"]*len(row)

            dcols = ["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)","Status"]
            st.dataframe(df_d[dcols].style.apply(row_color, axis=1), use_container_width=True, hide_index=True)
            st.markdown("<br>",unsafe_allow_html=True)
            section_label("Collection Chart")
            st.bar_chart(df_d.set_index("Name")[["Total","Paid (Rs)"]].head(30))
            st.markdown("---")
            csv = df_d[dcols].to_csv(index=False).encode("utf-8")
            st.download_button(f"Download {sel_month} Report (CSV)", csv, file_name=f"{hall}_{sel_month}.csv", mime="text/csv")

    with tab3:
        if dues.empty:
            st.info("No data available.")
        else:
            latest_m = sorted(dues["Month"].unique(), reverse=True)[0]
            lt_dues  = dues[dues["Month"]==latest_m].copy()
            lt_dues["_key"] = lt_dues["RoomNo"].astype(str).str.strip()+"||"+lt_dues["Name"].astype(str).str.strip()
            if not payments.empty and "Month" in payments.columns:
                mp = payments[payments["Month"]==latest_m].copy()
                mp["_key"] = mp["RoomNo"].astype(str).str.strip()+"||"+mp["Name"].astype(str).str.strip()
                def gpd(row):
                    sp = mp[mp["_key"]==row["_key"]]
                    return pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum() if (not sp.empty and "Amount_Paid" in sp.columns) else 0
                lt_dues["Paid"]      = lt_dues.apply(gpd, axis=1)
                lt_dues["Remaining"] = (lt_dues["Total"]-lt_dues["Paid"]).clip(lower=0)
            else:
                lt_dues["Paid"]=0; lt_dues["Remaining"]=lt_dues["Total"]
            pending    = lt_dues[lt_dues["Remaining"]>0].drop(columns=["_key"])
            fully_paid = len(lt_dues)-len(pending)
            section_label(f"Pending Payments — {latest_m}")
            c1,c2,c3 = st.columns(3)
            c1.metric("Pending Students", len(pending))
            c2.metric("Fully Paid",       fully_paid)
            c3.metric("Pending Amount",   f"Rs {int(pending['Remaining'].sum()):,}" if not pending.empty else "Rs 0")
            st.markdown("<br>",unsafe_allow_html=True)
            if pending.empty: st.success("All students have paid their dues for this month.")
            else:
                show = ["RoomNo","Name","Total","Paid","Remaining"]
                st.dataframe(pending[[c for c in show if c in pending.columns]], use_container_width=True, hide_index=True)

    with tab4:
        if payments.empty:
            st.info("No receipts have been submitted yet.")
        else:
            if "Month" in payments.columns:
                rec_months = ["All Months"] + sorted(payments["Month"].unique(), reverse=True)
                sel_rec_month = st.selectbox("Filter by Month", rec_months, key="rec_month")
                filtered_pays = payments if sel_rec_month=="All Months" else payments[payments["Month"]==sel_rec_month]
            else:
                filtered_pays = payments
            section_label(f"All Receipts — {len(filtered_pays)} submissions")
            import base64 as _b64
            for i,row in filtered_pays.iterrows():
                receipt_card(row["RoomNo"],row["Name"],row.get("Amount_Paid",""),row.get("Submission_Date",""),i)
                b64  = str(row.get("Receipt_B64","")).strip()
                ext  = str(row.get("Receipt_Ext","jpg")).strip().lower()
                path = str(row.get("Receipt_File","")).strip()

                # Try base64 first (new system — permanent)
                if b64 and len(b64) > 100:
                    try:
                        img_bytes = _b64.b64decode(b64)
                        mime = "image/png" if ext=="png" else "image/jpeg"
                        if ext in ("png","jpg","jpeg","webp"):
                            st.image(img_bytes, width=260)
                        st.download_button(
                            "Download Receipt", img_bytes,
                            file_name=f"receipt_{row['RoomNo']}_{row['Name']}.{ext}",
                            mime=mime, key=f"dl_{i}"
                        )
                    except Exception:
                        st.caption("Could not decode receipt image.")
                # Fallback: old file-based system
                elif path and os.path.exists(path):
                    if path.lower().endswith((".png",".jpg",".jpeg",".webp")):
                        st.image(path, width=260)
                    with open(path,"rb") as fp:
                        st.download_button("Download Receipt", fp, file_name=os.path.basename(path), key=f"dl_{i}")
                else:
                    st.markdown("""
<div style="background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.2);
            border-radius:10px;padding:10px 14px;font-size:0.8rem;color:#fb7185;">
  Receipt image not available — this receipt was submitted before the permanent storage update.
  New receipts are stored permanently in Google Sheets.
</div>""", unsafe_allow_html=True)

    with tab5:
        if dues.empty:
            st.info("No months available.")
        else:
            section_label("Delete a Billing Month")
            month_list   = sorted(dues["Month"].unique(), reverse=True)
            month_to_del = st.selectbox("Select Month to Delete", month_list, key="del_month")
            st.warning(f"This will permanently delete all dues and receipts for **{month_to_del}**.")
            col1,col2 = st.columns([1,3])
            with col1:
                if st.button("Delete Month", type="primary"):
                    updated_dues = dues[dues["Month"]!=month_to_del].copy()
                    updated_pays = payments[payments["Month"]!=month_to_del].copy() \
                        if (not payments.empty and "Month" in payments.columns) else payments

                    all_remaining = sorted(updated_dues["Month"].unique())
                    next_month = next((m for m in all_remaining if m>month_to_del), None)
                    if next_month is not None:
                        del_dues_orig = dues[dues["Month"]==month_to_del].copy()
                        for i,row in updated_dues[updated_dues["Month"]==next_month].iterrows():
                            kr,kn = str(row["RoomNo"]).strip(),str(row["Name"]).strip()
                            match = del_dues_orig[(del_dues_orig["RoomNo"].astype(str).str.strip()==kr)&(del_dues_orig["Name"].astype(str).str.strip()==kn)]
                            if match.empty: continue
                            del_tot = float(match.iloc[0]["Total"]); del_paid = 0.0
                            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                                sp = payments[(payments["RoomNo"].astype(str).str.strip()==kr)&(payments["Name"].astype(str).str.strip()==kn)&(payments["Month"]==month_to_del)]
                                del_paid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                            arrear = max(0.0, del_tot - del_paid)
                            new_prev = max(0.0, float(updated_dues.at[i,"Previous"]) - arrear)
                            updated_dues.at[i,"Previous"] = new_prev
                            updated_dues.at[i,"Total"]    = float(updated_dues.at[i,"Food_Dues"])+float(updated_dues.at[i,"Service_Charges"])+new_prev

                    save_dues(updated_dues, hall)
                    if not payments.empty and "Month" in payments.columns:
                        save_payments(updated_pays, hall)
                    msg = f"All data for {month_to_del} deleted."
                    if next_month: msg += f" Arrears recalculated for {next_month}."
                    st.success(msg); st.rerun()
            with col2:
                st.info("Deleting a month also removes its carried arrears from the following month.")


# ══════════════════════════════════════════════════════════════════
# SENIOR WARDEN
# ══════════════════════════════════════════════════════════════════
elif role == "Senior Warden":
    pw = st.sidebar.text_input("Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.error("Incorrect password")
        st.stop()

    page_header("Senior Warden Dashboard", "Financial overview across all 9 halls", badge="Senior Warden")
    all_data = load_all_sheets_data()

    all_months = set()
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            for m in hd["Month"].unique():
                if m and m != "Unknown": all_months.add(m)

    month_options = ["All Months (Combined)"] + sorted(all_months, reverse=True)
    if "warden_selected_month" not in st.session_state:
        st.session_state["warden_selected_month"] = "All Months (Combined)"
    if st.session_state["warden_selected_month"] not in month_options:
        st.session_state["warden_selected_month"] = "All Months (Combined)"

    selected_w_month = st.selectbox("Reporting Period", month_options,
        index=month_options.index(st.session_state["warden_selected_month"]), key="warden_month_select")
    st.session_state["warden_selected_month"] = selected_w_month

    total_all=collected_all=remaining_all=paid_students_all=unpaid_students_all=0
    summary = []

    for hall in halls:
        hd = get_dues_from_cache(all_data, hall)
        hp = get_payments_from_cache(all_data, hall)
        if not hd.empty and "Month" in hd.columns:
            if selected_w_month != "All Months (Combined)":
                hd_f = hd[hd["Month"]==selected_w_month]
                hp_f = hp[hp["Month"]==selected_w_month] if (not hp.empty and "Month" in hp.columns) else pd.DataFrame()
            else:
                hd_f,hp_f = hd,hp
            if hd_f.empty:
                summary.append({"Hall":hall,"Students":0,"Total":0,"Collected":0,"Remaining":0,"Pct":0}); continue
            total     = int(hd_f["Total"].sum())
            collected = int(pd.to_numeric(hp_f["Amount_Paid"], errors="coerce").fillna(0).sum()) \
                        if (not hp_f.empty and "Amount_Paid" in hp_f.columns) else 0
            remaining=total-collected; pct=int(collected/total*100) if total else 0
            total_all+=total; collected_all+=collected; remaining_all+=remaining
            for _,row in hd_f.iterrows():
                r,n = str(row["RoomNo"]).strip(),str(row["Name"]).strip()
                if not hp_f.empty and "Amount_Paid" in hp_f.columns:
                    sp = hp_f[(hp_f["RoomNo"].astype(str).str.strip()==r)&(hp_f["Name"].astype(str).str.strip()==n)]
                    pa = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    if pa>=row["Total"]: paid_students_all+=1
                    else: unpaid_students_all+=1
                else: unpaid_students_all+=1
            summary.append({"Hall":hall,"Students":len(hd_f),"Total":total,"Collected":collected,"Remaining":remaining,"Pct":pct})
        else:
            summary.append({"Hall":hall,"Students":0,"Total":0,"Collected":0,"Remaining":0,"Pct":0})

    overall_pct = int(collected_all/total_all*100) if total_all else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Grand Total Dues",  f"Rs {int(total_all):,}")
    c2.metric("Total Collected",   f"Rs {int(collected_all):,}", f"{overall_pct}% recovered")
    c3.metric("Total Remaining",   f"Rs {int(remaining_all):,}")
    c4.metric("Recovery Rate",     f"{overall_pct}%")
    st.markdown("<br>",unsafe_allow_html=True)

    col_pie,col_bar = st.columns([1,2])
    with col_pie:
        section_label("Collection Status")
        try:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Pie(
                labels=["Collected","Remaining"], values=[collected_all, remaining_all], hole=0.6,
                marker=dict(colors=["#10b981","#f43f5e"], line=dict(color="rgba(0,0,0,0)",width=0)),
                textinfo="percent",
                textfont=dict(size=13,family="Inter, sans-serif",color="#fff"),
                hovertemplate="<b>%{label}</b><br>Rs %{value:,.0f}<extra></extra>"
            )])
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h",y=-0.2,x=0.5,xanchor="center",font=dict(size=12,family="Inter, sans-serif",color="#94a3b8")),
                margin=dict(t=10,b=10,l=10,r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(text=f"<b>{overall_pct}%</b><br><span style='font-size:11px;color:#94a3b8'>Recovered</span>",
                    x=0.5,y=0.5,font_size=18,font_family="Inter, sans-serif",font_color="#f1f5f9",showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        except ImportError:
            st.info(f"Collected Rs {collected_all:,} of Rs {total_all:,}")

    with col_bar:
        section_label("Hall-wise Comparison")
        try:
            import plotly.graph_objects as go
            names = [s["Hall"].replace(" Hall","") for s in summary]
            fig2  = go.Figure()
            fig2.add_trace(go.Bar(name="Collected",x=names,y=[s["Collected"] for s in summary],
                marker_color="#10b981",marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Rs %{y:,.0f}<extra></extra>"))
            fig2.add_trace(go.Bar(name="Remaining",x=names,y=[s["Remaining"] for s in summary],
                marker_color="#f43f5e",marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Rs %{y:,.0f}<extra></extra>"))
            fig2.update_layout(
                barmode="stack", showlegend=True,
                legend=dict(orientation="h",y=1.05,x=1,xanchor="right",font=dict(size=11,family="Inter, sans-serif",color="#94a3b8")),
                margin=dict(t=30,b=10,l=10,r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False,tickfont=dict(size=11,family="Inter, sans-serif",color="#94a3b8")),
                yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",tickformat=",",tickfont=dict(size=10,family="Inter, sans-serif",color="#94a3b8"))
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        except ImportError:
            st.bar_chart(pd.DataFrame(summary).set_index("Hall")[["Collected","Remaining"]])

    try:
        import plotly.graph_objects as go
        col_d1,col_d2 = st.columns(2)
        with col_d1:
            section_label("Student Payment Status")
            total_s = paid_students_all + unpaid_students_all
            fig3 = go.Figure(data=[go.Pie(
                labels=["Paid","Pending"], values=[paid_students_all, unpaid_students_all], hole=0.64,
                marker=dict(colors=["#6366f1","#f59e0b"], line=dict(color="rgba(0,0,0,0)",width=0)),
                textinfo="percent+value",
                textfont=dict(size=12,family="Inter, sans-serif",color="#fff"),
                hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
            )])
            fig3.update_layout(
                showlegend=True,
                legend=dict(orientation="h",y=-0.25,x=0.5,xanchor="center",font=dict(size=12,family="Inter, sans-serif",color="#94a3b8")),
                margin=dict(t=10,b=10,l=10,r=10), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(text=f"<b>{total_s}</b><br><span style='color:#94a3b8;font-size:11px'>students</span>",
                    x=0.5,y=0.5,font_size=15,font_family="Space Grotesk, sans-serif",font_color="#f1f5f9",showarrow=False)]
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        with col_d2:
            section_label("Hall Recovery Rates")
            h_labels = [s["Hall"].replace(" Hall","") for s in summary if s["Total"]>0]
            h_pcts   = [s["Pct"] for s in summary if s["Total"]>0]
            fig4 = go.Figure(go.Bar(
                x=h_pcts, y=h_labels, orientation="h",
                marker=dict(color=h_pcts, colorscale=[[0,"#f43f5e"],[0.5,"#f59e0b"],[1,"#10b981"]], showscale=False, line=dict(width=0)),
                text=[f"{p}%" for p in h_pcts], textposition="outside",
                textfont=dict(size=11,family="Inter, sans-serif",color="#94a3b8"),
                hovertemplate="<b>%{y}</b><br>Recovery: %{x}%<extra></extra>"
            ))
            fig4.update_layout(
                margin=dict(t=10,b=10,l=10,r=45), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0,118],showgrid=False,visible=False),
                yaxis=dict(showgrid=False,tickfont=dict(size=11,family="Inter, sans-serif",color="#94a3b8"))
            )
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
    except ImportError:
        pass

    st.markdown("<br>",unsafe_allow_html=True)
    section_label("Hall-wise Breakdown")
    for row in summary:
        hall_summary_card(row["Hall"],row["Total"],row["Collected"],row["Remaining"],row["Pct"])

    st.markdown("---")
    export_df = pd.DataFrame([{
        "Hall":r["Hall"],"Students":r["Students"],
        "Total Dues (Rs)":r["Total"],"Collected (Rs)":r["Collected"],
        "Remaining (Rs)":r["Remaining"],"Recovery %":f"{r['Pct']}%"
    } for r in summary])
    st.download_button("Download Full Summary (CSV)", export_df.to_csv(index=False).encode("utf-8"),
        file_name="all_halls_summary.csv", mime="text/csv")

    st.markdown("<br>",unsafe_allow_html=True)
    section_label("Month-wise Payments Overview")
    all_pay_rows = []
    for h in halls:
        hd = get_dues_from_cache(all_data, h); hp = get_payments_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            months_to_show = ([selected_w_month] if selected_w_month!="All Months (Combined)"
                              else sorted(hd["Month"].unique(), reverse=True))
            for mv in months_to_show:
                if mv=="Unknown": continue
                mdf = hd[hd["Month"]==mv]
                if mdf.empty: continue
                tot=int(mdf["Total"].sum()); recs=col=0
                if not hp.empty and "Month" in hp.columns:
                    mp=hp[hp["Month"]==mv]; recs=len(mp)
                    if "Amount_Paid" in mp.columns:
                        col=int(pd.to_numeric(mp["Amount_Paid"], errors="coerce").fillna(0).sum())
                all_pay_rows.append({
                    "Hall":h,"Month":mv,"Students":len(mdf),"Total Dues (Rs)":tot,
                    "Receipts":recs,"Collected (Rs)":col,"Remaining (Rs)":max(0,tot-col),
                    "Recovery %":f"{int(col/tot*100) if tot else 0}%"
                })
    if all_pay_rows:
        st.dataframe(pd.DataFrame(all_pay_rows).sort_values(["Month","Hall"],ascending=[False,True]),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No payment data available yet.")


# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="footer">
  <div>
    <div class="footer-title">University Mess Dues System</div>
    <div class="footer-sub">Powered by Streamlit &amp; Google Sheets</div>
  </div>
  <div style="text-align:right;">
    <div class="footer-by">Designed &amp; Developed by Abdul Hadi</div>
    <div class="footer-meta">2025 (S)&nbsp;&nbsp;·&nbsp;&nbsp;CYS 90&nbsp;&nbsp;·&nbsp;&nbsp;University of Engineering &amp; Technology</div>
  </div>
</div>
""", unsafe_allow_html=True)
