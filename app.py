import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

st.set_page_config(page_title="University Mess Dues System", layout="wide", page_icon="🏛️")

def get_google_sheet():
    creds_dict = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(credentials)

# ====================== STRONG CASE INSENSITIVE STANDARDIZER ======================
def standardize_columns(df):
    df = df.rename(columns=str.strip)
    column_map = {
        "room no": "RoomNo", "roomno": "RoomNo", "room no.": "RoomNo", "ROOM NO": "RoomNo",
        "name": "Name", "NAME": "Name",
        "food dues": "Food_Dues", "food_dues": "Food_Dues", "FOOD DUES": "Food_Dues",
        "service charges": "Service_Charges", "service_charges": "Service_Charges", "SERVICE CHARGES": "Service_Charges",
        "previous": "Previous", "PREVIOUS": "Previous"
    }
    df = df.rename(columns=column_map)
    return df

def load_dues(hall_name):
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet(hall_name)
        df = pd.DataFrame(sheet.get_all_records())
        df = standardize_columns(df)
        
        numeric_cols = ["Food_Dues", "Service_Charges", "Previous", "Total"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if "Total" not in df.columns and {"Food_Dues", "Service_Charges", "Previous"}.issubset(df.columns):
            df["Total"] = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]
        return df
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"])

def save_dues(df, hall_name):
    gc = get_google_sheet()
    spreadsheet = gc.open("Hostel Dues Data")
    try:
        sheet = spreadsheet.worksheet(hall_name)
    except:
        sheet = spreadsheet.add_worksheet(title=hall_name, rows=5000, cols=20)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

def load_payments(hall_name):
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet(f"{hall_name}_Payments")
        return pd.DataFrame(sheet.get_all_records())
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Phone", "Submission_Date", "Receipt_File"])

def save_payments(df, hall_name):
    gc = get_google_sheet()
    spreadsheet = gc.open("Hostel Dues Data")
    try:
        sheet = spreadsheet.worksheet(f"{hall_name}_Payments")
    except:
        sheet = spreadsheet.add_worksheet(title=f"{hall_name}_Payments", rows=5000, cols=20)
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

# ====================== HALL ADMIN ======================
if role == "Hall Admin":
    hall_name = st.sidebar.selectbox("Select Your Hall", halls)
    if st.sidebar.text_input("Hall Admin Password", type="password") != hall_passwords.get(hall_name):
        st.sidebar.warning("Wrong Password")
        st.stop()

    st.header(f"🏠 {hall_name} Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Dues", "📊 Dashboard", "⏳ Pending", "🗑️ Manage Months"])

    with tab1:
        st.subheader("Upload New Month Dues")
        years = list(range(2025, 2031))
        months = [f"{y}-{m:02d}" for y in years for m in range(1,13)]
        month = st.selectbox("Month (YYYY-MM)", months, index=months.index(datetime.now().strftime("%Y-%m")))
        
        uploaded = st.file_uploader("Excel/CSV File", type=["csv", "xlsx"])
        if uploaded and st.button("Upload Dues List"):
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            
            df = standardize_columns(df)
            
            for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
                if col not in df.columns:
                    df[col] = 0 if col in ["Food_Dues", "Service_Charges", "Previous"] else ""
            
            df["Month"] = month
            if "Total" not in df.columns:
                df["Total"] = df.get("Food_Dues", 0) + df.get("Service_Charges", 0) + df.get("Previous", 0)
            
            existing = load_dues(hall_name)
            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]
            new_df = pd.concat([existing, df], ignore_index=True)
            save_dues(new_df, hall_name)
            st.success(f"✅ {len(df)} students ka data {month} ke liye upload ho gaya!")

    with tab2:
        st.subheader("Monthly Dashboard")
        dues = load_dues(hall_name)
        if dues.empty:
            st.info("Abhi koi data upload nahi hua.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected = st.selectbox("Select Month", month_list)
            month_dues = dues[dues["Month"] == selected]
            payments = load_payments(hall_name)
            
            total = month_dues["Total"].sum()
            collected = 0
            if not payments.empty and "RoomNo" in payments.columns:
                collected = month_dues[month_dues["RoomNo"].isin(payments["RoomNo"])]["Total"].sum()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Dues", f"Rs {total:,.0f}")
            col2.metric("Collected", f"Rs {collected:,.0f}")
            col3.metric("Remaining", f"Rs {total-collected:,.0f}")
            
            st.dataframe(month_dues[["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]], 
                        use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("⏳ Pending Dues")
        dues = load_dues(hall_name)
        payments = load_payments(hall_name)
        if dues.empty:
            st.info("No data yet.")
        else:
            pay_df = payments[["Month", "RoomNo", "Submission_Date"]] if not payments.empty else pd.DataFrame(columns=["Month", "RoomNo", "Submission_Date"])
            merged = dues.merge(pay_df, on=["Month", "RoomNo"], how="left")
            pending = merged[pd.isna(merged.get("Submission_Date"))].copy()
            if pending.empty:
                st.success("All students have paid!")
            else:
                st.dataframe(pending[["RoomNo", "Name", "Total"]], use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("🗑️ Manage Months (Delete / Update)")
        dues = load_dues(hall_name)
        if dues.empty:
            st.info("No months available.")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            month_to_manage = st.selectbox("Select Month to Manage", month_list)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Delete This Month", type="primary"):
                    new_dues = dues[dues["Month"] != month_to_manage]
                    save_dues(new_dues, hall_name)
                    st.success(f"{month_to_manage} ki puri list delete ho gayi!")
            with col2:
                st.info("To update: Simply upload new Excel with same month. It will replace old data.")

else:  # Student View
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
            st.error("Yeh Room Number is month mein nahi mila.")
        else:
            st.dataframe(student_df[["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]], 
                        use_container_width=True, hide_index=True)

st.caption("University Mess Dues System • Case Insensitive • Delete/Update Option Added")
