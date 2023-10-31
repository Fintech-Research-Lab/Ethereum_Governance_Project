// Regression Code

*Main directory

*Cesare 
cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project"

*Moazzam
*cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\"



graph set window fontface "Times New Roman"




use "Analysis\Ethereum_Cross-sectional_Data.dta", clear


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
label var ConsenSys_dummy "ConsenSys"
label var StarkWare_dummy "StarkWare"
label var EthereumNameService_dummy "Ethereum Name Service"
label var Nethermind_dummy "Nethermind"
label var Coinbase_dummy "Coinbase"
label var BraveSoftware_dummy "Brave Software"
label var SpruceSystemsInc_dummy "Spruce Systems"
label var ChainSafeSystems_dummy "Chain Safe Systems"
label var Polytrade_dummy "Polytrade"
label var Google_dummy "Google"
label var success "Finalized EIP"
label var implementation "Implemented EIP"
label var time_to_final "Time from EIP Start to Finalization"
	
gen client_commits = besu_commits + erigon_commits + geth_commits + nethermind_commits
label var client_commits "EIP Authors Client Commits"
gen client_commits_log = log(1+client_commits)
label var client_commits_log "EIP Authors Client Commits (log)" 
gen client_commits_dum = (client_commits>0)
label var client_commits_dum "EIP Author also Client Dev"

encode Category , gen(category_encoded)


replace eip_contributors = 0 if eip_contributors ==.

* Principal Component Analysis

pca log_gh log_tw 
predict pca_social, score 
label var pca_social "Social Influence Index (PCA)"

pca n_author eip_contributors total_commit
predict pca_author, score 
label var pca_author "Engagement Index (PCA)"

pca client_commits_dum author_commit between 
predict pca_skill, score 
label var pca_skill "Skill Index (PCA)"

gen implemented = implementation 
replace implemented = . if (status =="Draft" |  status =="Final"  |  status =="Last Call" |   status =="Living" |  status =="Review" ) & implementation ~=1


gen time_start_today = date("june 21, 2023", "MDY") - dofc(sdate)

gen year = year(dofc(sdate))


gen success2 = "Finalized" if status =="Final"
replace success2 = "In Progress" if status =="Draft" | status =="Review" |  status =="Last Call" 
replace success2 = "Failed" if status =="Withdrawn" | status =="Stagnant"  
encode success2 , gen (success2_enc)



// summary stats

local summary_list = "success implemented time_to_final n_author tf_scale gh_follower total_commit author_commit eip_contributors besu_commits erigon_commits geth_commits nethermind_commits client_commits betweenness"

eststo clear	
eststo: estpost summarize `summary_list', detail	
esttab using "analysis\Results\Tables\summstat.tex" , cells("count mean(fmt(%12.3fc)) sd(fmt(%13.3fc)) min(fmt(%12.3gc))  p25(fmt(%12.3gc)) p50(fmt(%12.3gc)) p75(fmt(%12.3gc)) max(fmt(%12.3gc))") ///
	collabels("N." " Mean" "St. Dev." "Min"  "p25" "p50" "p75" "Max" ) ///
	tex replace label nonumbers alignment(rrrrrrrr) noobs

  
  
// Individual Factors
// following are ols results probit specifications are in the end

* Finalization


*success
eststo clear
eststo : mlogit success2_enc log_gh log_tw  i.category_encoded *_dummy , robust
eststo : mlogit success2_enc n_author eip_contributors  i.category_encoded *_dummy , robust
eststo : mlogit success2_enc between client_commits_dum author_commit  i.category_encoded *_dummy , robust
eststo : mlogit success2_enc pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\final_all.tex , unstack varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

	
*Time to success
eststo clear
eststo : quietly reg time_to_final log_gh log_tw i.category_encoded *_dummy, robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded *_dummy, robust
eststo : quietly reg time_to_final between client_commits_dum author_commit  i.category_encoded *_dummy, robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\final_all_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

	

	
* EIP SUCCESS NO IMPL
	

*success
eststo clear
eststo : mlogit success2_enc log_gh log_tw  i.category_encoded *_dummy  if implementation ==., robust
eststo : mlogit success2_enc n_author eip_contributors  i.category_encoded *_dummy  if implementation ==., robust
eststo : mlogit success2_enc between client_commits_dum author_commit  i.category_encoded *_dummy  if implementation ==., robust
eststo : mlogit success2_enc pca_social pca_author pca_skill i.category_encoded *_dummy if implementation ==., robust
esttab using analysis\Results\Tables\final_noimpl.tex , unstack varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

	
	
	
*Time to success
eststo clear
eststo : quietly reg time_to_final log_gh log_tw  i.category_encoded *_dummy if implementation ==., robust
eststo : quietly reg time_to_final n_author eip_contributors  i.category_encoded *_dummy if implementation ==., robust
eststo : quietly reg time_to_final between client_commits_dum author_commit  i.category_encoded *_dummy if implementation ==., robust
eststo : quietly reg time_to_final pca_social pca_author pca_skill i.category_encoded *_dummy if implementation ==., robust
esttab using analysis\Results\Tables\final_noimpl_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

	
* implemented EIP

eststo clear
eststo : quietly reg implemented log_gh log_tw i.category_encoded *_dummy , robust
eststo : quietly reg implemented  n_author eip_contributors  i.category_encoded *_dummy , robust
eststo : quietly reg implemented between  client_commits_dum author_commit  i.category_encoded *_dummy, robust
eststo : quietly reg implemented  pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\implemented.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

	
eststo clear
eststo : quietly reg time_to_final log_gh log_tw i.category_encoded *_dummy , robust
eststo : quietly reg time_to_final  n_author eip_contributors  i.category_encoded *_dummy , robust
eststo : quietly reg time_to_final   between client_commits_dum author_commit  i.category_encoded *_dummy, robust
eststo : quietly reg time_to_final  pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\implemented_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 


	
* Figures: 

*Company

preserve 

keep eip_number *_dummy

foreach x of var *_dummy { 
	rename `x' c_`x' 
	} 

reshape long c_, i(eip_number) j(dum) string
rename c_ num

replace dum = subinstr(dum,"_dummy","",.)
label var num "N. EIPs"
graph hbar (sum) num, over(dum, sort((sum) num) descending) ytitle("N. EIPs") ///
	plotregion(fcolor(white)) graphregion(fcolor(white)) 
graph export "analysis\results\Figures\company_neip.png", as(png) replace

restore

* EIP Over time

graph bar (count) eip_number,  over(Category) over(year) stack asyvars ytitle("N. EIPs") ///
	plotregion(fcolor(white)) graphregion(fcolor(white)) 
graph export "analysis\results\Figures\neip_by_year.png", as(png) replace


* EIP STATUS OVER TIME

graph bar (count) eip_number ,  over(status) over(year) stack asyvars ytitle("% of EIPs") ///
	percent plotregion(fcolor(white)) graphregion(fcolor(white)) 
graph export "analysis\results\Figures\neip_by_yearstatus.png", as(png) replace



	
	
	
