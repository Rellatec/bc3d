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
    ('LCS On', 'LCS Off')
)

# Load the Excel data into a pandas DataFrame
file_path = 'report_hw_27092024.xlsx'  # Update with the correct path
df = pd.read_excel(file_path)

# Convert the 'utcTime' column to datetime
df['utcTime'] = pd.to_datetime(df['utcTime'], errors='coerce')

# Filter the data for valid dates and necessary columns
df_filtered = df.dropna(subset=['utcTime', 'hasLCS', 'MainStatusMC', 'sourceID'])

# Apply the filter based on the 'hasLCS' column (True for On, False for Off)
if filter_option == 'LCS On':
    df_filtered = df_filtered[df_filtered['hasLCS'] == True]
elif filter_option == 'LCS Off':
    df_filtered = df_filtered[df_filtered['hasLCS'] == False]

# Filter out invalid or missing MainStatusMC values
valid_statuses = ['GOOD', 'WRONG', 'AVERAGE']
df_filtered = df_filtered[df_filtered['MainStatusMC'].isin(valid_statuses)]

# Group the data by month and sourceID
df_filtered['month'] = df_filtered['utcTime'].dt.to_period('M')
df_filtered['month'] = df_filtered['month'].dt.to_timestamp()

# Create an option to select specific sourceID from the sidebar
source_ids = df_filtered['sourceID'].unique()
selected_source = st.sidebar.selectbox('Select Source ID:', source_ids)

# Filter the data by the selected sourceID
df_filtered = df_filtered[df_filtered['sourceID'] == selected_source]

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

# Status counts
total_good = df_filtered[df_filtered['MainStatusMC'] == 'GOOD'].shape[0]
total_wrong = df_filtered[df_filtered['MainStatusMC'] == 'WRONG'].shape[0]
total_average = df_filtered[df_filtered['MainStatusMC'] == 'AVERAGE'].shape[0]

# Bar chart for status counts
fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(x=['GOOD', 'WRONG', 'AVERAGE'], 
                         y=[total_good, total_wrong, total_average],
                         marker=dict(color=['#00B7F1', 'red', '#DAA520'])))

fig_bar.update_layout(title="Overview", xaxis_title="Status", yaxis_title="Count", template='plotly_white')
col2.plotly_chart(fig_bar, use_container_width=True)
