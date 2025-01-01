import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_date_picker import date_range_picker, date_picker, PickerType

# --------- Streamlit Layout -----------

# Set page configuration
st.set_page_config(page_title="Exercise Frequency Tracker", layout="wide")

# Title
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        Exercise Frequency Tracker 💪
    </h1>
    """,
    unsafe_allow_html=True,
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
        rows = [row + [None] * (len(header) - len(row)) for row in data[1:]]  # Normalize row lengths
        return pd.DataFrame(rows, columns=header)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no data

# Read data for Raw Form Responses
raw_form_df = fetch_data("Raw_Form_Responses", "A1:N1000")  # Adjust range as needed

# Read data for Inspirational Quotes (optional)
inspirational_quotes_df = fetch_data("Inspirational_Quotes", "A1:C100")  # Adjust range as needed

# Initialize filtered DataFrame for Raw Form Responses
filtered_df = raw_form_df.copy()

# STREAMLIT SECTION

# Data Preparation: Example for converting and renaming columns
filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"], dayfirst=True, errors="coerce")
filtered_df["Duration"] = pd.to_numeric(filtered_df["Duration"], errors="coerce")
filtered_df.rename(columns={"Optional: Distance (miles)": "Distance in Miles"}, inplace=True)
filtered_df["Distance in Miles"] = pd.to_numeric(filtered_df["Distance in Miles"], errors="coerce")

# ------------ Data Preparation ---------------

# Convert Timestamp to day first datetime type
filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], dayfirst=True)

if all(isinstance(val, pd.Timestamp) for val in filtered_df['Timestamp']):
    print("All values are datetime")
else:
    print("Not all values are datetime")


# Set Duration as numeric
filtered_df['Duration'] = pd.to_numeric(filtered_df['Duration'], errors="coerce")

# Set Distance as numbric
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




#top-level filters

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
    st.write("Week Picker is disabled. Showing all data.")

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
    st.write("Month Picker is disabled. Showing all data.")

# Display raw data
if st.sidebar.checkbox("Show Raw Data", value=False):
    st.markdown("### Raw Data")
    st.dataframe(df)

# Display the dataframe
if st.sidebar.checkbox("Show Filtered Data", value=False):
    st.markdown("### Filtered Data")
    st.dataframe(filtered_df)

# Filter the dataframe by exercise

# Add "All Exercise Types" to the filter options
exercise_types = ["All Exercise Types"] + all_exercise_types
exercise_type_filter = st.selectbox("Select the Exercise Type", exercise_types, index=0)


if exercise_type_filter != "All Exercise Types":
    filtered_df = filtered_df[filtered_df["Exercise Type"] == exercise_type_filter]

# Identify missing exercise types (those not in the dataframe)
missing_exercises = set(all_exercise_types) - set(filtered_df["Exercise Type"])


# Exercise Days Recent and Over Time

# Convert datestamp to weekday, number, and year number
filtered_df['Day of Week'] = filtered_df['Timestamp'].dt.day_name()
filtered_df['Week Number'] = filtered_df['Timestamp'].dt.isocalendar().week
filtered_df['Year'] = filtered_df['Timestamp'].dt.year

# Group and count occurrences of each exercise type
exercise_type_chart_data = filtered_df['Exercise Type'].value_counts().reset_index()
exercise_type_chart_data.columns = ['Exercise Type', 'Count']

# Create time of day bar chart
exercise_type_bar = go.Figure(
    data=[
        go.Bar(
            x=exercise_type_chart_data['Exercise Type'],  # Use the column for x-axis
            y=exercise_type_chart_data['Count'],          # Use the column for y-axis
            name="Exercise Type",
            marker=dict(color='skyblue'),  # Customize bar color
        )
    ],
    layout=dict(
        title="Exercise Sessions by Type",
        bargap=0.2,          # Gap between bars
        barcornerradius=15,  # Rounded corners for bars
    )
)

# Display the chart in Streamlit
st.plotly_chart(exercise_type_bar, use_container_width=True)

# Heatmaps

# Set number and layout of columns
left_column, right_column = st.columns(2)

# Ensure all days of the week are included, even if no exercise happens
all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = (
    filtered_df.groupby(['Year', 'Week Number', 'Day of Week']).size()
    .unstack(fill_value=0)  # Fill missing combinations with 0
    .reindex(columns=all_days, fill_value=0)  # Ensure all days of the week are included
)



# Overall Heatmap in the Left Column
overall_heatmap = heatmap_data.sum(axis=0).to_frame(name="Total Count").T
fig_overall = px.imshow(
overall_heatmap,
    labels={"x": "Day of Week", "y": " ", "color": "Total Exercises"},
    title="Overall Exercise Frequency by Day of Week",
    color_continuous_scale="Blues",
    text_auto=True,
)
st.plotly_chart(fig_overall, use_container_width=True)

# Function to calculate week range using ISO calendar
def calculate_week_range(year, week):
    # Find the first day of the week
    week_start = datetime.fromisocalendar(year, week, 1)  # ISO week starts on Monday
    week_end = week_start + timedelta(days=6)  # Add 6 days to get Sunday
    return week_start.date(), week_end.date()

# Weekly Heatmap: Sidebar Selection
selected_week_heatmap = st.sidebar.selectbox(
    "Select Week for Weekly Heatmap",
    options=heatmap_data.index,  # Use the MultiIndex directly
    format_func=lambda x: f"Week {x[1]} {x[0]} [{calculate_week_range(x[0], x[1])[0]} - {calculate_week_range(x[0], x[1])[1]}]",
)

# Extract selected year and week
selected_year, selected_week = selected_week_heatmap

# Weekly Heatmap
try:
    weekly_data_heatmap = heatmap_data.loc[(selected_year, selected_week)].to_frame(name="Count").T

    # Title Text
    weekly_heatmap_title_text = f"Week {selected_week} {selected_year} [{calculate_week_range(selected_year, selected_week)[0]} - {calculate_week_range(selected_year, selected_week)[1]}]"

    # Create the heatmap using Plotly
    fig_weekly = px.imshow(
        weekly_data_heatmap,
        labels={"x": "Day of Week", "y": " ", "color": "Exercises"},
        title=weekly_heatmap_title_text,
        color_continuous_scale="blues",
        text_auto=True,
    )
    st.plotly_chart(fig_weekly, use_container_width=True)
except KeyError:
    st.error("The selected week's data is unavailable. Please select another week.")

# Time of Day Exercised

# Create dictionary of times of day
time_of_day = {
    "Morning": range(6, 12),   # 6 AM to 11:59 AM
    "Afternoon": range(12, 17),  # 12 PM to 4:59 PM
    "Evening": range(17, 21),   # 5 PM to 8:59 PM
    "Night": range(21, 6),    # 9 PM to 5:59 AM (wraps around midnight)
}

# Function to classify time of day
def classify_time_of_day(hour):
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"

# Apply classification
filtered_df['time_of_day'] = (
    filtered_df['Timestamp'].dt.hour.apply(classify_time_of_day))

# Count Occurrences
time_of_day_counts = filtered_df['time_of_day'].value_counts()

# Re-order times of day into logical sequence
time_logical_order = ["Morning", "Afternoon", "Evening", "Night"]
time_of_day_counts = time_of_day_counts.reindex(time_logical_order, fill_value=0) # Ensures the order and handles missing categories

# Create time of day bar chart
time_of_day_bar = go.Figure(
    data=[
        go.Bar(
            x=time_of_day_counts.index,
            y=time_of_day_counts.values,
            name="Exercise Sessions",
            marker=dict(color='skyblue'),  # You can customize the color
        )
    ],
    layout=dict(
        title="Exercise Sessions by Time of Day",
        bargap=0.2,
        barcornerradius=15,  # Adds rounded corners

    )
)
st.plotly_chart(time_of_day_bar)