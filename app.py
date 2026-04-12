import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid
import hashlib
import os

st.set_page_config(page_title="Mess Dues System", layout="wide")

# ===== STYLE =====
st.markdown("""
<style>
.stButton>button {background:#4CAF50;color:white;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

# ===== GOOGLE SHEET =====
def get_google_sheet():
    creds = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(credentials)

# ===== CLEAN =====
def standardize_columns(df):
    df.columns = df.columns.str.strip()
    return df.rename(columns={
        "room no":"RoomNo","roomno":"RoomNo",
        "name":"Name",
        "food dues":"Food_Dues",
        "service charges":"Service_Charges",
        "previous":"Previous"
    })

# ===== LOAD / SAVE =====
def load_dues(hall):
    try:
        sheet = get_google_sheet().open("Hostel Dues Data").worksheet(hall)
        df = pd.DataFrame(sheet.get_all_records())
        df = standardize_columns(df)
        df["Total"] = df["Food_Dues"] + df["Service_Charges"] + df["Previous"]
        return df
    except:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Food_Dues","Service_Charges","Previous","Total"])

def save_dues(df, hall):
    sh = get_google_sheet().open("Hostel Dues Data")
    try:
        ws = sh.worksheet(hall)
    except:
        ws = sh.add_worksheet(title=hall, rows=5000, cols=20)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

def load_payments(hall):
    try:
        sheet = get_google_sheet().open("Hostel Dues Data").worksheet(f"{hall}_Payments")
        return pd.DataFrame(sheet.get_all_records())
    except:
        return pd.DataFrame(columns=["Month","RoomNo","Name","Submission_Date","Receipt_File","File_Hash"])

def save_payments(df, hall):
    sh = get_google_sheet().open("Hostel Dues Data")
    try:
        ws = sh.worksheet(f"{hall}_Payments")
    except:
        ws = sh.add_worksheet(title=f"{hall}_Payments", rows=5000, cols=20)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# ===== FOLDER =====
if not os.path.exists("receipts"):
    os.makedirs("receipts")

# ===== DATA =====
halls = ["SMG Hall","MBQ Hall","EIDHI Hall"]

hall_passwords = {
    "SMG Hall":"smg123",
    "MBQ Hall":"mbq456",
    "EIDHI Hall":"eidhi789"
}

senior_password = "senior@1122"

# ===== UI =====
st.title("🏛️ Mess Dues System")

role = st.sidebar.selectbox("Role", ["Student","Hall Admin","Senior Warden"])

# ================= STUDENT =================
if role == "Student":

    hall = st.sidebar.selectbox("Hall", halls)
    dues = load_dues(hall)

    if dues.empty:
        st.warning("No data")
        st.stop()

    month = st.selectbox("Month", sorted(dues["Month"].unique(), reverse=True))
    dues = dues[dues["Month"] == month].sort_values("RoomNo")

    payments = load_payments(hall)

    for i,row in dues.iterrows():
        room = str(row["RoomNo"])

        st.markdown("---")
        c1,c2,c3 = st.columns(3)

        with c1:
            st.write(f"Room: {room}")
            st.write(f"Name: {row['Name']}")

        with c2:
            st.write(f"Total: {row['Total']}")

        with c3:
            file = st.file_uploader("Receipt", key=f"{room}{i}")

            if file and st.button("Submit", key=f"btn{room}{i}"):

                hash = hashlib.md5(file.getvalue()).hexdigest()

                dup = payments[
                    (payments["RoomNo"].astype(str)==room) &
                    (payments["Month"]==month) &
                    (payments["File_Hash"]==hash)
                ]

                if not dup.empty:
                    st.error("Duplicate receipt ❌")
                else:
                    path = f"receipts/{uuid.uuid4()}_{file.name}"
                    with open(path,"wb") as f:
                        f.write(file.getvalue())

                    new = pd.DataFrame([{
                        "Month":month,
                        "RoomNo":room,
                        "Name":row["Name"],
                        "Submission_Date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Receipt_File":path,
                        "File_Hash":hash
                    }])

                    payments = pd.concat([payments,new],ignore_index=True)
                    save_payments(payments,hall)
                    st.success("Uploaded ✅")

# ================= ADMIN =================
elif role == "Hall Admin":

    hall = st.sidebar.selectbox("Hall", halls)
    if st.sidebar.text_input("Password", type="password") != hall_passwords[hall]:
        st.stop()

    dues = load_dues(hall)
    payments = load_payments(hall)

    tab1,tab2,tab3,tab4 = st.tabs(["Dashboard","Pending","Receipts","Manage Months"])

    # DASHBOARD
    with tab1:
        month = st.selectbox("Month", sorted(dues["Month"].unique(), reverse=True))
        df = dues[dues["Month"]==month]

        paid = payments["RoomNo"].astype(str).unique() if not payments.empty else []

        def color(row):
            if str(row["RoomNo"]) in paid:
                return ["background-color: lightgreen"]*len(row)
            return [""]*len(row)

        st.dataframe(df.style.apply(color,axis=1),use_container_width=True)

    # PENDING
    with tab2:
        if payments.empty:
            st.info("All pending")
        else:
            paid = payments["RoomNo"].astype(str).unique()
            pending = dues[~dues["RoomNo"].astype(str).isin(paid)]
            st.dataframe(pending,use_container_width=True)

    # RECEIPTS
    with tab3:
        for i,row in payments.iterrows():
            st.write(f"{row['RoomNo']} - {row['Name']}")
            if os.path.exists(row["Receipt_File"]):
                with open(row["Receipt_File"],"rb") as f:
                    st.download_button("Download",f,file_name=os.path.basename(row["Receipt_File"]))

    # DELETE MONTH
    with tab4:
        month = st.selectbox("Delete Month", dues["Month"].unique())
        if st.button("Delete"):
            new = dues[dues["Month"]!=month]
            save_dues(new,hall)
            st.success("Deleted")

# ================= SENIOR =================
elif role == "Senior Warden":

    pw = st.sidebar.text_input("Password", type="password")
    if pw != senior_password:
        st.warning("Wrong Password")
        st.stop()

    total = collected = 0

    for hall in halls:
        dues = load_dues(hall)
        payments = load_payments(hall)

        if not dues.empty:
            total += dues["Total"].sum()
            if not payments.empty:
                collected += dues[dues["RoomNo"].isin(payments["RoomNo"])]["Total"].sum()

    st.metric("Total", total)
    st.metric("Collected", collected)
    st.metric("Remaining", total-collected)
