import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

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
st.write("This interactive dashboard provides insights into how the Lens Cleaning System (LCS) impacts the performance of the BC3D over time. Use the filters to explore trends.")

# Load the CSV data into a pandas DataFrame
@st.cache_data
def load_data():
    file_path = 'report_hw_27092024.csv'  # Update with the correct path to your CSV file
    try:
        df = pd.read_csv(file_path)
        # Replace 'null' strings with actual NaN values
        df.replace('null', np.nan, inplace=True)
        df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')
        return df
    except ValueError as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        return None

df = load_data()

if df is not None:
    # Filter the data for valid dates and necessary columns
    df_filtered = df.dropna(subset=['utcTime', 'systemName', 'bucketCamera'])

    # --- Sidebar for Filter Options ---
    st.sidebar.title("Filters")
    
    # Filter based on LCS presence or not
    lcs_presence_filter = st.sidebar.selectbox(
        'Choose LCS Installation Status:',
        ('Has LCS', 'No LCS')
    )

    # Apply filter for systems with or without LCS
    if lcs_presence_filter == 'Has LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == True]
    elif lcs_presence_filter == 'No LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == False]

    # List of available system names after filtering by LCS status
    available_system_names = sorted(df_filtered['systemName'].unique())

    # Sidebar dropdown for selecting system name
    selected_system = st.sidebar.selectbox(
        'Select System:',
        available_system_names,
        key='selected_system'
    )

    # Filter the data by the selected system name
    df_filtered = df_filtered[df_filtered['systemName'] == selected_system]

    # Map bucketCamera values to cleanliness-related statuses
    bucket_camera_mapping = {
        0: "Good Condition",
        1: "Requires Cleaning",
        2: "Requires Adjustment",
        4: "Camera feed is black",
        5: "Camera condition unknown",
        6: "Mono Left/Right faulty",
        7: "Damaged"
    }
    df_filtered['cameraStatus'] = df_filtered['bucketCamera'].map(bucket_camera_mapping)

    # Group the data by date and aggregate counts for cleanliness status
    df_filtered['date'] = df_filtered['utcTime'].dt.date
    camera_trend = df_filtered.groupby(['date', 'cameraStatus']).size().unstack(fill_value=0).reset_index()

    # --- Line Chart for Bucket Camera Cleanliness Trend ---
    fig = go.Figure()

    if 'Good Condition' in camera_trend.columns:
        fig.add_trace(go.Scatter(
            x=camera_trend['date'],
            y=camera_trend['Good Condition'],
            mode='lines+markers',
            name='Good Condition (Clean)',
            line=dict(color='#00B7F1', width=2),
            marker=dict(size=8)
        ))
    
    if 'Requires Cleaning' in camera_trend.columns:
        fig.add_trace(go.Scatter(
            x=camera_trend['date'],
            y=camera_trend['Requires Cleaning'],
            mode='lines+markers',
            name='Requires Cleaning',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))

    fig.update_layout(
        title=f'Bucket Camera Cleanliness Trend for System: {selected_system} ({lcs_presence_filter})',
        xaxis_title='Date',
        yaxis_title='Count',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Display the cleanliness trend line chart
    st.plotly_chart(fig, use_container_width=True, key="camera_cleanliness_trend")

    # --- Pie chart based on bucketCamera aggregated by selected time frame ---
    # Sum the bucketCamera conditions over the time period for the pie chart
    bucket_camera_counts = df_filtered['bucketCamera'].value_counts()
    bucket_camera_counts.index = bucket_camera_counts.index.map(bucket_camera_mapping)

    # Create and display the pie chart
    fig_pie = go.Figure(data=[go.Pie(labels=bucket_camera_counts.index, 
                                     values=bucket_camera_counts.values)])

    fig_pie.update_layout(title="Bucket Camera Conditions", height=600, font=dict(size=18))

    st.plotly_chart(fig_pie, use_container_width=True, key="bucket_camera_conditions")

else:
    st.error("Failed to load data. Please check your CSV file and try again.")
