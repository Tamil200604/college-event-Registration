import streamlit as st
import os

from auth import admin_login
from audio_check import check_audio
from storage import load_csv, save_csv

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="College Event Registration System",
    layout="wide"
)

# ---------------- SIDEBAR ----------------
menu = st.sidebar.selectbox(
    "Navigate",
    [
        "Home",
        "Admin Dashboard",
        "Event Registration Portal",
        "Check Registration Status"
    ]
)

# =====================================================
# ✅ HOME
# =====================================================
if menu == "Home":
    st.title("🎓 College Event Registration & Management System")
    st.write("Online registration with AI-assisted validation.")

# =====================================================
# ✅ ADMIN DASHBOARD
# =====================================================
elif menu == "Admin Dashboard":

    st.title("🛠️ Admin Dashboard")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # ---------------- LOGIN ----------------
    if not st.session_state.logged_in:

        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")

        if st.button("Login"):
            if admin_login(username, password):
                st.session_state.logged_in = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    # ---------------- DASHBOARD ----------------
    else:

        st.success("Welcome Admin 😎")

        participants = load_csv("data/participants.csv")
        results = load_csv("data/results.csv")

        if participants.empty or results.empty:
            st.info("No submissions yet")

        else:
            merged = participants.merge(results, on="reg_no")

            # ---------------- FILTERS 🔥 ----------------
            st.subheader("🎯 Filters")

            event_list = ["All"] + list(merged["event"].unique())
            competition_list = ["All"] + list(merged["competition"].unique())

            selected_event = st.selectbox("Filter by Event", event_list)
            selected_competition = st.selectbox("Filter by Competition", competition_list)

            filtered_data = merged.copy()

            if selected_event != "All":
                filtered_data = filtered_data[
                    filtered_data["event"] == selected_event
                ]

            if selected_competition != "All":
                filtered_data = filtered_data[
                    filtered_data["competition"] == selected_competition
                ]

            # ---------------- ANALYTICS ----------------
            st.subheader("📊 Analytics")

            approved_count = len(filtered_data[filtered_data["status"] == "Approved"])
            review_count = len(filtered_data[filtered_data["status"] == "Needs Review"])
            rejected_count = len(filtered_data[filtered_data["status"] == "Rejected"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Approved", approved_count)
            col2.metric("Needs Review", review_count)
            col3.metric("Rejected", rejected_count)

            st.divider()

            # ---------------- NEEDS REVIEW ----------------
            st.subheader("🚨 Needs Review")

            review_data = filtered_data[
                filtered_data["status"] == "Needs Review"
            ]

            if len(review_data) == 0:
                st.info("No pending reviews")

            else:
                for index, row in review_data.iterrows():

                    st.write(f"👤 **{row['name']}**")
                    st.write(f"{row['college']} | {row['event']} | {row['competition']}")

                    if isinstance(row["audio_file"], str) and row["audio_file"] != "":
                        st.audio(row["audio_file"])

                    col1, col2 = st.columns(2)

                    if col1.button("✅ Approve", key=f"approve_{index}"):

                        results.loc[
                            results["reg_no"] == row["reg_no"],
                            "status"
                        ] = "Approved"

                        save_csv(results, "data/results.csv")
                        st.rerun()

                    if col2.button("❌ Reject", key=f"reject_{index}"):

                        results.loc[
                            results["reg_no"] == row["reg_no"],
                            "status"
                        ] = "Rejected"

                        save_csv(results, "data/results.csv")
                        st.rerun()

                    st.divider()

            # ---------------- APPROVED ----------------
            st.subheader("🎵 Approved Submissions")

            approved_data = filtered_data[
                filtered_data["status"] == "Approved"
            ]

            if len(approved_data) == 0:
                st.info("No approved submissions")

            else:
                for index, row in approved_data.iterrows():

                    st.write(f"👤 **{row['name']}**")
                    st.write(f"{row['college']} | {row['event']} | {row['competition']}")

                    if isinstance(row["audio_file"], str) and row["audio_file"] != "":
                        st.audio(row["audio_file"])

                    st.divider()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# =====================================================
# ✅ REGISTRATION PORTAL
# =====================================================
elif menu == "Event Registration Portal":

    st.title("📋 Event Registration Portal")
    st.caption("👉 Click Submit button after filling details")

    with st.form("registration_form"):

        name = st.text_input("Participant Name")
        college = st.text_input("College Name")
        reg_no = st.text_input("Register Number")
        event = st.text_input("Event Name")

        competition = st.selectbox(
            "Competition",
            ["Dance", "Singing", "Chess"]
        )

        audio_file = None

        if competition in ["Dance", "Singing"]:
            audio_file = st.file_uploader(
                "Upload Audio (WAV only)",
                type=["wav"]
            )

        submit = st.form_submit_button("🚀 Submit Registration")

    # ---------------- SUBMIT LOGIC ----------------
    if submit:

        if not name or not college or not reg_no or not event:
            st.warning("⚠ Fill all fields")
            st.stop()

        participants = load_csv("data/participants.csv")
        results = load_csv("data/results.csv")

        status = "Approved"
        audio_path = ""

        if competition in ["Dance", "Singing"]:

            if audio_file is None:
                st.warning("⚠ Upload audio file")
                st.stop()

            os.makedirs("uploads/audio_files", exist_ok=True)
            audio_path = f"uploads/audio_files/{reg_no}.wav"

            with open(audio_path, "wb") as f:
                f.write(audio_file.read())

            status = check_audio(audio_path)

        new_participant = {
            "name": name,
            "college": college,
            "reg_no": reg_no,
            "event": event,
            "competition": competition,
            "audio_file": audio_path
        }

        participants = participants._append(new_participant, ignore_index=True)

        new_result = {
            "reg_no": reg_no,
            "status": status
        }

        results = results._append(new_result, ignore_index=True)

        save_csv(participants, "data/participants.csv")
        save_csv(results, "data/results.csv")

        st.success(f"✅ Submitted Successfully — {status}")

# =====================================================
# ✅ STATUS CHECK
# =====================================================
elif menu == "Check Registration Status":

    st.title("🔎 Check Registration Status")

    reg_no = st.text_input("Enter Register Number")

    if st.button("Check Status"):

        results = load_csv("data/results.csv")

        record = results[results["reg_no"] == reg_no]

        if record.empty:
            st.warning("No registration found")

        else:
            status = record.iloc[0]["status"]

            if status == "Approved":
                st.success("✅ Registration Approved")

            elif status == "Needs Review":
                st.warning("⚠ Registration Under Review")

            elif status == "Rejected":
                st.error("❌ Registration Rejected")
