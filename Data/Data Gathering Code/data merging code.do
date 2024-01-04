// This is the code to merge disparate data on Ethereum Governance Project. Please read the replication document

// Import EIP data

*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"


********************************************************************************
* IMPORT FILES INTO STATA

//////////////////////
// import twitter and Github data and create a stata file

insheet using "Data\Raw Data\twitter_data.csv", comma clear 
save "Data\Raw Data\twitter_data.dta", replace


//////////////////////
// import github following data and save it as a stata file
insheet using "Data\Raw Data\GitHub_Data.csv", comma clear 
save "Data\Raw Data\Github_data.dta", replace


//////////////////////
//import linkedin data and save it as a stata file
insheet using "Data\Raw Data\linkedin_data.csv", clear comma
save "Data\Raw Data\linkedin_data.dta",replace

//////////////////////
//import Ethereum Foundation data and save it as a stata file
insheet using "Data\Raw Data\author_EF.csv", clear comma
save "Data\Raw Data\author_EF.dta",replace

//////////////////////
//import Ethereum Magician data and save it as a stata file
insheet using "Analysis\Magician Comments\FEM_Data_for_regressions.csv", clear comma
rename eip eip_number
save "Data\Raw Data\temp_FEM", replace


//////////////////////
// import EIP commit data
insheet using "Data\Raw Data\unique_author_names_with_id.csv", clear comma
drop if github_username ==""
replace github_username = lower(github_username)
save "Data\Raw Data\author_git.dta", replace

import excel "Data\Commit Data\Eip Commit Data\eip_commit_beg.xlsx", sheet("Sheet1") firstrow clear
rename Username github_username
rename EIP eip_number

replace github_username = lower(github_username)
merge m:1 github_username using "Data\Raw Data\author_git.dta" , keep(1 3)
erase "Data\Raw Data\author_git.dta"

drop if github_username == "eth-bot"

gen eip_author_flag = (_merge==3)
drop _merge

* Count number of contributors
bys eip_number: egen n_contributors_eip = nvals(github_username) if eip_author_flag ==0 

* create a variable that identifies the total number of commits for each EIPs
bysort eip_number : gen total_eip_commit = _N 

* author commit is the number of commits made by authors
egen author_commit = total(eip_author_flag), by(eip_number)

* number of authors that are committing. 
bys eip_number: egen n_committing_authors = nvals(github_username) if eip_author_flag ==1

collapse (max) n_contributors_eip total_eip_commit author_commit n_committing_authors, by(eip_number)

foreach var of varlist n_contributors_eip total_eip_commit author_commit n_committing_authors {
	replace `var' =0 if `var' ==.
	}
	
* WE USE THIS FILE TO MERGE INTO THE CROSS-SECTIONAL DATA THE TOTAL N. OF COMMITS, THE COMMITS MADE BY AUTHORS, AND THE N. OF CONTRIBUTORS (EXCLUDING AUTHORS)

save "Data\Commit Data\Eip Commit Data\eip_commit_data.dta", replace


//////////////////////
// Centrality Data

clear
import delimited "Analysis\Centrality Analysis\centrality_all.csv", clear
rename index author_id
save "Data\Raw Data\centrality.dta", replace



//////////////////////
// N of WORDS in EIP


import delimited "Data\Raw Data\eip_word_count.csv", clear
rename eipnumber eip_number
rename wordcount eip_nwords
rename readability eip_read

replace eip_read = 0 if eip_read <0
replace eip_nwords = eip_nwords/1000
save "Data\Raw Data\temp_nwords.dta", replace


//////////////////////
// add start date for all eips, end dates of all EIPs that have been finalized

import delimited "Data\Raw Data\eip_startdates.csv", clear
gen sdate = date(date, "MDY")
format sdate %td
rename eipnumber eip_number
save "Data\Raw Data\eip_startdates.dta", replace


import delimited "Data\Raw Data\finaleip_enddates.csv", clear
rename number eip_number
gen edate = date(end, "MDY")
format edate %td
save "Data\Raw Data\finaleip_enddates.dta", replace



//////////////////////
// add anynoymity variable to data

import delimited "Data\Raw Data\unique_author_names_with_id", clear
keep author_id anonymity_flag
rename anonymity_flag anon
save "Data\Raw Data\temp_anon.dta", replace


//////////////////////
// add implementation column in the data

import excel "Data\Raw Data\eip_implementation.xlsx", sheet("EIP Summary") firstrow clear
save "Data\Raw Data\eip_implementation.dta", replace

//////////////////////
// ADD CLIENT COMMMITS
import delimited "Data\Raw Data\unique_author_names_with_id", clear
replace github_username = lower(github_username)
drop if github_username ==""
save "Data\Raw Data\temp_author.dta", replace

foreach file in besu erigon geth nethermind {
	local f = "Data\Commit Data\client_commit\" + "`file'_commits"
	use "`f'", clear
	// remove dependabot[bot] and github-actions[bot]
	drop if identifier== "dependabot[bot]"|identifier == "github-actions[bot]"
    collapse (count) date, by(identifier)
	rename date `file'_commits
    rename identifier github_username
	replace github_username = lower(github_username)
    drop if github_username == "" 
    merge m:1 github_username using "Data\Raw Data\temp_author", keepusing(author_id)
    keep if _merge == 3
    drop _merge
    save "Data\Raw Data\author_commits_`file'.dta", replace
	}

erase "Data\Raw Data\temp_author.dta"


********************************************************************************
* MERGE IN TWITTER AND GITHUB DATA

// Merge the data by author_id one author at a time

insheet using "Data\Raw Data\Ethereum_Cross-sectional_Data_beg.csv", clear comma

* Merge in Twitter
forvalues id = 1/15{
	rename author`id'_id author_id
	merge m:1 author_id using "Data\Raw Data\twitter_data.dta", keepusing(follower following)
	destring(follower), replace force
	drop if _merge == 2 
	drop _merge
	rename author_id author`id'_id
	rename follower author`id'_follower
	rename following author`id'_following
	}

// create max twitter follower variable

egen tw_follower = rowmax(author1_follower author2_follower author3_follower author4_follower author5_follower author6_follower author7_follower author8_follower author9_follower author10_follower author11_follower author12_follower author13_follower author14_follower author15_follower)
erase "Data\Raw Data\twitter_data.dta"

* Merge in Github 

forvalues id = 1/15{
	rename author`id'_id author_id
	merge m:1 author_id using "Data\Raw Data\Github_data.dta",keepusing(github_followers)
	drop if _merge == 2
	drop _merge
	rename author_id author`id'_id
	rename github_follower author`id'_gh_follower
	}

// create a maximum github following variable
egen gh_follower = rowmax(author1_gh_follower author2_gh_follower author3_gh_follower author4_gh_follower author5_gh_follower author6_gh_follower author7_gh_follower author8_gh_follower author9_gh_follower author10_gh_follower author11_gh_follower author12_gh_follower author13_gh_follower author14_gh_follower author15_gh_follower)
erase "Data\Raw Data\GitHub_Data.dta"


********************************************************************************
* MERGE IN LINKEDIN DATA


forvalues id = 1/15 {
	rename author`id'_id author_id
	merge m:1 author_id using "Data\Raw Data\linkedin_data.dta",keepusing(company* ///
		pastcompany*  jobtitle*company*)
	drop if _merge == 2
	drop _merge
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
	
	merge m:1 author_id using "Data\Raw Data\author_EF.dta", keepusing(from end)
	drop if _merge==2
	drop _merge
	rename author_id author`id'_id
	rename from author`id'_EF_start
	rename end author`id'_EF_end
	}

// create number of authors

gen n_authors = 1 if author1_id != .

forvalues i = 2/15{
	replace n_authors = n_authors + 1 if author`i'_id != .	
	}

erase "Data\Raw Data\linkedin_data.dta"
erase "Data\Raw Data\author_EF.dta"



********************************************************************************
* MERGE IN EIP COMMIT DATA

merge 1:1 eip_number using "Data\Commit Data\Eip Commit Data\eip_commit_data", keep(1 3) 
drop _merge
erase "Data\Commit Data\Eip Commit Data\eip_commit_data.dta"


********************************************************************************
* MERGE IN N WORDS in EIP DATA

merge 1:1 eip_number using "Data\Raw Data\temp_nwords", keep(1 3) 
drop _merge
erase "Data\Raw Data\temp_nwords.dta"


********************************************************************************
* MERGE IN ANONYMITY DATA

forvalues id = 1/15{
	rename author`id'_id author_id
	merge m:1 author_id using "Data\Raw Data\temp_anon", keep(1 3)
	drop _merge
	rename author_id author`id'_id
	rename anon author`id'_anon
	}

egen anon_max = rowmax(author1_anon author2_anon author3_anon author4_anon author5_anon author6_anon author7_anon author8_anon author9_anon author10_anon author11_anon author12_anon author13_anon author14_anon author15_anon)

erase "Data\Raw Data\temp_anon.dta"


********************************************************************************
* MERGE IN CENTRALITY DATA

// Add centrality measure for each EIPs
forvalues id = 1/15{
	rename author`id'_id author_id
	merge m:1 author_id using "Data\Raw Data\centrality",keepusing(between close eigen) keep(1 3)
	drop _merge
	rename author_id author`id'_id
	rename between author`id'_betweenness
	rename close author`id'_closeness
	rename eigen author`id'_eigen_value_centrality
	}

egen betweenness_centrality = rowmax(author1_betweenness author2_betweenness author3_betweenness author4_betweenness author5_betweenness author6_betweenness author7_betweenness author8_betweenness author9_betweenness author10_betweenness author11_betweenness author12_betweenness author13_betweenness author14_betweenness author15_betweenness)
egen closeness_centrality = rowmax(author1_closeness author2_closeness author3_closeness author4_closeness author5_closeness author6_closeness author7_closeness author8_closeness author9_closeness author10_closeness author11_closeness author12_closeness author13_closeness author14_closeness author15_closeness)
egen eigen_value_centrality = rowmax(author1_eigen_value_centrality author2_eigen_value_centrality author3_eigen_value_centrality author4_eigen_value_centrality author5_eigen_value_centrality author6_eigen_value_centrality author7_eigen_value_centrality author8_eigen_value_centrality author9_eigen_value_centrality author10_eigen_value_centrality author11_eigen_value_centrality author12_eigen_value_centrality author13_eigen_value_centrality author14_eigen_value_centrality author15_eigen_value_centrality)

erase "Data\Raw Data\centrality.dta"



********************************************************************************
* MERGE IN EIP START DATE AND FINALIZATION DATE DATA

merge 1:1 eip_number using "Data\Raw Data\finaleip_enddates.dta", keepusing(edate) keep(1 3)
drop _merge
erase "Data\Raw Data\finaleip_enddates.dta"

merge 1:1 eip_number using "Data\Raw Data\eip_startdates.dta", keepusing(sdate)
drop if _merge == 2
drop _merge
erase "Data\Raw Data\eip_startdates.dta"


********************************************************************************
* MERGE IN IMPLEMENTATION DATA

merge 1:1 eip_number using "Data\Raw Data\eip_implementation.dta"
drop if _merge == 2
drop _merge
erase "Data\Raw Data\eip_implementation.dta"


********************************************************************************
* MERGE IN FEMN DATA

merge 1:1 eip_number using "Data\Raw Data\temp_fem.dta" , keepusing(eip_number replies views likes links createddate users)
drop if _merge == 2
drop _merge
erase "Data\Raw Data\temp_fem.dta"


// move variables
move sdate author1
move edate author1
move Category author1
move Implementable author1
move inFork author1
move n_authors author1
move tw_follower author1
move gh_follower author1 
move total_eip_commit author1
move author_commit author1
move n_contributors_eip author1
move betweenness_centrality author1
move closeness_centrality author1
move eigen_value_centrality author1


********************************************************************************
* MERGE IN CLIENT DATA

// add client repository commits by author 

local files = "besu erigon geth nethermind"
foreach file in `files' {
  forvalues id = 1/15{
    rename author`id'_id author_id
    merge m:1 author_id using "Data\Raw Data\author_commits_`file'", keepusing(`file'_commits)
    drop if _merge == 2
    drop _merge
    rename author_id author`id'_id
    rename `file'_commits author`id'_`file'_commits
  }
  egen `file'_commits = rowmax(author1_`file'_commits author2_`file'_commits author3_`file'_commits author4_`file'_commits author5_`file'_commits author6_`file'_commits author7_`file'_commits author8_`file'_commits author9_`file'_commits author10_`file'_commits author11_`file'_commits)
  move `file'_commits author1
  erase "Data\Raw Data\author_commits_`file'.dta"
}


// create 0 for missing client commits`file
foreach var of varlist(besu_commits-nethermind_commits){
	replace `var' = 0 if `var' == .
}


********************************************************************************
* FINAL CLEANUP

gen client_commits = besu_commits + erigon_commits + geth_commits + nethermind_commits
label var client_commits "EIP Authors Client Commits"
gen client_commits_log = log(1+client_commits)
label var client_commits_log "EIP Authors Client Commits (log)" 
gen client_commits_dum = (client_commits>0)
label var client_commits_dum "EIP Author also Client Dev"

encode Category , gen(category_encoded)

replace n_contributors_eip = 0 if n_contributors_eip ==.

* OTHER VARIABLES

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

// Create labels
label var log_tw "Twitter Followers (log)"
label var log_gh "GitHub Followers (log)"
label var tw_follower "N. Twitter Followers"
label var tf_scale "N. Twitter Followers (K)"
label var gh_follower "N. Github Followers"
label var n_author "N. EIP Authors"
label var betweenness "Betweenness Centrality"
label var author_commit "EIP Author Commits"
label var total_eip_commit "Total EIP Commits"
label var n_contributors_eip "EIP Contributors"
label var besu_commits "Besu Commits"
label var erigon_commits "Erigon Commits"
label var geth_commits "Geth Commits"
label var nethermind_commits "Nethermind Commits"
label var success "Finalized"
label var implementation "Implemented EIP"
label var time_to_final "Time from EIP Start to Finalization"
label var eip_nwords "N. Words in EIP (k)"	
label var eip_read "Readability Score"	
label var replies "FEM Comments"
label var views "FEM Views"
label var likes "FEM Likes"
label var users "FEM Unique Users"
label var anon_max "Anonymous Author"

// fix living
replace status = "Living" if status == "Living "

drop if Category =="Meta" | Category == "Informational" 

save "Data\Raw Data\Ethereum_Cross-sectional_Data.dta", replace

outsheet using "Data\Raw Data\Ethereum_Cross-sectional_Data_output.csv", comma nolabel replace




