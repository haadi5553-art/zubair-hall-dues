import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os
import numpy as np

AUTO_REFRESH = False

st.set_page_config(
    page_title="HOLO-MESS v2.1 | UET",
    layout="wide",
    page_icon="⬡",
    initial_sidebar_state="expanded"
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
_t = st.session_state["theme"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

:root {{
  --accent:   #1d4ed8;
  --accent2:  #0ea5e9;
  --green:    #059669;
  --red:      #dc2626;
  --orange:   #d97706;

  {"" if _t=="dark" else "/*"}
  --bg0:      #0f172a;
  --bg1:      #1e293b;
  --bg2:      #243347;
  --glass:    rgba(255,255,255,0.04);
  --glass2:   rgba(255,255,255,0.02);
  --border:   rgba(148,163,184,0.15);
  --border2:  rgba(148,163,184,0.10);
  --text1:    #f1f5f9;
  --text2:    #94a3b8;
  --text3:    #64748b;
  --input-bg: rgba(255,255,255,0.06);
  {"" if _t=="dark" else "*/"}

  {"/*" if _t=="dark" else ""}
  --bg0:      #f8fafc;
  --bg1:      #f1f5f9;
  --bg2:      #e2e8f0;
  --glass:    rgba(255,255,255,0.8);
  --glass2:   rgba(0,0,0,0.04);
  --border:   rgba(0,0,0,0.1);
  --border2:  rgba(0,0,0,0.07);
  --text1:    #0f172a;
  --text2:    #334155;
  --text3:    #64748b;
  --input-bg: rgba(255,255,255,0.9);
  {"*/" if _t=="dark" else ""}
}}

*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
  font-family: 'Inter', sans-serif !important;
  -webkit-font-smoothing: antialiased;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

.stApp {{
  background: var(--bg0) !important;
  min-height: 100vh;
}}

.block-container {{
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1500px !important;
}}

[data-testid="stSidebar"] {{
  background: var(--bg1) !important;
  border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: var(--text1) !important; }}
[data-testid="stSidebar"] label {{
  color: var(--text2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
}}
[data-testid="stSidebar"] .stSelectbox > div > div {{
  background: var(--input-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text1) !important;
  transition: all 0.2s;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input {{
  background: var(--input-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text1) !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
  border-color: var(--accent) !important;
}}

.sidebar-logo {{
  padding: 1.5rem 1.25rem 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem;
}}
.sidebar-logo h2 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 800 !important;
  color: #60a5fa !important;
  letter-spacing: 0.04em;
  text-shadow: 0 0 18px rgba(96,165,250,0.7), 0 0 36px rgba(96,165,250,0.35);
  margin: 0 !important;
}}
.sidebar-logo p {{
  font-size: 0.6rem !important;
  color: var(--text3) !important;
  margin-top: 4px !important;
  font-family: 'Inter', sans-serif !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.stButton > button {{
  background: var(--glass) !important;
  color: var(--text1) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  padding: 0.5rem 1.2rem !important;
  transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
  border-color: var(--accent) !important;
  color: var(--accent2) !important;
  transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"] {{
  background: rgba(220,38,38,0.1) !important;
  border-color: rgba(220,38,38,0.4) !important;
  color: #f87171 !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: rgba(220,38,38,0.18) !important;
}}

[data-testid="stSidebar"] .stButton > button {{
  width: 100% !important;
  text-align: left !important;
  margin-bottom: 6px !important;
  padding: 0.6rem 1rem !important;
  font-size: 0.82rem !important;
}}

.role-btn-active > button {{
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #ffffff !important;
}}

[data-testid="stDownloadButton"] > button {{
  background: rgba(5,150,105,0.1) !important;
  border-color: rgba(5,150,105,0.4) !important;
  color: #34d399 !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
  background: rgba(5,150,105,0.18) !important;
}}

.stTabs [data-baseweb="tab-list"] {{
  background: var(--bg1) !important;
  border-radius: 10px !important;
  padding: 5px !important;
  border: 1px solid var(--border) !important;
  gap: 3px !important;
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: 7px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  color: var(--text2) !important;
  padding: 0.45rem 1rem !important;
  transition: all 0.2s !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
  color: var(--text1) !important;
  background: var(--glass2) !important;
}}
.stTabs [aria-selected="true"] {{
  background: var(--accent) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
}}

[data-testid="metric-container"] {{
  background: var(--bg1) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 1.25rem 1.5rem !important;
  transition: all 0.2s ease !important;
}}
[data-testid="metric-container"]:hover {{
  transform: translateY(-2px) !important;
  border-color: var(--accent) !important;
}}
[data-testid="stMetricValue"] {{
  font-family: 'Inter', sans-serif !important;
  font-size: 1.6rem !important;
  font-weight: 800 !important;
  color: var(--text1) !important;
  -webkit-text-fill-color: initial !important;
}}
[data-testid="stMetricLabel"] {{
  font-family: 'Inter', sans-serif !important;
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  color: var(--text3) !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
}}
[data-testid="stMetricDelta"] {{
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  color: #34d399 !important;
}}

h1 {{
  font-family: 'Orbitron', sans-serif !important;
  font-size: 1.6rem !important;
  font-weight: 900 !important;
  color: var(--text1) !important;
  letter-spacing: 0.03em !important;
  -webkit-text-fill-color: initial !important;
}}
h2 {{
  font-family: 'Inter', sans-serif !important;
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  color: var(--text1) !important;
}}
h3 {{
  font-family: 'Inter', sans-serif !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  color: var(--text2) !important;
}}

[data-testid="stDataFrame"] {{
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
}}
.dataframe thead th {{
  background: var(--bg2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  color: var(--text2) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  padding: 12px 14px !important;
  border-bottom: 1px solid var(--border) !important;
}}
.dataframe td {{
  font-size: 0.84rem !important;
  color: var(--text1) !important;
  padding: 10px 14px !important;
  border-bottom: 1px solid var(--border2) !important;
}}
.dataframe tr:hover td {{
  background: var(--glass) !important;
}}

.stSuccess {{ border-radius: 10px !important; }}
.stWarning {{ border-radius: 10px !important; }}
.stInfo    {{ border-radius: 10px !important; }}
.stError   {{ border-radius: 10px !important; }}

.stSelectbox > div > div {{
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
  background: var(--input-bg) !important;
  color: var(--text1) !important;
  transition: all 0.2s !important;
}}
.stSelectbox > div > div:focus-within {{
  border-color: var(--accent) !important;
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
  border-color: var(--accent) !important;
}}
label {{ color: var(--text2) !important; }}

[data-testid="stFileUploadDropzone"] {{
  border: 2px dashed var(--border) !important;
  border-radius: 12px !important;
  background: var(--glass) !important;
  transition: all 0.2s !important;
}}
[data-testid="stFileUploadDropzone"]:hover {{
  border-color: var(--accent) !important;
}}

[data-testid="stExpander"] {{
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  background: var(--glass) !important;
  transition: all 0.2s !important;
}}
[data-testid="stExpander"]:hover {{
  border-color: var(--accent) !important;
}}
[data-testid="stExpander"] summary {{
  color: var(--text1) !important;
  font-weight: 600 !important;
}}

.section-header {{
  font-family: 'Inter', sans-serif !important;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 0.85rem;
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 10px;
}}
.section-header::before {{
  content: '';
  display: inline-block;
  width: 16px; height: 2px;
  background: var(--accent);
  border-radius: 2px;
}}
.section-header::after {{
  content: '';
  flex: 1; height: 1px;
  background: var(--border);
}}

.page-header-wrap {{
  background: var(--bg1);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.75rem 2rem;
  margin-bottom: 2rem;
  border-left: 4px solid var(--accent);
}}

::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: var(--bg2); }}
::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: 3px;
}}

hr {{
  border: none !important;
  height: 1px !important;
  background: var(--border) !important;
  margin: 1.5rem 0 !important;
}}

.stCaption {{ color: var(--text3) !important; font-size: 0.72rem !important; }}

.data-card {{
  background: var(--bg1);
  border: 1px solid var(--border);
  border-radius: 14px;
  transition: border-color 0.2s;
}}
.data-card:hover {{ border-color: var(--accent); }}

.prog-bar {{
  background: var(--accent);
  height: 4px;
  border-radius: 999px;
}}

.badge-paid    {{ border-color: rgba(5,150,105,0.5) !important; }}
.badge-partial {{ border-color: rgba(14,165,233,0.5) !important; }}
.badge-unpaid  {{ border-color: rgba(220,38,38,0.5) !important; }}

.role-section-label {{
  font-family: 'Inter', sans-serif;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--text3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 1rem 0 0.5rem 0;
  padding: 0 0.25rem;
}}
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
  {"" if not subtitle else f'<p style="color:var(--text2);margin:8px 0 0;font-size:0.82rem;font-family:Inter,sans-serif;letter-spacing:0.02em;">{subtitle}</p>'}
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
        "paid":    ("rgba(5,150,105,0.12)", "#059669", "badge-paid"),
        "partial": ("rgba(14,165,233,0.12)", "#0ea5e9", "badge-partial"),
        "unpaid":  ("rgba(220,38,38,0.12)", "#dc2626", "badge-unpaid"),
    }
    bg, col, anim = colors.get(cls, ("rgba(100,116,139,0.1)", "#64748b", ""))
    return f'<span class="{anim}" style="background:{bg};color:{col};border:1px solid {col}50;padding:4px 12px;border-radius:999px;font-family:Inter,sans-serif;font-size:0.68rem;font-weight:700;letter-spacing:0.06em;">{label}</span>'

def student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    if paid_amount >= total:
        accent, left_color, badge_cls = "#059669", "#059669", "paid"
        badge_txt   = "✓ Paid in Full"
        amount_html = f'<span style="color:#059669;font-weight:700;font-size:0.9rem;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Cleared</span>'
    elif paid_amount > 0:
        accent, left_color, badge_cls = "#0ea5e9", "#0ea5e9", "partial"
        badge_txt   = "◑ Partial"
        amount_html = f'<span style="color:#0ea5e9;font-weight:700;font-size:0.9rem;font-variant-numeric:tabular-nums;">Paid: Rs&nbsp;{int(paid_amount):,} · Due: Rs&nbsp;{int(remaining):,}</span>'
    else:
        accent, left_color, badge_cls = "#dc2626", "#dc2626", "unpaid"
        badge_txt   = "✗ Unpaid"
        amount_html = f'<span style="color:#dc2626;font-weight:700;font-size:0.9rem;font-variant-numeric:tabular-nums;">Rs&nbsp;{int(total):,} — Outstanding</span>'

    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    pct   = int(paid_amount / total * 100) if total else 0
    bar_w = min(100, pct)
    badge_html = status_badge(badge_txt, badge_cls)

    st.markdown(f"""
<div style="
  background: var(--bg1);
  border: 1px solid var(--border);
  border-left: 4px solid {left_color};
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 10px;
  transition: border-color 0.2s;
">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;">
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="width:44px;height:44px;border-radius:10px;
        background:{accent};opacity:0.9;
        display:flex;align-items:center;justify-content:center;
        font-family:Inter,sans-serif;font-size:14px;font-weight:800;color:#fff;flex-shrink:0;">{initials}</div>
      <div>
        <div style="font-size:0.95rem;font-weight:700;color:var(--text1);">{name}</div>
        <div style="font-size:0.72rem;color:var(--text3);margin-top:2px;">
          Room <strong style="color:var(--text2);">{room}</strong>
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
      {badge_html}
      {amount_html}
    </div>
  </div>

  <div style="margin-top:12px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
      <span style="font-size:0.65rem;color:var(--text3);letter-spacing:0.06em;text-transform:uppercase;">Payment Progress</span>
      <span style="font-size:0.65rem;color:{accent};font-weight:700;">{pct}%</span>
    </div>
    <div style="background:var(--border);border-radius:999px;height:4px;overflow:hidden;">
      <div style="background:{accent};height:4px;width:{bar_w}%;border-radius:999px;transition:width 0.4s ease;"></div>
    </div>
  </div>

  <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);
    display:flex;gap:18px;flex-wrap:wrap;">
    <span style="font-size:0.74rem;color:var(--text3);">Food&nbsp;<strong style="color:var(--text1);font-variant-numeric:tabular-nums;">Rs&nbsp;{int(food):,}</strong></span>
    <span style="font-size:0.74rem;color:var(--text3);">Service&nbsp;<strong style="color:var(--text1);font-variant-numeric:tabular-nums;">Rs&nbsp;{int(service):,}</strong></span>
    <span style="font-size:0.74rem;color:var(--text3);">Arrears&nbsp;<strong style="color:var(--text1);font-variant-numeric:tabular-nums;">Rs&nbsp;{int(prev):,}</strong></span>
    <span style="font-size:0.74rem;color:var(--text3);">Total&nbsp;<strong style="color:{accent};font-size:0.85rem;font-variant-numeric:tabular-nums;font-weight:700;">Rs&nbsp;{int(total):,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

def receipt_card(room, name, amount, date, idx):
    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    amt_fmt  = f"Rs\u00a0{int(float(amount)):,}" if amount else "Rs\u00a00"
    st.markdown(f"""
<div style="
  background:var(--bg1);
  border:1px solid var(--border);
  border-left:4px solid #059669;
  border-radius:12px;padding:14px 18px;margin-bottom:8px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;
">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:40px;height:40px;border-radius:10px;
      background:#059669;
      display:flex;align-items:center;justify-content:center;
      font-family:Inter,sans-serif;font-size:13px;font-weight:800;color:#fff;">{initials}</div>
    <div>
      <div style="font-size:0.9rem;font-weight:700;color:var(--text1);">{name}</div>
      <div style="font-size:0.7rem;color:var(--text3);margin-top:1px;">
        Room <strong style="color:var(--text2);">{room}</strong>
        &nbsp;·&nbsp;<span>{date}</span>
      </div>
    </div>
  </div>
  <div style="font-family:Inter,sans-serif;font-size:1.05rem;font-weight:800;
    color:#059669;font-variant-numeric:tabular-nums;">{amt_fmt}</div>
</div>
""", unsafe_allow_html=True)

def hall_summary_card(hall_name, total, collected, remaining, pct_int):
    if total == 0:
        accent, left_color = "#64748b", "#64748b"
    elif remaining == 0:
        accent, left_color = "#059669", "#059669"
    elif collected > 0:
        accent, left_color = "#0ea5e9", "#0ea5e9"
    else:
        accent, left_color = "#dc2626", "#dc2626"

    bar_width = min(100, pct_int)
    st.markdown(f"""
<div style="
  background:var(--bg1);
  border:1px solid var(--border);
  border-left:4px solid {left_color};
  border-radius:12px;padding:16px 20px;margin-bottom:10px;
  transition: border-color 0.2s;
">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <div>
      <div style="font-family:Inter,sans-serif;font-size:0.9rem;font-weight:700;color:var(--text1);">{hall_name}</div>
      <div style="font-size:0.72rem;color:var(--text3);margin-top:2px;">
        Total Dues: <strong style="color:var(--text2);font-variant-numeric:tabular-nums;">Rs&nbsp;{total:,}</strong>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.6rem;font-weight:800;color:{accent};font-variant-numeric:tabular-nums;">{pct_int}%</div>
      <div style="font-size:0.6rem;color:var(--text3);font-weight:600;letter-spacing:0.1em;text-transform:uppercase;">Collected</div>
    </div>
  </div>
  <div style="background:var(--border);border-radius:999px;height:4px;overflow:hidden;margin-bottom:12px;">
    <div style="background:{accent};height:4px;width:{bar_width}%;border-radius:999px;transition:width 0.4s ease;"></div>
  </div>
  <div style="display:flex;gap:20px;flex-wrap:wrap;">
    <span style="font-size:0.76rem;color:var(--text3);">Collected&nbsp;
      <strong style="color:#059669;font-variant-numeric:tabular-nums;">Rs&nbsp;{collected:,}</strong></span>
    <span style="font-size:0.76rem;color:var(--text3);">Remaining&nbsp;
      <strong style="color:#dc2626;font-variant-numeric:tabular-nums;">Rs&nbsp;{remaining:,}</strong></span>
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

# ── Role Selection Buttons ─────────────────────────────────────
# ── Role Selection ─────────────────────────────────────
st.sidebar.markdown('<p class="role-section-label">ACCESS LEVEL</p>', unsafe_allow_html=True)

if "selected_role" not in st.session_state:
    st.session_state["selected_role"] = "Student"

role_options = [
    ("Student", "◎ Student"),
    ("Hall Admin", "⬡ Hall Admin"),
    ("Senior Warden", "★ Senior Warden"),
]

for role_key, role_label in role_options:
    is_active = st.session_state["selected_role"] == role_key
    
    if st.sidebar.button(
        role_label, 
        key=f"role_btn_{role_key}", 
        use_container_width=True,
        type="primary" if is_active else "secondary"
    ):
        st.session_state["selected_role"] = role_key
        st.rerun()

# Show current active role
st.sidebar.success(f"✅ Active: **{st.session_state['selected_role']}**")

role = st.session_state["selected_role"]
st.sidebar.markdown("""
<div style="padding:14px 12px;margin-top:10px;
  border-top:1px solid var(--border);text-align:center;">
  <div style="font-family:Orbitron,sans-serif;font-size:0.78rem;font-weight:800;
    color:#60a5fa;letter-spacing:0.04em;
    text-shadow:0 0 14px rgba(96,165,250,0.7), 0 0 28px rgba(96,165,250,0.35);">Abdul Hadi</div>
  <div style="font-family:Inter,sans-serif;font-size:0.58rem;color:#64748b;
    margin-top:3px;font-weight:500;letter-spacing:0.06em;">2025 (S) · CYS 90</div>
  <div style="font-size:0.58rem;color:#64748b;margin-top:3px;">
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

            ai_extract_key = f"ai_amt_{room}_{idx}"
            ai_done_key    = f"ai_done_{room}_{idx}"

            if uploaded_files:
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
                                    import re as _re
                                    nums = _re.findall(r'\d[\d,]*', raw)
                                    if nums:
                                        val = int(nums[0].replace(",",""))
                                        total_extracted += val

                            if total_extracted > 0:
                                final_amt = min(total_extracted, int(total))
                                st.session_state[ai_extract_key] = final_amt
                                st.session_state[ai_done_key] = True
                            else:
                                st.session_state[ai_extract_key] = int(total)
                                st.session_state[ai_done_key] = True

                        except Exception as _e:
                            st.session_state[ai_extract_key] = int(total)
                            st.session_state[ai_done_key] = True

                extracted_amount = st.session_state.get(ai_extract_key, int(total))

                st.markdown(f"""
<div style="background:rgba(5,150,105,0.08);border:1px solid rgba(5,150,105,0.3);
  border-radius:10px;padding:12px 16px;margin:8px 0;display:flex;
  justify-content:space-between;align-items:center;">
  <div>
    <div style="font-family:Inter,sans-serif;font-size:0.65rem;color:#64748b;
      letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">AI Detected Amount</div>
    <div style="font-family:Inter,sans-serif;font-size:1.25rem;font-weight:800;
      color:#059669;font-variant-numeric:tabular-nums;">
      Rs&nbsp;{extracted_amount:,}
    </div>
  </div>
  <div style="font-size:1.4rem;">🤖</div>
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

            try:
                import plotly.graph_objects as go
                import plotly.express as px

                ch1, ch2, ch3, ch4 = st.columns(4)

                with ch1:
                    section_label("Payment Status")
                    fig_s = go.Figure(data=[go.Pie(
                        labels=["Paid","Partial","Unpaid"],
                        values=[paid_cnt, partial_cnt, unpaid_cnt],
                        hole=0.6,
                        marker=dict(colors=["#10b981","#3b82f6","#ef4444"], line=dict(color="rgba(0,0,0,0)", width=0)),
                        textinfo="percent",
                        textfont=dict(size=11, family="Inter", color="#fff"),
                        hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
                    )])
                    fig_s.update_layout(
                        showlegend=False, height=200,
                        margin=dict(t=5,b=5,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(text=f"<b>{len(df_d)}</b>", x=0.5, y=0.5,
                            font_size=18, font_color="#3b82f6", font_family="Inter", showarrow=False)]
                    )
                    st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

                with ch2:
                    section_label("Collection vs Total")
                    fig_cv = go.Figure()
                    fig_cv.add_trace(go.Bar(name="Total", x=["Dues"], y=[int(total_dues)],
                        marker_color="rgba(0,245,255,0.25)", marker_line_width=0,
                        hovertemplate="Total: Rs %{y:,.0f}<extra></extra>"))
                    fig_cv.add_trace(go.Bar(name="Collected", x=["Dues"], y=[int(collected)],
                        marker_color="#10b981", marker_line_width=0,
                        hovertemplate="Collected: Rs %{y:,.0f}<extra></extra>"))
                    fig_cv.update_layout(
                        barmode="overlay", height=200,
                        margin=dict(t=5,b=5,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        xaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=9)),
                        yaxis=dict(showgrid=True, gridcolor="rgba(0,245,255,0.05)",
                                   tickfont=dict(color="#64748b", size=8), tickformat=",")
                    )
                    st.plotly_chart(fig_cv, use_container_width=True, config={"displayModeBar": False})

                with ch3:
                    section_label("Top Unpaid")
                    top_unpaid = df_d[df_d["Status"] != "Paid"].nlargest(5, "Remaining (Rs)")
                    if not top_unpaid.empty:
                        fig_u = go.Figure(go.Bar(
                            x=top_unpaid["Remaining (Rs)"].tolist(),
                            y=top_unpaid["Name"].tolist(),
                            orientation="h",
                            marker=dict(color=top_unpaid["Remaining (Rs)"].tolist(),
                                colorscale=[[0,"#f59e0b"],[1,"#ef4444"]], showscale=False, line=dict(width=0)),
                            text=[f"Rs {v:,}" for v in top_unpaid["Remaining (Rs)"].tolist()],
                            textposition="outside",
                            textfont=dict(size=9, color="#94a3b8"),
                            hovertemplate="<b>%{y}</b><br>Rs %{x:,.0f}<extra></extra>"
                        ))
                        fig_u.update_layout(
                            height=200, margin=dict(t=5,b=5,l=5,r=60),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(showgrid=False, visible=False),
                            yaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=9))
                        )
                        st.plotly_chart(fig_u, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.success("All students paid!")

                with ch4:
                    section_label("Dues Breakdown")
                    fd_tot = int(df_d["Food_Dues"].sum())
                    sv_tot = int(df_d["Service_Charges"].sum())
                    pr_tot = int(df_d["Previous"].sum())
                    fig_br = go.Figure(data=[go.Pie(
                        labels=["Food","Service","Arrears"],
                        values=[fd_tot, sv_tot, pr_tot],
                        hole=0.55,
                        marker=dict(colors=["#8b5cf6","#3b82f6","#f59e0b"], line=dict(color="rgba(0,0,0,0)", width=0)),
                        textinfo="percent",
                        textfont=dict(size=10, family="Inter", color="#fff"),
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
                    return ["background-color:rgba(16,185,129,0.08);color:#10b981;font-weight:700"] * len(row)
                elif s == "Partial":
                    return ["background-color:rgba(59,130,246,0.08);color:#3b82f6;font-weight:600"] * len(row)
                return ["background-color:rgba(255,45,85,0.07);color:#ff6b6b;font-weight:500"] * len(row)

            display_cols = ["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)","Status"]
            st.dataframe(df_d[display_cols].style.apply(row_color, axis=1),
                         use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            section_label("Collection Chart")
            chart_data = df_d.set_index("Name")[["Total","Paid (Rs)"]].head(30)
            st.bar_chart(chart_data)

            st.markdown("---")
            csv = df_d[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button(f"⬇ Download {sel_month} Report (CSV)", csv,
                               file_name=f"{hall}_{sel_month}.csv", mime="text/csv")

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
                marker=dict(colors=["#10b981","#ef4444"], line=dict(color="rgba(0,0,0,0)", width=0)),
                textinfo="percent",
                textfont=dict(size=12, family="Inter", color="#fff"),
                hovertemplate="<b>%{label}</b><br>Rs %{value:,.0f}<extra></extra>"
            )])
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                            font=dict(size=10, family="Inter", color="#94a3b8")),
                margin=dict(t=10, b=10, l=10, r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(text=f"<b>{overall_pct}%</b>", x=0.5, y=0.5,
                    font_size=20, font_family="Inter", font_color="#3b82f6", showarrow=False)]
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
            fig_bar.add_trace(go.Bar(name="Collected", x=hall_names, y=collected_vals,
                marker_color="#10b981", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Collected: Rs %{y:,.0f}<extra></extra>"))
            fig_bar.add_trace(go.Bar(name="Remaining", x=hall_names, y=remaining_vals,
                marker_color="#ef4444", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Remaining: Rs %{y:,.0f}<extra></extra>"))
            fig_bar.update_layout(
                barmode="stack", showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=9, family="Inter", color="#94a3b8")),
                margin=dict(t=30, b=10, l=10, r=10), height=260,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=9, family="Inter", color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,245,255,0.04)",
                           tickformat=",", tickfont=dict(size=8, family="Inter", color="#64748b")),
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
                marker=dict(colors=["#3b82f6","#f59e0b"], line=dict(color="rgba(0,0,0,0)", width=0)),
                textinfo="percent+value",
                textfont=dict(size=11, family="Inter", color="#fff"),
                hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
            )])
            fig_d.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
                            font=dict(size=10, family="Inter", color="#94a3b8")),
                margin=dict(t=10, b=10, l=10, r=10), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(text=f"<b>{total_students_all}</b>", x=0.5, y=0.5,
                    font_size=16, font_family="Inter", font_color="#3b82f6", showarrow=False)]
            )
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

        with col_d2:
            section_label("Hall Recovery Rates")
            hall_labels = [s["Hall"].replace(" Hall","") for s in summary if s["Total"] > 0]
            hall_pcts   = [s["Pct"] for s in summary if s["Total"] > 0]
            fig_h = go.Figure(go.Bar(
                x=hall_pcts, y=hall_labels, orientation="h",
                marker=dict(color=hall_pcts, colorscale=[[0,"#ef4444"],[0.5,"#f59e0b"],[1,"#10b981"]],
                    showscale=False, line=dict(width=0)),
                text=[f"{p}%" for p in hall_pcts],
                textposition="outside",
                textfont=dict(size=10, family="Inter", color="#94a3b8"),
                hovertemplate="<b>%{y}</b><br>Recovery: %{x}%<extra></extra>"
            ))
            fig_h.update_layout(
                margin=dict(t=10, b=10, l=10, r=50), height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0,120], showgrid=False, visible=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=9, family="Inter", color="#94a3b8")),
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
<div style="margin-top:3rem;padding:1.25rem 2rem;
  background:var(--bg1);
  border:1px solid var(--border);
  border-radius:12px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
  <div>
    <span style="font-family:Orbitron,sans-serif;font-size:0.8rem;font-weight:800;
      color:#60a5fa;
      text-shadow:0 0 16px rgba(96,165,250,0.7), 0 0 32px rgba(96,165,250,0.3);">HOLO-MESS v2.1</span>
    <span style="color:var(--border);margin:0 8px;">|</span>
    <span style="font-size:0.74rem;color:var(--text3);">University Mess Dues System · Powered by Streamlit &amp; Google Sheets</span>
  </div>
  <div style="text-align:right;">
    <span style="font-family:Orbitron,sans-serif;font-size:0.76rem;font-weight:800;
      color:#60a5fa;
      text-shadow:0 0 14px rgba(96,165,250,0.7), 0 0 28px rgba(96,165,250,0.3);">Designed &amp; Developed by Abdul Hadi</span>
    <br>
    <span style="font-family:Inter,sans-serif;font-size:0.6rem;color:var(--text3);letter-spacing:0.06em;">
      2025 (S) &nbsp;·&nbsp; CYS 90 &nbsp;·&nbsp; UET
    </span>
  </div>
</div>
""", unsafe_allow_html=True)
