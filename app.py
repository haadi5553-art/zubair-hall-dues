import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

# Page Configuration - Fancy Look
st.set_page_config(
    page_title="Zubair Hall Mess Dues System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Fancy Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

def get_google_sheet():
    creds_dict = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(credentials)
    return gc

def load_dues():
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet("Dues")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"])

def save_dues(df):
    gc = get_google_sheet()
    sheet = gc.open("Hostel Dues Data").worksheet("Dues")
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

def load_payments():
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet("Payments")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Phone", "Submission_Date", "Receipt_File"])

def save_payments(df):
    gc = get_google_sheet()
    sheet = gc.open("Hostel Dues Data").worksheet("Payments")
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ====================== MAIN APP ======================
st.title("🏠 Zubair Hall Mess Dues System")
st.caption("**Made by Abdul Hadi 2025 (S) CYS 90**")

role = st.sidebar.selectbox("👤 Select Role", ["Student", "Admin"])

if role == "Admin":
    password = st.sidebar.text_input("🔑 Admin Password", type="password")
    if password != "hostel123":
        st.sidebar.warning("❌ Wrong Password")
        st.stop()

if role == "Admin":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload New Month", "📊 Monthly Dashboard", "⏳ All Pending Dues", "📋 Submissions", "🗑️ Clear Month"])

    with tab1:
        st.header("📤 Upload New Month Dues")
        
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("📅 Year", options=list(range(2025, 2031)), index=1)
        with col2:
            month_num = st.selectbox("🗓️ Month", 
                                   options=[("01","January"), ("02","February"), ("03","March"), 
                                            ("04","April"), ("05","May"), ("06","June"), 
                                            ("07","July"), ("08","August"), ("09","September"), 
                                            ("10","October"), ("11","November"), ("12","December")],
                                   format_func=lambda x: f"{x[0]} - {x[1]}")
        
        selected_month = f"{year}-{month_num[0]}"
        
        st.success(f"📅 Selected Month: **{selected_month}**")
        
        uploaded = st.file_uploader("Excel ya CSV file upload karo", type=["csv", "xlsx"], help="RoomNo, Name, Food_Dues, Service_Charges, Previous columns hone chahiye")
        
        if uploaded and st.button("🚀 Upload Dues List", type="primary"):
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)
                
                df = df.rename(columns={
                    "Room No": "RoomNo", "room no": "RoomNo", "Roomno": "RoomNo",
                    "Name": "Name", "name": "Name",
                    "Food Dues": "Food_Dues", "food dues": "Food_Dues",
                    "Service Charges": "Service_Charges", "service charges": "Service_Charges",
                    "Service Dues": "Service_Charges", "service dues": "Service_Charges",
                    "Previous": "Previous", "previous": "Previous"
                })
                
                for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
                    if col not in df.columns:
                        df[col] = 0 if col in ["Food_Dues", "Service_Charges", "Previous"] else ""
                
                df["Month"] = selected_month
                df["Total"] = (pd.to_numeric(df["Food_Dues"], errors='coerce').fillna(0) +
                               pd.to_numeric(df["Service_Charges"], errors='coerce').fillna(0) +
                               pd.to_numeric(df["Previous"], errors='coerce').fillna(0))
                
                existing = load_dues()
                existing = existing[existing["Month"] != selected_month]
                new_df = pd.concat([existing, df], ignore_index=True)
                save_dues(new_df)
                
                st.success(f"🎉 {len(df)} students ka data **{selected_month}** ke liye upload ho gaya!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Baqi tabs (Dashboard, Pending, Submissions, Clear Month) same rakhe hain
    with tab2:
        st.header("📊 Monthly Dashboard")
        # ... (baqi code same rahega)

    with tab3:
        st.header("⏳ All Pending Dues")
        # ... (baqi code)

    with tab4:
        st.header("📋 All Submissions")
        # ... (baqi code)

    with tab5:
        st.header("🗑️ Clear Month Data")
        # ... (baqi code)

else:
    st.header("Submit your Mess Dues Receipt")
    # Student section same rahega

st.caption("100% Google Safe • Modern Interface • Zubair Hall Mess Dues System")
