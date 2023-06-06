import pandas as pd

# read the CSV files
df_commit = pd.read_csv('commit_messages.csv')
df_status = pd.read_csv('AllEIPS.csv')

# fill missing values with a dummy string
df_commit['File'] = df_commit['File'].fillna('missing')

# then proceed with the split operation
df_commit['EIP'] = df_commit['File'].apply(lambda x: int(x.split('-')[1].split('.')[0]) if '-' in x else None)


# extract the EIP number from the 'Number' column in the status DataFrame
df_status['EIP'] = df_status['Number']

# perform the join operation based on the 'EIP' column
df = pd.merge(df_commit, df_status, on='EIP', how='left')

# save the result to a new CSV file
df.to_csv('result.csv', index=False)