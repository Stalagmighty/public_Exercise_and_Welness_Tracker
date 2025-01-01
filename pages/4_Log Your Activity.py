import streamlit as st
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from streamlit_date_picker import date_range_picker, date_picker, PickerType

# Page and data configuration

# Set page configuration
st.set_page_config(page_title="Exercise and Wellness Tracker", layout="centered")

left_column, right_column = st.columns(2)

# Add fire icons to the title
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        📈️Log Your Activity🤸‍♀️
    </h1>
    """,
    unsafe_allow_html=True
)

# Authenticate with the Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)

# Build the API service
service = build('sheets', 'v4', credentials=credentials)

# Fetch data from specific worksheets in the Google Sheet
SPREADSHEET_ID = "1dgjmSBRlBNNjQMQkj1jaFS6ml_uOTh0Gec5X1WsgCao"


# Function to fetch data from a specific sheet
def fetch_data(

        sheet_name, range_name):
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                 range=f"{sheet_name}!{range_name}").execute()
    data = result.get('values', [])
    if data:
        header = data[0]
        rows = [row + [None] * (len(header) - len(row)) for row in data[1:]]  # Normalize row lengths
        return pd.DataFrame(rows, columns=header)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no data


def append_data(sheet_name, values):
    body = {
        "values": [values]
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name,
        valueInputOption="RAW",
        body=body
    ).execute()
    return result


# Read data for Raw Form Responses
raw_form_df = fetch_data("Raw_Form_Responses", "A1:N1000")
filtered_df = raw_form_df.copy()

# ------ Input Section ------

# Exercise Type Question
person_input = st.radio(
    "Who are you?*",
    ["Tom C",
     "Pete C"],
    index=None,
    key="person_question"
)

activity_options = [
    "Cycling",
    "Strength",
    "Yoga",
    "Running",
    "Meditation",
    "Hiking"
]

# Exercise Type Question
exercise_type_input = st.selectbox(
    "Which activity have you completed?*",
    activity_options,
    index=None,
    placeholder="Please select an activity.",
    key="exercise_type_question"
)

# Map user-friendly labels to standardised values
activity_mapping = {
    "Cycling (or other cardio except hiking/walking)": "Cycling",
    "Strength (weights or climbing etc.)": "Strength",
    "Yoga": "Yoga",
    "Running": "Running",
    "Meditation": "Meditation",
    "Hiking/Fast Walking": "Hiking/Fast Walking"
}

# Get the standardised value using the selected input
activity_type = activity_mapping.get(exercise_type_input)

st.write("--------")

# Mood prior to exercising question

# Define mood options with corresponding emoji and descriptions
mood_options = {
    "Very Unhappy": "😟 Sluggish, Tired, Drained",
    "Unhappy": "🙁 Frustrated, Low Energy",
    "Neutral": "😐 Okay, Balanced, Indifferent",
    "Happy": "🙂 Content, Energetic, Positive",
    "Very Happy": "😁 Proud, Excited, Accomplished"
}

# Wrap the columns within a container to maintain position
with st.container():
    st.markdown("### Mood Prior to Exercising*")  # Section Title

    # Create columns
    left_column, right_column = st.columns(2)

    # Display mood radio buttons in the left column
    with left_column:
        mood_prior_num_input = st.radio(
            label="Select your mood:",
            options=list(mood_options.keys()),
            format_func=lambda mood: f"{mood_options[mood]} {mood}",  # Display emoji + label
            key="test_mood_prior_question"
        )

        # Display the selected value
        st.write(f"Selected Mood: {mood_prior_num_input}")

    # Display mood description text area in the right column
    with right_column:
        mood_prior_text_input = st.text_area(
            "Describe your prior to being active.",
            placeholder="Describe how you felt in a couple of sentences."
        )

weather_input = st.selectbox(
    "What was the weather like during your activity?*",
    (
        "Sunny",
        "Partly Cloudy",
        "Overcast",
        "Rainy",
        "Stormy (Thunder/Lightning)",
        "Snowy",
        "Hail",
        "Windy",
        "Foggy",
        "Humid"),
    index=None,
    placeholder="Please select the weather type",
    key="weather_question"
)

st.write("--------")


duration_input = st.slider(
    "How long were you active for?*",
    min_value=0,
    max_value=400,
    step=15,
    key="duration_question"
)

distance_input = st.slider(
    "How far did you travel?",
    min_value=0,
    max_value=40,
    step=1,
    key="distance_question"
)

part_of_body_input = st.selectbox(
    "Which part of the body did you focus on?",
    (
        "Upper Body",
        "Chest",
        "Core",
        "Legs",
        "Whole Body"),
    index=None,
    placeholder="Select from this list.",
    key="part_of_body_question"
)

# Reps question

reps_input = st.slider(
    "How many individual reps did you complete?",
    min_value=0,
    max_value=400,
    step=15,
    key="reps_question",

)

# Perceived Intensity Question

# Define the perceived intensity options and their numeric mappings
intensity_mapping = {
    "Very Light": 1,
    "Light": 2,
    "Moderate": 3,
    "Hard": 4,
    "Very Hard": 5,
}

st.write("--------")

# Create a select slider
intensity_selected = st.select_slider(
    "Select the perceived intensity of your workout*:",
    options=list(intensity_mapping.keys()),  # Display words to the user
    value="Moderate",  # Default value,
    key="perceived_intensity_question",
)

# Map the selected word to its corresponding numeric value
intensity_numeric = intensity_mapping[intensity_selected]

# Mood after activity


# Define mood options with corresponding emoji and descriptions
mood_options = {
    "Very Unhappy": "😟 Sluggish, Tired, Drained",
    "Unhappy": "🙁 Frustrated, Low Energy",
    "Neutral": "😐 Okay, Balanced, Indifferent",
    "Happy": "🙂 Content, Energetic, Positive",
    "Very Happy": "😁 Proud, Excited, Accomplished"
}

# Wrap the "Mood After Exercising" section in a container
with st.container():
    st.markdown("### Mood After Exercising*")  # Section Title

    # Create columns for layout
    left_column, right_column = st.columns(2)

    # Display mood radio buttons in the left column
    with left_column:
        mood_after_num_input = st.radio(
            label="Select your mood:",
            options=list(mood_options.keys()),
            format_func=lambda mood: f"{mood_options[mood]} {mood}",  # Display emoji + label
            key="mood_after_num_question"
        )

        # Display the selected value
        st.write(f"Selected Mood: {mood_after_num_input}")

    # Display mood description text area in the right column
    with right_column:
        mood_after_text_input = st.text_area(
            "Describe how you felt after being active.",
            placeholder="Describe how you felt in a couple of sentences.",
            key="mood_after_text_question"
        )

st.write("--------")

# Notes Question

notes_input = st.text_area(
    "Is there anything else useful you would like to record?",
    placeholder="Write your thoughts down here.",
    key="notes_question"
)

# Exercise tags (will probably delete later but handling here for now)

exercise_tags = "N/A"

# Log activity button

if st.button("Log your activity!!"):
    # Validate required fields
    if person_input and exercise_type_input and mood_prior_num_input and weather_input and duration_input and intensity_numeric and mood_after_num_input:
        # Collect data for all columns
        values = [
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),  # Timestamp
            exercise_type_input,  # Exercise Type
            mood_prior_num_input,  # Mood prior to exercising (numerical)
            weather_input,  # Weather
            mood_prior_text_input,  # Mood prior to exercising (text)
            duration_input,  # Duration
            distance_input,  # Distance travelled
            part_of_body_input,  # Part of body
            reps_input,  # Individual reps completed
            intensity_numeric,  # Perceived intensity of the workout
            mood_after_num_input,  # Mood prior to workout (numeric)
            mood_after_text_input,  # Mood after workout (text)
            exercise_tags,  # Will likely delete later
            notes_input,  # Anything else useful
            person_input,  # Who is logging
        ]

        # Try to save the data
        try:
            append_data("Raw_Form_Responses", values)  # Replace "YourSheetName" with your sheet name
            st.success("Data saved successfully!")
        except Exception as e:
            st.error(f"Failed to save data: {e}")
    else:
        st.error("Please fill in all required fields.")

