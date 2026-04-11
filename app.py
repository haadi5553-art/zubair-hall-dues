import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

st.set_page_config(page_title="Zubair Hall Mess Dues System", layout="wide")

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
        df = pd.DataFrame(sheet.get_all_records())
        numeric_cols = ["Food_Dues", "Service_Charges", "Previous", "Total"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
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
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except:
        return pd.DataFrame(columns=["Month", "RoomNo", "Name", "Phone", "Submission_Date", "Receipt_File"])

def save_payments(df):
    gc = get_google_sheet()
    sheet = gc.open("Hostel Dues Data").worksheet("Payments")
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ====================== MAIN APP ======================
st.title("Zubair Hall Mess Dues System")
st.caption("**Made by Abdul Hadi 2025 (S) CYS 90**")

role = st.sidebar.selectbox("Select Role", ["Student", "Admin"])

if role == "Admin":
    password = st.sidebar.text_input("Admin Password", type="password")
    if password != "hostel123":
        st.sidebar.warning("Wrong Password")
        st.stop()

if role == "Admin":
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload New Month", "📊 Monthly Dashboard", "⏳ All Pending Dues", "📋 Submissions"])

    with tab1:
        st.header("Upload New Month Dues")
        month = st.text_input("Month (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
        uploaded = st.file_uploader("Excel ya CSV file", type=["csv", "xlsx"])
        
        if uploaded and st.button("Upload Dues"):
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            
            df = df.rename(columns={
                "Room No": "RoomNo", "room no": "RoomNo", "Roomno": "RoomNo",
                "Name": "Name", "name": "Name",
                "Food Dues": "Food_Dues", "food dues": "Food_Dues",
                "Service Charges": "Service_Charges", "service charges": "Service_Charges",
                "Previous": "Previous", "previous": "Previous"
            })
            
            for col in ["RoomNo", "Name", "Food_Dues", "Service_Charges", "Previous"]:
                if col not in df.columns:
                    df[col] = 0 if col in ["Food_Dues", "Service_Charges", "Previous"] else ""
            
            df["Month"] = month
            df["Total"] = (pd.to_numeric(df.get("Food_Dues", 0), errors='coerce').fillna(0) +
                           pd.to_numeric(df.get("Service_Charges", 0), errors='coerce').fillna(0) +
                           pd.to_numeric(df.get("Previous", 0), errors='coerce').fillna(0))
            
            existing = load_dues()
            # Safe filter
            if "Month" in existing.columns:
                existing = existing[existing["Month"] != month]
            new_df = pd.concat([existing, df], ignore_index=True)
            save_dues(new_df)
            st.success(f"✅ {len(df)} students ka data {month} ke liye upload ho gaya!")

    with tab2:
        st.header("Monthly Dashboard")
        dues = load_dues()
        if not dues.empty:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected = st.selectbox("Month select karo", month_list)
            month_dues = dues[dues["Month"] == selected].copy()
            payments = load_payments()
            
            total_due = month_dues["Total"].sum()
            collected = 0
            if not payments.empty and "RoomNo" in payments.columns:
                month_payments = payments[payments["Month"] == selected]
                collected = month_dues[month_dues["RoomNo"].isin(month_payments["RoomNo"])]["Total"].sum()

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
        
        if dues.empty:
            st.info("No dues data uploaded yet.")
        else:
            pay_df = payments[["Month", "RoomNo", "Submission_Date"]] if not payments.empty and "RoomNo" in payments.columns else pd.DataFrame(columns=["Month", "RoomNo", "Submission_Date"])
            merged = dues.merge(pay_df, on=["Month", "RoomNo"], how="left")
            pending = merged[pd.isna(merged.get("Submission_Date"))].copy()
            
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
        st.header("All Submissions")
        payments = load_payments()
        if payments.empty:
            st.info("No submissions yet.")
        else:
            st.dataframe(payments, use_container_width=True, hide_index=True)

else:  # Student Section
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
            
            st.success(f"**Room No:** {student.get('RoomNo', '')}")
            st.success(f"**Name:** {student.get('Name', '')}")
            st.info(f"**Food Dues:** ₹ {student.get('Food_Dues', 0)}")
            st.info(f"**Service Charges:** ₹ {student.get('Service_Charges', 0)}")
            st.info(f"**Previous Amount:** ₹ {student.get('Previous', 0)}")
            st.info(f"**Total Amount:** ₹ {student.get('Total', 0)}")
            
            payments = load_payments()
            already = False
            if not payments.empty and "RoomNo" in payments.columns:
                already = not payments[(payments["Month"] == selected_month) & 
                                      (payments["RoomNo"].astype(str).str.strip() == str(room_input).strip())].empty
            
            if already:
                st.warning("Aap is month ke liye already submit kar chuke hain.")
            else:
                receipt = st.file_uploader("Fee Receipt upload karo (JPG, PNG ya PDF)", 
                                         type=["jpg", "jpeg", "png", "pdf"])
                
                if receipt and st.button("✅ Submit Receipt"):
                    file_ext = receipt.name.split(".")[-1]
                    filename = f"{selected_month}_Room{room_input}_{uuid.uuid4().hex[:8]}.{file_ext}"
                    
                    new_row = pd.DataFrame([{
                        "Month": selected_month,
                        "RoomNo": student.get("RoomNo", room_input),
                        "Name": student.get("Name", ""),
                        "Phone": student.get("Phone", ""),
                        "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Receipt_File": filename
                    }])
                    
                    updated = pd.concat([payments, new_row], ignore_index=True)
                    save_payments(updated)
                    st.success("🎉 Receipt successfully submit ho gaya! Shukriya.")
                    st.balloons()

st.caption("lo bhai sub kuch kr dya theek hy ab  • Zubair Hall Mess Dues System")
