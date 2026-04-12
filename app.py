import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os

st.set_page_config(page_title="University Mess Dues System", layout="wide", page_icon="🏛️")

# ================= STYLE =================
st.markdown("""
<style>
/* Sidebar */
[data-testid="stSidebar"] {background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);}
[data-testid="stSidebar"] * {color: #eee !important;}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #4CAF50, #2e7d32);
    color: white !important;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 0.4rem 1.2rem;
    transition: 0.2s;
}
.stButton>button:hover {opacity: 0.85;}

/* Title */
h1 {color: #1a1a2e; font-size: 2rem;}

/* Cards */
.student-card {
    padding: 14px 18px;
    background: #f8f9fb;
    border-left: 5px solid #4CAF50;
    border-radius: 10px;
    margin-bottom: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.paid-card {border-left-color: #388e3c; background: #e8f5e9;}

/* Metrics */
[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}

/* Tabs */
.stTabs [data-baseweb="tab"] {font-weight: 600; font-size: 0.95rem;}

.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)


# ================= GOOGLE SHEET =================
@st.cache_resource(ttl=300)
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

@st.cache_resource(ttl=300)
def get_spreadsheet():
    return get_gspread_client().open("Hostel Dues Data")

def get_google_sheet():
    return get_gspread_client()


# ================= STANDARDIZE COLUMNS =================
def standardize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    column_map = {
        "room no": "RoomNo",
        "roomno": "RoomNo",
        "room no.": "RoomNo",
        "room": "RoomNo",
        "room_no": "RoomNo",
        "name": "Name",
        "student name": "Name",
        "student_name": "Name",
        "food dues": "Food_Dues",
        "food_dues": "Food_Dues",
        "fooddues": "Food_Dues",
        "service charges": "Service_Charges",
        "service_charges": "Service_Charges",
        "servicecharges": "Service_Charges",
        "previous": "Previous",
        "prev": "Previous",
        "arrears": "Previous",
    }
    df = df.rename(columns=column_map)

    # Also map month column (lowercase)
    if "month" in df.columns and "Month" not in df.columns:
        df = df.rename(columns={"month": "Month"})

    for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
        if col not in df.columns:
            df[col] = "" if col in ["RoomNo", "Name"] else 0

    return df


# ================= LOAD / SAVE DUES =================
def load_dues(hall):
    try:
        sheet = get_spreadsheet().worksheet(hall)
        df = pd.DataFrame(sheet.get_all_records())

        if df.empty:
            return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])

        df = standardize_columns(df)

        # Ensure Month column exists
        if "Month" not in df.columns:
            df["Month"] = "Unknown"
        df["Month"] = df["Month"].astype(str).str.strip()

        for col in ["Food_Dues", "Service_Charges", "Previous"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
        df["Name"]   = df["Name"].astype(str).str.strip()
        df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]

        return df
    except Exception as e:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])


def clean_for_sheets(df):
    """Convert all values to JSON-safe Python native types."""
    import numpy as np
    df = df.copy()
    df = df.fillna("")
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: int(x) if isinstance(x, (np.integer,)) else
                      float(x) if isinstance(x, (np.floating,)) else
                      bool(x) if isinstance(x, (np.bool_,)) else
                      str(x) if not isinstance(x, (str, int, float, bool)) else x
        )
    return df


def save_dues(df, hall):
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(hall)
    except Exception:
        ws = sh.add_worksheet(title=hall, rows=5000, cols=20)
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    get_spreadsheet.clear()  # clear cache after write


# ================= LOAD / SAVE PAYMENTS =================
def load_payments(hall):
    try:
        sheet = get_spreadsheet().worksheet(f"{hall}_Payments")
        return pd.DataFrame(sheet.get_all_records())
    except Exception:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Amount_Paid","Submission_Date","Receipt_File","File_Hash"])


def save_payments(df, hall):
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(f"{hall}_Payments")
    except Exception:
        ws = sh.add_worksheet(title=f"{hall}_Payments", rows=5000, cols=20)
    ws.clear()
    df = clean_for_sheets(df)
    ws.update([df.columns.values.tolist()] + df.values.tolist())


# ================= RECEIPT FOLDER =================
if not os.path.exists("receipts"):
    os.makedirs("receipts")


# ================= HALLS & PASSWORDS =================
halls = [
    "SMG Hall", "MBQ Hall", "EIDHI Hall", "ZUBAIR Hall", "MUMTAZ Hall",
    "LIAQUAT Hall", "QUAID AZAM Hall", "IQBAL Hall", "SIR SYED Hall"
]

hall_passwords = {
    "SMG Hall":       "smg123",
    "MBQ Hall":       "mbq456",
    "EIDHI Hall":     "eidhi789",
    "ZUBAIR Hall":    "zubair012",
    "MUMTAZ Hall":    "mumtaz345",
    "LIAQUAT Hall":   "liaquat678",
    "QUAID AZAM Hall":"quaid901",
    "IQBAL Hall":     "iqbal234",
    "SIR SYED Hall":  "syed567",
}

senior_password = "senior@1122"


# ================= HEADER =================
st.title("🏛️ University Mess Dues Management System")
st.caption("Made by Abdul Hadi 2025 (S) CYS 90")

role = st.sidebar.selectbox("Select Role", ["Student", "Hall Admin", "Senior Warden"])


# ==========================================
# ================== STUDENT ==============
# ==========================================
if role == "Student":

    hall = st.sidebar.selectbox("Select Hall", halls)
    dues = load_dues(hall)

    if dues.empty:
        st.warning(f"⚠️ {hall} mein abhi koi dues upload nahi hue.")
        st.stop()

    month_list = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("📅 Month Select Karo", month_list)

    month_dues = dues[dues["Month"] == selected_month].sort_values("RoomNo")
    payments = load_payments(hall)
    if not payments.empty and "Month" in payments.columns:
        month_pays = payments[payments["Month"] == selected_month].copy()
        month_pays["_key"] = month_pays["RoomNo"].astype(str).str.strip() + "||" + month_pays["Name"].astype(str).str.strip()
        paid_keys = month_pays["_key"].values
    else:
        paid_keys = []

    st.subheader(f"📋 {hall} — {selected_month} — Sab Students ki Dues")
    st.markdown("---")

    for idx, row in month_dues.iterrows():
        room = str(row["RoomNo"]).strip()
        name = str(row["Name"]).strip()
        total = row["Total"]
        student_key = room + "||" + name
        is_paid = student_key in paid_keys

        # Calculate actual paid amount and remaining for this student+month
        if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
            student_pays = payments[
                (payments["RoomNo"].astype(str).str.strip() == room) &
                (payments["Name"].astype(str).str.strip() == name) &
                (payments["Month"] == selected_month)
            ]
            paid_amount = pd.to_numeric(student_pays["Amount_Paid"], errors="coerce").fillna(0).sum()
        else:
            paid_amount = 0

        remaining_amount = max(0, total - paid_amount)
        is_fully_paid  = paid_amount >= total
        is_partial     = 0 < paid_amount < total

        if is_fully_paid:
            bg, border = "#e8f5e9", "#388e3c"
            paid_badge, paid_color = "✅ FULLY PAID", "green"
        elif is_partial:
            bg, border = "#fff8e1", "#f9a825"
            paid_badge, paid_color = f"⚠️ PARTIAL (Paid: Rs {int(paid_amount)} | Remaining: Rs {int(remaining_amount)})", "darkorange"
        else:
            bg, border = "#f8f9fb", "#4CAF50"
            paid_badge, paid_color = "⏳ Unpaid", "orange"

        is_paid = is_fully_paid  # for expander logic

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
            amount_paid = st.number_input(
                f"Amount Jo Pay Kiya (Rs) — Room {room}",
                min_value=0, max_value=int(total)+10000,
                value=int(total),
                step=1,
                key=f"amt_{room}_{idx}"
            )

            if uploaded_files:
                if st.button(f"✅ Submit Receipt(s) — Room {room}", key=f"submit_{room}_{idx}"):
                    current_payments = load_payments(hall)
                    added = 0
                    errors = []

                    for f in uploaded_files:
                        file_bytes = f.getvalue()
                        file_hash  = hashlib.md5(file_bytes).hexdigest()
                        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        today_str  = datetime.now().strftime("%Y-%m-%d")

                        # Duplicate check: same hash + same student
                        if not current_payments.empty and "File_Hash" in current_payments.columns:
                            dup = current_payments[
                                (current_payments["RoomNo"].astype(str).str.strip() == room) &
                                (current_payments["Name"].astype(str).str.strip() == name) &
                                (current_payments["Month"] == selected_month) &
                                (current_payments["File_Hash"] == file_hash)
                            ]
                            if not dup.empty:
                                errors.append(f"❌ '{f.name}' — same receipt pehle already upload ho chuki hai!")
                                continue

                        # Save file
                        save_path = f"receipts/{uuid.uuid4()}_{f.name}"
                        with open(save_path, "wb") as fp:
                            fp.write(file_bytes)

                        new_row = pd.DataFrame([{
                            "Month":            selected_month,
                            "RoomNo":           room,
                            "Name":             name,
                            "Amount_Paid":      amount_paid,
                            "Submission_Date":  now_str,
                            "Receipt_File":     save_path,
                            "File_Hash":        file_hash
                        }])

                        current_payments = pd.concat([current_payments, new_row], ignore_index=True)
                        added += 1

                    save_payments(current_payments, hall)

                    if added:
                        st.success(f"✅ {added} receipt(s) upload ho gayi! Amount: Rs {amount_paid}")
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

    dues     = load_dues(hall)
    payments = load_payments(hall)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload Dues",
        "📊 Dashboard",
        "⏳ Pending",
        "📄 Receipts",
        "🗑️ Manage Months"
    ])

    # -------- UPLOAD DUES --------
    with tab1:
        st.subheader("New Month Dues Upload")
        years  = list(range(2025, 2032))
        months = [f"{y}-{m:02d}" for y in years for m in range(1, 13)]
        month  = st.selectbox("Month (YYYY-MM)", months,
                              index=months.index(datetime.now().strftime("%Y-%m")))

        uploaded = st.file_uploader("Excel / CSV File Upload Karo", type=["csv", "xlsx"])

        if uploaded and st.button("📤 Upload Karo"):
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            # Remove duplicate columns
            df = df.loc[:, ~df.columns.duplicated()]
            df = standardize_columns(df)

            for col in ["Food_Dues", "Service_Charges", "Previous"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            df["RoomNo"] = df["RoomNo"].astype(str).str.strip()
            df["Name"]   = df["Name"].astype(str).str.strip()
            df["Month"]  = month  # Always use admin-selected month (overwrite any existing)
            df["Total"]  = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]

            # Keep only needed columns
            keep_cols = ["Month", "RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]
            df = df[[c for c in keep_cols if c in df.columns]]

            existing = load_dues(hall)
            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]

            # Align columns before concat
            for c in keep_cols:
                if c not in existing.columns:
                    existing[c] = ""
                if c not in df.columns:
                    df[c] = ""

            existing = existing[keep_cols]
            df       = df[keep_cols]

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)
            st.success(f"✅ {len(df)} students ka data '{month}' ke liye upload ho gaya!")

    # -------- DASHBOARD --------
    with tab2:
        if dues.empty:
            st.info("Abhi koi data upload nahi hua.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            sel_month  = st.selectbox("Month Select Karo", month_list, key="dash_month")
            df = dues[dues["Month"] == sel_month].copy()

            search = st.text_input("🔍 Search by Room No or Name")
            if search:
                df = df[
                    df["RoomNo"].str.contains(search, case=False) |
                    df["Name"].str.contains(search, case=False)
                ]

            paid_rooms = payments["RoomNo"].astype(str).str.strip().unique() if not payments.empty else []

            total_dues = df["Total"].sum()

            # Collected = actual Amount_Paid sum for this month
            if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                month_pays = payments[payments["Month"] == sel_month]
                collected  = pd.to_numeric(month_pays["Amount_Paid"], errors="coerce").fillna(0).sum()
            else:
                collected = 0
            remaining  = total_dues - collected

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Total Dues",  f"Rs {int(total_dues):,}")
            c2.metric("✅ Collected",   f"Rs {int(collected):,}")
            c3.metric("⏳ Remaining",   f"Rs {int(remaining):,}")

            def highlight_paid(row):
                room_no  = str(row["RoomNo"]).strip()
                row_name = str(row["Name"]).strip()
                if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                    sp = payments[
                        (payments["RoomNo"].astype(str).str.strip() == room_no) &
                        (payments["Name"].astype(str).str.strip() == row_name) &
                        (payments["Month"] == sel_month)
                    ]
                    paid_amt = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    if paid_amt >= row["Total"]:
                        return ["background-color: #c8e6c9; color: #1b5e20; font-weight:600"] * len(row)
                    elif paid_amt > 0:
                        return ["background-color: #fff9c4; color: #5d4037; font-weight:600"] * len(row)
                return [""] * len(row)

            display_cols = ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]
            st.dataframe(
                df[display_cols].style.apply(highlight_paid, axis=1),
                use_container_width=True,
                hide_index=True
            )

            if not df.empty:
                chart_df = df.set_index("RoomNo")[["Total"]].sort_index()
                st.bar_chart(chart_df)

    # -------- PENDING --------
    with tab3:
        if dues.empty:
            st.info("Koi data nahi.")
        else:
            if not payments.empty and "Month" in payments.columns:
                latest_month = sorted(dues["Month"].unique(), reverse=True)[0]
                month_p = payments[payments["Month"] == latest_month].copy()
                month_p["_key"] = month_p["RoomNo"].astype(str).str.strip() + "||" + month_p["Name"].astype(str).str.strip()
                paid_keys_pending = month_p["_key"].values
                latest_dues = dues[dues["Month"] == latest_month].copy()
                latest_dues["_key"] = latest_dues["RoomNo"].astype(str).str.strip() + "||" + latest_dues["Name"].astype(str).str.strip()

                # Partial or unpaid = pending
                def get_paid_amt(row):
                    sp = month_p[month_p["_key"] == row["_key"]]
                    if "Amount_Paid" in sp.columns and not sp.empty:
                        return pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()
                    return 0

                latest_dues["Paid"] = latest_dues.apply(get_paid_amt, axis=1)
                latest_dues["Remaining"] = latest_dues["Total"] - latest_dues["Paid"]
                pending = latest_dues[latest_dues["Remaining"] > 0].drop(columns=["_key"])
            else:
                pending = dues.copy()
                pending["Paid"] = 0
                pending["Remaining"] = pending["Total"]

            if pending.empty:
                st.success("🎉 Sab students ne pay kar diya!")
            else:
                st.warning(f"⚠️ {len(pending)} students abhi pending hain")
                st.dataframe(
                    pending[["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]],
                    use_container_width=True,
                    hide_index=True
                )

    # -------- RECEIPTS --------
    with tab4:
        if payments.empty:
            st.info("Abhi koi receipt upload nahi hui.")
        else:
            st.subheader(f"📄 Total Receipts: {len(payments)}")
            for _, row in payments.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background:#f8f9fb;border-radius:8px;padding:10px 14px;
                                border-left:4px solid #4CAF50;margin-bottom:8px;">
                    🏠 <b>Room:</b> {row['RoomNo']} &nbsp;|&nbsp;
                    👤 <b>Name:</b> {row['Name']} &nbsp;|&nbsp;
                    📅 <b>Date:</b> {row['Submission_Date']}
                    </div>
                    """, unsafe_allow_html=True)

                    path = row.get("Receipt_File", "")
                    if path and os.path.exists(path):
                        ext = path.lower()
                        if ext.endswith((".png", ".jpg", ".jpeg")):
                            st.image(path, width=220)
                        elif ext.endswith(".pdf"):
                            st.caption("📕 PDF receipt")

                        with open(path, "rb") as fp:
                            st.download_button(
                                "⬇️ Download Receipt",
                                fp,
                                file_name=os.path.basename(path),
                                key=f"dl_{row['RoomNo']}_{_}"
                            )
                    else:
                        st.caption("⚠️ File server pe available nahi (cloud deploy issue)")

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
                    st.success(f"✅ '{month_to_del}' ka pura data delete ho gaya!")
            with col2:
                st.info("💡 Update karne ke liye same month dobara Upload Dues tab se upload karo.")


# ==========================================
# ============= SENIOR WARDEN =============
# ==========================================
elif role == "Senior Warden":

    pw = st.sidebar.text_input("Senior Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.warning("❌ Wrong Password")
        st.stop()

    st.header("👨‍💼 Senior Warden Dashboard — Sab 9 Halls")

    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        hall_dues = load_dues(hall)
        hall_pay  = load_payments(hall)

        if not hall_dues.empty:
            total = hall_dues["Total"].sum()
            collected = 0

            if not hall_pay.empty and "Amount_Paid" in hall_pay.columns:
                collected = pd.to_numeric(hall_pay["Amount_Paid"], errors="coerce").fillna(0).sum()
            elif not hall_pay.empty:
                paid_rooms = hall_pay["RoomNo"].astype(str).str.strip().unique()
                collected  = hall_dues[hall_dues["RoomNo"].str.strip().isin(paid_rooms)]["Total"].sum()

            remaining = total - collected

            total_all     += total
            collected_all += collected
            remaining_all += remaining

            summary.append({
                "Hall":      hall,
                "Total (Rs)":     int(total),
                "Collected (Rs)": int(collected),
                "Remaining (Rs)": int(remaining),
                "Paid %":  f"{int(collected/total*100) if total else 0}%"
            })
        else:
            summary.append({
                "Hall":           hall,
                "Total (Rs)":     0,
                "Collected (Rs)": 0,
                "Remaining (Rs)": 0,
                "Paid %":         "0%"
            })

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Grand Total (All Halls)", f"Rs {int(total_all):,}")
    c2.metric("✅ Total Collected",         f"Rs {int(collected_all):,}")
    c3.metric("⏳ Total Remaining",         f"Rs {int(remaining_all):,}")

    st.markdown("---")
    st.subheader("📊 Hall-wise Summary")

    summary_df = pd.DataFrame(summary)

    def warden_highlight(row):
        remaining = row["Remaining (Rs)"]
        if remaining == 0:
            return ["background-color: #c8e6c9; color: #1b5e20; font-weight:600"] * len(row)
        elif remaining > 0:
            return ["background-color: #fff9c4"] * len(row)
        return [""] * len(row)

    st.dataframe(
        summary_df.style.apply(warden_highlight, axis=1),
        use_container_width=True,
        hide_index=True
    )

    if not summary_df.empty:
        st.subheader("📈 Hall-wise Collection Chart")
        chart_data = summary_df.set_index("Hall")[["Collected (Rs)", "Remaining (Rs)"]]
        st.bar_chart(chart_data)

st.markdown("---")
st.caption("🏛️ University Mess Dues System | Abdul Hadi 2025 (S) CYS 90 | Powered by Streamlit + Google Sheets")
