import csv
import re

def extract_author_data(input_file, output_file):
    with open(input_file, 'r') as file:
        csv_data = file.read()
    pattern = r'([\w\s]+)\s?\(@([^\s<>@]+)\)'
    matches = re.findall(pattern, csv_data)
    full_names = [match[0] for match in matches]
    usernames = [match[1] for match in matches]
    urls = [f'https://github.com/{username}' for username in usernames]
    data = list(zip(full_names, usernames, urls))
    unique_data = list(dict.fromkeys(data))
    output_rows = []
    for full_name, username, url in unique_data:
        followers = get_github_followers(url)
        if followers:
            output_row = {
                'Full Name': full_name,
                'GitHub Username': username,
                'URL': url,
                'GitHub Followers': followers
            }
        else:
            output_row = {
                'Full Name': full_name,
                'GitHub Username': username,
                'URL': url,
                'GitHub Followers': 'n/a'
            }
        output_rows.append(output_row)
        print(f"Author: {full_name}, GitHub Followers: {followers if followers else 'n/a'}")
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Full Name', 'GitHub Username', 'URL', 'GitHub Followers'])
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Data has been written to '{output_file}' successfully.")

def get_github_followers(url):
    # Implement your logic to fetch the GitHub followers for a given URL
    # Replace the following line with your implementation
    return "n/a"

input_file = "eips.csv"
output_file = "github_followers.csv"

extract_author_data(input_file, output_file)
