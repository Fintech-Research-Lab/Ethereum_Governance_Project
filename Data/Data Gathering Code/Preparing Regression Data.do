// This code finds the 10 top most companies in our cross-sectional data and create dummy variables of that data

//I will use python code to create this code
cd "C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/"
use "Ethereum_Cross-sectional_Data.dta", clear

python:
import os
import pandas as pd

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")

linkedin = pd.read_csv("linkedin_Data.csv")
top_10_companies = linkedin[linkedin['company1'] != ""].groupby('company1').size().sort_values(ascending=False).head(10).reset_index()

cs = pd.read_stata("Ethereum_Cross-sectional_Data.dta")

for company in top_10_companies['company1']:
    column_name = f"{company}_dummy"
    cs[column_name] = (cs.loc[:, ['eip_number', 'author1_company1', 'author2_company1', 'author3_company1', 'author4_company1', 'author5_company1',
                  'author6_company1', 'author7_company1', 'author8_company1', 'author9_company1', 'author10_company1', 'author11_company1',
                  'author12_company1', 'author13_company1', 'author14_company1', 'author15_company1']] == company).any(axis=1).astype(int)

cs.to_excel('stata_data_with_dummies.xlsx', index=False)

end

// import newly created excel file into stata and move variables

import excel "stata_data_with_dummies.xlsx", sheet("Sheet1") firstrow clear

	foreach v of varlist(ConsenSys_dummy-Google_dummy){
	move `v' author1
}

// create success variable for statistical analysis
// fix living
replace status = "Living" if status == "Living "

gen success = 0
replace success = 1 if status == "Final"
replace success =. if status == "Last Call"|status == "Living"|status == "Review" | status == "Draft"
move success status

gen implementation = 1 if inFork != ""
replace implementation = 0 if Implementable == 1 & implementation != 1
replace implementation = . if Implementable ==0
move implementation status

// replace tw_follower/ gh_follower to 0

replace tw_follower = 0 if tw_follower ==.
replace gh_follower = 0 if gh_follower ==.

// create time to finalization

gen time_to_final = (edate - sdate) /86400000
move time_to_final Category

format title %20s
format author %20s

// create log measures for regressions

gen log_tw = log(1+tw_follower)
gen log_gh = log(1+gh_follower)

 
// create scaling variables 

gen tf_scale = tw_follower/1000 


save "Ethereum_Cross-sectional_Data", replace


