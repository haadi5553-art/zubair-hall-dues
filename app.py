import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

st.set_page_config(page_title="University Mess Dues System", layout="wide")

def get_google_sheet():
    creds_dict = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(credentials)
    return gc

def load_dues(hall_name):
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet(hall_name)
        df = pd.DataFrame(sheet.get_all_records())
        numeric_cols = ["Food_Dues", "Service_Charges", "Previous", "Total"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"])

def save_dues(df, hall_name):
    gc = get_google_sheet()
    sheet = gc.open("Hostel Dues Data").worksheet(hall_name)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

def load_payments(hall_name):
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet(f"{hall_name}_Payments")
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Phone", "Submission_Date", "Receipt_File"])

def save_payments(df, hall_name):
    gc = get_google_sheet()
    sheet = gc.open("Hostel Dues Data").worksheet(f"{hall_name}_Payments")
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ====================== HALLS ======================
halls = ["SMG Hall", "MBQ Hall", "EIDHI Hall", "ZUBAIR Hall", "MUMTAZ Hall", 
         "LIAQUAT Hall", "QUAID AZAM Hall", "IQBAL Hall", "SIR SYED Hall"]

hall_passwords = {
    "SMG Hall": "smg123", "MBQ Hall": "mbq456", "EIDHI Hall": "eidhi789",
    "ZUBAIR Hall": "zubair012", "MUMTAZ Hall": "mumtaz345", "LIAQUAT Hall": "liaquat678",
    "QUAID AZAM Hall": "quaid901", "IQBAL Hall": "iqbal234", "SIR SYED Hall": "syed567"
}

senior_password = "senior@1122"

st.title("🏛️ University Mess Dues Management System")
st.caption("**Made by Abdul Hadi 2025 (S) CYS 90**")

role = st.sidebar.selectbox("Select Role", ["Student", "Hall Admin", "Senior Warden"])

# ====================== SENIOR WARDEN ======================
if role == "Senior Warden":
    pw = st.sidebar.text_input("Senior Warden Password", type="password")
    if pw != senior_password:
        st.sidebar.warning("Wrong Password")
        st.stop()

    st.header("👨‍💼 Senior Warden Dashboard - All 9 Halls")
    
    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        dues = load_dues(hall)
        if not dues.empty:
            total = dues["Total"].sum()
            payments = load_payments(hall)
            collected = dues[dues["RoomNo"].isin(payments["RoomNo"])]["Total"].sum() if not payments.empty and "RoomNo" in payments.columns else 0
            remaining = total - collected
            total_all += total
            collected_all += collected
            remaining_all += remaining
            summary.append({"Hall": hall, "Total": total, "Collected": collected, "Remaining": remaining})

    col1, col2, col3 = st.columns(3)
    col1.metric("Grand Total (All Halls)", f"₹ {total_all:,.0f}")
    col2.metric("Total Collected", f"₹ {collected_all:,.0f}")
    col3.metric("Total Remaining", f"₹ {remaining_all:,.0f}")

    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

# ====================== HALL ADMIN ======================
elif role == "Hall Admin":
    hall_name = st.sidebar.selectbox("Select Your Hall", halls)
    pw = st.sidebar.text_input("Hall Admin Password", type="password")
    
    if pw != hall_passwords.get(hall_name):
        st.sidebar.warning("Wrong Password")
        st.stop()

    st.header(f"🏠 {hall_name} Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Dues", "📊 Dashboard", "⏳ Pending", "🗑️ Delete Month"])

    with tab1:
        st.subheader("Upload New Month Dues")
        month = st.text_input("Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
        uploaded = st.file_uploader("Excel/CSV File", type=["csv", "xlsx"])
        
        if uploaded and st.button("Upload Dues"):
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            
            df = df.rename(columns={"Room No": "RoomNo", "room no": "RoomNo", "Roomno": "RoomNo",
                                    "Name": "Name", "name": "Name",
                                    "Food Dues": "Food_Dues", "food dues": "Food_Dues",
                                    "Service Charges": "Service_Charges", "service charges": "Service_Charges",
                                    "Previous": "Previous", "previous": "Previous"})
            
            for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
                if col not in df.columns:
                    df[col] = 0 if col in ["Food_Dues", "Service_Charges", "Previous"] else ""
            
            df["Month"] = month
            df["Total"] = (pd.to_numeric(df.get("Food_Dues", 0), errors='coerce').fillna(0) +
                           pd.to_numeric(df.get("Service_Charges", 0), errors='coerce').fillna(0) +
                           pd.to_numeric(df.get("Previous", 0), errors='coerce').fillna(0))
            
            existing = load_dues(hall_name)
            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]
            new_df = pd.concat([existing, df], ignore_index=True)
            save_dues(new_df, hall_name)
            st.success(f"✅ {len(df)} students uploaded for {month} in {hall_name}")

    with tab2:
        st.subheader("Monthly Dashboard")
        dues = load_dues(hall_name)
        if not dues.empty:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected = st.selectbox("Select Month", month_list)
            month_dues = dues[dues["Month"] == selected]
            payments = load_payments(hall_name)
            
            total = month_dues["Total"].sum()
            collected = month_dues[month_dues["RoomNo"].isin(payments["RoomNo"])]["Total"].sum() if not payments.empty else 0
            st.metric("Total Dues", f"₹ {total:,.0f}")
            st.metric("Collected", f"₹ {collected:,.0f}")
            st.metric("Remaining", f"₹ {total-collected:,.0f}")
            st.dataframe(month_dues, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Pending Dues")
        dues = load_dues(hall_name)
        payments = load_payments(hall_name)
        if not dues.empty:
            merged = dues.merge(payments[["Month", "RoomNo", "Submission_Date"]] if not payments.empty else pd.DataFrame(), 
                              on=["Month", "RoomNo"], how="left")
            pending = merged[pd.isna(merged.get("Submission_Date"))].copy()
            if pending.empty:
                st.success("All Paid!")
            else:
                st.dataframe(pending[["RoomNo", "Name", "Total"]], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("🗑️ Delete Monthly List")
        dues = load_dues(hall_name)
        if not dues.empty:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            month_to_delete = st.selectbox("Select Month to Delete", month_list)
            if st.button("Delete This Month List", type="primary"):
                new_dues = dues[dues["Month"] != month_to_delete]
                save_dues(new_dues, hall_name)
                st.success(f"{month_to_delete} ki list delete ho gayi!")

else:  # Student
    st.header("Apni Mess Dues Receipt Submit Karo")
    hall_name = st.sidebar.selectbox("Select Your Hall", halls)
    dues = load_dues(hall_name)
    if dues.empty:
        st.error(f"{hall_name} mein abhi dues upload nahi hue.")
        st.stop()
    
    month_list = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Month select karo", month_list)
    room_input = st.text_input("Apna Room Number daalo")
    
    if room_input:
        student_df = dues[(dues["Month"] == selected_month) & 
                         (dues["RoomNo"].astype(str).str.strip() == str(room_input).strip())]
        if student_df.empty:
            st.error("Room Number nahi mila.")
        else:
            student = student_df.iloc[0]
            st.success(f"**Room No:** {student.get('RoomNo')}")
            st.success(f"**Name:** {student.get('Name')}")
            st.info(f"**Food Dues:** ₹ {student.get('Food_Dues',0)}")
            st.info(f"**Service Charges:** ₹ {student.get('Service_Charges',0)}")
            st.info(f"**Previous:** ₹ {student.get('Previous',0)}")
            st.info(f"**Total:** ₹ {student.get('Total',0)}")
            
            if st.button("✅ Submit Receipt"):
                st.success("Receipt submit ho gaya!")

st.caption("University Mess Dues System • 9 Halls • Senior Warden Access")
