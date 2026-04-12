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
                f"💵 Kitna Amount Jama Karwaya? (Rs) — Room {room}",
                min_value=1,
                max_value=int(total),
                value=int(total),
                step=1,
                key=f"amt_{room}_{idx}",
                help=f"Max: Rs {int(total)} — Total dues"
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
                        remaining_after = int(total) - amount_paid
                        if remaining_after > 0:
                            st.success(f"✅ Receipt upload ho gayi! Paid: Rs {amount_paid} | Remaining: Rs {remaining_after}")
                        else:
                            st.success(f"✅ Receipt upload ho gayi! Full payment: Rs {amount_paid} ✔️")
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

            # ===== AUTO CARRY FORWARD =====
            # Pichle month ka remaining dhundo aur current upload mein add karo
            all_dues     = load_dues(hall)
            all_payments = load_payments(hall)

            if not all_dues.empty and "Month" in all_dues.columns:
                past_months = sorted([m for m in all_dues["Month"].unique() if m != month], reverse=True)

                if past_months:
                    last_month     = past_months[0]
                    last_dues      = all_dues[all_dues["Month"] == last_month].copy()
                    carry_map      = {}  # key: "RoomNo||Name" -> remaining amount

                    for _, lrow in last_dues.iterrows():
                        lroom = str(lrow["RoomNo"]).strip()
                        lname = str(lrow["Name"]).strip()
                        ltotal = float(lrow["Total"])
                        lpaid  = 0.0

                        if not all_payments.empty and "Amount_Paid" in all_payments.columns and "Month" in all_payments.columns:
                            sp = all_payments[
                                (all_payments["RoomNo"].astype(str).str.strip() == lroom) &
                                (all_payments["Name"].astype(str).str.strip() == lname) &
                                (all_payments["Month"] == last_month)
                            ]
                            lpaid = pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum()

                        remaining = max(0.0, ltotal - lpaid)
                        if remaining > 0:
                            carry_map[f"{lroom}||{lname}"] = remaining

                    # Apply carry forward to new upload
                    if carry_map:
                        carried = 0
                        for i, row2 in df.iterrows():
                            key = f"{str(row2['RoomNo']).strip()}||{str(row2['Name']).strip()}"
                            if key in carry_map:
                                df.at[i, "Previous"] = float(df.at[i, "Previous"]) + carry_map[key]
                                df.at[i, "Total"]    = float(df.at[i, "Food_Dues"]) + float(df.at[i, "Service_Charges"]) + float(df.at[i, "Previous"])
                                carried += 1

                        if carried:
                            st.info(f"🔄 {carried} student(s) ka previous remaining carry forward ho gaya ({last_month} → {month})")

            final_df = pd.concat([existing, df], ignore_index=True)
            save_dues(final_df, hall)

            # Jab naya month upload ho, us month ki purani payments bhi reset karo
            existing_pays = load_payments(hall)
            if not existing_pays.empty and "Month" in existing_pays.columns:
                cleaned_pays = existing_pays[existing_pays["Month"] != month]
                save_payments(cleaned_pays, hall)
                removed = len(existing_pays) - len(cleaned_pays)
                if removed > 0:
                    st.info(f"ℹ️ '{month}' ki {removed} purani payment(s) bhi reset ho gayi (fresh upload)")

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

            # Add Paid and Remaining columns to dashboard
            def get_paid_for_row(row):
                if not payments.empty and "Amount_Paid" in payments.columns and "Month" in payments.columns:
                    sp = payments[
                        (payments["RoomNo"].astype(str).str.strip() == str(row["RoomNo"]).strip()) &
                        (payments["Name"].astype(str).str.strip() == str(row["Name"]).strip()) &
                        (payments["Month"] == sel_month)
                    ]
                    return int(pd.to_numeric(sp["Amount_Paid"], errors="coerce").fillna(0).sum())
                return 0

            df = df.copy()
            df["Paid (Rs)"]      = df.apply(get_paid_for_row, axis=1)
            df["Remaining (Rs)"] = (df["Total"] - df["Paid (Rs)"]).clip(lower=0).astype(int)

            display_cols = ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total", "Paid (Rs)", "Remaining (Rs)"]
            st.dataframe(
                df[display_cols].style.apply(highlight_paid, axis=1),
                use_container_width=True,
                hide_index=True
            )

            if not df.empty:
                chart_df = df.set_index("RoomNo")[["Total"]].sort_index()
                st.bar_chart(chart_df)

            # Export monthly report
            st.markdown("---")
            st.subheader("📥 Monthly Report Export")
            export_df = df[["RoomNo","Name","Food_Dues","Service_Charges","Previous","Total","Paid (Rs)","Remaining (Rs)"]].copy() if "Paid (Rs)" in df.columns else df.copy()
            csv = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"⬇️ Download {sel_month} Report (CSV)",
                data=csv,
                file_name=f"{hall}_{sel_month}_report.csv",
                mime="text/csv",
                key="export_csv"
            )

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
                show_cols = ["RoomNo", "Name", "Total"]
                if "Paid" in pending.columns:
                    show_cols += ["Paid", "Remaining"]
                st.dataframe(
                    pending[show_cols],
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
                    # Delete dues
                    new_dues = dues[dues["Month"] != month_to_del]
                    save_dues(new_dues, hall)
                    # Delete payments of same month
                    pay_df = load_payments(hall)
                    if not pay_df.empty and "Month" in pay_df.columns:
                        new_pay = pay_df[pay_df["Month"] != month_to_del]
                        save_payments(new_pay, hall)
                    st.success(f"✅ '{month_to_del}' ka dues + receipts dono delete ho gaye!")
                    st.rerun()
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

    # Collect all available months across all halls
    all_months = set()
    for h in halls:
        hd = load_dues(h)
        if not hd.empty and "Month" in hd.columns:
            for m in hd["Month"].unique():
                if m and m != "Unknown":
                    all_months.add(m)

    all_months = sorted(all_months, reverse=True)

    if all_months:
        selected_w_month = st.selectbox(
            "📅 Month Select Karo",
            ["Sab Months (Combined)"] + all_months,
            key="warden_month_filter"
        )
    else:
        selected_w_month = "Sab Months (Combined)"
        st.info("Abhi koi month data available nahi.")

    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        hall_dues = load_dues(hall)
        hall_pay  = load_payments(hall)

        if not hall_dues.empty and "Month" in hall_dues.columns:
            # Filter by month if selected
            if selected_w_month != "Sab Months (Combined)":
                hall_dues_f = hall_dues[hall_dues["Month"] == selected_w_month]
                hall_pay_f  = hall_pay[hall_pay["Month"] == selected_w_month] if (not hall_pay.empty and "Month" in hall_pay.columns) else pd.DataFrame()
            else:
                hall_dues_f = hall_dues
                hall_pay_f  = hall_pay

            if hall_dues_f.empty:
                summary.append({"Hall": hall, "Month": selected_w_month,
                                 "Total (Rs)": 0, "Collected (Rs)": 0,
                                 "Remaining (Rs)": 0, "Paid %": "0%"})
                continue

            total = hall_dues_f["Total"].sum()
            collected = 0

            if not hall_pay_f.empty and "Amount_Paid" in hall_pay_f.columns:
                collected = pd.to_numeric(hall_pay_f["Amount_Paid"], errors="coerce").fillna(0).sum()
            elif not hall_pay_f.empty:
                paid_rooms = hall_pay_f["RoomNo"].astype(str).str.strip().unique()
                collected  = hall_dues_f[hall_dues_f["RoomNo"].str.strip().isin(paid_rooms)]["Total"].sum()

            remaining = total - collected

            total_all     += total
            collected_all += collected
            remaining_all += remaining

            summary.append({
                "Hall":           hall,
                "Month":          selected_w_month,
                "Total (Rs)":     int(total),
                "Collected (Rs)": int(collected),
                "Remaining (Rs)": int(remaining),
                "Paid %":         f"{int(collected/total*100) if total else 0}%"
            })
        else:
            summary.append({
                "Hall":           hall,
                "Month":          selected_w_month,
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
        st.subheader("📥 Full Summary Export")
        csv_w = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download All Halls Summary (CSV)",
            data=csv_w,
            file_name="all_halls_summary.csv",
            mime="text/csv",
            key="warden_export"
        )

    # ===== MANAGE ALL HALLS =====
    st.markdown("---")
    st.subheader("🗑️ Kisi Bhi Hall ka Month Delete Karo")

    del_col1, del_col2 = st.columns(2)
    with del_col1:
        del_hall = st.selectbox("Hall Select Karo", halls, key="warden_del_hall")
    with del_col2:
        hall_dues_for_del = load_dues(del_hall)
        if not hall_dues_for_del.empty and "Month" in hall_dues_for_del.columns:
            available_months = sorted(hall_dues_for_del["Month"].unique(), reverse=True)
            del_month = st.selectbox("Month Select Karo", available_months, key="warden_del_month")
        else:
            del_month = None
            st.info("Is hall mein koi data nahi.")

    if del_month:
        st.warning(f"⚠️ {del_hall} — '{del_month}' ka dues + payments data delete hoga.")
        if st.button("🗑️ Delete Karo", type="primary", key="warden_delete_btn"):
            # Delete dues
            new_dues = hall_dues_for_del[hall_dues_for_del["Month"] != del_month]
            save_dues(new_dues, del_hall)
            # Delete payments
            hall_pay_for_del = load_payments(del_hall)
            if not hall_pay_for_del.empty and "Month" in hall_pay_for_del.columns:
                new_pay = hall_pay_for_del[hall_pay_for_del["Month"] != del_month]
                save_payments(new_pay, del_hall)
            st.success(f"✅ {del_hall} — '{del_month}' ka pura data delete ho gaya!")

    # ===== ALL HALLS PAYMENTS OVERVIEW =====
    st.markdown("---")
    st.subheader("📋 Sab Halls ki Payments Overview")

    all_pay_rows = []
    for h in halls:
        hp = load_payments(h)
        if not hp.empty and "Month" in hp.columns:
            for month_val in hp["Month"].unique():
                mp = hp[hp["Month"] == month_val]
                total_col = pd.to_numeric(mp.get("Amount_Paid", pd.Series([0])), errors="coerce").fillna(0).sum()
                all_pay_rows.append({
                    "Hall": h,
                    "Month": month_val,
                    "Receipts": len(mp),
                    "Amount Collected (Rs)": int(total_col)
                })

    if all_pay_rows:
        all_pay_df = pd.DataFrame(all_pay_rows).sort_values(["Hall", "Month"])
        st.dataframe(all_pay_df, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi koi hall ki payments record nahi hain.")

st.markdown("---")
st.caption("🏛️ University Mess Dues System | Abdul Hadi 2025 (S) CYS 90 | Powered by Streamlit + Google Sheets")
