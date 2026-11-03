import csv
import re
input_file = 'data.csv'
output_file = 'eip_startdates.csv'
# Regex pattern to match the EIP number and the creation date
pattern = r"eip-(\d+).md:created: (\d{4}-\d{2}-\d{2})"
with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    # Write header
    writer.writerow(['EIP Number', 'Date'])
    for row in reader:
        match = re.search(pattern, row[0])
        if match:
            eip_number, date = match.groups()
            writer.writerow([eip_number, date])
print(f"Transformed data saved in {output_file}") (edited) 