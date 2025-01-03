import streamlit as st
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from streamlit_date_picker import date_range_picker, date_picker, PickerType

# --------- Streamlit Layout -----------

# Set page configuration
st.set_page_config(page_title="Exercise and Wellness Tracker", layout="centered")

# Add fire icons to the title
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        Exercise and Wellness Tracker🔥
    </h1>
    """,
    unsafe_allow_html=True
)

# Authenticate with the Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)

# Build the API service
service = build('sheets', 'v4', credentials=credentials)

# Fetch data from specific worksheets in the Google Sheet
SPREADSHEET_ID = "1dgjmSBRlBNNjQMQkj1jaFS6ml_uOTh0Gec5X1WsgCao"

# Function to fetch data from a specific sheet
def fetch_data(sheet_name, range_name):
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!{range_name}").execute()
    data = result.get('values', [])
    if data:
        header = data[0]
        # Ensures each row has the same number
        # of elements as the header by appending None values for any missing columns.
        rows = [row + [None] * (len(header) - len(row)) for row in data[1:]]
        return pd.DataFrame(rows, columns=header)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no data

# Read data for Raw Form Responses
raw_form_df = fetch_data("Raw_Form_Responses", "A1:R1000")
filtered_df = raw_form_df.copy()

# Read data for users
user_df = fetch_data("App_Users", "A1:B1000")  # Adjust range as needed
filtered_user_df = user_df.copy()

# Read data for Inspirational Quotes
inspirational_quotes_df = fetch_data("Inspirational_Quotes", "A1:C100")
filtered_inspirational_quotes_df = inspirational_quotes_df.copy()

# Read data for Regime
regime_df = fetch_data("Regime", "A1:D100")
filtered_regime_df = regime_df.copy()

# STREAMLIT SECTION

# ------------ Data Preparation ---------------

# Convert Timestamp to day first datetime type
filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], dayfirst=True)

if all(isinstance(val, pd.Timestamp) for val in filtered_df['Timestamp']):
    print("All values are datetime")
else:
    print("Not all values are datetime")


# Set Duration as numeric
filtered_df['Duration'] = pd.to_numeric(filtered_df['Duration'], errors="coerce")

# Set Distance as numeric
filtered_df = filtered_df.rename(columns={'Optional: Distance (miles)': 'Distance in Miles'})
filtered_df['Distance in Miles'] = pd.to_numeric(filtered_df['Distance in Miles'], errors="coerce")

# Set number of reps as numeric
filtered_df = filtered_df.rename(columns={'Optional: Strength: Reps': 'Reps'})
filtered_df['Reps'] = pd.to_numeric(filtered_df['Reps'], errors="coerce")

# Set exercise types
all_exercise_types = [
    "Cycling",
    "Strength",
    "Yoga",
    "Running",
    "Meditation",
    "Hiking",
]

# Inspiration Quote

# Inspirational Quotes Section

# Convert 'Number' column to numeric, coercing errors to NaN
filtered_inspirational_quotes_df['Number'] = pd.to_numeric(filtered_inspirational_quotes_df['Number'], errors='coerce')

# Select and display random quote
if not filtered_inspirational_quotes_df.empty:
    random_quote = filtered_inspirational_quotes_df.sample().iloc[0]
    quote_text = random_quote['Quote']
    quote_author = random_quote['Author']

    # Display quote
    st.markdown(
        f"<h4 style='font-size:32px; text-align:left;'>&ldquo;{quote_text}&rdquo;</h4>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<h5 style='text-align:left; color:gray;'>— {quote_author}</h5>",
        unsafe_allow_html=True
    )
else:
    st.write("No quotes available to display.")

st.write("----")

# Filters Section

# Filters Section
with st.container():
    # Define two columns: left for exercise filter, right for user filter
    left_column, right_column = st.columns([1, 1])  # Equal-width columns; adjust as needed

    # Exercise Type Filter in the Left Column
    with left_column:
        exercise_types = ["All Exercise Types"] + all_exercise_types
        exercise_type_filter = st.selectbox(
            "Select the Exercise Type",
            exercise_types,
            index=0
        )

        # Filter DataFrame by Exercise Type
        if exercise_type_filter != "All Exercise Types":
            filtered_df = filtered_df[filtered_df["Exercise Type"] == exercise_type_filter]

    # User Filter in the Right Column
    with right_column:
        dynamic_users = filtered_user_df.iloc[1].unique()
        app_users_plus_all = ["All app users"] + list(dynamic_users)

        app_user_filter = st.multiselect(
            "Select which users to filter by.",
            options=app_users_plus_all,
            default="All app users"
        )

        # Filter DataFrame by Users
        if "All app users" in app_user_filter:
            # If "All App Users" is selected, show all data
            filtered_df = filtered_df
        else:
            # Filter for specific users
            filtered_df = filtered_df[filtered_df["User"].isin(app_user_filter)]



# Date Range Picker and week filter

# Create Week and Year columns for filtering
filtered_df["Year"] = filtered_df["Timestamp"].dt.isocalendar().year
filtered_df["Week"] = filtered_df["Timestamp"].dt.isocalendar().week

# Add a toggle to enable or disable the week picker
use_week_picker = st.sidebar.checkbox("Enable Week Picker", value=False, key="week_picker_toggle")

# Week Picker
if use_week_picker:
    st.markdown("Week Range Picker")
    default_start, default_end = datetime.now() - timedelta(days=7), datetime.now()
    refresh_value = timedelta(days=7)
    refresh_buttons = [
        {'button_name': 'Refresh Last 1 Week', 'refresh_value': refresh_value}
    ]

    # Week picker with default range
    date_range_string = date_range_picker(
        picker_type=PickerType.week,
        start=default_start,
        end=default_end,
        key='week_range_picker',
        refresh_buttons=refresh_buttons
    )

    # Filter based on the date range picker
    if date_range_string:
        # Extract year and week from the picker output
        year, week_str = date_range_string[0].split('-')
        week_number = int(''.join(filter(str.isdigit, week_str)))  # Extract digits from '1st', '2nd', etc.
        year = int(year)

        st.write(f"Selected Year: {year}, Week: {week_number}")

        # Filter dataframe by the selected week
        filtered_df = filtered_df[(filtered_df["Year"] == year) & (filtered_df["Week"] == week_number)]
    else:
        st.write("No valid range selected. Showing all data.")
else:
    st.write("")

# Month date picker

# Add a toggle to enable or disable the month date picker
use_month_picker = st.sidebar.checkbox("Enable Month Picker", value=False, key="month_picker_toggle")

if use_month_picker:
    st.markdown("#### Month Range Picker")

    # Set default start and end to the previous and current month
    today = datetime.now()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)

    default_start = first_day_last_month
    default_end = today

    refresh_value = timedelta(days=30)
    refresh_buttons = [
        {'button_name': 'Refresh Last 1 Month', 'refresh_value': refresh_value}
    ]

    # Month picker with default range
    date_range_string = date_range_picker(
        picker_type=PickerType.month,
        start=default_start,
        end=default_end,
        key='month_range_picker',
        refresh_buttons=refresh_buttons
    )

    # Process the selected date range
    if date_range_string:
        # Extract start and end from the picker
        start, end = date_range_string

        # Convert the string values to datetime objects
        start = datetime.strptime(start, "%Y-%m")
        end = datetime.strptime(end, "%Y-%m")

        # Adjust the end date to include the entire month
        end = end.replace(day=1) + timedelta(days=32)
        end = end.replace(day=1) - timedelta(days=1)  # Set to the last day of the month

        # Display the formatted date range
        st.write(f"Selected Month Range: {start.strftime('%Y-%m')} to {end.strftime('%Y-%m')}")

        # Ensure your dataframe has datetime-compatible dates
        if "Timestamp" in filtered_df.columns:
            filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"])

        # Filter dataframe by the selected month range
        filtered_df = filtered_df[
            (filtered_df["Timestamp"] >= start) &
            (filtered_df["Timestamp"] <= end)
            ]
    else:
        st.write("No valid range selected. Showing all data.")
else:
    st.write("")

# Filter the dataframe by exercise


# ------ Visualisations --------------------------------------------


# Get the current day of the week
day_of_week = datetime.today().strftime('%A')

# Find today's exercise
exercise_for_today = regime_df.loc[regime_df['Day of Week'] == day_of_week, 'Type'].values
if len(exercise_for_today) > 0:
    exercise_for_today = exercise_for_today[0]  # Get the first match
else:
    exercise_for_today = "No exercise scheduled"

# Create two columns
left_column, right_column = st.columns(2)

with right_column:
    st.markdown(
        f"<div style='font-size: 32px;'>"
        f"Today's Exercise: <span style='color: yellow;'>{exercise_for_today}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# Todays's Date
with left_column:
    st.markdown(
        f"<div style='font-size: 32px;'>"
        f"Today's Date: <span style='color: white;'>{datetime.today().strftime('%d/%m/%y')}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


# Create rows of cards using st.columns
row1 = st.columns(2)
row2 = st.columns(2)
row3 = st.columns(2)

# Count of number of times exercised
num_times_exercised = len(filtered_df['Timestamp'])

# Add 'num_times_exercised' to the first card
with row1[0]:
    with st.container():
        st.markdown(f"<h1 style='text-align: center; color: white;'>{num_times_exercised} times</h1>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<h6 style='text-align: center;'>Exercised since records began</h1>",
            unsafe_allow_html=True
        )

# Number of hours exercised
num_minutes_exercised = np.sum(filtered_df['Duration'])
num_hours_exercised = round(num_minutes_exercised/60, 1)

# Add 'num_hours_exercised' to card
with row1[1]:
    with st.container():
        # Display the large font number
        st.markdown(
            f"<h1 style='text-align: center; color: white;'>{num_hours_exercised} hours</h1>",
            unsafe_allow_html=True
        )
        # Display the smaller subtitle underneath
        st.markdown(
            f"<h6 style='text-align: center; color: white;'>Exercised since records began</h6>",
            unsafe_allow_html=True
        )

# Number of miles travelled
num_miles_travelled = np.sum(filtered_df['Distance in Miles'])

# Add 'num_hours_exercised' to card
with row2[0]:
    with st.container():
        # Display the large font number
        st.markdown(
            f"<h1 style='text-align: center; color: white;'>{num_miles_travelled} miles</h1>",
            unsafe_allow_html=True
        )
        # Display the smaller subtitle underneath
        st.markdown(
            f"<h6 style='text-align: center; color: white;'>Travelled since records began</h6>",
            unsafe_allow_html=True
        )

# Number of miles travelled
num_reps_completed = np.sum(filtered_df['Reps'])

# Add 'num_reps' to the card
with row2[1]:
    with st.container():
        # Display the large font number
        st.markdown(
            f"<h1 style='text-align: center; color: white;'>{num_reps_completed} reps</h1>",
            unsafe_allow_html=True
        )
        # Display the smaller subtitle underneath
        st.markdown(
            f"<h6 style='text-align: center; color: white;'>Completed since records began</h6>",
            unsafe_allow_html=True
        )

# Streak Tracker

# Create list of all virtual dates
virtual_dates_list_start_date = '2024-01-01'
virtual_dates_list_end_date = datetime.today().date()
full_virtual_date_range = pd.date_range(start=virtual_dates_list_start_date, end=virtual_dates_list_end_date)

# Create Dataframe from list of virtual dates
full_virtual_date_df = pd.DataFrame({'Virtual_Dates': full_virtual_date_range})
full_virtual_date_df["Virtual_Dates"] = pd.to_datetime(full_virtual_date_df["Virtual_Dates"]).dt.date

# Extract unique exercise dates from actual data
filtered_df["Date"] = pd.to_datetime(filtered_df["Timestamp"]).dt.date
unique_exercise_dates = set(filtered_df['Date'])

# Mark each virtual date as active or inactive
# Add a column 'Active' to indicate whether exercise occurred on each virtual date
# (1 if the date is in exercise_dates, otherwise 0)
full_virtual_date_df['Active'] = (
    full_virtual_date_df['Virtual_Dates'].apply
    (lambda x: 1 if x in unique_exercise_dates else 0))

# Initialize variables to track the current streak and store all streak values

current_streak = 0
streaks = []

# Iterate through the 'Active' column to calculate streaks

for active in full_virtual_date_df['Active']:
    if active == 1:
        current_streak += 1
    else:
        current_streak = 0
    streaks.append(current_streak)

# Add the calculated streak values as a new columns in filtered and virtual dataframes
full_virtual_date_df['Streak'] = streaks

# Calculate longest streak
longest_streak = full_virtual_date_df['Streak'].max()

# Display 'card' for streaks
with row3[0]:
    with st.container():
        # Display the large font number
        st.markdown(
            f"<h1 style='text-align: center; color: white;'>{current_streak} sessions</h1>",
            unsafe_allow_html=True
        )
        # Display the smaller subtitle underneath
        st.markdown(
            f"<h6 style='text-align: center; color: white;'>In your current streak</h6>",
            unsafe_allow_html=True
        )

with row3[1]:
    with st.container():
        # Display the large font number
        st.markdown(
            f"<h1 style='text-align: center; color: white;'>{longest_streak} sessions</h1>",
            unsafe_allow_html=True
        )
        # Display the smaller subtitle underneath
        st.markdown(
            f"<h6 style='text-align: center; color: white;'>Is your streak to beat</h6>",
            unsafe_allow_html=True
        )

if current_streak == 0:
    st.markdown(f"<h1 style='text-align: center; color: orange;"
                f"'>Get back on the horse, you'll feel better for it!!</h6>",
            unsafe_allow_html=True)
else:
    st.write("")

# Ensure this doesn't interfere with other layouts
# Any additional content should go below the card section
st.markdown("---")


# Write average Mood prior
#"Average Mood Prior to Exercising"

#Return mean of Mood prior to exercising (numerical)
#av_mood_prior = filtered_df.iloc[:, 2].astype(float).mean() # astype(float) ensures numeric value returned
#av_mood_prior

# Display the dataframe
if st.sidebar.checkbox("Show Filtered Data", value=False):
    st.markdown("### Filtered Data")
    st.dataframe(filtered_df)

# Display raw data
if st.sidebar.checkbox("Show Raw Data", value=False):
    st.markdown("### Raw Data")
    st.dataframe(raw_form_df)
