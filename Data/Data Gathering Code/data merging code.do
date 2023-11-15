// This is the code to merge disparate data on Ethereum Governance Project. Please read the replication document

// Import EIP data

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"
clear
import delimited "Ethereum_Cross-Sectional_Data_beg.csv"


// save this imported file as a stata file

save "Ethereum_Cross-sectional_Data.dta", replace

// import twitter data and create a stata file

import delimited "twitter_data.csv", numericcols(5) clear 
save "twitter_data.dta", replace

// Merge the data by author_id one author at a time

clear
use "Ethereum_Cross-sectional_Data.dta"

forvalues id = 1/15{
rename author`id'_id author_id
merge m:1 author_id using "twitter_data.dta",keepusing(follower following)
drop if _merge == 2
drop _merge
rename author_id author`id'_id
rename follower author`id'_follower
rename following author`id'_following
}

// create max twitter follower variable

egen tw_follower = rowmax(author1_follower author2_follower author3_follower author4_follower author5_follower author6_follower author7_follower author8_follower author9_follower author10_follower author11_follower author12_follower author13_follower author14_follower author15_follower)
erase "twitter_data.dta"
save "Ethereum_Cross-sectional_Data.dta", replace

// merge github 

// import github following data and save it as a stata file
import delimited "GitHub_Data.csv", numericcols(6) clear 
save "Github_data.dta", replace

// merge with ethereum data
clear
use "Ethereum_Cross-sectional_Data.dta"

forvalues id = 1/15{
rename author`id'_id author_id
merge m:1 author_id using "Github_data.dta",keepusing(github_followers)
drop if _merge == 2
drop _merge
rename author_id author`id'_id
rename github_follower author`id'_gh_follower
}

// create a maximum github following variable
egen gh_follower = rowmax(author1_gh_follower author2_gh_follower author3_gh_follower author4_gh_follower author5_gh_follower author6_gh_follower author7_gh_follower author8_gh_follower author9_gh_follower author10_gh_follower author11_gh_follower author12_gh_follower author13_gh_follower author14_gh_follower author15_gh_follower)
erase "GitHub_Data.dta"
save "Ethereum_Cross-sectional_Data.dta", replace


// merge LinkedIn Data

//import linkedin data and save it as a stata file
import delimited "linkedin_data.csv", clear
save "linkedin_data.dta",replace

// merge linkedin data
clear
use "Ethereum_Cross-sectional_Data.dta"

forvalues id = 1/15{
rename author`id'_id author_id
merge m:1 author_id using "linkedin_data.dta",keepusing(company1 company2 company3 company4 company5 pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10 jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle1_company3 jobtitle1_company4 jobtitle1_company5 jobtitle1_pastcompany1 jobtitle1_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)
drop if _merge == 2
drop _merge
rename author_id author`id'_id
rename company1 author`id'_company1
rename company2 author`id'_company2
rename company3 author`id'_company3
rename company4 author`id'_company4
rename company5 author`id'_company5
rename pastcompany1 author`id'_pastcompany1
rename pastcompany2 author`id'_pastcompany2
rename pastcompany3 author`id'_pastcompany3
rename pastcompany4 author`id'_pastcompany4
rename pastcompany5 author`id'_pastcompany5
rename pastcompany6 author`id'_pastcompany6
rename pastcompany7 author`id'_pastcompany7
rename pastcompany8 author`id'_pastcompany8
rename pastcompany9 author`id'_pastcompany9
rename pastcompany10 author`id'_pastcompany10
rename jobtitle1_company1 author`id'_jobtitle1_company1
rename jobtitle2_company1 author`id'_jobtitle2_company1
rename jobtitle3_company1 author`id'_jobtitle3_company1
rename jobtitle1_company2 author`id'_jobtitle1_company2
rename jobtitle1_company3 author`id'_jobtitle1_company3
rename jobtitle1_company4 author`id'_jobtitle1_company4
rename jobtitle1_company5 author`id'_jobtitle1_company5
rename jobtitle1_pastcompany1 author`id'_jobtitle1_pastcompany1
rename jobtitle1_pastcompany2 author`id'_jobtitle1_pastcompany2
rename jobtitle1_pastcompany3 author`id'_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author`id'_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author`id'_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author`id'_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author`id'_jobtitle1_pastcompany7
rename jobtitle1_pastcompany8 author`id'_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author`id'_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author`id'_jobtitle1_pastcompany10
}

// create number of authors

gen n_authors = 1 if author1 != ""

forvalues i = 2/15{
replace n_authors = n_authors + 1 if author`i' != ""	
}

erase "linkedin_data.dta"
save "Ethereum_Cross-sectional_Data.dta", replace

// add number of total commits and eip_contributors 
clear 
use "eip_commit.dta"
collapse (mean) total_commit eip_contributors author_commit, by (eip_number)
replace eip_contributors = 0 if eip_contributors ==.
save "total_commit.dta", replace

// merge
use "Ethereum_Cross-sectional_Data.dta", clear

merge 1:1 eip_number using "total_commit.dta"
drop if _merge ==2 // remove one additional EIP that is in commit data but not in cross-sectional
drop _merge

erase "total_commit.dta"
save "Ethereum_Cross-sectional_Data.dta", replace


// Add centrality measure for each EIPs

clear
cd "C:\Users\khojama\Box\Fintech Research Lab\\Ethereum_Governance_Project\Analysis\Centrality Analysis\"
import delimited "centrality_all.csv"
rename id author_id
cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"
save "centrality.dta", replace

use "Ethereum_Cross-sectional_Data.dta"
forvalues id = 1/15{
rename author`id'_id author_id
merge m:1 author_id using "centrality.dta",keepusing(between close eigen)
drop if _merge == 2
drop _merge
rename author_id author`id'_id
rename between author`id'_betweenness
rename close author`id'_closeness
rename eigen author`id'_eigen_value_centrality
}

egen betweenness_centrality = rowmax(author1_betweenness author2_betweenness author3_betweenness author4_betweenness author5_betweenness author6_betweenness author7_betweenness author8_betweenness author9_betweenness author10_betweenness author11_betweenness author12_betweenness author13_betweenness author14_betweenness author15_betweenness)

egen closeness_centrality = rowmax(author1_closeness author2_closeness author3_closeness author4_closeness author5_closeness author6_closeness author7_closeness author8_closeness author9_closeness author10_closeness author11_closeness author12_closeness author13_closeness author14_closeness author15_closeness)

egen eigen_value_centrality = rowmax(author1_eigen_value_centrality author2_eigen_value_centrality author3_eigen_value_centrality author4_eigen_value_centrality author5_eigen_value_centrality author6_eigen_value_centrality author7_eigen_value_centrality author8_eigen_value_centrality author9_eigen_value_centrality author10_eigen_value_centrality author11_eigen_value_centrality author12_eigen_value_centrality author13_eigen_value_centrality author14_eigen_value_centrality author15_eigen_value_centrality)

erase "centrality.dta"
save "Ethereum_Cross-sectional_Data.dta",replace

// add end dates of all EIPs that have been finalized
clear
import delimited "finaleip_enddates.csv"
rename number eip_number
gen edate = date(end, "MDY")
format edate %td
save "finaleip_enddates.dta", replace

use "Ethereum_Cross-sectional_Data" , clear
merge 1:1 eip_number using "finaleip_enddates.dta", keepusing(edate)
drop if _merge == 2
drop _merge
erase "finaleip_enddates.dta"
save "Ethereum_Cross-sectional_Data.dta", replace

// add start dates for all eips

import delimited "eip_startdates.csv", clear
gen sdate = date(date, "MDY")
format sdate %td
rename eipnumber eip_number
save "eip_startdates.dta", replace

use "Ethereum_Cross-sectional_Data" , clear
merge 1:1 eip_number using "eip_startdates.dta", keepusing(sdate)
drop if _merge == 2
drop _merge
erase "eip_startdates.dta"
save "Ethereum_Cross-sectional_Data.dta", replace


// add implementation column in the data

import excel "eip_implementation.xlsx", sheet("EIP Summary") firstrow clear
save "eip_implementation.dta", replace

use "Ethereum_Cross-sectional_Data" , clear
merge 1:1 eip_number using "eip_implementation.dta"
drop if _merge == 2
drop _merge
erase "eip_implementation.dta"
save "Ethereum_Cross-sectional_Data.dta", replace 


// move variables
move sdate author1
move edate author1
move Category author1
move Implementable author1
move inFork author1
move n_authors author1
move tw_follower author1
move gh_follower author1 
move total_commit author1
move author_commit author1
move eip_contributors author1
move betweenness_centrality author1
move closeness_centrality author1
move eigen_value_centrality author1

save "Ethereum_Cross-sectional_Data.dta", replace

// prepare files collapsing client commits and matching them with eip authors


// add client repository commits by author 

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"
import delimited "unique_author_names_with_id", clear
  save "author.dta", replace

local path "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Commit Data\client_commit\"
cd "`path'"
local files : dir "`path'" files "*.dta" // Get the list of .dta files in the directory
di `files'
foreach file of local files {
    use "`file'", clear
	// remove dependabot[bot] and github-actions[bot]
	drop if login == "dependabot[bot]"|login == "github-actions[bot]"
	local newvar = substr("`file'", 8, strlen("`file'")-11)
	di "`newvar'"
    collapse (count) date, by(login)
	rename date `newvar'_commits
    rename login github_username
    drop if github_username == "" 
    cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"
    merge 1:m github_username using "author", keepusing(author_id)
    keep if _merge == 3
    drop _merge
     save "`file'_author_commits.dta", replace
	cd "`path'"
}
cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Data\Raw Data\"
use "Ethereum_Cross-sectional_Data.dta", clear
local files = "besu erigon geth nethermind"
foreach file in `files' {
  forvalues id = 1/15{
    rename author`id'_id author_id
    merge m:1 author_id using "commits`file'.dta_author_commits.dta",keepusing(`file'_commits)
    drop if _merge == 2
    drop _merge
    rename author_id author`id'_id
    rename `file'_commits author`id'_`file'_commits
  }
  egen `file'_commits = rowmax(author1_`file'_commits author2_`file'_commits author3_`file'_commits author4_`file'_commits author5_`file'_commits author6_`file'_commits author7_`file'_commits author8_`file'_commits author9_`file'_commits author10_`file'_commits author11_`file'_commits)
  move `file'_commits author1
  erase "commits`file'.dta_author_commits.dta"
}
  erase "author.dta"
// create 0 for missing client commits`file
foreach var of varlist(besu_commits-nethermind_commits){
	replace `var' = 0 if `var' == .
}
save "Ethereum_Cross-sectional_Data.dta", replace


outsheet using "Ethereum_Cross-sectional_Data_output.csv", comma nolabel replace
 


