// This code finds the 10 top most companies in our cross-sectional data and create dummy variables of that data

//I will use python code to create this code
cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum Project Data\"
use "Ethereum_Cross-sectional_Data.dta", clear

python:
import pandas as pd
from collections import Counter

# Load data from Stata into a pandas DataFrame
stata_data = pd.read_stata("Ethereum_Cross-sectional_Data.dta")

# Define a custom delimiter that is unlikely to appear in your data
custom_delimiter = '|'

# Concatenate all author_company columns into one Series with the custom delimiter
all_companies = stata_data[['author1_company1', 'author2_company1', 'author3_company1', 'author4_company1', 'author5_company1', 'author6_company1', 'author7_company1', 'author8_company1', 'author9_company1', 'author10_company1', 
'author11_company1','author12_company1','author13_company1','author14_company1','author15_company1']].apply(lambda row: custom_delimiter.join(row), axis=1)
							
							
# Split the concatenated string by the custom delimiter to create a list of all companies
all_companies_list = [company.strip() for company in ' '.join(all_companies).split(custom_delimiter) if company.strip() != '' and company.strip() != '']

# Count the frequencies of each company
company_counts = Counter(all_companies_list)

# Get the top 10 most frequent companies
top_10_companies = company_counts.most_common(10)

# Create a DataFrame with original and modified company names
company_names_df = pd.DataFrame({'original_company_name': [company for company, _ in top_10_companies],
                                 'modified_company_name': [company.replace(' ', '_').replace('.', '_').replace(',', '_').lower() for company, _ in top_10_companies]})

for _, row in company_names_df.iterrows():
    original_name = row['original_company_name']
    modified_name = row['modified_company_name']
    
    # Create a dummy variable for the company
    stata_data[f'dummy_{modified_name}'] = (all_companies.str.contains(original_name)).astype(int)
    
    # Save the DataFrame with dummy variables to an Excel file
stata_data.to_excel('stata_data_with_dummies.xlsx', index=False)
end

// import newly created excel file into stata and move variables

import excel "stata_data_with_dummies.xlsx", sheet("Sheet1") firstrow clear

	foreach v of varlist(dummy_spearbit_labs-dummy_chainsafe_systems){
	move `v' author1
}

// create success variable for statistical analysis
// fix living
replace status = "Living" if status == "Living "

gen success = 0
replace success = 1 if status == "Final"
replace success =. if status == "Last Call"|status == "Living"|status == "Review"
move success status

gen implementation = 1 if inFork != ""
replace implementation = 0 if Implementable == 1 & implementation != 1
replace implementation = . if Implementable ==0
move implementation status

// create time to finalization

gen time_to_final = (edate - sdate) /86400000
move time_to_final Category

format title %20s
format author %20s

save "Ethereum_Cross-sectional_Data", replace

