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
st.markdown("This interactive dashboard provides insights into how the Lens Cleaning System (LCS) impacts the performance of the BC3D over time.The analysis is based on performance statuses from 'statusCalc', which reflect the overall health and cleanliness of the cameras. Use the filters to explore trends.")

# --- Sidebar for Filter Options ---
st.sidebar.title("Filters")
filter_option = st.sidebar.selectbox(
    'Choose LCS Status to display:',
    ('LCS On', 'LCS Off', 'Both')
)

# Load the Excel data into a pandas DataFrame
file_path = 'report_hw_27092024.xlsx'  # Update with the correct path
df = pd.read_excel(file_path)

# Convert the 'utcTime' column to datetime
df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')

# Filter the data for valid dates and necessary columns
df_filtered = df.dropna(subset=['utcTime', 'lcsStatus', 'statusCalc'])

# Apply the filter based on user selection (LCS On, LCS Off, Both)
if filter_option == 'LCS On':
    df_filtered = df_filtered[df_filtered['lcsStatus'] == 1.0]
elif filter_option == 'LCS Off':
    df_filtered = df_filtered[df_filtered['lcsStatus'] == 0.0]

# Filter out invalid or missing statusCalc values
valid_statuses = ['GOOD', 'WRONG', 'AVERAGE']
df_filtered = df_filtered[df_filtered['statusCalc'].isin(valid_statuses)]

# Group the data by month
df_filtered['month'] = df_filtered['utcTime'].dt.to_period('M')
df_filtered['month'] = df_filtered['month'].dt.to_timestamp()

# Count occurrences of each status by month
lcs_trend_month = df_filtered.groupby(['month', 'statusCalc']).size().unstack(fill_value=0)

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
    title=f'Bucket Camera Performance Trends Over Months ({filter_option})',
    xaxis_title='Month', yaxis_title='Count', legend_title='Status', template='plotly_white'
)
col1.plotly_chart(fig, use_container_width=True)

# Status counts
total_good = df_filtered[df_filtered['statusCalc'] == 'GOOD'].shape[0]
total_wrong = df_filtered[df_filtered['statusCalc'] == 'WRONG'].shape[0]
total_average = df_filtered[df_filtered['statusCalc'] == 'AVERAGE'].shape[0]

# Bar chart for status counts
fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(x=['GOOD', 'WRONG', 'AVERAGE'], 
                         y=[total_good, total_wrong, total_average],
                         marker=dict(color=['#00B7F1', 'red', '#DAA520'])))
fig_bar.update_layout(title="Overview", xaxis_title="Status", yaxis_title="Count", template='plotly_white')
col2.plotly_chart(fig_bar, use_container_width=True)

# --- Generate Report in Markdown ---
st.markdown(f"""
    ## LCS Performance Report

    ### Summary:
    This report provides a summary of bucket camera performance based on the LCS statuses categorized as **GOOD**, **WRONG**, and **AVERAGE**. The total counts of each status are provided below for the selected filter (**{filter_option}**):

    ### Insights:
    - The bucket camera recorded a total of **{total_good} GOOD** statuses, indicating that the camera was in good condition.
    - **{total_wrong} WRONG** statuses were recorded, indicating issues with the camera's feed.
    - The camera registered **{total_average} AVERAGE** statuses, indicating that the camera required cleaning.
""")
