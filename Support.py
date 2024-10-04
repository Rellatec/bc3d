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
        # Drop rows where 'lcsStatus' or 'hasLCS' contain NaN
        df = df.dropna(subset=['lcsStatus', 'hasLCS'])
        df = df[df['systemGeneration'] == 'Gen 3']
        df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')
        return df
    except ValueError as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        return None

df = load_data()

if df is not None:
    # Filter the data for valid dates and necessary columns
    df_filtered = df.dropna(subset=['utcTime', 'lcsStatus', 'systemName', 'bucketCamera'])

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

    # Map 0 and 1 to 'OFF' and 'ON' for better readability in the lcsStatus column
    df_filtered['lcsStatus'] = df_filtered['lcsStatus'].replace({0: 'OFF', 1: 'ON'})

    # Add time aggregation selector
    time_aggregation = st.sidebar.selectbox(
        'Select Time Aggregation:',
        ('Daily', 'Weekly', 'Monthly')
    )

    # Prepare data based on selected time aggregation
    if time_aggregation == 'Daily':
        df_filtered['date'] = df_filtered['utcTime'].dt.date
        group_by = 'date'
    elif time_aggregation == 'Weekly':
        df_filtered['date'] = df_filtered['utcTime'].dt.to_period('W').apply(lambda r: r.start_time)
        group_by = 'date'
    else:  # Monthly
        df_filtered['date'] = df_filtered['utcTime'].dt.to_period('M').apply(lambda r: r.start_time)
        group_by = 'date'

    # Group the data by date and count ON and OFF statuses for LCS trend
    lcs_trend = df_filtered.groupby(group_by)['lcsStatus'].value_counts().unstack(fill_value=0).reset_index()

    # --- Line Chart for LCS Status Trend ---
    fig = go.Figure()
    
    if 'ON' in lcs_trend.columns:
        fig.add_trace(go.Scatter(
            x=lcs_trend[group_by],
            y=lcs_trend['ON'],
            mode='lines+markers',
            name='ON',
            line=dict(color='#00B7F1', width=2),
            marker=dict(size=8)
        ))
    
    if 'OFF' in lcs_trend.columns:
        fig.add_trace(go.Scatter(
            x=lcs_trend[group_by],
            y=lcs_trend['OFF'],
            mode='lines+markers',
            name='OFF',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))

    fig.update_layout(
        title=f'LCS Status Trend ({time_aggregation}) for System: {selected_system} ({lcs_presence_filter})',
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

    # Display the LCS trend line chart as the first chart
    st.plotly_chart(fig, use_container_width=True, key="lcs_status_trend")

    # --- Bar Chart for LCS Status Counts with Counts Displayed on Hover ---
    fig_bar = go.Figure()
    
    if 'ON' in lcs_trend.columns:
        fig_bar.add_trace(go.Bar(
            x=lcs_trend[group_by],
            y=lcs_trend['ON'],
            name='LCS Working (ON)',
            marker=dict(color='#00B7F1'),
            hovertemplate='LCS Working (ON): %{y}<extra></extra>'
        ))
    
    if 'OFF' in lcs_trend.columns:
        fig_bar.add_trace(go.Bar(
            x=lcs_trend[group_by],
            y=lcs_trend['OFF'],
            name='LCS Not Working (OFF)',
            marker=dict(color='red'),
            hovertemplate='LCS Not Working (OFF): %{y}<extra></extra>'
        ))

    fig_bar.update_layout(
        title=f'LCS Working vs. Not Working ({time_aggregation}) for System: {selected_system}',
        xaxis_title='Date',
        yaxis_title='Count',
        barmode='group',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Display the bar chart as the second chart
    st.plotly_chart(fig_bar, use_container_width=True, key="lcs_status_bar_chart")

    # --- Pie chart based on bucketCamera aggregated by selected time frame ---
    # Merge cleaning-related issues (bucketCamera values 1 and 3)
    df_filtered['bucketCamera'] = df_filtered['bucketCamera'].replace({3: 1})

    # Aggregate bucket camera data by selected time frame
    bucket_camera_counts = df_filtered.groupby(group_by)['bucketCamera'].value_counts().unstack(fill_value=0)

    # Sum the bucketCamera conditions over the time period for the pie chart
    bucket_camera_totals = bucket_camera_counts.sum().reset_index()
    bucket_camera_totals.columns = ['bucketCamera', 'Count']

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
    bucket_camera_totals['bucketCamera'] = bucket_camera_totals['bucketCamera'].map(bucket_camera_mapping)

    # Create and display the pie chart
    fig_pie = go.Figure(data=[go.Pie(labels=bucket_camera_totals['bucketCamera'], 
                                     values=bucket_camera_totals['Count'])])

    fig_pie.update_layout(title=f"Bucket Camera Conditions ({time_aggregation})", height=600, font=dict(size=18))

    st.plotly_chart(fig_pie, use_container_width=True, key="bucket_camera_conditions")

else:
    st.error("Failed to load data. Please check your CSV file and try again.")
