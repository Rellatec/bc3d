import pandas as pd

# Load the Excel file with the merged column
try:
    df = pd.read_excel('Book 1_merged.xlsx')
    print("Merged Excel file loaded successfully.")
except FileNotFoundError:
    print("Error: 'Book 1_merged.xlsx' not found.")
    exit()
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit()

# Function to split the 'merged' column safely
def split_merged_column(merged_value):
    if isinstance(merged_value, str) and '-' in merged_value:
        return merged_value.split('-', 1)  # Split only once at the first hyphen
    else:
        return [merged_value, None]  # Return the original value and None if not split-able

# Apply the splitting function to create two new columns
df[['merged_systemName', 'merged_sourceID']] = pd.DataFrame(df['merged'].apply(split_merged_column).tolist(), index=df.index)

# Function to match sourceID with 'merged_sourceID' and return systemName
def find_system_name(source_id):
    result = df.loc[df['merged_sourceID'] == str(source_id), 'merged_systemName']
    return result.values[0] if not result.empty else 'Not Found'

# Apply the function for each sourceID in the 'sourceID' column
df['matched_systemName'] = df['sourceID'].apply(find_system_name)

# Save the updated DataFrame to a new Excel file
output_file_path = 'Book_1_with_systemNames.xlsx'
df.to_excel(output_file_path, index=False)
print(f"Updated data with matched system names saved to {output_file_path}")
