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

# Load the CSV data into a pandas DataFrame
@st.cache_data
def load_data():
    file_path = 'report_hw_27092024.csv'  # Update with the correct path to your CSV file
    try:
        df = pd.read_csv(file_path)
        df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')
        return df
    except ValueError as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        return None

df = load_data()

if df is not None:
    # Filter the data for valid dates and necessary columns
    df_filtered = df.dropna(subset=['utcTime', 'hasLCS', 'MainStatusMC', 'systemName', 'bucketCamera'])

    # --- Sidebar for Filter Options ---
    st.sidebar.title("Filters")
    filter_option = st.sidebar.selectbox(
        'Choose LCS Status to display:',
        ('Has LCS', 'Has not LCS')
    )

    # Apply the filter based on the 'hasLCS' column (True for On, False for Off)
    if filter_option == 'Has LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == True]
    elif filter_option == 'Has not LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == False]

    # Filter out invalid or missing MainStatusMC values
    valid_statuses = ['GOOD', 'WRONG', 'AVERAGE']
    df_filtered = df_filtered[df_filtered['MainStatusMC'].isin(valid_statuses)]

    # Map MainStatusMC to new labels
    status_mapping = {
        'GOOD': 'Led is Working',
        'WRONG': 'Led needs Adjustment',
        'AVERAGE': 'Needs Cleaning'
    }
    df_filtered['MainStatusMC'] = df_filtered['MainStatusMC'].map(status_mapping)

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

    # Group the data by month and systemName
    df_filtered['month'] = df_filtered['utcTime'].dt.to_period('M')
    df_filtered['month'] = df_filtered['month'].dt.to_timestamp()

    # Count occurrences of each status by month for the selected system
    lcs_trend_month = df_filtered.groupby(['month', 'MainStatusMC']).size().unstack(fill_value=0)

    # Layout with columns to organize the dashboard
    col1, col2 = st.columns([3, 1])

    # Plot trends with custom colors
    fig = go.Figure()
    status_colors = {'Led Working': '#00B7F1', 'Needs Adjustment': 'red', 'Needs Cleaning': '#DAA520'}
    for status in lcs_trend_month.columns:
        fig.add_trace(go.Scatter(x=lcs_trend_month.index, y=lcs_trend_month[status], 
                                 mode='lines+markers', name=f'{status}', 
                                 line=dict(color=status_colors.get(status, 'gray'))))

    fig.update_layout(
        title=f'Bucket Camera Performance Trends Over Months for System: {selected_system} ({filter_option})',
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
        1: "Requires Cleaning",
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
else:
    st.error("Failed to load data. Please check your CSV file and try again.")
