* Analysis of Fellowship Ethereum Magicians Determinants

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"


insheet using "Analysis\Magician Comments\FEM_Data_for_regressions.csv", clear comma

rename eip eip_number

merge 1:1 eip_number using "Data\Raw Data\Ethereum_Cross-sectional_Data", keep(1 3) keepusing(n_authors tw_follower gh_follower author_commit n_contributors_eip betweenness_centrality log_tw log_gh tf_scale category_encoded client_commits* eip_read eip_nwords n_committing_authors Category anon_max)

label var replies "N. Comments"
label var views "N. Views"
label var likes "N. Likes"
label var users "N. Unique Users"
label var anon_max "Anonymous Author"
foreach var of varlist replies views likes users { 
	gen log_`var' = log(1+`var')
	}

eststo clear
eststo: reg replies n_authors log_tw log_gh betweenness_centrality anon_max eip_nwords eip_read i.category_encoded i.year
eststo: reg views n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year
eststo: reg likes n_authors log_tw log_gh betweenness_centrality anon_max  eip_nwords eip_read i.category_encoded i.year
eststo: reg users n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year


esttab using "Analysis\Magician Comments\FEM_reg_out.tex", unstack varwidth(35)  ///
	b(2) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace  nonotes noconstant ///
	indicate(  "Year FE = *year") 

eststo clear
eststo: reg log_replies n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year
eststo: reg log_views n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year
eststo: reg log_likes n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year
eststo: reg log_users n_authors log_tw log_gh betweenness_centrality  anon_max eip_nwords eip_read i.category_encoded i.year


esttab using "Analysis\Magician Comments\FEM_reg_out_log.tex", unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace  nonotes noconstant ///
	indicate(  "Year FE = *year") 
