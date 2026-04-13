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
    page_title="University Mess Dues System",
    layout="wide",
    page_icon="🏛️",
    initial_sidebar_state="expanded"
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
_t = st.session_state["theme"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {{
  --accent:        #6366f1;
  --accent2:       #8b5cf6;
  --accent3:       #06b6d4;
  --green:         #10b981;
  --red:           #f43f5e;
  --amber:         #f59e0b;
  --radius-xs:     8px;
  --radius-sm:     12px;
  --radius-md:     16px;
  --radius-lg:     22px;
  --radius-xl:     28px;

  {"" if _t=="dark" else "/*"}
  --bg-base:       #070711;
  --bg-surface:    #0d0d1a;
  --bg-card:       rgba(255,255,255,0.038);
  --bg-card-h:     rgba(255,255,255,0.065);
  --bg-sidebar:    #08080f;
  --border:        rgba(255,255,255,0.07);
  --border-s:      rgba(255,255,255,0.13);
  --border-accent: rgba(99,102,241,0.35);
  --text-1:        #f8fafc;
  --text-2:        #94a3b8;
  --text-3:        #475569;
  --input-bg:      rgba(255,255,255,0.055);
  --glass:         rgba(255,255,255,0.042);
  --glass-b:       rgba(255,255,255,0.09);
  --shadow:        0 8px 32px rgba(0,0,0,0.4);
  --shadow-glow:   0 0 40px rgba(99,102,241,0.2);
  {"" if _t=="dark" else "*/"}

  {"/*" if _t=="dark" else ""}
  --bg-base:       #f0f2ff;
  --bg-surface:    #e8eafe;
  --bg-card:       rgba(255,255,255,0.75);
  --bg-card-h:     rgba(255,255,255,0.92);
  --bg-sidebar:    #12103a;
  --border:        rgba(99,102,241,0.1);
  --border-s:      rgba(99,102,241,0.22);
  --border-accent: rgba(99,102,241,0.4);
  --text-1:        #0c0b2e;
  --text-2:        #3730a3;
  --text-3:        #6366f1;
  --input-bg:      rgba(255,255,255,0.88);
  --glass:         rgba(255,255,255,0.65);
  --glass-b:       rgba(99,102,241,0.18);
  --shadow:        0 8px 32px rgba(99,102,241,0.12);
  --shadow-glow:   0 0 40px rgba(99,102,241,0.15);
  {"*/" if _t=="dark" else ""}
}}

/* ─────────────────────────────────────────
   BASE
───────────────────────────────────────── */
*, html, body, [class*="css"] {{
  font-family: 'Inter', sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  box-sizing: border-box;
}}

.stApp {{
  background: var(--bg-base) !important;
  background-image:
    radial-gradient(ellipse 90% 60% at 15% -5%,  rgba(99,102,241,0.18) 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 85% 105%, rgba(139,92,246,0.14) 0%, transparent 50%),
    radial-gradient(ellipse 50% 40% at 50% 50%,  rgba(6,182,212,0.05) 0%, transparent 60%) !important;
  background-attachment: fixed !important;
  min-height: 100vh;
}}

.block-container {{
  padding: 0 2.25rem 4rem !important;
  max-width: 1480px !important;
}}

/* ─────────────────────────────────────────
   ANIMATED PRISMATIC TOP BAR
───────────────────────────────────────── */
.stApp::before {{
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    #6366f1 0%, #8b5cf6 20%, #06b6d4 40%,
    #10b981 60%, #f59e0b 80%, #6366f1 100%);
  background-size: 400% 100%;
  animation: prism 6s linear infinite;
  z-index: 99999;
}}
@keyframes prism {{
  0%   {{ background-position: 0%   0%; }}
  100% {{ background-position: 400% 0%; }}
}}

/* ─────────────────────────────────────────
   SCROLLBAR
───────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
  background: rgba(99,102,241,0.35);
  border-radius: 99px;
}}
::-webkit-scrollbar-thumb:hover {{ background: rgba(99,102,241,0.6); }}

/* ─────────────────────────────────────────
   SIDEBAR
───────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: var(--bg-sidebar) !important;
  border-right: 1px solid rgba(99,102,241,0.12) !important;
  box-shadow: 6px 0 40px rgba(99,102,241,0.08) !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: #c7d2fe !important; }}
[data-testid="stSidebar"] label {{
  color: rgba(99,102,241,0.8) !important;
  font-size: 0.67rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div {{
  background: rgba(99,102,241,0.08) !important;
  border: 1px solid rgba(99,102,241,0.22) !important;
  border-radius: var(--radius-sm) !important;
  color: #e0e7ff !important;
  font-size: 0.86rem !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input {{
  background: rgba(99,102,241,0.08) !important;
  border: 1px solid rgba(99,102,241,0.22) !important;
  border-radius: var(--radius-sm) !important;
  color: #e0e7ff !important;
  font-size: 0.86rem !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}}

/* ─────────────────────────────────────────
   SIDEBAR LOGO BLOCK
───────────────────────────────────────── */
.sb-logo {{
  padding: 2rem 1.4rem 1.4rem;
  border-bottom: 1px solid rgba(99,102,241,0.15);
  margin-bottom: 1.4rem;
  position: relative;
  overflow: hidden;
}}
.sb-logo::after {{
  content: '';
  position: absolute;
  top: -30px; right: -30px;
  width: 100px; height: 100px;
  background: radial-gradient(circle, rgba(99,102,241,0.18), transparent 70%);
  pointer-events: none;
}}
.sb-logo .icon-ring {{
  width: 46px; height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.2));
  border: 1px solid rgba(99,102,241,0.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  margin-bottom: 14px;
  box-shadow: 0 4px 16px rgba(99,102,241,0.25);
}}
.sb-logo h2 {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.05rem; font-weight: 700;
  color: #e0e7ff !important;
  letter-spacing: -0.02em;
  margin: 0 0 4px;
}}
.sb-logo p {{
  font-size: 0.67rem; font-weight: 600;
  color: rgba(99,102,241,0.7) !important;
  letter-spacing: 0.1em; text-transform: uppercase;
  margin: 0;
}}

/* ─────────────────────────────────────────
   SIDEBAR FOOTER CREDIT
───────────────────────────────────────── */
.sb-credit {{
  margin: 12px 10px 0;
  padding: 14px 14px;
  border-top: 1px solid rgba(99,102,241,0.14);
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(139,92,246,0.05));
  text-align: center;
}}
.sb-credit .name {{
  font-size: 0.86rem; font-weight: 800;
  background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.01em;
}}
.sb-credit .sub {{
  font-size: 0.68rem; font-weight: 600;
  color: rgba(99,102,241,0.65) !important;
  margin-top: 3px; letter-spacing: 0.06em;
}}
.sb-credit .tag {{
  font-size: 0.62rem; color: rgba(99,102,241,0.4) !important;
  margin-top: 5px; font-style: italic; letter-spacing: 0.04em;
}}

/* ─────────────────────────────────────────
   BUTTONS
───────────────────────────────────────── */
.stButton > button {{
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 700 !important;
  font-size: 0.84rem !important;
  padding: 0.6rem 1.6rem !important;
  letter-spacing: 0.02em !important;
  box-shadow: 0 4px 18px rgba(99,102,241,0.38), inset 0 1px 0 rgba(255,255,255,0.12) !important;
  transition: all 0.22s cubic-bezier(.4,0,.2,1) !important;
  position: relative !important;
  overflow: hidden !important;
}}
.stButton > button::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.14), transparent);
  border-radius: inherit;
  opacity: 0;
  transition: opacity 0.2s;
}}
.stButton > button:hover {{
  transform: translateY(-2px) scale(1.01) !important;
  box-shadow: 0 10px 30px rgba(99,102,241,0.5), inset 0 1px 0 rgba(255,255,255,0.15) !important;
}}
.stButton > button:hover::after {{ opacity: 1; }}
.stButton > button:active {{ transform: translateY(0) scale(0.99) !important; }}
.stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
  box-shadow: 0 4px 18px rgba(244,63,94,0.38), inset 0 1px 0 rgba(255,255,255,0.1) !important;
}}
.stButton > button[kind="primary"]:hover {{
  box-shadow: 0 10px 30px rgba(244,63,94,0.52) !important;
}}
[data-testid="stDownloadButton"] > button {{
  background: linear-gradient(135deg, #10b981, #059669) !important;
  box-shadow: 0 4px 18px rgba(16,185,129,0.32) !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
  box-shadow: 0 10px 28px rgba(16,185,129,0.5) !important;
}}

/* ─────────────────────────────────────────
   TABS
───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: var(--glass) !important;
  border: 1px solid var(--glass-b) !important;
  border-radius: var(--radius-md) !important;
  padding: 5px !important;
  gap: 3px !important;
  backdrop-filter: blur(16px) !important;
  box-shadow: var(--shadow) !important;
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: var(--radius-xs) !important;
  font-weight: 500 !important;
  font-size: 0.84rem !important;
  color: var(--text-2) !important;
  padding: 0.48rem 1.1rem !important;
  transition: all 0.18s ease !important;
  letter-spacing: 0.01em !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
  background: var(--bg-card-h) !important;
  color: var(--text-1) !important;
}}
.stTabs [aria-selected="true"] {{
  background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
  color: #fff !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 16px rgba(99,102,241,0.42), inset 0 1px 0 rgba(255,255,255,0.12) !important;
}}

/* ─────────────────────────────────────────
   METRIC CARDS
───────────────────────────────────────── */
[data-testid="metric-container"] {{
  background: var(--glass) !important;
  border: 1px solid var(--glass-b) !important;
  border-radius: var(--radius-md) !important;
  padding: 1.35rem 1.6rem 1.2rem !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: var(--shadow) !important;
  transition: transform 0.25s ease, box-shadow 0.25s ease !important;
  position: relative; overflow: hidden;
}}
[data-testid="metric-container"]::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
}}
[data-testid="metric-container"]::after {{
  content: '';
  position: absolute; top: -50%; right: -30%;
  width: 120px; height: 120px;
  background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%);
  pointer-events: none;
}}
[data-testid="metric-container"]:hover {{
  transform: translateY(-4px) !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.3), 0 0 32px rgba(99,102,241,0.18) !important;
  border-color: rgba(99,102,241,0.35) !important;
}}
[data-testid="stMetricValue"] {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.05em !important;
  background: linear-gradient(135deg, var(--text-1) 40%, rgba(99,102,241,0.85));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
[data-testid="stMetricLabel"] {{
  font-size: 0.68rem !important; font-weight: 800 !important;
  color: var(--text-3) !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; font-weight: 600 !important; }}

/* ─────────────────────────────────────────
   HEADINGS
───────────────────────────────────────── */
h1 {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2rem !important; font-weight: 800 !important;
  letter-spacing: -0.04em !important; line-height: 1.15 !important;
  background: linear-gradient(135deg, var(--text-1) 50%, #818cf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
h2 {{
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.25rem !important; font-weight: 700 !important;
  color: var(--text-1) !important; letter-spacing: -0.025em !important;
}}
h3 {{
  font-size: 0.95rem !important; font-weight: 600 !important;
  color: var(--text-2) !important;
}}

/* ─────────────────────────────────────────
   DATAFRAME
───────────────────────────────────────── */
[data-testid="stDataFrame"] {{
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
  border: 1px solid var(--glass-b) !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(12px) !important;
}}
.dataframe thead th {{
  background: rgba(99,102,241,0.1) !important;
  font-size: 0.7rem !important; font-weight: 800 !important;
  color: #818cf8 !important;
  text-transform: uppercase !important; letter-spacing: 0.1em !important;
  padding: 13px 16px !important;
  border-bottom: 1px solid rgba(99,102,241,0.2) !important;
}}
.dataframe td {{
  font-size: 0.875rem !important; color: var(--text-1) !important;
  padding: 11px 16px !important;
  border-bottom: 1px solid var(--border) !important;
}}
.dataframe tr:last-child td {{ border-bottom: none !important; }}

/* ─────────────────────────────────────────
   ALERTS
───────────────────────────────────────── */
.stSuccess, .stWarning, .stInfo, .stError {{
  border-radius: var(--radius-sm) !important;
  backdrop-filter: blur(12px) !important;
  border-left-width: 3px !important;
  border-width: 1px !important;
  font-size: 0.875rem !important;
}}

/* ─────────────────────────────────────────
   FORM INPUTS
───────────────────────────────────────── */
.stSelectbox > div > div {{
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border-s) !important;
  background: var(--input-bg) !important;
  font-size: 0.875rem !important;
  color: var(--text-1) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  backdrop-filter: blur(8px) !important;
}}
.stSelectbox > div > div:focus-within {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}}
.stNumberInput > div > div > input,
.stTextInput > div > div > input {{
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border-s) !important;
  background: var(--input-bg) !important;
  color: var(--text-1) !important;
  font-size: 0.875rem !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stNumberInput > div > div > input:focus,
.stTextInput > div > div > input:focus {{
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
  outline: none !important;
}}

/* ─────────────────────────────────────────
   FILE UPLOADER
───────────────────────────────────────── */
[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed rgba(99,102,241,0.35) !important;
  border-radius: var(--radius-md) !important;
  background: rgba(99,102,241,0.04) !important;
  transition: all 0.22s ease !important;
  backdrop-filter: blur(8px) !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{
  border-color: rgba(99,102,241,0.7) !important;
  background: rgba(99,102,241,0.08) !important;
}}

/* ─────────────────────────────────────────
   EXPANDER
───────────────────────────────────────── */
[data-testid="stExpander"] {{
  border: 1px solid var(--glass-b) !important;
  border-radius: var(--radius-md) !important;
  background: var(--glass) !important;
  backdrop-filter: blur(14px) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  overflow: hidden !important;
}}
[data-testid="stExpander"]:hover {{
  border-color: rgba(99,102,241,0.28) !important;
  box-shadow: 0 4px 24px rgba(99,102,241,0.1) !important;
}}
[data-testid="stExpander"] summary {{
  font-size: 0.88rem !important; font-weight: 600 !important;
  color: var(--text-1) !important; padding: 0.9rem 1.1rem !important;
}}

/* ─────────────────────────────────────────
   SECTION LABEL
───────────────────────────────────────── */
.section-header {{
  font-size: 0.65rem; font-weight: 900;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.18em; text-transform: uppercase;
  margin-bottom: 1rem; margin-top: 0.2rem;
  display: flex; align-items: center; gap: 10px;
}}
.section-header::before {{
  content: '';
  display: inline-block; width: 20px; height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 99px; flex-shrink: 0;
}}
.section-header::after {{
  content: ''; flex: 1; height: 1px;
  background: linear-gradient(90deg, var(--border-s), transparent);
}}

/* ─────────────────────────────────────────
   PAGE HEADER BLOCK
───────────────────────────────────────── */
.ph-wrap {{
  background: var(--glass);
  border: 1px solid var(--glass-b);
  border-radius: var(--radius-lg);
  padding: 1.75rem 2.25rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
}}
.ph-wrap::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), rgba(139,92,246,0.4), transparent);
}}
.ph-wrap::after {{
  content: '';
  position: absolute; top: -60px; right: -40px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(99,102,241,0.12), transparent 70%);
  pointer-events: none;
}}
.ph-badge {{
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.28);
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em;
  color: #a5b4fc;
  margin-bottom: 10px;
}}

/* ─────────────────────────────────────────
   HR
───────────────────────────────────────── */
hr {{
  border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--border-s), transparent) !important;
  margin: 1.75rem 0 !important;
}}

.stCaption {{ color: var(--text-3) !important; font-size: 0.73rem !important; }}
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
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_File","File_Hash"])
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
def page_header(title, subtitle="", badge=""):
    badge_html = f'<div class="ph-badge">{badge}</div>' if badge else ""
    st.markdown(f"""
<div class="ph-wrap">
  {badge_html}
  <h1 style="margin:0;padding:0;">{title}</h1>
  {"" if not subtitle else f'<p style="color:var(--text-2);margin:8px 0 0;font-size:0.9rem;font-weight:500;">{subtitle}</p>'}
</div>
""", unsafe_allow_html=True)
    _c1, _c2 = st.columns([8,1])
    with _c2:
        icon  = "☀️" if _t == "dark" else "🌙"
        label = "Light" if _t == "dark" else "Dark"
        if st.button(f"{icon} {label}", key="theme_btn"):
            st.session_state["theme"] = "light" if _t == "dark" else "dark"
            st.rerun()

def section_label(text):
    st.markdown(f'<p class="section-header">{text}</p>', unsafe_allow_html=True)

def student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    pct = int(min(100, paid_amount / total * 100)) if total else 0

    if paid_amount >= total:
        accent = "#10b981"; glow = "rgba(16,185,129,0.2)"
        grad   = "linear-gradient(135deg,#10b981,#059669)"
        badge  = "✓  PAID IN FULL"; border_col = "rgba(16,185,129,0.3)"
        amt_html = f'<span style="color:#10b981;font-weight:800;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Cleared</span>'
    elif paid_amount > 0:
        accent = "#6366f1"; glow = "rgba(99,102,241,0.2)"
        grad   = "linear-gradient(135deg,#6366f1,#8b5cf6)"
        badge  = "◑  PARTIAL PAYMENT"; border_col = "rgba(99,102,241,0.3)"
        amt_html = f'<span style="color:#818cf8;font-weight:800;font-variant-numeric:tabular-nums;">Paid&nbsp;Rs&nbsp;{int(paid_amount):,}&nbsp;<span style="opacity:.4">·</span>&nbsp;Due&nbsp;Rs&nbsp;{int(remaining):,}</span>'
    else:
        accent = "#f43f5e"; glow = "rgba(244,63,94,0.18)"
        grad   = "linear-gradient(135deg,#f43f5e,#e11d48)"
        badge  = "✗  UNPAID"; border_col = "rgba(244,63,94,0.28)"
        amt_html = f'<span style="color:#fb7185;font-weight:800;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Outstanding</span>'

    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"

    st.markdown(f"""
<div style="
  background:var(--glass);
  border:1px solid {border_col};
  border-radius:18px;
  padding:20px 24px 18px;
  margin-bottom:12px;
  backdrop-filter:blur(20px);
  box-shadow:0 4px 28px {glow}, 0 1px 3px rgba(0,0,0,0.12);
  transition:transform 0.22s ease,box-shadow 0.22s ease;
  position:relative; overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:2px;background:{grad};"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
    <div style="display:flex;align-items:center;gap:16px;">
      <div style="
        width:48px;height:48px;border-radius:14px;
        background:{grad};
        display:flex;align-items:center;justify-content:center;
        font-size:15px;font-weight:900;color:#fff;flex-shrink:0;
        box-shadow:0 6px 18px {glow};">{initials}</div>
      <div>
        <div style="font-size:1.05rem;font-weight:700;color:var(--text-1);letter-spacing:-0.015em;">{name}</div>
        <div style="font-size:0.78rem;color:var(--text-3);margin-top:3px;">
          Room&nbsp;<strong style="color:{accent};font-weight:700;">{room}</strong>
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
      <span style="
        background:{grad};color:#fff;
        padding:5px 14px;border-radius:999px;
        font-size:0.7rem;font-weight:800;letter-spacing:0.07em;
        box-shadow:0 3px 10px {glow};">{badge}</span>
      {amt_html}
    </div>
  </div>
  <div style="margin-top:16px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
      <span style="font-size:0.7rem;color:var(--text-3);font-weight:600;">Payment Progress</span>
      <span style="font-size:0.7rem;font-weight:800;color:{accent};">{pct}%</span>
    </div>
    <div style="background:rgba(255,255,255,0.07);border-radius:999px;height:5px;overflow:hidden;margin-bottom:16px;">
      <div style="background:{grad};height:5px;width:{pct}%;border-radius:999px;
                  box-shadow:0 0 10px {glow};transition:width 0.6s cubic-bezier(.4,0,.2,1);"></div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;
                background:rgba(255,255,255,0.04);border-radius:12px;
                border:1px solid var(--border);overflow:hidden;">
      <div style="padding:10px 14px;border-right:1px solid var(--border);">
        <div style="font-size:0.62rem;font-weight:700;color:var(--text-3);letter-spacing:0.1em;text-transform:uppercase;">Food</div>
        <div style="font-size:0.92rem;font-weight:700;color:var(--text-1);margin-top:3px;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(food):,}</div>
      </div>
      <div style="padding:10px 14px;border-right:1px solid var(--border);">
        <div style="font-size:0.62rem;font-weight:700;color:var(--text-3);letter-spacing:0.1em;text-transform:uppercase;">Service</div>
        <div style="font-size:0.92rem;font-weight:700;color:var(--text-1);margin-top:3px;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(service):,}</div>
      </div>
      <div style="padding:10px 14px;border-right:1px solid var(--border);">
        <div style="font-size:0.62rem;font-weight:700;color:var(--text-3);letter-spacing:0.1em;text-transform:uppercase;">Previous</div>
        <div style="font-size:0.92rem;font-weight:700;color:var(--text-1);margin-top:3px;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(prev):,}</div>
      </div>
      <div style="padding:10px 14px;background:rgba(99,102,241,0.06);">
        <div style="font-size:0.62rem;font-weight:700;color:{accent};letter-spacing:0.1em;text-transform:uppercase;">Total Due</div>
        <div style="font-size:0.98rem;font-weight:900;color:{accent};margin-top:3px;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,}</div>
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
<div style="
  background:var(--glass);border:1px solid rgba(16,185,129,0.2);
  border-radius:14px;padding:14px 20px;margin-bottom:8px;
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:10px;
  backdrop-filter:blur(14px);
  box-shadow:0 2px 16px rgba(16,185,129,0.08);
  transition:all 0.2s ease;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="
      width:42px;height:42px;border-radius:12px;
      background:linear-gradient(135deg,#10b981,#059669);
      display:flex;align-items:center;justify-content:center;
      font-size:13px;font-weight:800;color:#fff;flex-shrink:0;
      box-shadow:0 4px 12px rgba(16,185,129,0.35);">{initials}</div>
    <div>
      <div style="font-size:0.92rem;font-weight:700;color:var(--text-1);">{name}</div>
      <div style="font-size:0.76rem;color:var(--text-3);margin-top:2px;">
        Room&nbsp;<strong style="color:#6366f1;">{room}</strong>&nbsp;&nbsp;·&nbsp;&nbsp;{date}
      </div>
    </div>
  </div>
  <div style="
    font-family:'Space Grotesk',sans-serif;
    font-size:1.15rem;font-weight:800;
    background:linear-gradient(135deg,#10b981,#34d399);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;font-variant-numeric:tabular-nums;">{amt_fmt}</div>
</div>
""", unsafe_allow_html=True)

def hall_summary_card(hall_name, total, collected, remaining, pct_int):
    if total == 0:
        accent = "#64748b"; glow = "rgba(100,116,139,0.1)"
        grad   = "linear-gradient(135deg,#64748b,#475569)"
    elif remaining == 0:
        accent = "#10b981"; glow = "rgba(16,185,129,0.15)"
        grad   = "linear-gradient(135deg,#10b981,#059669)"
    elif collected > 0:
        accent = "#6366f1"; glow = "rgba(99,102,241,0.15)"
        grad   = "linear-gradient(135deg,#6366f1,#8b5cf6)"
    else:
        accent = "#f43f5e"; glow = "rgba(244,63,94,0.15)"
        grad   = "linear-gradient(135deg,#f43f5e,#e11d48)"

    bar_w = min(100, pct_int)
    st.markdown(f"""
<div style="
  background:var(--glass);
  border:1px solid var(--glass-b);
  border-left:3px solid {accent};
  border-radius:18px;padding:20px 24px;margin-bottom:10px;
  backdrop-filter:blur(16px);
  box-shadow:0 4px 24px {glow};
  transition:all 0.25s ease;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;gap:12px;">
    <div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:1.02rem;font-weight:700;color:var(--text-1);">{hall_name}</div>
      <div style="font-size:0.75rem;color:var(--text-3);margin-top:3px;">
        Total Outstanding:&nbsp;<strong style="color:var(--text-2);font-variant-numeric:tabular-nums;">Rs&nbsp;{total:,}</strong>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="
        font-family:'Space Grotesk',sans-serif;
        font-size:1.7rem;font-weight:900;
        background:{grad};
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        background-clip:text;font-variant-numeric:tabular-nums;
        line-height:1;">{pct_int}%</div>
      <div style="font-size:0.65rem;color:var(--text-3);font-weight:800;letter-spacing:0.1em;margin-top:2px;">COLLECTED</div>
    </div>
  </div>
  <div style="background:rgba(255,255,255,0.07);border-radius:999px;height:6px;overflow:hidden;margin-bottom:16px;">
    <div style="background:{grad};height:6px;width:{bar_w}%;border-radius:999px;
                box-shadow:0 0 12px {glow};transition:width 0.5s cubic-bezier(.4,0,.2,1);"></div>
  </div>
  <div style="display:flex;gap:24px;flex-wrap:wrap;">
    <span style="font-size:0.79rem;color:var(--text-3);">Collected&nbsp;
      <strong style="color:#10b981;font-variant-numeric:tabular-nums;">Rs&nbsp;{collected:,}</strong></span>
    <span style="font-size:0.79rem;color:var(--text-3);">Remaining&nbsp;
      <strong style="color:#f43f5e;font-variant-numeric:tabular-nums;">Rs&nbsp;{remaining:,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div class="sb-logo">
  <div class="icon-ring">🏛️</div>
  <h2>Mess Dues System</h2>
  <p>University Hostel Management</p>
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
  <div class="name">Abdul Hadi</div>
  <div class="sub">2025 (S)&nbsp;·&nbsp;CYS 90</div>
  <div class="tag">Designed &amp; Developed</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# STUDENT
# ══════════════════════════════════════════════════════════════════
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

        with st.expander(f"Submit Receipt — Room {room}  ·  {name}"):
            uploaded_files = st.file_uploader("Upload receipt image(s)", accept_multiple_files=True, key=f"files_{room}_{idx}")
            amount_paid_input = st.number_input("Amount Submitted (Rs)", min_value=1, max_value=int(total), value=int(total), step=1, key=f"amt_{room}_{idx}")

            if uploaded_files:
                if st.button(f"Submit Receipt — Room {room}", key=f"submit_{room}_{idx}"):
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
                                errors.append(f"Duplicate receipt: {f.name}")
                                continue
                        save_path = f"receipts/{uuid.uuid4()}_{f.name}"
                        with open(save_path,"wb") as fp: fp.write(file_bytes)
                        new_row = pd.DataFrame([{
                            "Month":selected_month,"RoomNo":room,"Name":name,
                            "Amount_Paid":amount_paid_input,"Submission_Date":now_str,
                            "Receipt_File":save_path,"File_Hash":file_hash
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
            for i,row in filtered_pays.iterrows():
                receipt_card(row["RoomNo"],row["Name"],row.get("Amount_Paid",""),row.get("Submission_Date",""),i)
                path = str(row.get("Receipt_File",""))
                if path and os.path.exists(path):
                    if path.lower().endswith((".png",".jpg",".jpeg")): st.image(path, width=220)
                    with open(path,"rb") as fp:
                        st.download_button("Download Receipt", fp, file_name=os.path.basename(path), key=f"dl_{i}")
                else:
                    st.caption("Receipt image not available on server (cloud restart clears uploaded files)")

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
<div style="
  margin-top:3.5rem;
  padding:1.6rem 2.25rem;
  background:var(--glass);
  border:1px solid var(--glass-b);
  border-radius:var(--radius-lg);
  backdrop-filter:blur(20px);
  box-shadow:var(--shadow);
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:12px;
  position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:1px;
              background:linear-gradient(90deg,transparent,rgba(99,102,241,0.4),rgba(139,92,246,0.35),transparent);"></div>
  <div>
    <div style="
      font-family:'Space Grotesk',sans-serif;
      font-size:0.95rem;font-weight:800;
      background:linear-gradient(135deg,#a5b4fc,#c4b5fd);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
      background-clip:text;letter-spacing:-0.01em;">
      University Mess Dues System
    </div>
    <div style="font-size:0.76rem;color:var(--text-3);margin-top:3px;">
      Powered by Streamlit &amp; Google Sheets
    </div>
  </div>
  <div style="text-align:right;">
    <div style="
      font-family:'Space Grotesk',sans-serif;
      font-size:0.88rem;font-weight:800;
      background:linear-gradient(135deg,#6366f1,#a5b4fc);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
      background-clip:text;">
      Designed &amp; Developed by Abdul Hadi
    </div>
    <div style="font-size:0.72rem;color:var(--text-3);margin-top:4px;letter-spacing:0.03em;">
      2025 (S)&nbsp;&nbsp;·&nbsp;&nbsp;CYS 90&nbsp;&nbsp;·&nbsp;&nbsp;University of Engineering &amp; Technology
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
