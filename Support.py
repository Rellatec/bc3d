import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

# --- Page Configuration ---
st.set_page_config(page_title="Bucket Camera & LCS Performance Dashboard", layout="wide")

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
st.title('Bucket Camera and LCS Performance Analysis')
st.write("This interactive dashboard provides insights into the performance of the BC3D bucket camera and Lens Cleaning System (LCS) over time. Use the filters to explore trends.")

# Load the CSV data into a pandas DataFrame
@st.cache_data
def load_data():
    file_path = 'report_hw_27092024.csv'  # Update with the correct path to your CSV file
    try:
        df = pd.read_csv(file_path)
        df.replace('null', np.nan, inplace=True)
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
    df_filtered = df.dropna(subset=['utcTime', 'bucketCamera', 'lcsStatus'])

    # --- Sidebar for Filter Options ---
    st.sidebar.title("Filters")
    
    lcs_presence_filter = st.sidebar.selectbox(
        'Choose LCS Installation Status:',
        ('Has LCS', 'Has not LCS')
    )

    if lcs_presence_filter == 'Has LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == True]
    elif lcs_presence_filter == 'Has not LCS':
        df_filtered = df_filtered[df_filtered['hasLCS'] == False]

    available_system_names = sorted(df_filtered['systemName'].unique())

    selected_system = st.sidebar.selectbox(
        'Select System:',
        available_system_names,
        key='selected_system'
    )

    df_filtered = df_filtered[df_filtered['systemName'] == selected_system]

    time_aggregation = st.sidebar.selectbox(
        'Select Time Aggregation:',
        ('Daily', 'Weekly', 'Monthly')
    )

    if time_aggregation == 'Daily':
        df_filtered['date'] = df_filtered['utcTime'].dt.date
        group_by = 'date'
    elif time_aggregation == 'Weekly':
        df_filtered['date'] = df_filtered['utcTime'].dt.to_period('W').apply(lambda r: r.start_time)
        group_by = 'date'
    else:
        df_filtered['date'] = df_filtered['utcTime'].dt.to_period('M').apply(lambda r: r.start_time)
        group_by = 'date'

    # Simplify Bucket Camera Conditions for Bar Chart
    df_filtered['bucketCameraStatus'] = df_filtered['bucketCamera'].replace({1: 'Dirty', 3: 'Dirty'})
    df_filtered['bucketCameraStatus'] = df_filtered['bucketCameraStatus'].apply(lambda x: 'Other' if x not in ['Dirty'] else x)

    # Bucket Camera Condition Bar Chart with custom colors
    bucket_camera_trend = df_filtered.groupby([group_by, 'bucketCameraStatus']).size().unstack(fill_value=0).reset_index()

    fig_bucket_bar = go.Figure()
    fig_bucket_bar.add_trace(go.Bar(
        x=bucket_camera_trend[group_by],
        y=bucket_camera_trend['Dirty'],
        name='Dirty',
        marker_color='red'  # Set color to red for Dirty condition
    ))
    fig_bucket_bar.add_trace(go.Bar(
        x=bucket_camera_trend[group_by],
        y=bucket_camera_trend['Other'],
        name='Other',
        marker_color='#00B7F1'  # Set color to blue for Other condition
    ))

    fig_bucket_bar.update_layout(
        title=f'Bucket Camera Condition Bar Chart ({time_aggregation}) for System: {selected_system}',
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

    st.plotly_chart(fig_bucket_bar, use_container_width=True, key="bucket_camera_bar")

    # LCS Working vs. Not Working Bar Chart with custom colors
    df_filtered['lcsStatus'] = df_filtered['lcsStatus'].replace({0: 'OFF', 1: 'ON'})
    lcs_trend = df_filtered.groupby([group_by, 'lcsStatus']).size().unstack(fill_value=0).reset_index()

    fig_lcs_bar = go.Figure()
    fig_lcs_bar.add_trace(go.Bar(
        x=lcs_trend[group_by],
        y=lcs_trend['ON'],
        name='LCS ON',
        marker_color='#00B7F1'  # Set color to blue for ON status
    ))
    fig_lcs_bar.add_trace(go.Bar(
        x=lcs_trend[group_by],
        y=lcs_trend['OFF'],
        name='LCS OFF',
        marker_color='red'  # Set color to red for OFF status
    ))

    fig_lcs_bar.update_layout(
        title=f'LCS Status Bar Chart ({time_aggregation}) for System: {selected_system}',
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

    st.plotly_chart(fig_lcs_bar, use_container_width=True, key="lcs_status_bar")

    # Pie Chart for Bucket Camera Conditions with Original Categories
    bucket_camera_mapping = {
        0: "Good Condition",
        1: "Requires Cleaning",
        2: "Requires Adjustment",
        4: "Camera feed is black",
        5: "Camera condition unknown",
        6: "Mono Left/Right faulty",
        7: "Damaged"
    }

    df_filtered['bucketCamera'] = df_filtered['bucketCamera'].replace({3: 1})
    bucket_camera_counts = df_filtered.groupby(group_by)['bucketCamera'].value_counts().unstack(fill_value=0)
    bucket_camera_totals = bucket_camera_counts.sum().reset_index()
    bucket_camera_totals.columns = ['bucketCamera', 'Count']
    bucket_camera_totals['bucketCamera'] = bucket_camera_totals['bucketCamera'].map(bucket_camera_mapping)

    fig_pie = go.Figure(data=[go.Pie(labels=bucket_camera_totals['bucketCamera'], 
                                     values=bucket_camera_totals['Count'])])

    fig_pie.update_layout(
        title=f"Bucket Camera Conditions ({time_aggregation})",
        height=600,
        font=dict(size=18)
    )

    st.plotly_chart(fig_pie, use_container_width=True, key="bucket_camera_conditions")

else:
    st.error("Failed to load data. Please check your CSV file and try again.")
