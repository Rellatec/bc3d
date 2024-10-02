import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- Page Configuration ---
st.set_page_config(page_title="LCS Performance Dashboard", layout="wide")

# --- Simple CSS Styling for the Dashboard ---
st.markdown("""
    <style>
    .main {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
    }
    h1 {
        color: #00B7F1;
        font-family: Arial, sans-serif;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Title and Introduction ---
st.title('LCS Status and BC3D Performance Analysis')
st.write("This interactive dashboard provides insights into how the Lens Cleaning System (LCS) impacts the performance of the BC3D over time. The analysis is based on performance statuses from 'MainStatusMC', which reflect the overall health and cleanliness of the cameras. Use the filters to explore trends.")

# --- Sidebar for Filter Options ---
st.sidebar.title("Filters")
filter_option = st.sidebar.selectbox(
    'Choose LCS Status to display:',
    ('Has LCS', 'Has not LCS')
)

# Load the Excel data into a pandas DataFrame
file_path = 'report_hw_27092024.xlsx'  # Update with the correct path
df = pd.read_excel(file_path)

# Convert the 'utcTime' column to datetime
df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')

# Filter the data for valid dates and necessary columns
df_filtered = df.dropna(subset=['utcTime', 'hasLCS', 'MainStatusMC', 'sourceID', 'bucketCamera'])

# Apply the filter based on the 'hasLCS' column (True for On, False for Off)
if filter_option == 'LCS On':
    df_filtered = df_filtered[df_filtered['hasLCS'] == True]
elif filter_option == 'LCS Off':
    df_filtered = df_filtered[df_filtered['hasLCS'] == False]

# Filter out invalid or missing MainStatusMC values
valid_statuses = ['GOOD', 'WRONG', 'AVERAGE']
df_filtered = df_filtered[df_filtered['MainStatusMC'].isin(valid_statuses)]

# List of available source IDs after filtering by LCS status
available_source_ids = df_filtered['sourceID'].unique()

# Retain the previously selected source ID if it exists, otherwise use the first one
if 'selected_source' in st.session_state and st.session_state['selected_source'] in available_source_ids:
    selected_source = st.session_state['selected_source']
else:
    selected_source = available_source_ids[0]  # Default to the first available source ID

# Sidebar dropdown for selecting source ID
selected_source = st.sidebar.selectbox('Select Source ID:', available_source_ids, index=list(available_source_ids).index(selected_source))

# Store the selected source ID in session_state
st.session_state['selected_source'] = selected_source

# Filter the data by the selected sourceID
df_filtered = df_filtered[df_filtered['sourceID'] == selected_source]

# Group the data by month and sourceID
df_filtered['month'] = df_filtered['utcTime'].dt.to_period('M')
df_filtered['month'] = df_filtered['month'].dt.to_timestamp()

# Count occurrences of each status by month for the selected sourceID
lcs_trend_month = df_filtered.groupby(['month', 'MainStatusMC']).size().unstack(fill_value=0)

# Layout with columns to organize the dashboard
col1, col2 = st.columns([3, 1])

# Plot trends with custom colors
fig = go.Figure()
status_colors = {'GOOD': '#00B7F1', 'WRONG': 'red', 'AVERAGE': '#DAA520'}
for status in lcs_trend_month.columns:
    fig.add_trace(go.Scatter(x=lcs_trend_month.index, y=lcs_trend_month[status], 
                             mode='lines+markers', name=f'{status}', 
                             line=dict(color=status_colors.get(status, 'gray'))))

fig.update_layout(
    title=f'Bucket Camera Performance Trends Over Months for Source ID: {selected_source} ({filter_option})',
    xaxis_title='Month', yaxis_title='Count', legend_title='Status', template='plotly_white'
)
col1.plotly_chart(fig, use_container_width=True)

# --- Pie chart based on bucketCamera ---
# Merge cleaning-related issues (bucketCamera values 1 and 3)
df_filtered['bucketCamera'] = df_filtered['bucketCamera'].replace({3: 1})

# Count occurrences of all bucketCamera values (0-7)
bucket_camera_counts = df_filtered['bucketCamera'].value_counts()

# Map bucketCamera values to meaningful labels
bucket_camera_mapping = {
    0: "Good Condition",
    1: "Requires Cleaning / Cleaning & Adjustment needed",
    2: "Requires Adjustment",
    4: "Camera feed is black",
    5: "Camera condition unknown",
    6: "Mono Left/Right faulty",
    7: "Damaged"
}
bucket_camera_counts.index = bucket_camera_counts.index.map(bucket_camera_mapping)

# Create a pie chart
fig_pie = go.Figure(data=[go.Pie(labels=bucket_camera_counts.index, 
                                 values=bucket_camera_counts.values)])

# Update layout to make the pie chart larger and place it underneath
fig_pie.update_layout(title="Bucket Camera Conditions", height=600, font=dict(size=18))

# Display the pie chart underneath
st.plotly_chart(fig_pie, use_container_width=True)
