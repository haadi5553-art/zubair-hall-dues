import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

st.set_page_config(
    page_title="Zubair Hall Mess Dues System",
    page_icon="🏠",
    layout="wide"
)

# Fancy Background + Style
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.75)), 
                    url('https://source.unsplash.com/1600x900/?hostel,building');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    h1 { color: white; text-shadow: 3px 3px 10px rgba(0,0,0,0.8); }
    .stButton>button {
        background: linear-gradient(45deg, #ff4757, #ff6b81);
        color: white;
        border-radius: 12px;
        height: 3.2em;
        font-weight: bold;
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
        
        uploaded = st.file_uploader("Excel ya CSV file upload karo (RoomNo, Name, Food_Dues, Service_Charges, Previous)", 
                                  type=["csv", "xlsx"])
        
        if uploaded and st.button("🚀 Upload Dues List", type="primary"):
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)
                
                # Rename columns
                df = df.rename(columns={
                    "Room No": "RoomNo", "room no": "RoomNo", "Roomno": "RoomNo",
                    "Name": "Name", "name": "Name",
                    "Food Dues": "Food_Dues", "food dues": "Food_Dues",
                    "Service Charges": "Service_Charges", "service charges": "Service_Charges",
                    "Service Dues": "Service_Charges", "service dues": "Service_Charges",
                    "Previous": "Previous", "previous": "Previous"
                })
                
                # Required columns check & fill
                for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
                    if col not in df.columns:
                        df[col] = 0 if col in ["Food_Dues", "Service_Charges", "Previous"] else ""
                
                # Auto add Month (Yeh naya feature hai)
                df["Month"] = selected_month
                
                # Calculate Total
                df["Total"] = (pd.to_numeric(df["Food_Dues"], errors='coerce').fillna(0) +
                               pd.to_numeric(df["Service_Charges"], errors='coerce').fillna(0) +
                               pd.to_numeric(df["Previous"], errors='coerce').fillna(0))
                
                # Remove duplicate month data
                existing = load_dues()
                existing = existing[existing["Month"] != selected_month]
                new_df = pd.concat([existing, df], ignore_index=True)
                save_dues(new_df)
                
                st.success(f"🎉 {len(df)} students ka data **{selected_month}** month ke liye upload ho gaya!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab2:
        st.header("📊 Monthly Dashboard")
        dues = load_dues()
        if not dues.empty:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected = st.selectbox("Month select karo", month_list)
            month_dues = dues[dues["Month"] == selected]
            payments = load_payments()
            month_payments = payments[payments["Month"] == selected]
            
            total_due = month_dues["Total"].sum()
            collected = month_dues[month_dues["RoomNo"].isin(month_payments.get("RoomNo", []))]["Total"].sum() if not month_payments.empty else 0
            remaining = total_due - collected
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Dues", f"₹ {total_due:,.0f}")
            col2.metric("Collected", f"₹ {collected:,.0f}")
            col3.metric("Remaining", f"₹ {remaining:,.0f}")
            
            st.dataframe(month_dues[["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous", "Total"]], 
                        use_container_width=True, hide_index=True)

    with tab3:
        st.header("⏳ All Pending Dues")
        dues = load_dues()
        payments = load_payments()
        merged = dues.merge(payments[["Month", "RoomNo", "Submission_Date"]], on=["Month", "RoomNo"], how="left")
        pending = merged[pd.isna(merged["Submission_Date"])].copy()
        
        if pending.empty:
            st.success("Sab students ne payment kar diya! 🎉")
        else:
            summary = pending.groupby(["RoomNo", "Name"]).agg(
                Total_Remaining=("Total", "sum"),
                Pending_Months=("Month", lambda x: ", ".join(sorted(x)))
            ).reset_index()
            st.metric("Total Pending Amount", f"₹ {pending['Total'].sum():,.0f}")
            st.dataframe(summary[["RoomNo", "Name", "Total_Remaining", "Pending_Months"]], 
                        use_container_width=True, hide_index=True)

    with tab4:
        st.header("📋 All Submissions")
        payments = load_payments()
        if not payments.empty:
            st.dataframe(payments, use_container_width=True, hide_index=True)

    with tab5:
        st.header("🗑️ Clear Month Data")
        dues = load_dues()
        if not dues.empty:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected_month = st.selectbox("Kis month ko delete karna hai?", month_list)
            
            if st.button("🗑️ Clear This Month", type="primary"):
                if st.checkbox("Kya aap pakka is month ko delete karna chahte hain?", value=False):
                    existing = load_dues()
                    new_df = existing[existing["Month"] != selected_month]
                    save_dues(new_df)
                    st.success(f"✅ Month **{selected_month}** ki puri list delete kar di gayi hai.")
                    st.rerun()

else:
    st.header("Apni Mess Dues Receipt Submit Karo")
    dues = load_dues()
    if dues.empty:
        st.error("Admin ne abhi dues list upload nahi ki.")
        st.stop()
    
    month_list = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Month select karo", month_list)
    
    room_input = st.text_input("Apna Room Number daalo")
    
    if room_input:
        student_df = dues[(dues["Month"] == selected_month) & 
                         (dues["RoomNo"].astype(str).str.strip() == str(room_input).strip())]
        
        if student_df.empty:
            st.error("❌ Yeh Room Number is month ki list mein nahi mila.")
        else:
            student = student_df.iloc[0]
            
            st.success(f"**Room No:** {student['RoomNo']}")
            st.success(f"**Name:** {student['Name']}")
            st.info(f"**Food Dues:** ₹ {student.get('Food_Dues', 0)}")
            st.info(f"**Service Charges:** ₹ {student.get('Service_Charges', 0)}")
            st.info(f"**Previous Amount:** ₹ {student.get('Previous', 0)}")
            st.info(f"**Total Amount:** ₹ {student.get('Total', 0)}")
            
            payments = load_payments()
            already = payments[(payments["Month"] == selected_month) & 
                              (payments["RoomNo"].astype(str).str.strip() == str(room_input).strip())]
            
            if not already.empty:
                st.warning("Aap is month ke liye already submit kar chuke hain.")
            else:
                receipt = st.file_uploader("Fee Receipt upload karo (JPG, PNG ya PDF)", 
                                         type=["jpg", "jpeg", "png", "pdf"])
                
                if receipt and st.button("✅ Submit Receipt"):
                    file_ext = receipt.name.split(".")[-1]
                    filename = f"{selected_month}_Room{room_input}_{uuid.uuid4().hex[:8]}.{file_ext}"
                    
                    new_row = pd.DataFrame([{
                        "Month": selected_month,
                        "RoomNo": student["RoomNo"],
                        "Name": student["Name"],
                        "Phone": student.get("Phone", ""),
                        "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Receipt_File": filename
                    }])
                    
                    updated = pd.concat([payments, new_row], ignore_index=True)
                    save_payments(updated)
                    st.success("🎉 Receipt successfully submit ho gaya! Shukriya.")
                    st.balloons()

st.caption("Pakistan Zindabad")
