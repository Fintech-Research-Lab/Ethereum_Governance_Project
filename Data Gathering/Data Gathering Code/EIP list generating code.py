import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://eips.ethereum.org/all"

response = requests.get(url)
response.raise_for_status()
response.encoding = 'utf-8'

soup = BeautifulSoup(response.text, 'html.parser')

# Scope down to the div where the tables are
post_content = soup.find('div', class_='post-content')
if post_content is None:
    raise ValueError("No post-content div found")

# Find all tables within the post-content div
tables = post_content.find_all('table')
if not tables:
    raise ValueError("No tables found")

# Find all category names within the post-content div
categories = [header.text.strip() for header in post_content.find_all('h2')]
print("Categories extracted:", categories)

# Ensure equal number of tables and categories
if len(tables) != len(categories):
    raise ValueError("Mismatch in number of categories and tables")

data = []

for category, table in zip(categories, tables):
    rows = table.find_all('tr')
    if not rows:
        raise ValueError(f"No rows found in {category} table")
    
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) >= 3:  # Check if at least 3 columns exist
            # If 4th column exists, take 1st, 3rd and 4th columns
            if len(cols) >= 4:
                selected_data = [cols[0].text.strip(), cols[2].text.strip(), cols[3].text.strip(), category]
            # If 4th column does not exist, take the first three columns
            else:
                selected_data = [col.text.strip() for col in cols[:3]]
                selected_data.append(category)
            data.append(selected_data)



if not data:
    raise ValueError("No data found")

column_names = ['EIP', 'Title', 'Author', 'Status']
df = pd.DataFrame(data, columns=column_names)
df.to_csv('allEIPsandAuthorsv2.csv', index=False)
