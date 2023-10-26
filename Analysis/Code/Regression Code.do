// Regression Code

*Main directory

*Cesare 
cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project"

*Moazzam
*cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\"

use "Regressions\Ethereum_Cross-sectional_Data.dta", clear


// create labels

// Create labels
label var log_tw "Twitter Followers (log)"
label var log_gh "GitHub Followers (log)"
label var tw_follower "N. Twitter Followers"
label var tf_scale "N. Twitter Followers (K)"
label var gh_follower "N. Github Followers"
label var n_author "Number of EIP Authors"
label var betweenness "Betweenness Centrality"
label var author_commit "EIP Author Commits"
label var total_commit "Total EIP Commits"
label var eip_contributors "EIP Contributors"
label var besu_commits "Besu Commits"
label var erigon_commits "Erigon Commits"
label var geth_commits "Geth Commits"
label var nethermind_commits "Nethermind Commits"
label var dummy_spearbit_labs "Spearbit"
label var dummy_ethereum_name_service "Ethereum Name Service"
label var dummy_consensys "ConsenSys"
label var dummy_stoneshot "Stoneshot"
label var dummy_cube_code "Cube Code"
label var dummy_google "Google"
label var dummy_serv_eth_support "Eth Support"
label var dummy_dyno_security_ab "Dyno Security Lab"
label var dummy_chainsafe_systems "Chain Safe Systems"
label var success "Finalized EIP"
label var implementation "Implemented EIP"

foreach var in besu erigon geth nethermind {
	replace `var' = 0 if `var' ==.
	}
	
gen client_commits = besu_commits + erigon_commits + geth_commits + nethermind_commits
label var client_commits "EIP Authors Client Commits"
gen client_commits_log = log(1+client_commits)
label var client_commits_log "EIP Authors Client Commits (log)" 
gen client_commits_dummy = (client_commits>0)
label var client_commits_dummy "EIP Author also Client Dev"

encode Category , gen(category_encoded)


* Principal Component Analysis

pca log_gh log_tw between
predict pca_social, score 
label var pca_social "Social Influence Index (PCA)"

pca n_author eip_contributors total_commit
predict pca_author, score 
label var pca_author "Engagement Index (PCA)"

pca client_commits_log author_commit  
predict pca_skill, score 
label var pca_skill "Skill Index (PCA)"

gen implemented = implementation 
replace implemented = . if (status =="Draft" |  status =="Final"  |  status =="Last Call" |   status =="Living" |  status =="Review" ) & implementation ~=1


gen time_start_today = date("june 21, 2023", "MDY") - dofc(sdate)





// summary stats

local summary_list = "success implemented time_to_final n_author tf_scale gh_follower total_commit author_commit eip_contributors besu_commits erigon_commits geth_commits nethermind_commits client_commits betweenness"

eststo clear	
eststo: estpost summarize `summary_list', detail	
esttab using "Regressions\Results\Tables\summstat.tex" , cells("count mean(fmt(%12.3fc)) sd(fmt(%13.3fc)) min(fmt(%12.3gc))  p25(fmt(%12.3gc)) p50(fmt(%12.3gc)) p75(fmt(%12.3gc)) max(fmt(%12.3gc))") ///
	collabels("N." " Mean" "St. Dev." "Min"  "p25" "p50" "p75" "Max" ) ///
	tex replace label nonumbers alignment(rrrrrrrr) noobs

  
  
// Individual Factors
// following are ols results probit specifications are in the end

* Finalization

*success
eststo clear
eststo : quietly reg success log_gh log_tw between i.category_encoded, robust
eststo : quietly reg success n_author eip_contributors  i.category_encoded, robust
eststo : quietly reg success client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg success pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\final_all.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

*Time to success
eststo clear
eststo : quietly reg time_to_final log_gh log_tw between i.category_encoded, robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded, robust
eststo : quietly reg time_to_final client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\final_all_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

	
	
	
	
	
*success
eststo clear
eststo : quietly reg success log_gh log_tw between i.category_encoded, robust
eststo : quietly reg success n_author eip_contributors  i.category_encoded, robust
eststo : quietly reg success client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg success pca_social pca_author pca_skill i.category_encoded, robust
eststo : quietly reg time_to_final log_gh log_tw between i.category_encoded, robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded, robust
eststo : quietly reg time_to_final client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\final_allall.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

*Time to success
eststo clear
eststo : quietly reg time_to_final log_gh log_tw between i.category_encoded, robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded, robust
eststo : quietly reg time_to_final client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\final_all_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

	
* Finalization of not-implementable EIP


eststo clear
eststo : quietly reg success log_gh log_tw between i.category_encoded if implementation ==., robust
eststo : quietly reg success n_author eip_contributors  i.category_encoded if implementation ==., robust
eststo : quietly reg success client_commits_log author_commit  i.category_encoded if implementation ==., robust
eststo : quietly reg success pca_social pca_author pca_skill i.category_encoded if implementation ==., robust
esttab using Regressions\Results\Tables\final_noimpl.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

	
*Time to success
eststo clear
eststo : quietly reg time_to_final log_gh log_tw between i.category_encoded if implementation ==., robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded if implementation ==., robust
eststo : quietly reg time_to_final client_commits_log author_commit  i.category_encoded if implementation ==., robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded if implementation ==., robust
esttab using Regressions\Results\Tables\final_noimpl_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

	
* implemented EIP

eststo clear
eststo : quietly reg implemented log_gh log_tw between i.category_encoded , robust
eststo : quietly reg implemented  n_author eip_contributors  i.category_encoded , robust
eststo : quietly reg implemented  client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg implemented  pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\implemented.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 

	
* implemented EIP

eststo clear
eststo : quietly reg time_to_final log_gh log_tw between i.category_encoded , robust
eststo : quietly reg time_to_final  n_author eip_contributors  i.category_encoded , robust
eststo : quietly reg time_to_final  client_commits_log author_commit  i.category_encoded, robust
eststo : quietly reg time_to_final  pca_social pca_author pca_skill i.category_encoded, robust
esttab using Regressions\Results\Tables\implemented_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded") 


	
	

// company 



label var dummy_spearbit_labs "Spearbit"
label var dummy_ethereum_name_service "Ethereum Name Service"
label var dummy_consensys "ConsenSys"
label var dummy_stoneshot "Stoneshot"
label var dummy_cube_code "Cube Code"
label var dummy_google "Google"
label var dummy_serv_eth_support "Eth Support"
label var dummy_dyno_security_ab "Dyno Security Lab"
label var dummy_chainsafe_systems "Chain Safe Systems"

eststo clear
eststo : quietly reg success dummy_spearbit_labs
eststo : quietly reg success dummy_ethereum_name_service
eststo : quietly reg success dummy_consensys
eststo : quietly reg success dummy_stoneshot
eststo : quietly reg success dummy_cube_code
eststo : quietly reg success dummy_google
eststo : quietly reg success dummy_serv_eth_support
eststo : quietly reg success dummy_dyno_security_ab
eststo : quietly reg success dummy_chainsafe_systems
eststo : quietly reg success dummy_spearbit_labs dummy_ethereum_name_service dummy_consensys dummy_stoneshot dummy_cube_code dummy_serv_eth_support dummy_google dummy_dyno_security_ab dummy_chainsafe_systems
esttab ,  varwidth(20) modelwidth(8) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2 r2(2) title("Author's Employer Associated with success of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace

eststo clear
eststo : quietly reg implementation dummy_spearbit_labs
eststo : quietly reg implementation dummy_ethereum_name_service
eststo : quietly reg implementation dummy_consensys
eststo : quietly reg implementation dummy_stoneshot
eststo : quietly reg implementation dummy_cube_code
eststo : quietly reg implementation dummy_google
eststo : quietly reg implementation dummy_serv_eth_support
eststo : quietly reg implementation dummy_dyno_security_ab
eststo : quietly reg implementation dummy_chainsafe_systems
eststo : quietly reg implementation dummy_spearbit_labs dummy_ethereum_name_service dummy_consensys dummy_stoneshot dummy_cube_code dummy_serv_eth_support dummy_google dummy_dyno_security_ab dummy_chainsafe_systems
esttab ,  varwidth(20) modelwidth(8) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2 r2(2) title("Author's Employer Associated with implementation of EIP") star (* .1 ** .05 *** .01) replace


