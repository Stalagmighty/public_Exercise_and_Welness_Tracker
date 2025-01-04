import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# App Prep

# Set page configuration
st.set_page_config(page_title="Weight Tracker", layout="centered")

# Title
st.markdown(
    f"""
    <h1 style='text-align: center;'>
        Weight Tracker 📊
    </h1>
    """,
    unsafe_allow_html=True,
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


# Read data for Weight Tracker
weight_data_df = fetch_data("Weight_Tracker", "A1:D1000")  # Adjust range as needed

# Read data for users
user_df = fetch_data("App_Users", "A1:B1000")  # Adjust range as needed

# Data Preparation Section
filtered_weight_data = weight_data_df.copy()

# Convert Timestamp to datetime and create Date column
filtered_weight_data["Timestamp"] = pd.to_datetime(
    filtered_weight_data["Timestamp"], errors="coerce"
)
filtered_weight_data["Date"] = filtered_weight_data["Timestamp"].dt.date

# Convert Current Weight to numeric
filtered_weight_data["Current Weight"] = pd.to_numeric(
    filtered_weight_data["Current Weight"], errors="coerce"
)

# Reorganize columns: Date to front, Timestamp to back
filtered_weight_data = filtered_weight_data[
    ['Date'] + [col for col in filtered_weight_data.columns if col != 'Date']
]
filtered_weight_data = filtered_weight_data[
    [col for col in filtered_weight_data.columns if col != 'Timestamp'] + ['Timestamp']
]

# Display the filtered data in Streamlit
st.subheader("Weight Tracker Data")

# User Filter
dynamic_users = user_df.iloc[:, 1].unique()

app_users_plus_all = ["All app users"] + list(dynamic_users)

app_user_filter = st.multiselect(
    "Select which users to filter by.",
    options=app_users_plus_all,
    default="All app users",
    key="User Filter"
)

# Filter DataFrame by Users
if "All app users" in app_user_filter:
    # If "All App Users" is selected, show all data
    filtered_weight_data = filtered_weight_data
else:
    # Filter for specific users
    filtered_weight_data = filtered_weight_data[filtered_weight_data["User"].isin(app_user_filter)]

# Sort weight data by timestamp
filtered_weight_data = filtered_weight_data.sort_values('Timestamp')

# Current weight input

# Weight checkbox behaviour
current_weight_checkbox = st.checkbox(
    "Log current weight",
    key="current_weight_checkbox",
    disabled=st.session_state.get("target_weight_checkbox", False)  # Disabled if the other checkbox is checked
)

target_weight_checkbox = st.checkbox(
    "Set target weight",
    key="target_weight_checkbox",
    disabled=current_weight_checkbox  # Disabled if current_weight_checkbox is checked
)

# Checkbox to toggle log activity functionality
if current_weight_checkbox:
    # Create a container for better organization
    with st.container():
        # Split layout into two columns
        col1, col2 = st.columns(2)

        # User selection in the left column
        with col1:
            app_user_selector_for_input = st.multiselect(
                "Select which app user you are from the list.",
                options=dynamic_users,
                placeholder="Select from list.",
                key="User Selector For Input",
            )
            current_user = app_user_selector_for_input

        # Weight input in the right column
        with col2:
            current_weight_input = st.text_input(
                "What is your current weight in kg?",
                placeholder="Please enter your weight using only numbers."
            )

        # Submit button centered below both columns
        if st.button("Log your current weight."):
            # Validate required fields
            if current_user and current_weight_input:
                # Collect data for all columns
                values = [
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),  # Timestamp
                    current_weight_input,
                    current_user[0] if current_user else "",  # Assuming single selection
                ]

                # Try to save the data
                try:
                    append_data("Weight_Tracker", values)  # Replace "Weight_Tracker" with your sheet name
                    st.success("Data saved successfully!")
                except Exception as e:
                    st.error(f"Failed to save data: {e}")
            else:
                st.error("Please fill in all required fields.")

# Target weight input

# Checkbox to toggle log activity functionality
if target_weight_checkbox:
    # Create a container for better organization
    with st.container():
        # Split layout into two columns
        col1, col2 = st.columns(2)

        # User selection in the left column
        with col1:
            app_user_selector_for_input = st.multiselect(
                "Select which app user you are from the list.",
                options=dynamic_users,
                placeholder="Select from list.",
                key="User Selector For Input2",
            )
            current_user = app_user_selector_for_input

        # Weight input in the right column
        with col2:
            target_weight_input = st.text_input(
                "What is your target weight in kg?",
                placeholder="Please enter your target weight using only numbers."
            )

        # Target date input in the right column
        with col2:
            target_date = st.date_input(
                "Which date would you like to reach your target weight by?",
                datetime.today().date() + timedelta(90),
                min_value=datetime.today(),
                key="target_date_question"

            )

        # Submit button centered below both columns
        if st.button("Log your target weight."):
            # Validate required fields
            if current_user and current_weight_input and target_date:
                # Collect data for all columns
                values = [
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),  # Timestamp
                    current_user[0] if current_user else "",  # Assuming single selection
                    target_weight_input,
                    target_date.strftime("%d/%m/%Y %H:%M:%S"),

                ]

                # Try to save the data
                try:
                    append_data("Weight_Tracker", values)  # Replace "Weight_Tracker" with your sheet name
                    st.success("Data saved successfully!")
                except Exception as e:
                    st.error(f"Failed to save data: {e}")
            else:
                st.error("Please fill in all required fields.")



# Calculate start and end dates for the trend line
regime_start_date = datetime(2025, 1, 1)
regime_end_date = regime_start_date + timedelta(days=6 * 30)  # Approx 6 months

# Define the trend line data (80kg - 70kg)
weight_trend_line_data = {
    'Date': [regime_start_date, regime_end_date],
    'Weight': [80, 70],
}

# Calculate the dynamic y-axis (min weight)
min_weight = min(filtered_weight_data['Current Weight'])
y_axis_min = min(68, min_weight - 2)

# Create Line Graph
weight_Line_fig = px.line(
    filtered_weight_data,
    x='Date',
    y='Current Weight',
    title='Weight Tracker',
    markers=False,
    color='User'
)

# Add the trend line
weight_Line_fig.add_trace(
    go.Scatter(
        x=weight_trend_line_data['Date'],
        y=weight_trend_line_data['Weight'],
        mode='lines',
        name='Trend Line',
        line=dict(color='orange', dash='dot'),
        showlegend=False,  # Hide from legend
    )
)

# Set y-axis with a dynamic range
weight_Line_fig.update_layout(
    yaxis=dict(range=[y_axis_min, None])
)

# Set user target weights
user_target_weights = {
    "Tom C": 72,
    "Pete C": 85,
    "Saffi": 53,
    "Maximus": 100,

}

# Extract color mapping from the chart
# This gets the assigned colors for each user
user_colors = {trace['name']: trace['line']['color'] for trace in weight_Line_fig.to_dict()['data']}

# Add target lines for users
if "All app users" in app_user_filter:
    # Add target lines for all users
    for user, target_weight in user_target_weights.items():
        if user in user_colors:  # Check if the user has a color in the chart
            weight_Line_fig.add_hline(
                y=target_weight,
                line_color=user_colors[user],  # Match the user's line color
                line_dash="dash",
                annotation_text=f"{user} Target: {target_weight} kg",
                annotation_position="top left"
            )
else:
    # Add target lines only for selected users
    for user in app_user_filter:
        if user in user_target_weights and user in user_colors:
            target_weight = user_target_weights[user]
            weight_Line_fig.add_hline(
                y=target_weight,
                line_color=user_colors[user],  # Match the user's line color
                line_dash="dash",
                annotation_text=f"{user} Target: {target_weight} kg",
                annotation_position="top left"
            )

# Display the line chart
st.plotly_chart(weight_Line_fig)

# Display (toggle) filtered weight data
use_filtered_weight_data = st.checkbox(
    "Display All Weight Data", value=False, key="weight_data_display_toggle"
)

if use_filtered_weight_data:
    st.dataframe(filtered_weight_data)

# Embed Arnie Image
st.image("https://www.trainmag.com/wp-content/uploads/2017/08/Arnold-Schwarzenegger-Now-Hero.jpg")
