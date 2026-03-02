import streamlit as st
import os
from datetime import datetime

from auth import admin_login
from audio_check import check_audio
from storage import load_csv, save_csv

# PAGE CONFIG
st.set_page_config(
    page_title="College Event Registration System",
    layout="wide"
)

# HELPER - Load Events
def load_events():
    events_df = load_csv("data/events.csv")
    if events_df.empty:
        return []
    return events_df['event_name'].tolist()

# HELPER - Save Event
def save_event(event_name, description, competition_types):
    events_df = load_csv("data/events.csv")
    
    if event_name in events_df['event_name'].values:
        st.error("Event already exists!")
        return False
    
    new_event = {
        "event_name": event_name,
        "description": description,
        "competition_types": ",".join(competition_types),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    events_df = events_df._append(new_event, ignore_index=True)
    save_csv(events_df, "data/events.csv")
    return True

# HELPER - Get Competition Types
def get_competition_types(event_name):
    events_df = load_csv("data/events.csv")
    event = events_df[events_df['event_name'] == event_name]
    
    if event.empty:
        return ["Dance", "Singing", "Chess"]
    
    comp_types = event.iloc[0]['competition_types'].split(',')
    return comp_types

# HELPER - Get Event Details
def get_event_details(event_name):
    events_df = load_csv("data/events.csv")
    event = events_df[events_df['event_name'] == event_name]
    
    if event.empty:
        return None
    
    return {
        "name": event.iloc[0]['event_name'],
        "description": event.iloc[0]['description'],
        "created_at": event.iloc[0]['created_at']
    }

# SIDEBAR
menu = st.sidebar.selectbox(
    "Navigate",
    [
        "Home",
        "Admin Dashboard",
        "Event Registration Portal",
        "Check Registration Status"
    ]
)

# HOME PAGE
if menu == "Home":
    st.title("🎓 College Event Registration & Management System")
    st.write("Online registration with AI-assisted validation.")
    
    st.divider()
    st.subheader("📅 Available Events")
    
    events = load_events()
    
    if not events:
        st.info("No events available yet. Please check back later!")
    else:
        for event_name in events:
            event_details = get_event_details(event_name)
            if event_details:
                with st.container(border=True):
                    st.write(f"### 🎉 {event_details['name']}")
                    st.write(f"📝 {event_details['description']}")
                    st.write(f"📅 Created: {event_details['created_at']}")

# ADMIN DASHBOARD
elif menu == "Admin Dashboard":

    st.title("🛠️ Admin Dashboard")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # LOGIN
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

    # DASHBOARD
    else:

        st.success("Welcome Admin 😎")
        
        # TABS
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 Dashboard", "➕ Create Event", "🎯 Review Submissions"])
        
        # TAB 1: DASHBOARD
        with admin_tab1:
            participants = load_csv("data/participants.csv")
            results = load_csv("data/results.csv")

            if participants.empty or results.empty:
                st.info("No submissions yet")

            else:
                merged = participants.merge(results, on="reg_no")

                # FILTERS
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

                # ANALYTICS
                st.subheader("📊 Analytics")

                approved_count = len(filtered_data[filtered_data["status"] == "Approved"])
                review_count = len(filtered_data[filtered_data["status"] == "Needs Review"])
                rejected_count = len(filtered_data[filtered_data["status"] == "Rejected"])

                col1, col2, col3 = st.columns(3)
                col1.metric("Approved", approved_count)
                col2.metric("Needs Review", review_count)
                col3.metric("Rejected", rejected_count)

                st.divider()

                # NEEDS REVIEW
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

                # APPROVED
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
        
        # TAB 2: CREATE EVENT
        with admin_tab2:
            st.subheader("➕ Create New Event")
            
            with st.form("create_event_form"):
                event_name = st.text_input("Event Name", placeholder="e.g., College Fest 2024")
                event_description = st.text_area("Event Description", placeholder="Describe the event...")
                
                competition_options = ["Dance", "Singing", "Chess", "Drama", "Art", "Sports"]
                selected_competitions = st.multiselect(
                    "Select Competition Types",
                    competition_options,
                    default=["Dance", "Singing", "Chess"]
                )
                
                create_btn = st.form_submit_button("✅ Create Event")
            
            if create_btn:
                if not event_name or not event_description:
                    st.error("Please fill in all fields")
                elif not selected_competitions:
                    st.error("Please select at least one competition type")
                else:
                    if save_event(event_name, event_description, selected_competitions):
                        st.success(f"✅ Event '{event_name}' created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create event")
            
            st.divider()
            st.subheader("📋 Existing Events")
            
            events_df = load_csv("data/events.csv")
            if events_df.empty:
                st.info("No events created yet")
            else:
                for idx, event in events_df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Event:** {event['event_name']}")
                        st.write(f"**Description:** {event['description']}")
                        st.write(f"**Competitions:** {event['competition_types']}")
                        st.write(f"**Created:** {event['created_at']}")
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_event_{idx}"):
                            events_df = events_df.drop(idx)
                            save_csv(events_df, "data/events.csv")
                            st.success("Event deleted!")
                            st.rerun()
                    st.divider()
        
        # TAB 3: REVIEW
        with admin_tab3:
            st.subheader("🎯 Review All Submissions")
            
            participants = load_csv("data/participants.csv")
            results = load_csv("data/results.csv")
            
            if not participants.empty and not results.empty:
                merged = participants.merge(results, on="reg_no")
                st.metric("Total Submissions", len(merged))

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# REGISTRATION PORTAL
elif menu == "Event Registration Portal":

    st.title("📋 Event Registration Portal")
    st.caption("👉 Fill in all details and select an event to register")

    available_events = load_events()
    
    if not available_events:
        st.error("❌ No events available for registration. Please check back later!")
        st.stop()
    
    with st.form("registration_form"):

        name = st.text_input("Participant Name")
        college = st.text_input("College Name")
        reg_no = st.text_input("Register Number")
        
        selected_event = st.selectbox("Select Event", available_events)
        
        competition_types = get_competition_types(selected_event)
        
        competition = st.selectbox(
            "Select Competition",
            competition_types
        )

        audio_file = None

        if competition in ["Dance", "Singing"]:
            audio_file = st.file_uploader(
                "Upload Audio (WAV only)",
                type=["wav"]
            )

        submit = st.form_submit_button("🚀 Submit Registration")

    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    
    if st.session_state.show_success:
        st.success("✅ Submitted Successfully — Registration Confirmed!")
        st.session_state.show_success = False
    
    if submit:

        if not name or not college or not reg_no:
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
            "event": selected_event,
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
        
        st.session_state.show_success = True
        st.rerun()

# STATUS CHECK
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