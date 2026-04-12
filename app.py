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
[data-testid="stSidebar"] {background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);}
[data-testid="stSidebar"] * {color: #eee !important;}
.stButton>button {
    background: linear-gradient(135deg, #4CAF50, #2e7d32);
    color: white !important; border-radius: 8px; border: none;
    font-weight: 600; padding: 0.4rem 1.2rem; transition: 0.2s;
}
.stButton>button:hover {opacity: 0.85;}
h1 {color: #1a1a2e; font-size: 2rem;}
[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
.stTabs [data-baseweb="tab"] {font-weight: 600; font-size: 0.95rem;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)


# ================= GOOGLE SHEET =================
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


# ================= LOAD ALL DATA — EK HI BAAR =================
@st.cache_data(ttl=30, show_spinner=False)
def load_all_sheets_data():
    """
    Poori spreadsheet ek hi API call mein load karo.
    9 halls x 2 sheets = 18 calls ki jagah sirf 1 call.
    ttl=30 => 30 second baad fresh data.
    """
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


# ================= SHEET NAME FINDER =================
def find_sheet_key(all_data, name):
    name_clean = name.strip().lower().replace(" ", "")
    for key in all_data:
        if key.strip().lower().replace(" ", "") == name_clean:
            return key
    return None


# ================= STANDARDIZE COLUMNS =================
def standardize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    column_map = {
        "room no": "RoomNo", "roomno": "RoomNo", "room no.": "RoomNo",
        "room": "RoomNo", "room_no": "RoomNo",
        "name": "Name", "student name": "Name", "student_name": "Name",
        "food dues": "Food_Dues", "food_dues": "Food_Dues", "fooddues": "Food_Dues",
        "service charges": "Service_Charges", "service_charges": "Service_Charges",
        "servicecharges": "Service_Charges",
        "previous": "Previous", "prev": "Previous", "arrears": "Previous",
        "month": "Month",
    }
    df = df.rename(columns=column_map)
    for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
        if col not in df.columns:
            df[col] = "" if col in ["RoomNo", "Name"] else 0
    return df


# ================= GET DUES FROM CACHE =================
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


# ================= GET PAYMENTS FROM CACHE =================
def get_payments_from_cache(all_data, hall):
    key = find_sheet_key(all_data, f"{hall}_Payments")
    if key is None or all_data.get(key, pd.DataFrame()).empty:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_File","File_Hash"])
    return all_data[key].copy()


# ================= CLEAN FOR SHEETS =================
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


# ================= WORKSHEET FIND OR CREATE =================
def find_or_create_worksheet(name):
    sh = get_spreadsheet()
    name_clean = name.strip().lower().replace(" ", "")
    for ws in sh.worksheets():
        if ws.title.strip().lower().replace(" ", "") == name_clean:
            return ws
    return sh.add_worksheet(title=name, rows=5000, cols=20)


# ================= SAVE DUES =================
def save_dues(df, hall):
    ws = find_or_create_worksheet(hall)
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()


# ================= SAVE PAYMENTS =================
def save_payments(df, hall):
    ws = find_or_create_worksheet(f"{hall}_Payments")
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    invalidate_cache()


# ================= RECEIPT FOLDER =================
if not os.path.exists("receipts"):
    os.makedirs("receipts")


# ================= HALLS & PASSWORDS =================
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


# ================= HEADER =================
st.title("🏛️ University Mess Dues Management System")
st.caption("Made by Abdul Hadi 2025 (S) CYS 90")

role = st.sidebar.selectbox("Select Role", ["Student", "Hall Admin", "Senior Warden"])

if AUTO_REFRESH:
    refresh_rate = st.sidebar.selectbox("🔄 Auto Refresh", ["Off", "30 sec", "60 sec", "2 min"], index=2)
    rate_map = {"Off": 0, "30 sec": 30000, "60 sec": 60000, "2 min": 120000}
    if rate_map[refresh_rate] > 0:
        st_autorefresh(interval=rate_map[refresh_rate], key="autorefresh")


# ==========================================
# ================== STUDENT ==============
# ==========================================
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

    st.subheader(f"📋 {hall} — {selected_month} — Sab Students ki Dues")
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

        remaining_amount = max(0.0, total - paid_amount)
        is_fully_paid    = paid_amount >= total
        is_partial       = 0 < paid_amount < total

        if is_fully_paid:
            bg, border, paid_badge, paid_color = "#e8f5e9", "#388e3c", "✅ FULLY PAID", "green"
        elif is_partial:
            bg, border = "#fff8e1", "#f9a825"
            paid_badge = f"⚠️ PARTIAL — Paid: Rs {int(paid_amount)} | Remaining: Rs {int(remaining_amount)}"
            paid_color = "darkorange"
        else:
            bg, border, paid_badge, paid_color = "#f8f9fb", "#4CAF50", "⏳ Unpaid", "gray"

        st.markdown(
            f'''<div style="padding:14px 18px;background:{bg};border-left:5px solid {border};
            border-radius:10px;margin-bottom:4px;box-shadow:0 2px 6px rgba(0,0,0,0.06);">
            <b>🏠 Room: {room}</b> &nbsp;|&nbsp;
            <b>👤 {name}</b> &nbsp;|&nbsp;
            🍽️ Food: Rs {int(row["Food_Dues"])} &nbsp;
            🔧 Service: Rs {int(row["Service_Charges"])} &nbsp;
            📌 Prev: Rs {int(row["Previous"])} &nbsp;|&nbsp;
            <b>💰 Total: Rs {int(total)}</b> &nbsp;
            <span style="color:{paid_color};font-weight:700;">{paid_badge}</span>
            </div>''',
            unsafe_allow_html=True
        )

        with st.expander(f"📎 Receipt Upload — Room {room}"):
            uploaded_files = st.file_uploader(
                "Receipt(s) upload karo (multiple allowed)",
                accept_multiple_files=True,
                key=f"files_{room}_{idx}"
            )
            amount_paid_input = st.number_input(
                f"💵 Kitna Amount Jama Karwaya? (Rs)",
                min_value=1, max_value=int(total), value=int(total), step=1,
                key=f"amt_{room}_{idx}",
                help=f"Max: Rs {int(total)}"
            )

            if uploaded_files:
                if st.button(f"✅ Submit Receipt(s) — Room {room}", key=f"submit_{room}_{idx}"):
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
                                errors.append(f"❌ '{f.name}' — same receipt pehle already upload ho chuki hai!")
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
                        remaining_after = int(total) - amount_paid_input
                        if remaining_after > 0:
                            st.success(f"✅ Paid: Rs {amount_paid_input} | Remaining: Rs {remaining_after}")
                        else:
                            st.success(f"✅ Full payment: Rs {amount_paid_input} ✔️")
                        st.rerun()
                    for e in errors:
                        st.error(e)


# ==========================================
# ================ HALL ADMIN =============
# ==========================================
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

    # -------- UPLOAD DUES --------
    with tab1:
        st.subheader("New Month Dues Upload")
        years       = list(range(2025, 2032))
        months_list = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
        month       = st.selectbox("Month (YYYY-MM)", months_list,
                                   index=months_list.index(datetime.now().strftime("%Y-%m")))
        uploaded = st.file_uploader("Excel / CSV File Upload Karo", type=["csv", "xlsx"])

        if uploaded and st.button("📤 Upload Karo"):
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            df = df.loc[:, ~df.columns.duplicated()]
            df = standardize_columns(df)

            for col in ["Food_Dues", "Service_Charges", "Previous"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
            df["Name"]   = df["Name"].astype(str).str.strip()
            df["Month"]  = month
            df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]

            keep_cols = ["Month", "RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]
            df = df[[c for c in keep_cols if c in df.columns]]

            # Fresh data for carry forward
            invalidate_cache()
            fresh_all    = load_all_sheets_data()
            existing     = get_dues_from_cache(fresh_all, hall)
            all_payments = get_payments_from_cache(fresh_all, hall)

            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]

            for c in keep_cols:
                if c not in existing.columns: existing[c] = ""
                if c not in df.columns:       df[c] = ""

            existing = existing[keep_cols]
            df       = df[keep_cols]

            # ===== AUTO CARRY FORWARD =====
            if not existing.empty and "Month" in existing.columns:
                past_months = sorted([m for m in existing["Month"].unique() if m != month], reverse=True)
                if past_months:
                    last_month = past_months[0]
                    last_dues  = existing[existing["Month"] == last_month].copy()
                    carry_map  = {}

                    for _, lrow in last_dues.iterrows():
                        lroom  = str(lrow["RoomNo"]).strip()
                        lname  = str(lrow["Name"]).strip()
                        ltotal = float(lrow["Total"])
                        lpaid  = 0.0

                        if not all_payments.empty and "Amount_Paid" in all_payments.columns and "Month" in all_payments.columns:
                            sp = all_payments[
                                (all_payments["RoomNo"].astype(str).str.strip() == lroom) &
                                (all_payments["Name"].astype(str).str.strip()   == lname) &
                                (all_payments["Month"] == last_month)
                            ]
                            lpaid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()

                        remaining = max(0.0, ltotal - lpaid)
                        if remaining > 0:
                            carry_map[f"{lroom}||{lname}"] = remaining

                    if carry_map:
                        carried = 0
                        for i, row2 in df.iterrows():
                            key = f"{str(row2['RoomNo']).strip()}||{str(row2['Name']).strip()}"
                            if key in carry_map:
                                df.at[i, "Previous"] = float(df.at[i, "Previous"]) + carry_map[key]
                                df.at[i, "Total"]    = float(df.at[i, "Food_Dues"]) + float(df.at[i, "Service_Charges"]) + float(df.at[i, "Previous"])
                                carried += 1
                        if carried:
                            st.info(f"🔄 {carried} student(s) ka remaining carry forward ho gaya ({last_month} → {month})")

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)

            # Same month ki purani payments reset
            if not all_payments.empty and "Month" in all_payments.columns:
                cleaned_pays = all_payments[all_payments["Month"] != month]
                removed = len(all_payments) - len(cleaned_pays)
                save_payments(cleaned_pays, hall)
                if removed > 0:
                    st.info(f"ℹ️ '{month}' ki {removed} purani payment(s) reset ho gayi")

            st.success(f"✅ {len(df)} students ka data '{month}' ke liye upload ho gaya!")

    # -------- DASHBOARD --------
    with tab2:
        if dues.empty:
            st.info("Abhi koi data upload nahi hua.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Month Select Karo", month_list, key="dash_month")
            df_dash    = dues[dues["Month"] == sel_month].copy()

            search = st.text_input("🔍 Search by Room No or Name")
            if search:
                df_dash = df_dash[
                    df_dash["RoomNo"].str.contains(search, case=False) |
                    df_dash["Name"].str.contains(search, case=False)
                ]

            total_dues = df_dash["Total"].sum()

            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                month_pays = payments[payments["Month"] == sel_month]
                collected  = pd.to_numeric(month_pays["Amount_Paid"], errors="coerce").fillna(0).sum()
            else:
                collected = 0
            remaining = total_dues - collected

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Total Dues",  f"Rs {int(total_dues):,}")
            c2.metric("✅ Collected",   f"Rs {int(collected):,}")
            c3.metric("⏳ Remaining",   f"Rs {int(remaining):,}")

            def get_paid_for_row(row):
                if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                    sp = payments[
                        (payments["RoomNo"].astype(str).str.strip() == str(row["RoomNo"]).strip()) &
                        (payments["Name"].astype(str).str.strip()   == str(row["Name"]).strip()) &
                        (payments["Month"] == sel_month)
                    ]
                    return int(pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum())
                return 0

            df_dash = df_dash.copy()
            df_dash["Paid (Rs)"]      = df_dash.apply(get_paid_for_row, axis=1)
            df_dash["Remaining (Rs)"] = (df_dash["Total"] - df_dash["Paid (Rs)"]).clip(lower=0).astype(int)

            def highlight_paid(row):
                paid_amt = row.get("Paid (Rs)", 0)
                if paid_amt >= row["Total"]:
                    return ["background-color:#c8e6c9;color:#1b5e20;font-weight:600"] * len(row)
                elif paid_amt > 0:
                    return ["background-color:#fff9c4;color:#5d4037;font-weight:600"] * len(row)
                return [""] * len(row)

            display_cols = ["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)"]
            st.dataframe(
                df_dash[display_cols].style.apply(highlight_paid, axis=1),
                use_container_width=True, hide_index=True
            )

            if not df_dash.empty:
                st.bar_chart(df_dash.set_index("RoomNo")[["Total"]])

            st.markdown("---")
            csv = df_dash[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"⬇️ Download {sel_month} Report (CSV)",
                data=csv, file_name=f"{hall}_{sel_month}_report.csv",
                mime="text/csv", key="export_csv"
            )

    # -------- PENDING --------
    with tab3:
        if dues.empty:
            st.info("Koi data nahi.")
        else:
            latest_month = sorted(dues["Month"].unique(), reverse=True)[0]
            latest_dues  = dues[dues["Month"] == latest_month].copy()
            latest_dues["_key"] = latest_dues["RoomNo"].astype(str).str.strip() + "||" + latest_dues["Name"].astype(str).str.strip()

            if not payments.empty and "Month" in payments.columns:
                month_p = payments[payments["Month"] == latest_month].copy()
                month_p["_key"] = month_p["RoomNo"].astype(str).str.strip() + "||" + month_p["Name"].astype(str).str.strip()

                def get_paid_pending(row):
                    sp = month_p[month_p["_key"] == row["_key"]]
                    if not sp.empty and "Amount_Paid" in sp.columns:
                        return pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    return 0

                latest_dues["Paid"]      = latest_dues.apply(get_paid_pending, axis=1)
                latest_dues["Remaining"] = (latest_dues["Total"] - latest_dues["Paid"]).clip(lower=0)
            else:
                latest_dues["Paid"]      = 0
                latest_dues["Remaining"] = latest_dues["Total"]

            pending = latest_dues[latest_dues["Remaining"] > 0].drop(columns=["_key"])

            if pending.empty:
                st.success("🎉 Sab students ne pay kar diya!")
            else:
                st.warning(f"⚠️ {len(pending)} students pending — Month: {latest_month}")
                show_cols = ["RoomNo","Name","Total","Paid","Remaining"]
                st.dataframe(pending[[c for c in show_cols if c in pending.columns]],
                             use_container_width=True, hide_index=True)

    # -------- RECEIPTS --------
    with tab4:
        if payments.empty:
            st.info("Abhi koi receipt upload nahi hui.")
        else:
            st.subheader(f"📄 Total Receipts: {len(payments)}")
            for i, row in payments.iterrows():
                st.markdown(f"""
                <div style="background:#f8f9fb;border-radius:8px;padding:10px 14px;
                            border-left:4px solid #4CAF50;margin-bottom:8px;">
                🏠 <b>Room:</b> {row['RoomNo']} &nbsp;|&nbsp;
                👤 <b>Name:</b> {row['Name']} &nbsp;|&nbsp;
                💰 <b>Amount:</b> Rs {row.get('Amount_Paid','')} &nbsp;|&nbsp;
                📅 <b>Date:</b> {row.get('Submission_Date','')}
                </div>
                """, unsafe_allow_html=True)

                path = str(row.get("Receipt_File", ""))
                if path and os.path.exists(path):
                    ext = path.lower()
                    if ext.endswith((".png", ".jpg", ".jpeg")):
                        st.image(path, width=220)
                    with open(path, "rb") as fp:
                        st.download_button("⬇️ Download Receipt", fp,
                                           file_name=os.path.basename(path),
                                           key=f"dl_{i}")
                else:
                    st.caption("⚠️ File server pe available nahi (cloud restart issue)")

    # -------- MANAGE MONTHS --------
    with tab5:
        if dues.empty:
            st.info("Koi month available nahi.")
        else:
            month_list   = sorted(dues["Month"].unique(), reverse=True)
            month_to_del = st.selectbox("Month Select Karo", month_list, key="del_month")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Is Month ko Delete Karo", type="primary"):
                    new_dues = dues[dues["Month"] != month_to_del]
                    save_dues(new_dues, hall)
                    pay_df = payments
                    if not pay_df.empty and "Month" in pay_df.columns:
                        save_payments(pay_df[pay_df["Month"] != month_to_del], hall)
                    st.success(f"✅ '{month_to_del}' ka dues + receipts delete ho gaye!")
                    st.rerun()
            with col2:
                st.info("💡 Update ke liye same month dobara Upload tab se upload karo.")


# ==========================================
# ============= SENIOR WARDEN =============
# ==========================================
elif role == "Senior Warden":

    pw = st.sidebar.text_input("Senior Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.warning("❌ Wrong Password")
        st.stop()

    st.header("👨‍💼 Senior Warden Dashboard — Sab 9 Halls")

    # EK HI BAAR sara data load karo — sab halls ka
    all_data = load_all_sheets_data()

    # Sab available months collect karo (cache se — no extra API calls)
    all_months = set()
    for h in halls:
        hd = get_dues_from_cache(all_data, h)
        if not hd.empty and "Month" in hd.columns:
            for m in hd["Month"].unique():
                if m and m != "Unknown":
                    all_months.add(m)

    all_months_sorted = sorted(all_months, reverse=True)

    # Month filter — session state se stable rakho
    month_options = ["Sab Months (Combined)"] + all_months_sorted

    # Session state mein store karo taake page rerun pe reset na ho
    if "warden_selected_month" not in st.session_state:
        st.session_state["warden_selected_month"] = "Sab Months (Combined)"

    # Agar stored value options mein nahi hai to reset
    if st.session_state["warden_selected_month"] not in month_options:
        st.session_state["warden_selected_month"] = "Sab Months (Combined)"

    selected_w_month = st.selectbox(
        "📅 Month Select Karo",
        month_options,
        index=month_options.index(st.session_state["warden_selected_month"]),
        key="warden_month_select"
    )
    # Selection update karo session state mein
    st.session_state["warden_selected_month"] = selected_w_month

    # ===== SUMMARY CALCULATE — sab cache se, 0 extra API calls =====
    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        hall_dues = get_dues_from_cache(all_data, hall)
        hall_pay  = get_payments_from_cache(all_data, hall)

        if not hall_dues.empty and "Month" in hall_dues.columns:
            if selected_w_month != "Sab Months (Combined)":
                hall_dues_f = hall_dues[hall_dues["Month"] == selected_w_month]
                hall_pay_f  = hall_pay[hall_pay["Month"] == selected_w_month] \
                              if (not hall_pay.empty and "Month" in hall_pay.columns) \
                              else pd.DataFrame()
            else:
                hall_dues_f = hall_dues
                hall_pay_f  = hall_pay

            if hall_dues_f.empty:
                summary.append({"Hall": hall, "Total (Rs)": 0,
                                 "Collected (Rs)": 0, "Remaining (Rs)": 0, "Paid %": "0%"})
                continue

            total     = int(hall_dues_f["Total"].sum())
            collected = 0

            if not hall_pay_f.empty and "Amount_Paid" in hall_pay_f.columns:
                collected = int(pd.to_numeric(hall_pay_f["Amount_Paid"], errors="coerce").fillna(0).sum())

            remaining      = total - collected
            total_all     += total
            collected_all += collected
            remaining_all += remaining

            summary.append({
                "Hall":           hall,
                "Total (Rs)":     total,
                "Collected (Rs)": collected,
                "Remaining (Rs)": remaining,
                "Paid %":         f"{int(collected/total*100) if total else 0}%"
            })
        else:
            summary.append({
                "Hall": hall, "Total (Rs)": 0,
                "Collected (Rs)": 0, "Remaining (Rs)": 0, "Paid %": "0%"
            })

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Grand Total",    f"Rs {int(total_all):,}")
    c2.metric("✅ Total Collected", f"Rs {int(collected_all):,}")
    c3.metric("⏳ Total Remaining", f"Rs {int(remaining_all):,}")

    st.markdown("---")
    st.subheader("📊 Hall-wise Summary")

    summary_df = pd.DataFrame(summary)

    def warden_highlight(row):
        if row["Remaining (Rs)"] == 0 and row["Total (Rs)"] > 0:
            return ["background-color:#c8e6c9;color:#1b5e20;font-weight:600"] * len(row)
        elif row["Remaining (Rs)"] > 0:
            return ["background-color:#fff9c4"] * len(row)
        return [""] * len(row)

    st.dataframe(
        summary_df.style.apply(warden_highlight, axis=1),
        use_container_width=True, hide_index=True
    )

    if not summary_df.empty:
        st.subheader("📈 Hall-wise Collection Chart")
        st.bar_chart(summary_df.set_index("Hall")[["Collected (Rs)", "Remaining (Rs)"]])

        st.markdown("---")
        csv_w = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download All Halls Summary (CSV)",
            data=csv_w, file_name="all_halls_summary.csv",
            mime="text/csv", key="warden_export"
        )

    # ===== PAYMENTS OVERVIEW =====
    st.markdown("---")
    st.subheader("📋 Sab Halls ki Payments Overview")

    all_pay_rows = []
    for h in halls:
        h_dues = get_dues_from_cache(all_data, h)
        h_pays = get_payments_from_cache(all_data, h)

        if not h_dues.empty and "Month" in h_dues.columns:
            months_to_show = [selected_w_month] if selected_w_month != "Sab Months (Combined)" \
                             else sorted(h_dues["Month"].unique(), reverse=True)

            for month_val in months_to_show:
                if month_val == "Unknown":
                    continue
                month_dues_f = h_dues[h_dues["Month"] == month_val]
                if month_dues_f.empty:
                    continue

                total_dues = int(month_dues_f["Total"].sum())
                students   = len(month_dues_f)
                collected  = 0
                receipts   = 0

                if not h_pays.empty and "Month" in h_pays.columns:
                    mp = h_pays[h_pays["Month"] == month_val]
                    receipts = len(mp)
                    if "Amount_Paid" in mp.columns:
                        collected = int(pd.to_numeric(mp["Amount_Paid"], errors="coerce").fillna(0).sum())

                all_pay_rows.append({
                    "Hall": h, "Month": month_val,
                    "Students": students, "Total Dues (Rs)": total_dues,
                    "Receipts": receipts, "Collected (Rs)": collected,
                    "Remaining (Rs)": max(0, total_dues - collected),
                })

    if all_pay_rows:
        all_pay_df = pd.DataFrame(all_pay_rows).sort_values(["Month","Hall"], ascending=[False,True])
        st.dataframe(all_pay_df, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi kisi bhi hall mein data upload nahi hua.")


st.markdown("---")
st.caption("🏛️ University Mess Dues System | Abdul Hadi 2025 (S) CYS 90 | Powered by Streamlit + Google Sheets")
