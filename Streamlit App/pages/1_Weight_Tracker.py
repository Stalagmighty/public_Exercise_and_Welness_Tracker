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

# Read data for Weight Tracker
weight_data_df = fetch_data("Weight_Tracker", "A1:D1000")  # Adjust range as needed

# Data Preparation Section
filtered_weight_data = weight_data_df.copy()

# Convert Timestamp to datetime and create Date column
filtered_weight_data["Timestamp"] = pd.to_datetime(filtered_weight_data["Timestamp"], errors="coerce")
filtered_weight_data["Date"] = filtered_weight_data["Timestamp"].dt.date

# Convert Current Weight to numeric
filtered_weight_data["Current Weight"] = pd.to_numeric(filtered_weight_data["Current Weight"], errors="coerce")

# Put Date column at front of filtered_weight_data table and Timestamp at the back
filtered_weight_data = filtered_weight_data[['Date'] + [col for col in filtered_weight_data.columns if col != 'Date']]
filtered_weight_data = filtered_weight_data[[col for col in filtered_weight_data.columns if col != 'Timestamp'] + ['Timestamp']]

# Display the filtered data in Streamlit
st.subheader("Weight Tracker Data")
filtered_weight_data = filtered_weight_data[[col for col in filtered_weight_data.columns if col != 'Timestamp'] + ['Timestamp']]

# Create Line Graph
# Add Gradual Trend Line

# Sort weight data by timestamp
filtered_weight_data = filtered_weight_data.sort_values('Timestamp')

# Calculate start and end dates for the trend line
regime_start_date = datetime(2025,1,1)
regime_end_date = regime_start_date + timedelta(days=6 * 30) # Approx 6 months

# Define the trend line data (80kg - 70g)
weight_trend_line_data = {
    'Date':[regime_start_date, regime_end_date],
    'Weight': [80, 70]
}

# Calculate the dynamic y-axis (min weight)
min_weight = min(filtered_weight_data['Current Weight'])
y_axis_min = min(68, min_weight-2)

weight_Line_fig = px.line(
    filtered_weight_data,
    x='Date',
    y='Current Weight',
    title= 'Weight Tracker',
)

# Add the trend line
weight_Line_fig.add_trace(
    go.Scatter(
        x=weight_trend_line_data['Date'],
        y=weight_trend_line_data['Weight'],
        mode='lines',
        name='Trend Line',
        line=dict(color='orange', dash='dot'),
        showlegend=False  # Hide it from the legend
    )
)

# Set y-axis with a dynamics range
weight_Line_fig.update_layout(
    yaxis=dict(
        range=[y_axis_min, None]
    )
)

# Add Horizontal Target Line

target_weight = 70
weight_Line_fig.add_hline(
    y=target_weight,
    line_color="red",
    line_dash="dash",
    annotation_text=f"Target Weight: {target_weight} kg",
    annotation_position="top left"
)

st.plotly_chart(weight_Line_fig)


# Display (toggle) filtered weight data
use_filtered_weight_data = st.checkbox("Display All Weight Data", value=False, key="weight_data_display_toggle")

if use_filtered_weight_data:
    st.dataframe(filtered_weight_data)
else:
    ""

# Embedd Arnie Image
st.image("https://www.trainmag.com/wp-content/uploads/2017/08/Arnold-Schwarzenegger-Now-Hero.jpg")

