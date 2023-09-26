// This code created on 8-29-2023 create commit data which is a panel data containing datewise github commitment 

// first we import updated commit file which contains the raw data of commitment and convert it into an stata file

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum Project Data"
clear
 import excel "updated_commits.xlsx", sheet("Sheet 1") firstrow
 rename EIP eip_number
 save "ethereum_commit.dta", replace
 
 // import unique author ids with client information file
 
  import delimited "unique_author_names_with_id", clear
  save "author.dta", replace
  
  // merge commit data with authors using author_id
  
  use "ethereum_commit.dta", clear
  rename Author_Id author_id
merge m:1 author_id using "author.dta", keepusing(github_username)
drop if _merge == 2 // remove authors that did not add any 

// create a flag whether the commit author is an EIP author. If the commit author does not exist in our author list then we assume that commit author is not
// an EIP author. This is expressed in _merge == 1

gen eip_author_flag = 1 if _merge == 3
replace eip_author_flag = 0 if eip_author_flag == .
drop _merge
// save this file as comit


// create a variable that identifies the total number of commits for each EIPs

bysort eip_number : gen total_commit = _N 
egen author_commit = total(eip_author_flag), by(eip_number)

save "ethereum_commit.dta", replace

// create unique contributors on eip_commt 

python :
import os
import pandas as pd
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data")
stata = pd.read_stata("ethereum_commit.dta")
contributors = stata.groupby('eip_number')['github_username'].nunique()
contributors = pd.DataFrame(contributors)
contributors.rename(columns={'github_username': 'eip_contributors'}, inplace=True)
stata = pd.merge(stata,contributors, on = 'eip_number', how = 'left')
stata.to_excel("ethereum_commit.xlsx")

end

clear
import excel "C:\Users\khojama\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum Project Data\ethereum_commit.xlsx", sheet("Sheet1") firstrow clear

save "ethereum_commit.dta", replace
