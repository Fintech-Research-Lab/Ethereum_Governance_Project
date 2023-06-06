import requests
import pandas as pd
from getpass import getpass

token = getpass("Enter your GitHub token: ")

headers = {
    "Authorization": f"token {token}"
}

api_url = "https://api.github.com"

repo_owner = "ethereum"
repo_name = "EIPs"

# Get the list of files in the repository
files_url = f"{api_url}/repos/{repo_owner}/{repo_name}/contents/EIPS"
files_response = requests.get(files_url, headers=headers)

# Check if the request was successful
if files_response.status_code != 200:
    print(f"Failed to get files: {files_response.status_code}")
    exit()

files = files_response.json()

commit_history_df = pd.DataFrame(columns=["File", "Commit SHA", "Commit Message", "Commit Date"])

for file in files:
    # Get the commit history for the file
    commits_url = f"{api_url}/repos/{repo_owner}/{repo_name}/commits?path=EIPS/{file['name']}"
    commits_response = requests.get(commits_url, headers=headers)

    if commits_response.status_code != 200:
        print(f"Failed to get commits for {file['name']}: {commits_response.status_code}")
        continue

    commits = commits_response.json()

    for commit in commits:
        # Add the commit to the DataFrame
        commit_history_df = commit_history_df.append({
            "File": file['name'],
            "Commit SHA": commit['sha'],
            "Commit Message": commit['commit']['message'],
            "Commit Date": commit['commit']['committer']['date']
        }, ignore_index=True)

commit_history_df.to_csv('commit_history.csv', index=False)
