import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os

st.set_page_config(page_title="Mess Dues PRO System", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stButton>button {background:#4CAF50;color:white;border-radius:8px;}
.block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

# ================= GOOGLE =================
def get_google_sheet():
    creds = st.secrets["gspread"]
    credentials = Credentials.from_service_account_info(
        creds,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(credentials)

# ================= CLEAN =================
def standardize_columns(df):
    df.columns = df.columns.str.strip()
    return df.rename(columns={
        "room no":"RoomNo","roomno":"RoomNo","room no.":"RoomNo",
        "name":"Name",
        "food dues":"Food_Dues",
        "service charges":"Service_Charges",
        "previous":"Previous"
    })

# ================= LOAD SAVE =================
def load_dues(hall):
    try:
        sheet = get_google_sheet().open("Hostel Dues Data").worksheet(hall)
        df = pd.DataFrame(sheet.get_all_records())
        df = standardize_columns(df)

        for col in ["Food_Dues","Service_Charges","Previous"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

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

# ================= FOLDER =================
if not os.path.exists("receipts"):
    os.makedirs("receipts")

# ================= HALLS =================
halls = [
"SMG Hall","MBQ Hall","EIDHI Hall","ZUBAIR Hall","MUMTAZ Hall",
"LIAQUAT Hall","QUAID AZAM Hall","IQBAL Hall","SIR SYED Hall"
]

hall_passwords = {
"SMG Hall":"smg123","MBQ Hall":"mbq456","EIDHI Hall":"eidhi789",
"ZUBAIR Hall":"zubair012","MUMTAZ Hall":"mumtaz345","LIAQUAT Hall":"liaquat678",
"QUAID AZAM Hall":"quaid901","IQBAL Hall":"iqbal234","SIR SYED Hall":"syed567"
}

senior_password = "senior@1122"

# ================= UI =================
st.title("🏛️ University Mess Dues PRO System")

role = st.sidebar.selectbox("Select Role", ["Student","Hall Admin","Senior Warden"])

# ================= STUDENT =================
if role == "Student":

    hall = st.sidebar.selectbox("Hall", halls)
    dues = load_dues(hall)

    if dues.empty:
        st.warning("No data uploaded")
        st.stop()

    month = st.selectbox("Month", sorted(dues["Month"].unique(), reverse=True))
    dues = dues[dues["Month"]==month].sort_values("RoomNo")

    payments = load_payments(hall)

    st.subheader("All Students")

    for i,row in dues.iterrows():
        room = str(row["RoomNo"])

        st.markdown(f"""
        <div style="padding:15px;background:#f1f3f6;border-radius:10px;margin-bottom:10px">
        <b>Room:</b> {room} <br>
        <b>Name:</b> {row['Name']} <br>
        <b>Total:</b> Rs {row['Total']}
        </div>
        """, unsafe_allow_html=True)

        paid_rooms = payments["RoomNo"].astype(str).values if not payments.empty else []
        if room in paid_rooms:
            st.success("✅ Paid")

        file = st.file_uploader("Upload Receipt", key=f"{room}{i}")

        if file and st.button("Submit", key=f"btn{room}{i}"):

            file_bytes = file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()

            duplicate = payments[
                (payments["RoomNo"].astype(str)==room) &
                (payments["Month"]==month) &
                (
                    (payments["File_Hash"]==file_hash) |
                    (payments["Submission_Date"].str[:10]==datetime.now().strftime("%Y-%m-%d"))
                )
            ]

            if not duplicate.empty:
                st.error("Duplicate receipt ❌")
            else:
                path = f"receipts/{uuid.uuid4()}_{file.name}"
                with open(path,"wb") as f:
                    f.write(file_bytes)

                new = pd.DataFrame([{
                    "Month":month,
                    "RoomNo":room,
                    "Name":row["Name"],
                    "Submission_Date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Receipt_File":path,
                    "File_Hash":file_hash
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

        search = st.text_input("Search")

        if search:
            df = df[df["RoomNo"].astype(str).str.contains(search) |
                    df["Name"].str.contains(search, case=False)]

        paid = payments["RoomNo"].astype(str).unique() if not payments.empty else []

        def color(row):
            if str(row["RoomNo"]) in paid:
                return ["background-color: lightgreen"]*len(row)
            return [""]*len(row)

        st.dataframe(df.style.apply(color,axis=1),use_container_width=True)

        st.line_chart(df.groupby("RoomNo")["Total"].sum())

    # PENDING
    with tab2:
        paid = payments["RoomNo"].astype(str).unique() if not payments.empty else []
        pending = dues[~dues["RoomNo"].astype(str).isin(paid)]

        st.warning(f"{len(pending)} students pending")
        st.dataframe(pending,use_container_width=True)

    # RECEIPTS
    with tab3:
        for _,row in payments.iterrows():
            st.write(f"{row['RoomNo']} - {row['Name']}")

            path = row["Receipt_File"]

            if os.path.exists(path):
                if path.lower().endswith((".png",".jpg",".jpeg")):
                    st.image(path,width=200)

                with open(path,"rb") as f:
                    st.download_button("Download",f,file_name=os.path.basename(path))

    # DELETE MONTH
    with tab4:
        m = st.selectbox("Delete Month", dues["Month"].unique())
        if st.button("Delete"):
            new = dues[dues["Month"]!=m]
            save_dues(new,hall)
            st.success("Deleted")

# ================= SENIOR =================
elif role == "Senior Warden":

    pw = st.sidebar.text_input("Password", type="password")
    if pw != senior_password:
        st.warning("Wrong Password")
        st.stop()

    total_all = collected_all = remaining_all = 0
    summary = []

    for hall in halls:
        dues = load_dues(hall)
        payments = load_payments(hall)

        if not dues.empty:
            total = dues["Total"].sum()
            collected = 0

            if not payments.empty:
                collected = dues[dues["RoomNo"].isin(payments["RoomNo"])]["Total"].sum()

            remaining = total - collected

            total_all += total
            collected_all += collected
            remaining_all += remaining

            summary.append({
                "Hall":hall,
                "Total":total,
                "Collected":collected,
                "Remaining":remaining
            })

    col1,col2,col3 = st.columns(3)
    col1.metric("Total", total_all)
    col2.metric("Collected", collected_all)
    col3.metric("Remaining", remaining_all)

    st.dataframe(pd.DataFrame(summary), use_container_width=True)
