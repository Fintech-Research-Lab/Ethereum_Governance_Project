import os
import pandas as pd
import re
def extract_md(directory_path, output_csv_path):
    # List to store data from all markdown files
    data = []

    # Regular expression pattern to match the date/time line in markdown files
    pattern = r"### Meeting Date/Time: (.+)"

    # Loop through each file in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".md"):
            with open(os.path.join(directory_path, filename), 'r', encoding="utf-8") as file:
                file_content = file.read()

                # Search for the date/time pattern in the file content
                match = re.search(pattern, file_content)

                # Extract the date/time text directly
                date_time_text = match.group(1) if match else None

                # Extract filename without extension
                eip = os.path.splitext(filename)[0]
                data.append([eip, file_content, date_time_text])

    # Convert the list to a pandas dataframe
    df = pd.DataFrame(data, columns=["EIP", "Text", "Date"])

    # Save the dataframe to a CSV file
    df.to_csv(output_csv_path, index=False)


# Placeholder for testing
extract_md("/Users/user/Documents/Pycharm/DevCalls/AllCoreDevs-CL-Meetings", "devcalls.csv")