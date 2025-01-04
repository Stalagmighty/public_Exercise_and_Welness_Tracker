import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# Page and data configuration
st.set_page_config(page_title="Exercise and Wellness Tracker", layout="centered")

# Add fire icons to the title
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        📈️Log Your Activity🧘‍♀️
    </h1>
    """,
    unsafe_allow_html=True
)

st.write("-----")

# Authenticate with the Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)

# Build the API service
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = "1dgjmSBRlBNNjQMQkj1jaFS6ml_uOTh0Gec5X1WsgCao"

# Function to fetch data from a specific sheet
def fetch_data(sheet_name, range_name):
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!{range_name}").execute()
    data = result.get('values', [])
    if data:
        header = data[0]
        rows = [row + [None] * (len(header) - len(row)) for row in data[1:]]
        return pd.DataFrame(rows, columns=header)
    else:
        return pd.DataFrame()

# Function to append data to a sheet
def append_data(sheet_name, values):
    body = {"values": [values]}
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name,
        valueInputOption="RAW",
        body=body
    ).execute()
    return result

# Fetch initial data
def init_data():
    raw_form_df = fetch_data("Raw_Form_Responses", "A1:N1000")
    weight_data_df = fetch_data("Weight_Tracker", "A1:C1000")
    return raw_form_df, weight_data_df

raw_form_df, weight_data_df = init_data()
dynamic_users = weight_data_df.iloc[:, 2].unique()

# Initialize session state variables
session_state_defaults = {
    "selected_person": None,
    "selected_exercise": None,
    "mood_prior": None,
    "date_exercised": datetime.today(),
    "duration": 0,
    "distance": 0,
    "part_of_body": None,
    "reps": 0,
    "intensity": "Moderate",
    "mood_after": None,
    "notes": ""
}

for key, default in session_state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Form inputs
left_column, right_column = st.columns(2)

with left_column:
    st.session_state.selected_person = st.radio(
        "Who are you?*",
        dynamic_users,
        index=None,
        key="person_question"
    )

st.session_state.date_exercised = st.date_input(
    "Which date did you exercise?",
    value=st.session_state.date_exercised,
    key="date_exercised_question"
)

selected_datetime = datetime.combine(st.session_state.date_exercised, datetime.now().time())
formatted_datetime = selected_datetime.strftime("%d/%m/%Y %H:%M:%S")

activity_options = ["Cycling", "Strength", "Yoga", "Running", "Meditation", "Hiking"]
st.session_state.selected_exercise = st.selectbox(
    "Which activity have you completed?*",
    activity_options,
    key="exercise_type_question"
)

mood_options = {
    "Very Unhappy": "😟 Sluggish, Tired, Drained",
    "Unhappy": "🙁 Frustrated, Low Energy",
    "Neutral": "😐 Okay, Balanced, Indifferent",
    "Happy": "🙂 Content, Energetic, Positive",
    "Very Happy": "😁 Proud, Excited, Accomplished"
}

with st.container():
    st.session_state.mood_prior = st.radio(
        "Mood Prior to Exercising*",
        options=list(mood_options.keys()),
        format_func=lambda mood: f"{mood_options[mood]} {mood}",
        key="test_mood_prior_question"
    )

st.session_state.duration = st.slider(
    "How long were you active for?*",
    min_value=0,
    max_value=400,
    step=15,
    key="duration_question"
)

st.session_state.distance = st.slider(
    "How far did you travel?",
    min_value=0,
    max_value=40,
    step=1,
    key="distance_question"
)

st.session_state.part_of_body = st.selectbox(
    "Which part of the body did you focus on?",
    ("Upper Body", "Chest", "Core", "Legs", "Whole Body"),
    index=None,
    placeholder="Select from this list.",
    key="part_of_body_question"
)

st.session_state.reps = st.slider(
    "How many individual reps did you complete?",
    min_value=0,
    max_value=400,
    step=15,
    key="reps_question"
)

intensity_mapping = {
    "Very Light": 1,
    "Light": 2,
    "Moderate": 3,
    "Hard": 4,
    "Very Hard": 5,
}

st.session_state.intensity = st.select_slider(
    "Select the perceived intensity of your workout*:",
    options=list(intensity_mapping.keys()),
    value=st.session_state.intensity,
    key="perceived_intensity_question"
)

with st.container():
    st.session_state.mood_after = st.radio(
        "Mood After Exercising*",
        options=list(mood_options.keys()),
        format_func=lambda mood: f"{mood_options[mood]} {mood}",
        key="mood_after_num_question"
    )

st.session_state.notes = st.text_area(
    "Is there anything else useful you would like to record?",
    placeholder="Write your thoughts down here.",
    key="notes_question"
)

if st.button("Log your activity!!"):
    required_fields = [
        st.session_state.selected_person,
        st.session_state.selected_exercise,
        st.session_state.mood_prior,
        st.session_state.date_exercised,
        st.session_state.duration,
        st.session_state.intensity,
        st.session_state.mood_after
    ]

    if all(required_fields):
        values = [
            formatted_datetime,
            st.session_state.selected_exercise,
            st.session_state.mood_prior,
            st.session_state.duration,
            st.session_state.distance,
            st.session_state.part_of_body,
            st.session_state.reps,
            st.session_state.intensity,
            st.session_state.mood_after,
            st.session_state.notes,
            st.session_state.selected_person
        ]
        try:
            append_data("Raw_Form_Responses", values)
            st.success("Data saved successfully!")
        except Exception as e:
            st.error(f"Failed to save data: {e}")
    else:
        st.error("Please fill in all required fields.")
