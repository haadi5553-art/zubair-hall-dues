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

st.set_page_config(page_title="University Mess Dues System", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1a1a2e !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #e8e8f0 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #2a2a45 !important;
    color: #e8e8f0 !important;
    border: 1px solid #4a4a70 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #2e7d32 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.45rem 1.25rem !important;
    letter-spacing: 0.01em;
}
.stButton > button:hover {
    background: #1b5e20 !important;
    color: #ffffff !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    font-size: 0.9rem;
    color: #444 !important;
}
.stTabs [aria-selected="true"] {
    color: #1a1a2e !important;
    border-bottom: 3px solid #2e7d32 !important;
}

/* ── Metric cards ── */
[data-testid="stMetricValue"] {
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: #1a1a2e !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #555 !important;
    font-weight: 500 !important;
}

/* ── Dataframe text ── */
.dataframe td, .dataframe th {
    font-size: 0.88rem !important;
    color: #111 !important;
}

/* ── General ── */
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
h1 {font-size: 1.9rem; color: #1a1a2e;}
h2 {color: #1a1a2e;}
h3 {color: #1a1a2e;}
</style>
""", unsafe_allow_html=True)


# ── Student card renderer ─────────────────────────────────────────────────────
def render_student_card(room, name, food, service, prev, total, paid_amount):
    remaining = max(0.0, total - paid_amount)
    is_fully  = paid_amount >= total
    is_partial = 0 < paid_amount < total

    if is_fully:
        left_color  = "#2e7d32"
        bg_color    = "#f1f8f1"
        status_html = '<span style="background:#2e7d32;color:#fff;padding:3px 10px;border-radius:4px;font-size:0.8rem;font-weight:700;">FULLY PAID</span>'
    elif is_partial:
        left_color  = "#e65100"
        bg_color    = "#fff8f0"
        status_html = f'<span style="background:#e65100;color:#fff;padding:3px 10px;border-radius:4px;font-size:0.8rem;font-weight:700;">PARTIAL &nbsp; Paid: Rs {int(paid_amount)} &nbsp;|&nbsp; Remaining: Rs {int(remaining)}</span>'
    else:
        left_color  = "#1565c0"
        bg_color    = "#f5f8ff"
        status_html = '<span style="background:#1565c0;color:#fff;padding:3px 10px;border-radius:4px;font-size:0.8rem;font-weight:700;">UNPAID</span>'

    st.markdown(f"""
<div style="
    background:{bg_color};
    border-left:5px solid {left_color};
    border-radius:8px;
    padding:14px 18px;
    margin-bottom:8px;
    border:1px solid #e0e0e0;
">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      <span style="font-size:1rem;font-weight:700;color:#1a1a2e;">Room {room}</span>
      <span style="margin:0 10px;color:#888;">|</span>
      <span style="font-size:1rem;font-weight:600;color:#1a1a2e;">{name}</span>
    </div>
    <div>{status_html}</div>
  </div>
  <div style="margin-top:10px;display:flex;gap:24px;flex-wrap:wrap;">
    <span style="font-size:0.85rem;color:#444;"><strong style="color:#222;">Food:</strong> Rs {int(food)}</span>
    <span style="font-size:0.85rem;color:#444;"><strong style="color:#222;">Service:</strong> Rs {int(service)}</span>
    <span style="font-size:0.85rem;color:#444;"><strong style="color:#222;">Previous:</strong> Rs {int(prev)}</span>
    <span style="font-size:0.9rem;font-weight:700;color:{left_color};"><strong>Total: Rs {int(total)}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Google Sheets ─────────────────────────────────────────────────────────────
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


# ── Load ALL sheets in ONE call ───────────────────────────────────────────────
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


# ── Sheet name finder (fuzzy) ─────────────────────────────────────────────────
def find_sheet_key(all_data, name):
    name_clean = name.strip().lower().replace(" ", "")
    for key in all_data:
        if key.strip().lower().replace(" ", "") == name_clean:
            return key
    return None


# ── Standardize columns ───────────────────────────────────────────────────────
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


# ── Get dues from cache ───────────────────────────────────────────────────────
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


# ── Get payments from cache ───────────────────────────────────────────────────
def get_payments_from_cache(all_data, hall):
    key = find_sheet_key(all_data, f"{hall}_Payments")
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_File","File_Hash"])
    return all_data[key].copy()


# ── Clean for Sheets ──────────────────────────────────────────────────────────
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


# ── Worksheet find or create ──────────────────────────────────────────────────
def find_or_create_worksheet(name):
    sh = get_spreadsheet()
    clean = name.strip().lower().replace(" ", "")
    for ws in sh.worksheets():
        if ws.title.strip().lower().replace(" ", "") == clean:
            return ws
    return sh.add_worksheet(title=name, rows=5000, cols=20)


# ── Save dues ─────────────────────────────────────────────────────────────────
def save_dues(df, hall):
    ws = find_or_create_worksheet(hall)
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()


# ── Save payments ─────────────────────────────────────────────────────────────
def save_payments(df, hall):
    ws = find_or_create_worksheet(f"{hall}_Payments")
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()


# ── Setup ─────────────────────────────────────────────────────────────────────
if not os.path.exists("receipts"):
    os.makedirs("receipts")

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


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏛️ University Mess Dues Management System")
st.caption("Made by Abdul Hadi 2025 (S) CYS 90")

role = st.sidebar.selectbox("Select Role", ["Student", "Hall Admin", "Senior Warden"])

if AUTO_REFRESH:
    refresh_rate = st.sidebar.selectbox("🔄 Auto Refresh", ["Off", "30 sec", "60 sec", "2 min"], index=2)
    rate_map = {"Off": 0, "30 sec": 30000, "60 sec": 60000, "2 min": 120000}
    if rate_map[refresh_rate] > 0:
        st_autorefresh(interval=rate_map[refresh_rate], key="autorefresh")


# ══════════════════════════════════════════════════════════════════
# STUDENT
# ══════════════════════════════════════════════════════════════════
if role == "Student":
    hall     = st.sidebar.selectbox("Select Hall", halls)
    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    if dues.empty:
        st.warning(f"⚠️ {hall} mein abhi koi dues upload nahi hue.")
        st.stop()

    month_list     = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("📅 Month Select Karo", month_list)
    month_dues     = dues[dues["Month"] == selected_month].sort_values("RoomNo")

    st.subheader(f"📋 {hall} — {selected_month}")
    st.markdown("---")

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

        render_student_card(room, name, row["Food_Dues"], row["Service_Charges"], row["Previous"], total, paid_amount)

        with st.expander(f"📎 Receipt Upload — Room {room}"):
            uploaded_files = st.file_uploader(
                "Receipt(s) upload karo",
                accept_multiple_files=True,
                key=f"files_{room}_{idx}"
            )
            amount_paid_input = st.number_input(
                "💵 Amount Jama Karwaya (Rs)",
                min_value=1, max_value=int(total), value=int(total), step=1,
                key=f"amt_{room}_{idx}"
            )

            if uploaded_files:
                if st.button(f"✅ Submit — Room {room}", key=f"submit_{room}_{idx}"):
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
                                errors.append(f"❌ '{f.name}' — duplicate receipt!")
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
                            st.success(f"✅ Paid: Rs {amount_paid_input} | Remaining: Rs {rem}")
                        else:
                            st.success(f"✅ Full payment submitted: Rs {amount_paid_input}")
                        st.rerun()
                    for e in errors:
                        st.error(e)


# ══════════════════════════════════════════════════════════════════
# HALL ADMIN
# ══════════════════════════════════════════════════════════════════
elif role == "Hall Admin":
    hall = st.sidebar.selectbox("Select Hall", halls)
    pw   = st.sidebar.text_input("Admin Password", type="password")

    if pw != hall_passwords.get(hall, ""):
        st.sidebar.warning("❌ Wrong Password")
        st.stop()

    st.header(f"🏠 {hall} — Admin Dashboard")

    all_data = load_all_sheets_data()
    dues     = get_dues_from_cache(all_data, hall)
    payments = get_payments_from_cache(all_data, hall)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload Dues", "📊 Dashboard", "⏳ Pending", "📄 Receipts", "🗑️ Manage Months"
    ])

    # ── Upload Dues ──
    with tab1:
        st.subheader("New Month Dues Upload")
        years       = list(range(2025, 2032))
        months_list = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
        month       = st.selectbox("Month (YYYY-MM)", months_list,
                                   index=months_list.index(datetime.now().strftime("%Y-%m")))
        uploaded = st.file_uploader("Excel / CSV File", type=["csv", "xlsx"])

        if uploaded and st.button("📤 Upload Karo"):
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

            # Auto carry forward
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
                            st.info(f"🔄 {carried} student(s) ka remaining carry forward ho gaya ({last_m} → {month})")

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)

            if not all_payments.empty and "Month" in all_payments.columns:
                cleaned = all_payments[all_payments["Month"] != month]
                removed = len(all_payments) - len(cleaned)
                save_payments(cleaned, hall)
                if removed:
                    st.info(f"ℹ️ {removed} purani payment(s) reset ho gayi")

            st.success(f"✅ {len(df)} students uploaded for {month}!")

    # ── Dashboard ──
    with tab2:
        if dues.empty:
            st.info("Koi data nahi.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Month", month_list, key="dash_month")
            df_d       = dues[dues["Month"] == sel_month].copy()

            srch = st.text_input("🔍 Room No ya Name search karo")
            if srch:
                df_d = df_d[df_d["RoomNo"].str.contains(srch, case=False) | df_d["Name"].str.contains(srch, case=False)]

            total_dues = df_d["Total"].sum()
            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                collected = pd.to_numeric(payments[payments["Month"]==sel_month]["Amount_Paid"], errors="coerce").fillna(0).sum()
            else:
                collected = 0

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Total Dues",  f"Rs {int(total_dues):,}")
            c2.metric("✅ Collected",   f"Rs {int(collected):,}")
            c3.metric("⏳ Remaining",   f"Rs {int(total_dues - collected):,}")

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

            # Color rows by status — NO highlighting of individual cells, full row color
            def row_color(row):
                p = row.get("Paid (Rs)", 0)
                t = row["Total"]
                if p >= t:
                    # Fully paid — green row, dark green text
                    return ["background-color:#e8f5e9; color:#1b5e20; font-weight:600"] * len(row)
                elif p > 0:
                    # Partial — amber row, dark amber text
                    return ["background-color:#fff8e1; color:#5d4037; font-weight:600"] * len(row)
                else:
                    # Unpaid — light blue row, dark blue text
                    return ["background-color:#e3f2fd; color:#0d47a1; font-weight:500"] * len(row)

            cols = ["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)"]
            st.dataframe(
                df_d[cols].style.apply(row_color, axis=1),
                use_container_width=True, hide_index=True
            )

            if not df_d.empty:
                st.bar_chart(df_d.set_index("Name")[["Total","Paid (Rs)"]])

            st.markdown("---")
            csv = df_d[cols].to_csv(index=False).encode("utf-8")
            st.download_button(f"⬇️ Download {sel_month} Report", csv,
                               file_name=f"{hall}_{sel_month}.csv", mime="text/csv")

    # ── Pending ──
    with tab3:
        if dues.empty:
            st.info("Koi data nahi.")
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

            if pending.empty:
                st.success("🎉 Sab students ne pay kar diya!")
            else:
                st.warning(f"⚠️ {len(pending)} students pending — {latest_m}")
                show = ["RoomNo","Name","Total","Paid","Remaining"]
                st.dataframe(pending[[c for c in show if c in pending.columns]],
                             use_container_width=True, hide_index=True)

    # ── Receipts ──
    with tab4:
        if payments.empty:
            st.info("Koi receipt nahi.")
        else:
            st.subheader(f"📄 Total Receipts: {len(payments)}")
            for i, row in payments.iterrows():
                st.markdown(f"""
<div style="background:#f9f9f9;border:1px solid #ddd;border-left:4px solid #2e7d32;
            border-radius:6px;padding:10px 14px;margin-bottom:8px;">
  <span style="font-weight:700;color:#1a1a2e;">Room {row['RoomNo']}</span>
  <span style="color:#888;margin:0 8px;">|</span>
  <span style="font-weight:600;color:#1a1a2e;">{row['Name']}</span>
  <span style="color:#888;margin:0 8px;">|</span>
  <span style="color:#2e7d32;font-weight:700;">Rs {row.get('Amount_Paid','')}</span>
  <span style="color:#888;margin:0 8px;">|</span>
  <span style="color:#555;font-size:0.85rem;">{row.get('Submission_Date','')}</span>
</div>
""", unsafe_allow_html=True)
                path = str(row.get("Receipt_File",""))
                if path and os.path.exists(path):
                    if path.lower().endswith((".png",".jpg",".jpeg")):
                        st.image(path, width=200)
                    with open(path,"rb") as fp:
                        st.download_button("⬇️ Download", fp,
                                           file_name=os.path.basename(path),
                                           key=f"dl_{i}")
                else:
                    st.caption("⚠️ File server pe nahi (cloud restart issue)")

    # ── Manage Months ──
    with tab5:
        if dues.empty:
            st.info("Koi month nahi.")
        else:
            month_list   = sorted(dues["Month"].unique(), reverse=True)
            month_to_del = st.selectbox("Month Select Karo", month_list, key="del_month")
            col1, col2   = st.columns(2)
            with col1:
                if st.button("🗑️ Delete Karo", type="primary"):
                    save_dues(dues[dues["Month"] != month_to_del], hall)
                    if not payments.empty and "Month" in payments.columns:
                        save_payments(payments[payments["Month"] != month_to_del], hall)
                    st.success(f"✅ '{month_to_del}' deleted!")
                    st.rerun()
            with col2:
                st.info("Update ke liye same month dobara upload karo.")


# ══════════════════════════════════════════════════════════════════
# SENIOR WARDEN
# ══════════════════════════════════════════════════════════════════
elif role == "Senior Warden":
    pw = st.sidebar.text_input("Senior Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.warning("❌ Wrong Password")
        st.stop()

    st.header("👨‍💼 Senior Warden Dashboard — Sab 9 Halls")

    # ONE API call — sab data
    all_data = load_all_sheets_data()

    # Sab months collect karo (cache se)
    all_months = set()
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            for m in hd["Month"].unique():
                if m and m != "Unknown":
                    all_months.add(m)

    month_options = ["Sab Months (Combined)"] + sorted(all_months, reverse=True)

    # Session state se stable month filter
    if "warden_selected_month" not in st.session_state:
        st.session_state["warden_selected_month"] = "Sab Months (Combined)"
    if st.session_state["warden_selected_month"] not in month_options:
        st.session_state["warden_selected_month"] = "Sab Months (Combined)"

    selected_w_month = st.selectbox(
        "📅 Month Select Karo",
        month_options,
        index=month_options.index(st.session_state["warden_selected_month"]),
        key="warden_month_select"
    )
    st.session_state["warden_selected_month"] = selected_w_month

    # Calculate summary — all from cache, 0 extra API calls
    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        hd = get_dues_from_cache(all_data, hall)
        hp = get_payments_from_cache(all_data, hall)

        if not hd.empty and "Month" in hd.columns:
            if selected_w_month != "Sab Months (Combined)":
                hd_f = hd[hd["Month"] == selected_w_month]
                hp_f = hp[hp["Month"] == selected_w_month] if (not hp.empty and "Month" in hp.columns) else pd.DataFrame()
            else:
                hd_f, hp_f = hd, hp

            if hd_f.empty:
                summary.append({"Hall": hall, "Total (Rs)": 0, "Collected (Rs)": 0, "Remaining (Rs)": 0, "Paid %": "—"})
                continue

            total     = int(hd_f["Total"].sum())
            collected = int(pd.to_numeric(hp_f["Amount_Paid"], errors="coerce").fillna(0).sum()) \
                        if (not hp_f.empty and "Amount_Paid" in hp_f.columns) else 0
            remaining      = total - collected
            total_all     += total
            collected_all += collected
            remaining_all += remaining

            summary.append({
                "Hall": hall,
                "Total (Rs)":     total,
                "Collected (Rs)": collected,
                "Remaining (Rs)": remaining,
                "Paid %":         f"{int(collected/total*100) if total else 0}%"
            })
        else:
            summary.append({"Hall": hall, "Total (Rs)": 0, "Collected (Rs)": 0, "Remaining (Rs)": 0, "Paid %": "—"})

    # Top metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Grand Total",     f"Rs {int(total_all):,}")
    c2.metric("✅ Total Collected",  f"Rs {int(collected_all):,}")
    c3.metric("⏳ Total Remaining",  f"Rs {int(remaining_all):,}")

    st.markdown("---")
    st.subheader("📊 Hall-wise Summary")

    # Render summary as colored cards (not just a table)
    for row in summary:
        hall_name = row["Hall"]
        tot       = row["Total (Rs)"]
        col       = row["Collected (Rs)"]
        rem       = row["Remaining (Rs)"]
        pct       = row["Paid %"]

        if tot == 0:
            left, bg, tc = "#9e9e9e", "#f5f5f5", "#555"
        elif rem == 0:
            left, bg, tc = "#2e7d32", "#f1f8f1", "#1b5e20"
        elif col > 0:
            left, bg, tc = "#e65100", "#fff8f0", "#5d4037"
        else:
            left, bg, tc = "#1565c0", "#f5f8ff", "#0d47a1"

        st.markdown(f"""
<div style="background:{bg};border-left:5px solid {left};border:1px solid #e0e0e0;
            border-radius:8px;padding:12px 18px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
    <span style="font-size:1rem;font-weight:700;color:#1a1a2e;">{hall_name}</span>
    <span style="font-size:0.85rem;font-weight:700;color:{left};background:{bg};
                 border:1.5px solid {left};padding:2px 10px;border-radius:4px;">{pct} collected</span>
  </div>
  <div style="margin-top:8px;display:flex;gap:24px;flex-wrap:wrap;">
    <span style="font-size:0.85rem;color:#444;"><strong style="color:#222;">Total:</strong> Rs {tot:,}</span>
    <span style="font-size:0.85rem;color:#2e7d32;"><strong>Collected:</strong> Rs {col:,}</span>
    <span style="font-size:0.85rem;color:#c62828;"><strong>Remaining:</strong> Rs {rem:,}</span>
  </div>
</div>
""", unsafe_allow_html=True)

    if summary:
        st.markdown("---")
        st.subheader("📈 Collection Chart")
        chart_df = pd.DataFrame(summary).set_index("Hall")[["Collected (Rs)", "Remaining (Rs)"]]
        st.bar_chart(chart_df)

        csv_w = pd.DataFrame(summary).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Summary CSV", csv_w,
                           file_name="all_halls_summary.csv", mime="text/csv")

    # Payments overview
    st.markdown("---")
    st.subheader("📋 Sab Halls ki Payments Overview")

    all_pay_rows = []
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        hp = get_payments_from_cache(all_data, h)

        if not hd.empty and "Month" in hd.columns:
            months_to_show = ([selected_w_month] if selected_w_month != "Sab Months (Combined)"
                              else sorted(hd["Month"].unique(), reverse=True))
            for mv in months_to_show:
                if mv == "Unknown": continue
                mdf = hd[hd["Month"] == mv]
                if mdf.empty: continue
                tot  = int(mdf["Total"].sum())
                recs = 0
                col  = 0
                if not hp.empty and "Month" in hp.columns:
                    mp   = hp[hp["Month"] == mv]
                    recs = len(mp)
                    if "Amount_Paid" in mp.columns:
                        col = int(pd.to_numeric(mp["Amount_Paid"], errors="coerce").fillna(0).sum())
                all_pay_rows.append({
                    "Hall": h, "Month": mv, "Students": len(mdf),
                    "Total Dues (Rs)": tot, "Receipts": recs,
                    "Collected (Rs)": col, "Remaining (Rs)": max(0, tot - col)
                })

    if all_pay_rows:
        apdf = pd.DataFrame(all_pay_rows).sort_values(["Month","Hall"], ascending=[False,True])
        st.dataframe(apdf, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi kisi bhi hall mein data nahi.")


st.markdown("---")
st.caption("🏛️ University Mess Dues System | Abdul Hadi 2025 (S) CYS 90 | Powered by Streamlit + Google Sheets")
