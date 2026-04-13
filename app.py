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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Page background ── */
.stApp { background: #f1f5f9; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] label { color: #94a3b8 !important; font-size: 0.75rem !important; font-weight: 600 !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }

/* ── Sidebar logo area ── */
.sidebar-logo {
    padding: 1.5rem 1rem 1rem;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1rem;
}
.sidebar-logo h2 { font-size: 1rem; font-weight: 700; color: #f1f5f9 !important; }
.sidebar-logo p { font-size: 0.7rem; color: #64748b !important; margin-top: 2px; }

/* ── Main buttons ── */
.stButton > button {
    background: #3b82f6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.4rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover { background: #2563eb !important; transform: translateY(-1px); }
.stButton > button[kind="primary"] { background: #ef4444 !important; }
.stButton > button[kind="primary"]:hover { background: #dc2626 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #fff;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #e2e8f0;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #64748b !important;
    padding: 0.45rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: #3b82f6 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Metric cards ── */
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    letter-spacing: -0.04em !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
}

/* ── Headings ── */
h1 { font-size: 1.75rem !important; font-weight: 800 !important; color: #0f172a !important; letter-spacing: -0.03em !important; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; color: #0f172a !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; color: #334155 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #e2e8f0 !important; }
.dataframe thead th { background: #f8fafc !important; font-size: 0.78rem !important; font-weight: 700 !important; color: #374151 !important; text-transform: uppercase !important; letter-spacing: 0.04em !important; }
.dataframe td { font-size: 0.88rem !important; color: #1e293b !important; padding: 10px 14px !important; }

/* ── Alerts ── */
.stSuccess { border-radius: 8px !important; }
.stWarning { border-radius: 8px !important; }
.stInfo { border-radius: 8px !important; }

/* ── Divider ── */
hr { border-color: #e2e8f0 !important; }

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #cbd5e1 !important;
    border-radius: 10px !important;
    background: #f8fafc !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    background: #fff !important;
}

/* ── Select box ── */
.stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.88rem !important;
}

/* ── Number input ── */
.stNumberInput > div > div > input {
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
}

/* ── Caption ── */
.stCaption { color: #94a3b8 !important; font-size: 0.75rem !important; }

/* ── Section header ── */
.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    margin-top: 0.25rem;
}
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

STATUS_COLORS = {
    "paid":    {"bg": "#f0fdf4", "border": "#16a34a", "badge_bg": "#15803d", "text": "#14532d"},
    "partial": {"bg": "#eff6ff", "border": "#2563eb", "badge_bg": "#1d4ed8", "text": "#1e3a8a"},
    "unpaid":  {"bg": "#fef2f2", "border": "#dc2626", "badge_bg": "#b91c1c", "text": "#7f1d1d"},
}


# ══════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ══════════════════════════════════════════════════════════════════
def page_header(title, subtitle=""):
    st.markdown(f"""
<div style="margin-bottom:2rem;">
  <h1 style="margin:0;padding:0;">{title}</h1>
  {"" if not subtitle else f'<p style="color:#64748b;margin:4px 0 0;font-size:0.9rem;">{subtitle}</p>'}
</div>
""", unsafe_allow_html=True)

def section_label(text):
    st.markdown(f'<p class="section-header">{text}</p>', unsafe_allow_html=True)

def status_badge(label, color):
    return f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:6px;font-size:0.75rem;font-weight:700;letter-spacing:0.03em;">{label}</span>'

def student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    if paid_amount >= total:
        s = STATUS_COLORS["paid"]
        badge = status_badge("PAID IN FULL", s["badge_bg"])
        amount_line = f'<span style="color:#15803d;font-weight:700;">Rs {int(total):,} — Fully Cleared</span>'
    elif paid_amount > 0:
        s = STATUS_COLORS["partial"]
        badge = status_badge("PARTIAL PAYMENT", s["badge_bg"])
        amount_line = f'<span style="color:#1d4ed8;font-weight:700;">Paid: Rs {int(paid_amount):,} &nbsp;·&nbsp; Remaining: Rs {int(remaining):,}</span>'
    else:
        s = STATUS_COLORS["unpaid"]
        badge = status_badge("UNPAID", s["badge_bg"])
        amount_line = f'<span style="color:#b91c1c;font-weight:700;">Rs {int(total):,} — Outstanding</span>'

    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    st.markdown(f"""
<div style="background:{s['bg']};border:1px solid {s['border']};border-radius:12px;
            padding:16px 20px;margin-bottom:10px;transition:all 0.2s;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
    <div style="display:flex;align-items:center;gap:14px;">
      <div style="width:42px;height:42px;border-radius:10px;background:{s['border']};
                  display:flex;align-items:center;justify-content:center;
                  font-size:14px;font-weight:800;color:#fff;flex-shrink:0;">{initials}</div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#0f172a;">{name}</div>
        <div style="font-size:0.8rem;color:#64748b;margin-top:1px;">Room {room}</div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
      {badge}
      {amount_line}
    </div>
  </div>
  <div style="margin-top:12px;padding-top:12px;border-top:1px solid {s['border']};
              display:flex;gap:20px;flex-wrap:wrap;">
    <span style="font-size:0.8rem;color:#64748b;">Food Dues <strong style="color:#0f172a;">Rs {int(food):,}</strong></span>
    <span style="font-size:0.8rem;color:#64748b;">Service <strong style="color:#0f172a;">Rs {int(service):,}</strong></span>
    <span style="font-size:0.8rem;color:#64748b;">Previous <strong style="color:#0f172a;">Rs {int(prev):,}</strong></span>
    <span style="font-size:0.8rem;color:#64748b;">Total <strong style="color:#0f172a;font-size:0.95rem;">Rs {int(total):,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

def receipt_card(room, name, amount, date, idx):
    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name else "?"
    st.markdown(f"""
<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
            padding:14px 18px;margin-bottom:8px;display:flex;
            justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:38px;height:38px;border-radius:9px;background:#dbeafe;
                display:flex;align-items:center;justify-content:center;
                font-size:12px;font-weight:800;color:#1d4ed8;">{initials}</div>
    <div>
      <div style="font-size:0.9rem;font-weight:700;color:#0f172a;">{name}</div>
      <div style="font-size:0.78rem;color:#64748b;">Room {room} &nbsp;·&nbsp; {date}</div>
    </div>
  </div>
  <div style="font-size:1.1rem;font-weight:800;color:#16a34a;">Rs {int(float(amount)) if amount else 0:,}</div>
</div>
""", unsafe_allow_html=True)

def hall_summary_card(hall_name, total, collected, remaining, pct_int):
    if total == 0:
        accent, bg, pct_color = "#94a3b8", "#f8fafc", "#94a3b8"
    elif remaining == 0:
        accent, bg, pct_color = "#16a34a", "#f0fdf4", "#16a34a"
    elif collected > 0:
        accent, bg, pct_color = "#1d4ed8", "#eff6ff", "#1d4ed8"
    else:
        accent, bg, pct_color = "#dc2626", "#fef2f2", "#b91c1c"

    bar_width = min(100, pct_int)
    st.markdown(f"""
<div style="background:{bg};border:1px solid #e2e8f0;border-radius:14px;
            padding:18px 22px;margin-bottom:10px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <div>
      <div style="font-size:1rem;font-weight:700;color:#0f172a;">{hall_name}</div>
      <div style="font-size:0.78rem;color:#64748b;margin-top:2px;">Total Outstanding: Rs {total:,}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.5rem;font-weight:800;color:{pct_color};">{pct_int}%</div>
      <div style="font-size:0.72rem;color:#94a3b8;font-weight:500;">COLLECTED</div>
    </div>
  </div>
  <div style="background:#e2e8f0;border-radius:999px;height:6px;overflow:hidden;margin-bottom:12px;">
    <div style="background:{accent};height:6px;width:{bar_width}%;border-radius:999px;transition:width 0.4s;"></div>
  </div>
  <div style="display:flex;gap:20px;flex-wrap:wrap;">
    <span style="font-size:0.8rem;color:#64748b;">Collected <strong style="color:#16a34a;">Rs {collected:,}</strong></span>
    <span style="font-size:0.8rem;color:#64748b;">Remaining <strong style="color:#dc2626;">Rs {remaining:,}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div class="sidebar-logo">
  <h2>🏛️ Mess Dues System</h2>
  <p>University Hostel Management</p>
</div>
""", unsafe_allow_html=True)

role = st.sidebar.selectbox("Role", ["Student", "Hall Admin", "Senior Warden"])

if AUTO_REFRESH:
    refresh_rate = st.sidebar.selectbox("Auto Refresh", ["Off", "30 sec", "60 sec", "2 min"], index=2)
    rate_map = {"Off": 0, "30 sec": 30000, "60 sec": 60000, "2 min": 120000}
    if rate_map[refresh_rate] > 0:
        st_autorefresh(interval=rate_map[refresh_rate], key="autorefresh")

st.sidebar.markdown("""
<div style="padding:12px 10px;margin-top:8px;border-top:1px solid #1e293b;text-align:center;">
  <div style="font-size:0.78rem;font-weight:700;color:#e2e8f0;letter-spacing:0.02em;">Abdul Hadi</div>
  <div style="font-size:0.68rem;color:#64748b;margin-top:2px;">2025 (S) &nbsp;·&nbsp; CYS 90</div>
  <div style="font-size:0.65rem;color:#334155;margin-top:4px;font-style:italic;">Designed & Developed</div>
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

    page_header(f"{hall}", "View your mess dues and submit payment receipts")

    if dues.empty:
        st.warning("No dues have been uploaded for this hall yet.")
        st.stop()

    month_list     = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Select Month", month_list)
    month_dues     = dues[dues["Month"] == selected_month].sort_values("RoomNo")

    # Summary strip
    total_due = month_dues["Total"].sum()
    total_students = len(month_dues)
    paid_count = 0
    total_collected = 0
    for _, r in month_dues.iterrows():
        if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
            sp = payments[
                (payments["RoomNo"].astype(str).str.strip() == str(r["RoomNo"]).strip()) &
                (payments["Name"].astype(str).str.strip() == str(r["Name"]).strip()) &
                (payments["Month"] == selected_month)
            ]
            pa = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
            if pa >= r["Total"]: paid_count += 1
            total_collected += pa

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total_students)
    c2.metric("Total Dues", f"Rs {int(total_due):,}")
    c3.metric("Fully Paid", paid_count)
    c4.metric("Remaining", total_students - paid_count)

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

        with st.expander(f"Submit Receipt — Room {room} · {name}"):
            uploaded_files = st.file_uploader(
                "Upload receipt image(s)",
                accept_multiple_files=True,
                key=f"files_{room}_{idx}"
            )
            amount_paid_input = st.number_input(
                "Amount Submitted (Rs)",
                min_value=1, max_value=int(total), value=int(total), step=1,
                key=f"amt_{room}_{idx}"
            )

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
                            st.success(f"Receipt submitted. Paid: Rs {amount_paid_input:,} · Remaining: Rs {rem:,}")
                        else:
                            st.success(f"Full payment submitted successfully. Amount: Rs {amount_paid_input:,}")
                        st.rerun()
                    for e in errors:
                        st.error(e)


# ══════════════════════════════════════════════════════════════════
# HALL ADMIN
# ══════════════════════════════════════════════════════════════════
elif role == "Hall Admin":
    hall = st.sidebar.selectbox("Select Hall", halls)
    pw   = st.sidebar.text_input("Administrator Password", type="password")

    if pw != hall_passwords.get(hall, ""):
        st.sidebar.error("Incorrect password")
        st.stop()

    page_header(f"{hall} — Admin Panel", "Manage dues, track payments and review receipts")

    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Upload Dues", "Dashboard", "Pending", "Receipts", "Manage Months"
    ])

    # ── Upload Dues ──────────────────────────────────────────────
    with tab1:
        section_label("Upload Monthly Dues")
        years       = list(range(2025, 2032))
        months_list = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
        month       = st.selectbox("Billing Month", months_list,
                                   index=months_list.index(datetime.now().strftime("%Y-%m")))
        uploaded = st.file_uploader("Select Excel or CSV File", type=["csv", "xlsx"])

        if uploaded and st.button("Upload and Save"):
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

            # Auto carry forward previous arrears
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

            st.success(f"{len(df)} student records uploaded successfully for {month}.")

    # ── Dashboard ────────────────────────────────────────────────
    with tab2:
        if dues.empty:
            st.info("No data available. Please upload dues first.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Select Month", month_list, key="dash_month")
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
            remaining   = total_dues - collected
            pct         = int(collected / total_dues * 100) if total_dues else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Dues",   f"Rs {int(total_dues):,}")
            c2.metric("Collected",    f"Rs {int(collected):,}", f"{pct}% recovered")
            c3.metric("Remaining",    f"Rs {int(remaining):,}")
            c4.metric("Students",     len(df_d))

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

            def row_color(row):
                s = row.get("Status","")
                if s == "Paid":    return ["background-color:#f0fdf4;color:#14532d;font-weight:600"] * len(row)
                elif s == "Partial": return ["background-color:#eff6ff;color:#1e3a8a;font-weight:600"] * len(row)
                return ["background-color:#fef2f2;color:#7f1d1d;font-weight:500"] * len(row)

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
                f"Download {sel_month} Report (CSV)",
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

            pending = lt_dues[lt_dues["Remaining"] > 0].drop(columns=["_key"])
            fully_paid = len(lt_dues) - len(pending)

            section_label(f"Pending Payments — {latest_m}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pending Students", len(pending))
            c2.metric("Fully Paid",       fully_paid)
            c3.metric("Pending Amount",   f"Rs {int(pending['Remaining'].sum()):,}" if not pending.empty else "Rs 0")

            st.markdown("<br>", unsafe_allow_html=True)
            if pending.empty:
                st.success("All students have paid their dues for this month.")
            else:
                show = ["RoomNo","Name","Total","Paid","Remaining"]
                st.dataframe(pending[[c for c in show if c in pending.columns]],
                             use_container_width=True, hide_index=True)

    # ── Receipts ─────────────────────────────────────────────────
    with tab4:
        if payments.empty:
            st.info("No receipts have been submitted yet.")
        else:
            section_label(f"All Receipts — {len(payments)} submissions")

            # Month filter for receipts
            if "Month" in payments.columns:
                rec_months = ["All Months"] + sorted(payments["Month"].unique(), reverse=True)
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
                        st.download_button("Download Receipt", fp,
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

            st.warning(f"This will permanently delete all dues and receipts for **{month_to_del}**.")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Delete Month", type="primary"):
                    save_dues(dues[dues["Month"] != month_to_del], hall)
                    if not payments.empty and "Month" in payments.columns:
                        save_payments(payments[payments["Month"] != month_to_del], hall)
                    st.success(f"All data for {month_to_del} has been deleted.")
                    st.rerun()
            with col2:
                st.info("To update a month's data, simply re-upload via the Upload Dues tab.")


# ══════════════════════════════════════════════════════════════════
# SENIOR WARDEN
# ══════════════════════════════════════════════════════════════════
elif role == "Senior Warden":
    pw = st.sidebar.text_input("Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.error("Incorrect password")
        st.stop()

    page_header("Senior Warden Dashboard", "Financial overview across all 9 halls")

    all_data = load_all_sheets_data()

    # Collect all months
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
        "Reporting Period",
        month_options,
        index=month_options.index(st.session_state["warden_selected_month"]),
        key="warden_month_select"
    )
    st.session_state["warden_selected_month"] = selected_w_month

    # ── Build summary data ────────────────────────────────────
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

            # Count paid vs unpaid students
            for _, row in hd_f.iterrows():
                room, name = str(row["RoomNo"]).strip(), str(row["Name"]).strip()
                if not hp_f.empty and "Amount_Paid" in hp_f.columns:
                    sp = hp_f[(hp_f["RoomNo"].astype(str).str.strip() == room) &
                               (hp_f["Name"].astype(str).str.strip() == name)]
                    pa = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    if pa >= row["Total"]:
                        paid_students_all += 1
                    else:
                        unpaid_students_all += 1
                else:
                    unpaid_students_all += 1

            summary.append({"Hall": hall, "Students": len(hd_f), "Total": total,
                             "Collected": collected, "Remaining": remaining, "Pct": pct})
        else:
            summary.append({"Hall": hall, "Students": 0, "Total": 0, "Collected": 0, "Remaining": 0, "Pct": 0})

    # ── Top KPI row ───────────────────────────────────────────
    overall_pct = int(collected_all / total_all * 100) if total_all else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Grand Total Dues",   f"Rs {int(total_all):,}")
    c2.metric("Total Collected",    f"Rs {int(collected_all):,}", f"{overall_pct}% recovered")
    c3.metric("Total Remaining",    f"Rs {int(remaining_all):,}")
    c4.metric("Recovery Rate",      f"{overall_pct}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row ────────────────────────────────────────────
    col_pie, col_bar = st.columns([1, 2])

    with col_pie:
        section_label("Collection Status")
        # Pie chart via plotly
        try:
            import plotly.graph_objects as go

            labels  = ["Collected", "Remaining"]
            values  = [collected_all, remaining_all]
            colors  = ["#22c55e", "#f87171"]

            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textinfo="percent",
                textfont=dict(size=13, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>Rs %{value:,.0f}<extra></extra>"
            )])
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                            font=dict(size=12, family="Inter, sans-serif")),
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{overall_pct}%</b><br><span style='font-size:11px'>Recovered</span>",
                    x=0.5, y=0.5, font_size=16, font_family="Inter, sans-serif",
                    showarrow=False
                )]
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            st.info(f"Collection: Rs {collected_all:,} of Rs {total_all:,}")

    with col_bar:
        section_label("Hall-wise Comparison")
        try:
            import plotly.graph_objects as go

            hall_names = [s["Hall"].replace(" Hall","") for s in summary]
            collected_vals = [s["Collected"] for s in summary]
            remaining_vals = [s["Remaining"] for s in summary]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Collected", x=hall_names, y=collected_vals,
                marker_color="#22c55e",
                hovertemplate="<b>%{x}</b><br>Collected: Rs %{y:,.0f}<extra></extra>"
            ))
            fig_bar.add_trace(go.Bar(
                name="Remaining", x=hall_names, y=remaining_vals,
                marker_color="#f87171",
                hovertemplate="<b>%{x}</b><br>Remaining: Rs %{y:,.0f}<extra></extra>"
            ))
            fig_bar.update_layout(
                barmode="stack",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, family="Inter, sans-serif")),
                margin=dict(t=30, b=10, l=10, r=10),
                height=260,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=11, family="Inter, sans-serif")),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9",
                           tickformat=",", tickfont=dict(size=10, family="Inter, sans-serif")),
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            chart_df = pd.DataFrame(summary).set_index("Hall")[["Collected","Remaining"]]
            st.bar_chart(chart_df)

    # ── Student status donut ──────────────────────────────────
    try:
        import plotly.graph_objects as go
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            section_label("Student Payment Status")
            total_students_all = paid_students_all + unpaid_students_all
            fig_d = go.Figure(data=[go.Pie(
                labels=["Paid", "Pending"],
                values=[paid_students_all, unpaid_students_all],
                hole=0.6,
                marker=dict(colors=["#3b82f6","#f59e0b"], line=dict(color="#ffffff", width=2)),
                textinfo="percent+value",
                textfont=dict(size=12, family="Inter, sans-serif"),
                hovertemplate="<b>%{label}</b><br>%{value} students<extra></extra>"
            )])
            fig_d.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
                            font=dict(size=12, family="Inter, sans-serif")),
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[dict(
                    text=f"<b>{total_students_all}</b><br><span>students</span>",
                    x=0.5, y=0.5, font_size=14, font_family="Inter, sans-serif", showarrow=False
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
                    colorscale=[[0,"#f87171"],[0.5,"#fbbf24"],[1,"#22c55e"]],
                    showscale=False
                ),
                text=[f"{p}%" for p in hall_pcts],
                textposition="outside",
                textfont=dict(size=11, family="Inter, sans-serif"),
                hovertemplate="<b>%{y}</b><br>Recovery: %{x}%<extra></extra>"
            ))
            fig_h.update_layout(
                margin=dict(t=10, b=10, l=10, r=40),
                height=240,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(range=[0,115], showgrid=False, visible=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=11, family="Inter, sans-serif")),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        pass

    # ── Hall cards ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Hall-wise Breakdown")

    for row in summary:
        hall_summary_card(row["Hall"], row["Total"], row["Collected"], row["Remaining"], row["Pct"])

    # ── Export ────────────────────────────────────────────────
    st.markdown("---")
    export_df = pd.DataFrame([{
        "Hall": r["Hall"], "Students": r["Students"],
        "Total Dues (Rs)": r["Total"], "Collected (Rs)": r["Collected"],
        "Remaining (Rs)": r["Remaining"], "Recovery %": f"{r['Pct']}%"
    } for r in summary])
    csv_w = export_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Full Summary (CSV)", csv_w,
                       file_name="all_halls_summary.csv", mime="text/csv")

    # ── Payments overview table ───────────────────────────────
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


# ── Footer ────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding:1.5rem 2rem;border-top:1px solid #e2e8f0;
            background:#fff;border-radius:12px;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
  <div>
    <span style="font-size:0.85rem;font-weight:700;color:#0f172a;">University Mess Dues System</span>
    <span style="color:#cbd5e1;margin:0 8px;">|</span>
    <span style="font-size:0.8rem;color:#64748b;">Powered by Streamlit &amp; Google Sheets</span>
  </div>
  <div style="text-align:right;">
    <span style="font-size:0.8rem;font-weight:700;color:#1d4ed8;">Designed &amp; Developed by Abdul Hadi</span>
    <br>
    <span style="font-size:0.72rem;color:#94a3b8;">2025 (S) &nbsp;·&nbsp; CYS 90 &nbsp;·&nbsp; University of Engineering &amp; Technology</span>
  </div>
</div>
""", unsafe_allow_html=True)
