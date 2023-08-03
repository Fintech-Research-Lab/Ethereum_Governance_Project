// This is the code to merge disparate data on Ethereum Governance Project.
// There are several independently collected data sources. We have manually collected twitter following and twitter follower data for EIP authors
// We begin with a file that contains all EIPs on Github with author names. We assigned a unique author id for each authors
// In addition, there is a separate data manually collected on companies where they worked and author's job titles 
// Also there is a manual collection of github followers
// Once these data were collected, we matched author names using a fuzzy logic. We added author_ids for matched names and for those that did not match we manually added author_ids
// The following code is a way to merger twitter, github, company, and jobs data into the beginning file with EIP numbers, author names, and author_ids



// DIARY OF CHANGES MADE TO THE CODE
// 6-25-2023: This is the master file which contains ALL EIPs as of 6-25-2023
// 7-20-2023: The file Ethereum_Data which was initially created on 6-25-2023 was modified to include twitter followers on new authors. In the initial file, we had twitter data limited until author_id 585, subsequently we manually collected twitter following information on remaining authors. The code is therefore modified to now include twitter followers data for those authors which were not covered initially.  
// 8-3-2023, the data file was modified to add GitHub commit data by author_id

import delimited "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\ALLEIPS_with_author_id_postmanualreconciliation.csv"

// save this imported file as a stata file

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

// As a first step we merge twitter following and twitter data by author_id key. We create a stata file 

 import delimited "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\modified_twitter_data_6-7-2023_postmanualreconciliation.csv", numericcols(5) clear 
 
 // check for duplicates
 
 duplicates report author_id
 duplicates tag author_id, gen(dup)
  gsort -dup author_name
  
   drop if _n == 2 // marius incorrect observation dropped
    duplicates drop author_id, force // all other duplicates dropped

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta", replace

// merge the two data by author_id, we merge it by each author. There are up to 11 authors for differet eips

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

rename author1_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
rename author_id author1_id 
rename follower author1_follower
rename following author1_following

rename author2_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop_merge
rename author_id author2_id 
rename follower author2_follower
rename following author2_following

rename author3_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename follower author3_follower
rename following author3_following

rename author4_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename follower author4_follower
rename following author4_following

rename author5_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename follower author5_follower
rename following author5_following

rename author6_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename follower author6_follower
rename following author6_following

rename author7_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename follower author7_follower
rename following author7_following

rename author8_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename follower author8_follower
rename following author8_following

rename author9_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename follower author9_follower
rename following author9_following

rename author10_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename follower author10_follower
rename following author10_following

rename author11_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter data.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename follower author11_follower
rename following author11_following

// create max twitter follower variable

egen tw_follower = rowmax(author1_follower author2_follower author3_follower author4_follower author5_follower author6_follower author7_follower author8_follower author9_follower author10_follower author11_follower)

// move data for clarity

rename number EIP
move EIP author11
move status author11
move title author11
move tw_follower author11

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// merge github following data to the Ethereum data

// create github data in stata file

import delimited "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\GitHub_Follower_Data_afterreconciliation.csv", numericcols(6) clear 

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta"

// add github follower data by author id

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

rename author1_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename github_followers author1_gh_followers

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename github_followers author2_gh_followers

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename github_followers author3_gh_followers

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename github_followers author4_gh_followers

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename github_followers author5_gh_followers

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename github_followers author6_gh_followers

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename github_followers author7_gh_followers

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename github_followers author8_gh_followers

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename github_followers author9_gh_followers

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename github_followers author10_gh_followers

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Github_data.dta",keepusing(github_followers)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename github_followers author11_gh_followers

// create a rowmax of all github followers


egen gh_follower = rowmax(author1_gh_follower author2_gh_follower author3_gh_follower author4_gh_follower author5_gh_follower author6_gh_follower author7_gh_follower author8_gh_follower author9_gh_follower author10_gh_follower author11_gh_follower)

move gh_follower author11

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// add company data to the Ethereum Data file

import delimited "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.csv", clear

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta", replace

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

// merge current company information using author_ids

rename author1_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename company1 author1_company1
rename company2 author1_company2
rename company3 author1_company3
rename company4 author1_company4

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename company1 author2_company1
rename company2 author2_company2
rename company3 author2_company3
rename company4 author2_company4

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename company1 author3_company1
rename company2 author3_company2
rename company3 author3_company3
rename company4 author3_company4

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename company1 author4_company1
rename company2 author4_company2
rename company3 author4_company3
rename company4 author4_company4

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename company1 author5_company1
rename company2 author5_company2
rename company3 author5_company3
rename company4 author5_company4

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename company1 author6_company1
rename company2 author6_company2
rename company3 author6_company3
rename company4 author6_company4

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename company1 author7_company1
rename company2 author7_company2
rename company3 author7_company3
rename company4 author7_company4

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename company1 author8_company1
rename company2 author8_company2
rename company3 author8_company3
rename company4 author8_company4

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename company1 author9_company1
rename company2 author9_company2
rename company3 author9_company3
rename company4 author9_company4

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename company1 author10_company1
rename company2 author10_company2
rename company3 author10_company3
rename company4 author10_company4

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(company1 company2 company3 company4)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename company1 author11_company1
rename company2 author11_company2
rename company3 author11_company3
rename company4 author11_company4

// save

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// Adding Author's past companies

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

rename author1_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename pastcompany1 author1_pastcompany1
rename pastcompany2 author1_pastcompany2
rename pastcompany3 author1_pastcompany3
rename pastcompany4 author1_pastcompany4
rename pastcompany5 author1_pastcompany5
rename pastcompany6 author1_pastcompany6
rename pastcompany7 author1_pastcompany7
rename pastcompany8 author1_pastcompany8
rename pastcompany9 author1_pastcompany9
rename pastcompany10 author1_pastcompany10

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename pastcompany1 author2_pastcompany1
rename pastcompany2 author2_pastcompany2
rename pastcompany3 author2_pastcompany3
rename pastcompany4 author2_pastcompany4
rename pastcompany5 author2_pastcompany5
rename pastcompany6 author2_pastcompany6
rename pastcompany7 author2_pastcompany7
rename pastcompany8 author2_pastcompany8
rename pastcompany9 author2_pastcompany9
rename pastcompany10 author2_pastcompany10

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename pastcompany1 author3_pastcompany1
rename pastcompany2 author3_pastcompany2
rename pastcompany3 author3_pastcompany3
rename pastcompany4 author3_pastcompany4
rename pastcompany5 author3_pastcompany5
rename pastcompany6 author3_pastcompany6
rename pastcompany7 author3_pastcompany7
rename pastcompany8 author3_pastcompany8
rename pastcompany9 author3_pastcompany9
rename pastcompany10 author3_pastcompany10

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename pastcompany1 author4_pastcompany1
rename pastcompany2 author4_pastcompany2
rename pastcompany3 author4_pastcompany3
rename pastcompany4 author4_pastcompany4
rename pastcompany5 author4_pastcompany5
rename pastcompany6 author4_pastcompany6
rename pastcompany7 author4_pastcompany7
rename pastcompany8 author4_pastcompany8
rename pastcompany9 author4_pastcompany9
rename pastcompany10 author4_pastcompany10

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename pastcompany1 author5_pastcompany1
rename pastcompany2 author5_pastcompany2
rename pastcompany3 author5_pastcompany3
rename pastcompany4 author5_pastcompany4
rename pastcompany5 author5_pastcompany5
rename pastcompany6 author5_pastcompany6
rename pastcompany7 author5_pastcompany7
rename pastcompany8 author5_pastcompany8
rename pastcompany9 author5_pastcompany9
rename pastcompany10 author5_pastcompany10

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename pastcompany1 author6_pastcompany1
rename pastcompany2 author6_pastcompany2
rename pastcompany3 author6_pastcompany3
rename pastcompany4 author6_pastcompany4
rename pastcompany5 author6_pastcompany5
rename pastcompany6 author6_pastcompany6
rename pastcompany7 author6_pastcompany7
rename pastcompany8 author6_pastcompany8
rename pastcompany9 author6_pastcompany9
rename pastcompany10 author6_pastcompany10

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename pastcompany1 author7_pastcompany1
rename pastcompany2 author7_pastcompany2
rename pastcompany3 author7_pastcompany3
rename pastcompany4 author7_pastcompany4
rename pastcompany5 author7_pastcompany5
rename pastcompany6 author7_pastcompany6
rename pastcompany7 author7_pastcompany7
rename pastcompany8 author7_pastcompany8
rename pastcompany9 author7_pastcompany9
rename pastcompany10 author7_pastcompany10

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename pastcompany1 author8_pastcompany1
rename pastcompany2 author8_pastcompany2
rename pastcompany3 author8_pastcompany3
rename pastcompany4 author8_pastcompany4
rename pastcompany5 author8_pastcompany5
rename pastcompany6 author8_pastcompany6
rename pastcompany7 author8_pastcompany7
rename pastcompany8 author8_pastcompany8
rename pastcompany9 author8_pastcompany9
rename pastcompany10 author8_pastcompany10

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename pastcompany1 author9_pastcompany1
rename pastcompany2 author9_pastcompany2
rename pastcompany3 author9_pastcompany3
rename pastcompany4 author9_pastcompany4
rename pastcompany5 author9_pastcompany5
rename pastcompany6 author9_pastcompany6
rename pastcompany7 author9_pastcompany7
rename pastcompany8 author9_pastcompany8
rename pastcompany9 author9_pastcompany9
rename pastcompany10 author9_pastcompany10

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename pastcompany1 author10_pastcompany1
rename pastcompany2 author10_pastcompany2
rename pastcompany3 author10_pastcompany3
rename pastcompany4 author10_pastcompany4
rename pastcompany5 author10_pastcompany5
rename pastcompany6 author10_pastcompany6
rename pastcompany7 author10_pastcompany7
rename pastcompany8 author10_pastcompany8
rename pastcompany9 author10_pastcompany9
rename pastcompany10 author10_pastcompany10

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(pastcompany1 pastcompany2 pastcompany3 pastcompany4 pastcompany5 pastcompany6 pastcompany7 pastcompany8 pastcompany9 pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename pastcompany1 author11_pastcompany1
rename pastcompany2 author11_pastcompany2
rename pastcompany3 author11_pastcompany3
rename pastcompany4 author11_pastcompany4
rename pastcompany5 author11_pastcompany5
rename pastcompany6 author11_pastcompany6
rename pastcompany7 author11_pastcompany7
rename pastcompany8 author11_pastcompany8
rename pastcompany9 author11_pastcompany9
rename pastcompany10 author11_pastcompany10

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// Add job title of current company

rename author1_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename jobtitle1_company1 author1_jobtitle1_company1
rename jobtitle2_company1 author1_jobtitle2_company1
rename jobtitle3_company1 author1_jobtitle3_company1
rename jobtitle1_company2 author1_jobtitle1_company2
rename jobtitle2_company2 author1_jobtitle2_company2
rename jobtitle1_company3 author1_jobtitle1_company3
rename jobtitle2_company3 author1_jobtitle2_company3
rename jobtitle1_company4 author1_jobtitle1_company4

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename jobtitle1_company1 author2_jobtitle1_company1
rename jobtitle2_company1 author2_jobtitle2_company1
rename jobtitle3_company1 author2_jobtitle3_company1
rename jobtitle1_company2 author2_jobtitle1_company2
rename jobtitle2_company2 author2_jobtitle2_company2
rename jobtitle1_company3 author2_jobtitle1_company3
rename jobtitle2_company3 author2_jobtitle2_company3
rename jobtitle1_company4 author2_jobtitle1_company4

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename jobtitle1_company1 author3_jobtitle1_company1
rename jobtitle2_company1 author3_jobtitle2_company1
rename jobtitle3_company1 author3_jobtitle3_company1
rename jobtitle1_company2 author3_jobtitle1_company2
rename jobtitle2_company2 author3_jobtitle2_company2
rename jobtitle1_company3 author3_jobtitle1_company3
rename jobtitle2_company3 author3_jobtitle2_company3
rename jobtitle1_company4 author3_jobtitle1_company4

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename jobtitle1_company1 author4_jobtitle1_company1
rename jobtitle2_company1 author4_jobtitle2_company1
rename jobtitle3_company1 author4_jobtitle3_company1
rename jobtitle1_company2 author4_jobtitle1_company2
rename jobtitle2_company2 author4_jobtitle2_company2
rename jobtitle1_company3 author4_jobtitle1_company3
rename jobtitle2_company3 author4_jobtitle2_company3
rename jobtitle1_company4 author4_jobtitle1_company4

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename jobtitle1_company1 author5_jobtitle1_company1
rename jobtitle2_company1 author5_jobtitle2_company1
rename jobtitle3_company1 author5_jobtitle3_company1
rename jobtitle1_company2 author5_jobtitle1_company2
rename jobtitle2_company2 author5_jobtitle2_company2
rename jobtitle1_company3 author5_jobtitle1_company3
rename jobtitle2_company3 author5_jobtitle2_company3
rename jobtitle1_company4 author5_jobtitle1_company4

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename jobtitle1_company1 author6_jobtitle1_company1
rename jobtitle2_company1 author6_jobtitle2_company1
rename jobtitle3_company1 author6_jobtitle3_company1
rename jobtitle1_company2 author6_jobtitle1_company2
rename jobtitle2_company2 author6_jobtitle2_company2
rename jobtitle1_company3 author6_jobtitle1_company3
rename jobtitle2_company3 author6_jobtitle2_company3
rename jobtitle1_company4 author6_jobtitle1_company4

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename jobtitle1_company1 author7_jobtitle1_company1
rename jobtitle2_company1 author7_jobtitle2_company1
rename jobtitle3_company1 author7_jobtitle3_company1
rename jobtitle1_company2 author7_jobtitle1_company2
rename jobtitle2_company2 author7_jobtitle2_company2
rename jobtitle1_company3 author7_jobtitle1_company3
rename jobtitle2_company3 author7_jobtitle2_company3
rename jobtitle1_company4 author7_jobtitle1_company4

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename jobtitle1_company1 author8_jobtitle1_company1
rename jobtitle2_company1 author8_jobtitle2_company1
rename jobtitle3_company1 author8_jobtitle3_company1
rename jobtitle1_company2 author8_jobtitle1_company2
rename jobtitle2_company2 author8_jobtitle2_company2
rename jobtitle1_company3 author8_jobtitle1_company3
rename jobtitle2_company3 author8_jobtitle2_company3
rename jobtitle1_company4 author8_jobtitle1_company4

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename jobtitle1_company1 author9_jobtitle1_company1
rename jobtitle2_company1 author9_jobtitle2_company1
rename jobtitle3_company1 author9_jobtitle3_company1
rename jobtitle1_company2 author9_jobtitle1_company2
rename jobtitle2_company2 author9_jobtitle2_company2
rename jobtitle1_company3 author9_jobtitle1_company3
rename jobtitle2_company3 author9_jobtitle2_company3
rename jobtitle1_company4 author9_jobtitle1_company4

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename jobtitle1_company1 author10_jobtitle1_company1
rename jobtitle2_company1 author10_jobtitle2_company1
rename jobtitle3_company1 author10_jobtitle3_company1
rename jobtitle1_company2 author10_jobtitle1_company2
rename jobtitle2_company2 author10_jobtitle2_company2
rename jobtitle1_company3 author10_jobtitle1_company3
rename jobtitle2_company3 author10_jobtitle2_company3
rename jobtitle1_company4 author10_jobtitle1_company4

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_company1 jobtitle2_company1 jobtitle3_company1 jobtitle1_company2 jobtitle2_company2 jobtitle1_company3 jobtitle2_company3 jobtitle1_company4)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename jobtitle1_company1 author11_jobtitle1_company1
rename jobtitle2_company1 author11_jobtitle2_company1
rename jobtitle3_company1 author11_jobtitle3_company1
rename jobtitle1_company2 author11_jobtitle1_company2
rename jobtitle2_company2 author11_jobtitle2_company2
rename jobtitle1_company3 author11_jobtitle1_company3
rename jobtitle2_company3 author11_jobtitle2_company3
rename jobtitle1_company4 author11_jobtitle1_company4

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// Add past job titles 

rename author1_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename jobtitle1_pastcompany1 author1_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author1_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author1_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author1_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author1_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author1_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author1_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author1_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author1_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author1_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author1_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author1_jobtitle1_pastcompany10

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename jobtitle1_pastcompany1 author2_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author2_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author2_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author2_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author2_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author2_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author2_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author2_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author2_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author2_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author2_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author2_jobtitle1_pastcompany10

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename jobtitle1_pastcompany1 author3_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author3_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author3_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author3_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author3_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author3_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author3_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author3_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author3_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author3_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author3_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author3_jobtitle1_pastcompany10

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename jobtitle1_pastcompany1 author4_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author4_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author4_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author4_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author4_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author4_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author4_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author4_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author4_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author4_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author4_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author4_jobtitle1_pastcompany10

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename jobtitle1_pastcompany1 author5_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author5_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author5_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author5_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author5_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author5_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author5_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author5_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author5_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author5_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author5_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author5_jobtitle1_pastcompany10

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename jobtitle1_pastcompany1 author6_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author6_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author6_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author6_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author6_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author6_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author6_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author6_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author6_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author6_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author6_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author6_jobtitle1_pastcompany10

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename jobtitle1_pastcompany1 author7_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author7_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author7_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author7_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author7_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author7_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author7_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author7_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author7_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author7_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author7_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author7_jobtitle1_pastcompany10

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename jobtitle1_pastcompany1 author8_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author8_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author8_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author8_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author8_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author8_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author8_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author8_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author8_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author8_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author8_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author8_jobtitle1_pastcompany10

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename jobtitle1_pastcompany1 author9_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author9_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author9_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author9_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author9_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author9_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author9_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author9_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author9_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author9_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author9_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author9_jobtitle1_pastcompany10

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename jobtitle1_pastcompany1 author10_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author10_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author10_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author10_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author10_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author10_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author10_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author10_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author10_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author10_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author10_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author10_jobtitle1_pastcompany10

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\company_and_jobs_data.dta",keepusing(jobtitle1_pastcompany1 jobtitle2_pastcompany1 jobtitle1_pastcompany2 jobtitle2_pastcompany2 jobtitle1_pastcompany3 jobtitle1_pastcompany4 jobtitle1_pastcompany5 jobtitle1_pastcompany6 jobtitle1_pastcompany7 jobtitle1_pastcompany8 jobtitle1_pastcompany9 jobtitle1_pastcompany10)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename jobtitle1_pastcompany1 author11_jobtitle1_pastcompany1
rename jobtitle2_pastcompany1 author11_jobtitle2_pastcompany1
rename jobtitle1_pastcompany2 author11_jobtitle1_pastcompany2
rename jobtitle2_pastcompany2 author11_jobtitle2_pastcompany2
rename jobtitle1_pastcompany3 author11_jobtitle1_pastcompany3
rename jobtitle1_pastcompany4 author11_jobtitle1_pastcompany4
rename jobtitle1_pastcompany5 author11_jobtitle1_pastcompany5
rename jobtitle1_pastcompany6 author11_jobtitle1_pastcompany6
rename jobtitle1_pastcompany7 author11_jobtitle1_pastcompany7 
rename jobtitle1_pastcompany8 author11_jobtitle1_pastcompany8
rename jobtitle1_pastcompany9 author11_jobtitle1_pastcompany9
rename jobtitle1_pastcompany10 author11_jobtitle1_pastcompany10

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// adding github handle

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

rename author1_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author1_id
rename github_username author1_githubn_username

rename author2_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author2_id
rename github_username author2_githubn_username

rename author3_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author3_id
rename github_username author3_githubn_username

rename author4_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author4_id
rename github_username author4_githubn_username

rename author5_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author5_id
rename github_username author5_githubn_username

rename author6_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author6_id
rename github_username author6_githubn_username

rename author7_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author7_id
rename github_username author7_githubn_username

rename author8_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author8_id
rename github_username author8_githubn_username

rename author9_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author9_id
rename github_username author9_githubn_username

rename author10_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author10_id
rename github_username author10_githubn_username

rename author11_id author_id 

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta",keepusing(github_username)

drop if _merge == 2
drop _merge
rename author_id author11_id
rename github_username author11_githubn_username

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// Code added on 7-20-2023

// create a new stata file of new twitter data

import delimited "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7-20-2023.csv.csv", numericcols(5) 

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta"

// replace old twitter following data with new one in the Ethereum_Data

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// remove old twitter following and follower data for each of the authors

drop tw_follower author1_following-author11_follower

rename author1_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author1_id 
rename follower author1_follower
rename following author1_following

rename author2_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author2_id 
rename follower author2_follower
rename following author2_following

rename author3_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author3_id 
rename follower author3_follower
rename following author3_following

rename author4_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author4_id 
rename follower author4_follower
rename following author4_following

rename author5_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author5_id 
rename follower author5_follower
rename following author5_following

rename author6_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author6_id 
rename follower author6_follower
rename following author6_following

rename author7_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author7_id 
rename follower author7_follower
rename following author7_following

rename author8_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author8_id 
rename follower author8_follower
rename following author8_following

rename author9_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author9_id 
rename follower author9_follower
rename following author9_following

rename author10_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author10_id 
rename follower author10_follower
rename following author10_following

rename author11_id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\twitter_data_7_20_2023.dta",keepusing(follower following)

drop if _merge == 2
drop _merge
rename author_id author11_id 
rename follower author11_follower
rename following author11_following

// create max twitter follower variable

egen tw_follower = rowmax(author1_follower author2_follower author3_follower author4_follower author5_follower author6_follower author7_follower author8_follower author9_follower author10_follower author11_follower)

// move data for clarity

move tw_follower author11

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace

// This part of the code adds commits data into the Ethereum Data. The nature of Commit data is that it is a panel data so we first prepare this data and then merge it to the current Ethereum_Data.dta
// The commit data is organized by EIP_Number and Date of Commit, furthermore we also have author_id. Separately, we have a master author_id file which contains whether author_id is part of "client" or not
// The code below imports timeseries commit data, then merge that data with author_id key to add whether the author is a client or not and then create a 0/1 flag on this

// import excel file that contains time series of commit data

import excel "C:\Users\moazz\Downloads\updated_commits.xlsx", sheet("Sheet 1") firstrow

save "C:\Users\moazz\Downloads\commit.dta", replace

// merge commit data with author data to create a client flag

use "C:\Users\moazz\Downloads\commit.dta"

rename Author_Id author_id

merge m:1 author_id using "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\author.dta", keepusing(client)

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

save "C:\Users\moazz\Downloads\commit.dta", replace

// Merge the commit data with Ethereum_Data to create a panel representation of this data

use "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta"

merge 1:m EIP using "C:\Users\moazz\Downloads\commit.dta"

// found EIP 6596 which has github commit but does not exist in the current Ethereum_Data

save "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum_Data.dta", replace








