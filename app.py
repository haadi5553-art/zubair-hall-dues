import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid
import hashlib
import os

st.set_page_config(page_title="University Mess Dues System", layout="wide", page_icon="🏛️")

# ========= STYLE =========
st.markdown("""
<style>
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ========= GOOGLE SHEET =========
def get_google_sheet():
    creds_dict = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(credentials)

# ========= STANDARDIZE =========
def standardize_columns(df):
    df = df.rename(columns=str.strip)
    column_map = {
        "room no": "RoomNo", "roomno": "RoomNo", "room no.": "RoomNo",
        "name": "Name",
        "food dues": "Food_Dues",
        "service charges": "Service_Charges",
        "previous": "Previous"
    }
    return df.rename(columns=column_map)

# ========= LOAD / SAVE =========
def load_dues(hall_name):
    gc = get_google_sheet()
    try:
        sheet = gc.open("Hostel Dues Data").worksheet(hall_name)
        df = pd.DataFrame(sheet.get_all_records())
        df = standardize_columns(df)

        for col in ["Food_Dues", "Service_Charges", "Previous", "Total"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        if "Total" not in df.columns:
            df["Total"] = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]

        return df
    except:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])

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
        return pd.DataFrame(columns=["Month","RoomNo","Name","Submission_Date","Receipt_File","File_Hash"])

def save_payments(df, hall_name):
    gc = get_google_sheet()
    spreadsheet = gc.open("Hostel Dues Data")
    try:
        sheet = spreadsheet.worksheet(f"{hall_name}_Payments")
    except:
        sheet = spreadsheet.add_worksheet(title=f"{hall_name}_Payments", rows=5000, cols=20)
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# ========= RECEIPT FOLDER =========
if not os.path.exists("receipts"):
    os.makedirs("receipts")

# ========= HALLS =========
halls = ["SMG Hall", "MBQ Hall", "EIDHI Hall"]

hall_passwords = {
    "SMG Hall": "smg123",
    "MBQ Hall": "mbq456",
    "EIDHI Hall": "eidhi789"
}

senior_password = "senior@1122"

# ========= UI =========
st.title("🏛️ Mess Dues System")
role = st.sidebar.selectbox("Role", ["Student", "Hall Admin", "Senior Warden"])

# ================= STUDENT =================
if role == "Student":

    hall_name = st.sidebar.selectbox("Hall", halls)
    dues = load_dues(hall_name)

    if dues.empty:
        st.warning("No data uploaded")
        st.stop()

    month_list = sorted(dues["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Month", month_list)

    dues = dues[dues["Month"] == selected_month]
    dues = dues.sort_values(by="RoomNo")

    payments_df = load_payments(hall_name)

    st.subheader("All Students Dues")

    for i, row in dues.iterrows():
        room = str(row["RoomNo"])

        st.markdown("---")
        col1, col2, col3 = st.columns([2,2,2])

        with col1:
            st.write(f"**Room:** {room}")
            st.write(f"**Name:** {row['Name']}")

        with col2:
            st.write(f"Total: Rs {row['Total']}")

        with col3:
            receipt = st.file_uploader("Upload Receipt", key=f"{room}_{i}")

            if receipt and st.button("Submit", key=f"btn_{room}_{i}"):

                file_bytes = receipt.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                # 🔒 Duplicate check
                duplicate = payments_df[
                    (payments_df["RoomNo"].astype(str) == room) &
                    (payments_df["Month"] == selected_month) &
                    (payments_df["File_Hash"] == file_hash)
                ]

                if not duplicate.empty:
                    st.error("❌ Same receipt already uploaded!")
                else:
                    file_id = str(uuid.uuid4())
                    file_path = f"receipts/{file_id}_{receipt.name}"

                    with open(file_path, "wb") as f:
                        f.write(file_bytes)

                    new_entry = pd.DataFrame([{
                        "Month": selected_month,
                        "RoomNo": room,
                        "Name": row["Name"],
                        "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Receipt_File": file_path,
                        "File_Hash": file_hash
                    }])

                    payments_df = pd.concat([payments_df, new_entry], ignore_index=True)
                    save_payments(payments_df, hall_name)

                    st.success("✅ Uploaded!")

# ================= ADMIN =================
elif role == "Hall Admin":

    hall_name = st.sidebar.selectbox("Hall", halls)
    if st.sidebar.text_input("Password", type="password") != hall_passwords.get(hall_name):
        st.stop()

    dues = load_dues(hall_name)
    payments = load_payments(hall_name)

    tab1, tab2 = st.tabs(["Dashboard", "Receipts"])

    # ===== Dashboard =====
    with tab1:
        if dues.empty:
            st.info("No data")
        else:
            month_list = sorted(dues["Month"].unique(), reverse=True)
            selected = st.selectbox("Month", month_list)

            df = dues[dues["Month"] == selected]

            paid_rooms = payments["RoomNo"].astype(str).unique() if not payments.empty else []

            def highlight(row):
                if str(row["RoomNo"]) in paid_rooms:
                    return ["background-color: lightgreen"] * len(row)
                return [""] * len(row)

            st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

    # ===== Receipts =====
    with tab2:
        if payments.empty:
            st.info("No receipts")
        else:
            for i, row in payments.iterrows():
                st.markdown("---")
                st.write(f"Room: {row['RoomNo']} | {row['Name']}")

                file_path = row["Receipt_File"]

                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(
                            "Download Receipt",
                            f,
                            file_name=os.path.basename(file_path)
                        )
