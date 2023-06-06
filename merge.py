import pandas as pd

# Load the two CSV files
commits = pd.read_csv('first_last_commit_v2.csv')
status = pd.read_csv('AllEIPS.csv')

# Extract EIP numbers from the commit history file names
commits['Number'] = commits['File'].apply(lambda x: int(x.split('-')[1].split('.')[0]))

# Merge the two DataFrames on EIP number
merged = pd.merge(commits, status, on='Number')

# Save the merged DataFrame to a new CSV file
merged.to_csv('merged_v2.csv', index=False)
