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

# ====================== STUDENT VIEW (Multiple Students per Room) ======================
if role == "Student":
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
        # Get all students in that room
        student_df = dues[(dues["Month"] == selected_month) & 
                         (dues["RoomNo"].astype(str).str.strip() == str(room_input).strip())]
        
        if student_df.empty:
            st.error("❌ Yeh Room Number is month mein nahi mila.")
        else:
            st.subheader(f"Room No: {room_input} — {len(student_df)} Students")

            payments = load_payments(hall_name)

            for idx, student in student_df.iterrows():
                name = student["Name"]
                total_amount = student["Total"]

                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{name}**")
                with col2:
                    st.write(f"Total: **Rs {total_amount:,.0f}**")
                with col3:
                    # Check if already submitted
                    already = not payments[(payments["Month"] == selected_month) & 
                                          (payments["RoomNo"].astype(str).str.strip() == str(room_input).strip()) & 
                                          (payments["Name"] == name)].empty
                    
                    if already:
                        st.success("✅ Submitted")
                    else:
                        if st.button(f"Upload Receipt", key=f"btn_{idx}"):
                            st.session_state.selected_student = name
                            st.session_state.selected_room = room_input
                            st.session_state.selected_month = selected_month
                            st.rerun()

            # Receipt upload logic
            if 'selected_student' in st.session_state:
                name = st.session_state.selected_student
                st.subheader(f"Upload Receipt for: {name}")
                receipt = st.file_uploader("Fee Receipt (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key="receipt_upload")
                
                if receipt and st.button("Submit Receipt"):
                    file_ext = receipt.name.split(".")[-1]
                    filename = f"{st.session_state.selected_month}_Room{st.session_state.selected_room}_{name}_{uuid.uuid4().hex[:8]}.{file_ext}"
                    
                    new_row = pd.DataFrame([{
                        "Month": st.session_state.selected_month,
                        "RoomNo": st.session_state.selected_room,
                        "Name": name,
                        "Phone": "",
                        "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Receipt_File": filename
                    }])
                    
                    updated = pd.concat([payments, new_row], ignore_index=True)
                    save_payments(updated, hall_name)
                    st.success(f"🎉 {name} ka receipt successfully submit ho gaya!")
                    st.balloons()
                    
                    # Clear session state
                    del st.session_state.selected_student
                    st.rerun()

else:
    st.info("Student section ke liye Room Number daalein.")

st.caption("University Mess Dues System • Multiple Students per Room")
