// Regression Code

********************************************************************************
* SETUP

*Main directory

*Cesare 
cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project"

*Moazzam
*cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\"



graph set window fontface "Times New Roman"


********************************************************************************
* UPLOAD AND CLEAN DATA + DEFINE NEW VARIABLES

use "Data\Raw Data\Ethereum_Cross-sectional_Data.dta", clear


drop if Category =="Meta" | Category == "Informational" 

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
label var success "Finalized"
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
replace implemented = . if (status =="Draft" |  status =="Final"  | ///
	status =="Last Call" |   status =="Living" |  status =="Review" ) & implementation ~=1
label var implemented "Implemented"

gen time_start_today = date("june 21, 2023", "MDY") - dofc(sdate)

gen year = year(dofc(sdate))

gen success2 = "Finalized" if status =="Final"
replace success2 = "In Progress" if status =="Draft" | status =="Review" |  status =="Last Call" 
replace success2 = "Failed" if status =="Withdrawn" | status =="Stagnant"  
encode success2 , gen (success2_enc)


********************************************************************************
* Summary Statistics


local summary_list = "success implemented time_to_final n_author tf_scale gh_follower total_commit author_commit eip_contributors besu_commits erigon_commits geth_commits nethermind_commits client_commits betweenness"

eststo clear	
eststo: estpost summarize `summary_list', detail	
esttab using "analysis\Results\Tables\summstat.tex" , cells("count mean(fmt(%12.3fc)) sd(fmt(%13.3fc)) min(fmt(%12.3gc))  p25(fmt(%12.3gc)) p50(fmt(%12.3gc)) p75(fmt(%12.3gc)) max(fmt(%12.3gc))") ///
	collabels("N." " Mean" "St. Dev." "Min"  "p25" "p50" "p75" "Max" ) ///
	tex replace label nonumbers alignment(rrrrrrrr) noobs


	
********************************************************************************
* Stats on Success

generate order =4 if status=="Final"
replace order = 5 if status=="Withdrawn"
replace order = 6 if status=="Stagnant"
replace order = 1 if status=="Draft"
replace order = 2 if status=="Review"
replace order = 3 if status=="Last Call"


graph pie, over(status) sort(order) plabel(_all percent , format(%9.1f) color(black))  pie(4, explode) plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\success.png", as(png) replace




********************************************************************************
* Regressions

*success
eststo clear
eststo : logit success log_gh log_tw  i.category_encoded *_dummy i.year , robust or
eststo : logit success n_author eip_contributors  i.category_encoded *_dummy  i.year, robust or
eststo : logit success between client_commits_dum author_commit  i.category_encoded *_dummy  i.year, robust or
eststo : logit success pca_social pca_author pca_skill i.category_encoded *_dummy i.year, robust or
esttab using analysis\Results\Tables\final_all.tex , eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy" "Year FE = *year") 

eststo clear
eststo res: logit success pca_social pca_author pca_skill i.category_encoded  i.year,  or
eststo full: logit success pca_social pca_author pca_skill i.category_encoded *_dummy i.year,  or
test ConsenSys_dummy StarkWare_dummy Nethermind_dummy Coinbase_dummy BraveSoftware_dummy SpruceSystemsInc_dummy ChainSafeSystems_dummy EthereumNameService_dummy Polytrade_dummy Google_dummy	
lrtest full res


	eststo : logit success log_gh log_tw n_author eip_contributors between client_commits_dum author_commit  i.category_encoded *_dummy  i.year, robust or
	
* EIP SUCCESS NO IMPL/ IMPL
	

*success
eststo clear
eststo : logit success log_gh log_tw  i.category_encoded *_dummy  i.year if implementation ==., robust or
eststo : logit success n_author eip_contributors  i.category_encoded *_dummy   i.year if implementation ==., robust or
eststo : logit success between client_commits_dum author_commit  i.category_encoded *_dummy  i.year  if implementation ==., robust or
eststo : logit success pca_social pca_author pca_skill i.category_encoded *_dummy  i.year if implementation ==., robust or
eststo : logit implemented log_gh log_tw *_dummy  i.year , robust or
eststo : logit implemented  n_author eip_contributors  *_dummy  i.year , robust or
eststo : logit implemented between  client_commits_dum author_commit   *_dummy i.year , robust 
eststo : logit implemented  pca_social pca_author pca_skill  *_dummy i.year , robust or


esttab using analysis\Results\Tables\final_noimpl_impl.tex ,  eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy" "Year FE = *year") ///
	mgroups("Finalized ERC EIP" "Implemented Core EIP", pattern(1 0 0 0 1 0 0 0 ) prefix(\multicolumn{@span}{c}{) ///
	suffix(}) span erepeat(\cmidrule(lr){@span})) 
	
	
	
* implemented EIP

eststo clear
eststo : logit implemented log_gh log_tw *_dummy , robust or
eststo : logit implemented  n_author eip_contributors  *_dummy , robust or
eststo : logit implemented between  client_commits_dum author_commit   *_dummy, robust 
eststo : logit implemented  pca_social pca_author pca_skill  *_dummy, robust or
esttab using analysis\Results\Tables\implemented.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant  eform ///
	indicate("Company FE = *_dummy") 

	

*Time to success
eststo clear
eststo :   reg time_to_final log_gh log_tw i.category_encoded *_dummy, robust or
eststo :   reg time_to_final n_author eip_contributors  i.category_encoded *_dummy, robust or
eststo :   reg time_to_final between client_commits_dum author_commit  i.category_encoded *_dummy, robust
eststo :   reg time_to_final pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\final_all_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 

		
	
*Time to success
eststo clear
eststo :   reg time_to_final log_gh log_tw  i.category_encoded *_dummy if implementation ==., robust or
eststo :   reg time_to_final n_author eip_contributors  i.category_encoded *_dummy if implementation ==., robust or
eststo :   reg time_to_final between client_commits_dum author_commit  i.category_encoded *_dummy if implementation ==., robust or
eststo :   reg time_to_final pca_social pca_author pca_skill i.category_encoded *_dummy if implementation ==., robust or
esttab using analysis\Results\Tables\final_noimpl_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 


eststo clear
eststo :   reg time_to_final log_gh log_tw i.category_encoded *_dummy , robust
eststo :   reg time_to_final  n_author eip_contributors  i.category_encoded *_dummy , robust
eststo :   reg time_to_final   between client_commits_dum author_commit  i.category_encoded *_dummy, robust
eststo :   reg time_to_final  pca_social pca_author pca_skill i.category_encoded *_dummy, robust
esttab using analysis\Results\Tables\implemented_time.tex ,  varwidth(35) modelwidth(10) ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = *_dummy") 


	
********************************************************************************
* Concentration of EIP Development 
* Company Involvment

preserve 

keep eip_number author*id *company*
drop *pastcompany* *jobtitle*

tostring author*_company*, replace

reshape long author@_id author@_company1 author@_company2 author@_company3 author@_company4, i(eip_number) j(id) string
drop if author_id==.
drop id
duplicates drop
reshape long author_company, i(eip_number author_id) j(c) string
rename author_company company
drop if company ==""
drop c

* raw count of companies-eip

save temp, replace
gen one = 1
drop if company =="."
collapse (sum) one, by(company)
gsort -one
graph hbar one if _n<11, ytitle("N. EIP-Authors") over(company, sort((sum) one) descending) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\company_neip1.png", as(png) replace

use temp, clear

drop eip_number
duplicates drop
gen one = 1
drop if company =="."
collapse (sum) one, by(company)
gsort -one
graph hbar one if _n<11, ytitle("N. Authors") over(company, sort((sum) one) descending) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\company_neip2.png", as(png) replace

erase temp.dta

restore




********************************************************************************
* EVOLUTION OF EIP DEVELOPMENT OVER TIME.

* EIP Over time

graph bar (count) eip_number,  over(Category) over(year) stack asyvars ytitle("N. EIPs") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\neip_by_year.png", as(png) replace


* EIP STATUS OVER TIME

graph bar (count) eip_number ,  over(status) over(year) stack asyvars ytitle("% of EIPs") ///
	percent plotregion(fcolor(white))  graphregion(fcolor(white) lcolor(white) ilcolor(white)) 
graph export "analysis\results\Figures\neip_by_yearstatus.png", as(png) replace



	

********************************************************************************
* Concentration of EIP Development

preserve




*top 10 authors	
keep eip_number author* status implemented Category
drop author author*commit* author*_follo* author*_job* author*comp* 


foreach var of varlist author*id {
	local newname = "id_" + subinstr("`var'", "_id","", .)
   	rename `var' `newname'	
	}
	
reshape long author id_author , i(eip status) j(id) string
drop if id_author ==.	
bys id_author: egen n_eip = count(id) 	
bys id_author: egen n_eip_final = count(id) if status=="Final" & (Category =="ERC" | Category == "Interface")	
bys id_author: egen n_eip_imp = count(id) if implemented==1 	


save temp, replace

* Number of authors working on EIPs.
use temp,clear
gen one = 1
collapse (sum) one , by(id_author Category)
bys id_author: egen N = total(one)
replace one = one/N
drop N
bys Category: egen N_All= total(one)
duplicates drop Category, force
keep Category N_All
save temp_all, replace

use temp,clear
keep if status == "Final"  & (Category =="ERC" | Category == "Interface")	
gen one = 1
collapse (sum) one , by(id_author Category)
bys id_author: egen N = total(one)
replace one = one/N
drop N
bys Category: egen N_Finalized= total(one)
duplicates drop Category, force
keep Category N_Finalized
save temp_final, replace


use temp,clear
keep if implemented ==1
gen one = 1
collapse (sum) one , by(id_author Category)
bys id_author: egen N = total(one)
replace one = one/N
drop N
bys Category: egen N_Implemented= total(one)
duplicates drop Category, force
keep Category N_Implemented
merge m:m Category using temp_final
drop _merge
merge m:m Category using temp_all
drop _merge 

reshape long N_, i(Category) j(type) string
drop if N_ ==.
replace type = "All EIPs" if type == "All"
replace type = "Finalized ERC/Interf." if type =="Finalized"
replace type = "Implemented Core/Network EIP" if type =="Implemented"

graph bar (sum) N_ , over(Category) over(type) asyvars stack  ///
	ytitle("N. of Authors")  plotregion(fcolor(white)) graphregion(fcolor(white) ///
	lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\n_authors_by_stage.png", as(png) replace

erase temp_all.dta
erase temp_final.dta


* Implemented EIPs
use temp, clear
keep author n_eip* 
duplicates drop
gsort author -n_eip_imp
bys author: keep if _n==1
gsort -n_eip_imp
graph hbar n_eip_imp if _n<11,  over(author , sort(n_eip_imp) descending) ///
	ytitle("N. of Implemented Core/Network. EIPs") plotregion(fcolor(white)) graphregion(fcolor(white) ///
	lcolor(white) ilcolor(white)) 
graph export "analysis\results\Figures\neip_imp_top10author.png", as(png) replace

* All and Finalized EIPs
use temp, clear
keep author n_eip* 
duplicates drop
gsort author -n_eip_final
bys author: keep if _n==1
gsort -n_eip
graph hbar n_eip if _n<11,  over(author , sort(n_eip) descending) ///
	ytitle("N. of EIPs") plotregion(fcolor(white)) graphregion(fcolor(white) ///
	lcolor(white) ilcolor(white)) 
graph export "analysis\results\Figures\neip_top10author.png", as(png) replace

gsort -n_eip_final
graph hbar n_eip_final if _n<11,  over(author , sort(n_eip_final) descending) ///
	ytitle("N. of Finalized ERCs/Inter.") plotregion(fcolor(white)) ///
	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\neip_final_top10author.png", as(png) replace

** Lorenz Curves
use temp, clear
bys eip_number: gen frac = 1/_N
egen toteip = nvals(eip_number)
bys id_author: egen n_eip_frac = total(frac)	
replace n_eip_frac = n_eip_frac/toteip 

egen toteip_final = nvals(eip_number) if status =="Final"  & (Category =="ERC" | Category == "Interface")	
bys id_author: egen n_eip_frac_final = total(frac) if status =="Final"  & (Category =="ERC" | Category == "Interface")		
replace n_eip_frac_final = n_eip_frac_final/toteip_final 

egen toteip_imp = nvals(eip_number) if implemented == 1
bys id_author: egen n_eip_frac_imp = total(frac) if implemented ==1	
replace n_eip_frac_imp = n_eip_frac_imp/toteip_imp 

keep author id_author n_eip_frac*

duplicates drop

save temp3, replace

* Compute Gini Coefficient
use temp3, clear
gsort id_author -n_eip_frac_imp
bys id_author: keep if _n==1
drop if n_eip_frac_imp ==.
sort n_eip_frac_imp
ineqdec0 n_eip_frac_imp

use temp3, clear
gsort id_author -n_eip_frac_final
bys id_author: keep if _n==1
drop if n_eip_frac_final ==.
sort n_eip_frac_final
ineqdec0 n_eip_frac_final


use temp3, clear
gsort id_author -n_eip_frac
bys id_author: keep if _n==1
drop if n_eip_frac ==.
sort n_eip_frac
ineqdec0 n_eip_frac


* Prepare to plot Lorenz curve

use temp3, clear
gsort id_author -n_eip_frac_final
bys id_author: keep if _n==1
gsort -n_eip_frac_final
gen cum_n_final = sum(n_eip_frac_final)
gen n_final = _n 
replace n_final = . if n_eip_frac_final ==.
label var cum_n_final "Finalized ERCs/Inter."
label var n_final "N. Authors"
keep *_final
rename n_final n
drop if n==.
save temp_final, replace

use temp3, clear
gsort id_author -n_eip_frac_imp
bys id_author: keep if _n==1
gsort -n_eip_frac_imp
gen cum_n_imp = sum(n_eip_frac_imp)
gen n_imp = _n 
replace n_imp = . if n_eip_frac_imp ==.
label var cum_n_imp "Implemented Core/Network. EIPs"
label var n_imp "N. Authors"
keep *_imp
rename n_imp n
drop if n==.
save temp_imp, replace

use temp3, clear
gsort id_author -n_eip_frac
bys id_author: keep if _n==1
gsort -n_eip_frac
gen cum_n = sum(n_eip_frac)
gen n = _n
label var cum_n "All EIPs"
label var n "N. Authors"

keep cum_n n
merge m:1 n using temp_final
drop _merge
merge m:1 n using temp_imp
drop _merge

* add zero obs
insobs 1, before(1)
replace cum_n =0 if n==.
replace cum_n_final =0 if n==.
replace cum_n_imp =0 if n==.
replace n =0 if n==.


* gen percentile of n. 
foreach var in "" "_final" "_imp" {
	egen ntot = count(cum_n`var')  
	gen np`var' = n/(ntot-1) if cum_n`var'~=.
	drop ntot
	}
	
label var np "% of Authors"

* plot lorenz curve
twoway line cum_n n ,  ytitle("% of EIPs") || line cum_n_final n ,  ytitle("% of EIPs") || ///
    line cum_n_imp n ,  ytitle("% of EIPs") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(0) position(4) cols(1))
graph export "analysis\results\Figures\neip_by_author.png", as(png) replace


* plot lorenz curve percentile
twoway line cum_n np ,  ytitle("% of EIPs") || line cum_n_final np_final ,  ytitle("% of EIPs") || ///
    line cum_n_imp np_imp ,  ytitle("% of EIPs") xtitle("% of Authors") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(0) position(4) cols(1))
graph export "analysis\results\Figures\npeip_by_author.png", as(png) replace





erase temp_final.dta
erase temp3.dta
erase temp.dta
erase temp_imp.dta

*% top 10 authors  
di cum_n[10]
di cum_n_final[10]
di cum_n_imp[10]


restore
  
// Individual Factors
// following are ols results probit specifications are in the end




	
	
