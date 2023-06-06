import pandas as pd

commit_history_df = pd.read_csv('commit_history.csv')

commit_history_df['Commit Date'] = pd.to_datetime(commit_history_df['Commit Date'])

commit_history_df = commit_history_df.sort_values(['File', 'Commit Date'])

grouped = commit_history_df.groupby('File')

first_last_commit_df = pd.DataFrame(columns=["File", "First Commit Message", "First Commit Date", "Last Commit Message", "Last Commit Date"])

for name, group in grouped:
    first_commit = group.iloc[0]

    # Check if last commit message contains "Force usage of included LICENSE file"
    if "Force usage of included LICENSE file" in group.iloc[-1]['Commit Message']:
        last_commit = group.iloc[-2]  # If yes, select second last commit
    else:
        last_commit = group.iloc[-1]  # If no, select last commit

    first_last_commit_df = first_last_commit_df.append({
        "File": name,
        "First Commit Message": first_commit['Commit Message'],
        "First Commit Date": first_commit['Commit Date'],
        "Last Commit Message": last_commit['Commit Message'],
        "Last Commit Date": last_commit['Commit Date']
    }, ignore_index=True)

first_last_commit_df.to_csv('first_last_commit_v2.csv', index=False)
