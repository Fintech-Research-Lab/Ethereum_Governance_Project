import pandas as pd

commit_history_df = pd.read_csv('commit_history.csv')

# Convert the 'Commit Date' column to datetime
commit_history_df['Commit Date'] = pd.to_datetime(commit_history_df['Commit Date'])

# Sort by 'File' and 'Commit Date'
commit_history_df = commit_history_df.sort_values(['File', 'Commit Date'])

results_df = pd.DataFrame(columns=['File', 'First Commit Message', 'First Commit Date', 'Final Commit Message', 'Final Commit Date'])

for file in commit_history_df['File'].unique():
    file_commits = commit_history_df[commit_history_df['File'] == file]

    # Get the first commit
    first_commit = file_commits.iloc[0]

    # Get the final commit (with the word "final" in the message)
    final_commits = file_commits[file_commits['Commit Message'].str.contains('Final', case=False)]
    if not final_commits.empty:
        final_commit = final_commits.iloc[-1]
    else:
        final_commit = pd.Series()

    # Add the results to the DataFrame
    results_df = results_df.append({
        'File': file,
        'First Commit Message': first_commit['Commit Message'],
        'First Commit Date': first_commit['Commit Date'],
        'Final Commit Message': final_commit.get('Commit Message'),
        'Final Commit Date': final_commit.get('Commit Date')
    }, ignore_index=True)

results_df.to_csv('commit_messages.csv', index=False)
