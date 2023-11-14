// first we import updated commit file which contains the raw data of commitment and convert it into an stata file

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Commit Data\Eip Commit Data\"
clear
 import excel "eip_commit_beg.xlsx", sheet("Sheet1") firstrow
 rename EIP eip_number
 save "eip_commit_wip.dta", replace
 
 // import unique author ids with client information file
cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\" 
  import delimited "unique_author_names_with_id", clear
  save "author.dta", replace
  
  // merge commit data with authors using author_id
  cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Commit Data\Eip Commit Data\"
  use "eip_commit_wip.dta", clear
  rename Author_Id author_id
merge m:1 author_id using "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\author.dta"
drop if _merge == 2 // remove authors that did not add any 

// create a flag whether the commit author is an EIP author. If the commit author does not exist in our author list then we assume that commit author is not
// an EIP author. This is expressed in _merge == 1

gen eip_author_flag = 1 if author_id != .
replace eip_author_flag = 0 if eip_author_flag == .
drop _merge
// save this file as comit


// create a variable that identifies the total number of commits for each EIPs

bysort eip_number : gen total_commit = _N 
egen author_commit = total(eip_author_flag), by(eip_number)

save "eip_commit_wip.dta", replace


python :
import os
import pandas as pd
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/Eip Commit Data/")
stata = pd.read_stata("eip_commit_wip.dta")
contributors = stata[(stata['eip_author_flag'] == 0) & (stata['Author'] != "eth-bot")].groupby('eip_number')['Author'].nunique()
contributors = pd.DataFrame(contributors)
contributors.rename(columns={'Author': 'eip_contributors'}, inplace=True)
stata = pd.merge(stata,contributors, on = 'eip_number', how = 'left')
stata.to_excel("eip_commit.xlsx")
end

clear
import excel "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Commit Data\Eip Commit Data\eip_commit.xlsx", sheet("Sheet1") firstrow clear

save "eip_commit_wip.dta", replace

// add meeting dates as event in the commit data

python:
import pandas as pd
import os as os

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/Eip Commit Data/")
data = pd.read_csv("Calls_Updated_standardized.csv")
data =data[data['EIP_Mention'] == True] # remove false from the data
commit = pd.read_stata("eip_commit_wip.dta")

EIP_list = data['EIP'].str.split(',')
eip_df = EIP_list.explode()
eip_df = eip_df.str.replace("EIP-","")
eip_df = eip_df.dropna()
eip_df = eip_df.astype(int)

# merge

data2 = pd.merge(data,eip_df, left_index = True, right_index = True, how = 'outer', indicator = True)
data2 = data2.rename(columns = {'EIP_x' : "EIP_list",'EIP_y' : "eip_number"})
data2 = data2[data2['EIP_list'].notna()]
data2.index.name = 'old_index'
data2.reset_index(inplace = True)

# select first meeting dates

data2['Date'] = pd.to_datetime(data2['Date'])
data2 = data2.sort_values('eip_number')
data3 = data2.drop_duplicates(subset= ['Meeting','eip_number'])
data4 = data2.loc[:,['Date','Meeting','eip_number']]
data4 = data4.rename(columns = {'Date' : 'MeetingDate'})
data5 = data4.groupby('eip_number').head(1)

# merge data to commit data

commit2 = pd.merge(commit,data5, on = 'eip_number', how = 'left', indicator = True)
commit2 = commit2.sort_values(['eip_number','CommitDate','MeetingDate', 'Meeting'])
new_order = ['A', 'File', 'eip_number','CommitDate', 'MeetingDate','CommitSHA', 'CommitMessage', 
       'Author', 'author_id', 'github_username', 'eip_author_flag',
       'total_commit', 'author_commit', 'eip_contributors', 
        '_merge']
commit2 = commit2[new_order]

commit2.to_excel("eip_commit.xlsx")
end
clear
cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Commit Data\Eip Commit Data\"

import excel "eip_commit.xlsx", sheet("Sheet1") firstrow

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"

 save "eip_commit.dta", replace
