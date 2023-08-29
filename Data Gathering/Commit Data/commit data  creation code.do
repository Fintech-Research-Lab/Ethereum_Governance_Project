// This code created on 8-29-2023 create commit data which is a panel data containing datewise github commitment 

// first we import updated commit file which contains the raw data of commitment and convert it into an stata file

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum Project Data"

 import excel "updated_commits.xlsx", sheet("Sheet 1") firstrow
 save "ethereum_commit.dta", replace
 
 // import unique author ids with client information file
 
  import delimited "unique_author_names_with_id_plusclient.csv", clear
  save "author.dta"
  
  // merge commit data with authors using author_id
  
  use "ethereum_commit.dta", clear
  rename Author_Id author_id
merge m:1 author_id using "author.dta", keepusing(client)
drop if _merge == 2 // remove 290 authors that did not do any commits 

// create a flag to see if commitment author is a client

gen cl_flag = 1 if client != ""
replace cl_flag = 0 if cl_flag ==.

// create a flag whether the commit author is an EIP author. If the commit author does not exist in our author list then we assume that commit author is not
// an EIP author. This is expressed in _merge == 1

gen eip_author_flag = 1 if _merge == 1
replace eip_author_flag = 0 if eip_author_flag == .
drop _merge
// save this file as comit

save "ethereum_commit.dta", replace

// Merge the commit data with Ethereum_Data to create a panel representation of this data

use "Ethereum_Data.dta"

merge 1:m EIP using "ethereum_commit.dta"

// found EIP 6596 which has github commit but does not exist in the current Ethereum_Data
// since we are restricting our analysis to EIPs until 6/15/2023 and 6596 was created after this date, we will remove it

drop if _merge == 2

save "ethereum_commit.dta", replace