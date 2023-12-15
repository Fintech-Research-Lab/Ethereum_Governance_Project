// Regression Code

********************************************************************************
* SETUP

*Main directory

*Cesare 
cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project"

*Moazzam
*cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum_Governance_Project\"



graph set window fontface "Times New Roman"


********************************************************************************
* UPLOAD AND CLEAN DATA + DEFINE NEW VARIABLES

use "Data\Raw Data\Ethereum_Cross-sectional_Data.dta", clear


********************************************************************************
* ADD TOP10 COMPANY DUMMIES AND PLOT EMPLOYMENT OF EIP AUTHORS

keep eip_number author*id *company*
drop *pastcompany* *jobtitle*

tostring author*_company*, replace

reshape long author@_id author@_company1 author@_company2 author@_company3 author@_company4 author@_company5, i(eip_number) j(id) string
drop if author_id==.
drop id
duplicates drop
reshape long author_company, i(eip_number author_id) j(c) string
rename author_company company
drop if company ==""
drop c
save temp, replace

* raw count of companies-eip

* THIS COUNTS THE FREQUENCY OF COMPANY COUNT FOR EACH AUTHOR-EIP PAIR
gen one = 1
drop if company =="."

collapse (sum) one, by(company)
gsort -one company
graph hbar one if _n<11, ytitle("N. EIP-Authors") over(company, sort((sum) one) descending) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\company_neip1.png", as(png) replace

ineqdec0 one

gsort -one company

gen cum_n_one = sum(one)
egen tot = total(one)
replace cum_n_one = cum_n_one / tot

gen n_one = _n
label var cum_n_one "% EIP-Authors"
label var n_one "%Companies"

keep n_one cum_n_one

save temp_lor1, replace




* THIS COUNTS THE FREQUENCY OF COMPANY COUNT FOR EACH AUTHOR
use temp, clear
drop eip_number
duplicates drop
gen one = 1
drop if company =="."
collapse (sum) one, by(company)
gsort -one company
graph hbar one if _n<11, ytitle("N. Authors") over(company, sort((sum) one) descending) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\company_neip2.png", as(png) replace

ineqdec0 one

gsort -one company

gen cum_n_one2 = sum(one)
egen tot = total(one)
replace cum_n_one2 = cum_n_one / tot

gen n_one = _n
label var cum_n_one2 "% Authors"
label var n_one "%Companies"

keep n_one cum_n_one2

save temp_lor2, replace




* THIS COUNTS THE FREQUENCY OF COMPANY COUNT FOR EACH EIP
use temp, clear
drop author_id
duplicates drop
gen one = 1
drop if company =="."
collapse (sum) one, by(company)
gsort -one company
graph hbar one if _n<11, ytitle("N. EIP") over(company, sort((sum) one) descending) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\company_neip3.png", as(png) replace


ineqdec0 one

gsort -one company
gen cum_n_one3 = sum(one)
egen tot = total(one)
replace cum_n_one3 = cum_n_one / tot

gen n_one = _n 
label var cum_n_one3 "% EIP"
label var n_one "% Companies"

keep cum_n_one3 n_one 


merge m:1 n using temp_lor1
drop _merge
erase temp_lor1.dta

merge m:1 n using temp_lor2
drop _merge
erase temp_lor2.dta

replace n_one = n_one / _N

* add zero obs
insobs 1, before(1)
replace cum_n_one =0 if n==.
replace cum_n_one2 =0 if n==.
replace cum_n_one3 =0 if n==.
replace n_one =0 if n_one==.


* plot lorenz curve
twoway line cum_n_one2 n_one,  ytitle("% of EIPs / Authors") || line cum_n_one3 n_one , ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(0) position(4) cols(1))
graph export "analysis\results\Figures\company_lorenz.png", as(png) replace

	
	
	
	




erase temp.dta

gsort -one
keep if _n<11
keep company
save "Data\Raw Data\temp_top10" , replace

levelsof company, local(top10) 

use "Data\Raw Data\Ethereum_Cross-sectional_Data.dta", clear

	
foreach comp in `top10' {
	di "`comp'"
	local comp2 = subinstr("`comp'"," ","_",.)
	local comp2 = subinstr("`comp2'",".","_",.)

	gen cdum_`comp2' = 0
	forvalues x = 1 / 15 {
		forvalues c = 1/5{
			replace cdum_`comp2' = 1 if author`x'_company`c' == "`comp'"
			}
		}
	}

erase "Data\Raw Data\temp_top10.dta"
	
********************************************************************************
* ETHEREUM FOUNDATION TIME TRENDS

gen year = year(sdate)

save temp_ef, replace

forvalues y = 2015/2023 {
	use temp_ef, clear
	keep if year == `y' | year == `y'-1
	gen tot = _N
	egen EF = count(eip_number) if cdum_Ethereum_Foundation ==1
	egen tot_erc = count(eip_number) if Category =="ERC" | Category =="Interface"
	egen EF_erc = count(eip_number) if cdum_Ethereum_Foundation ==1 & (Category =="ERC" | Category =="Interface")
	egen tot_core = count(eip_number) if Category =="Core" | Category =="Networking"
	egen EF_core = count(eip_number) if cdum_Ethereum_Foundation ==1 & (Category =="Core" | Category =="Networking")
	gen frac = EF / tot
	gen frac_erc = EF_erc / tot_erc
	gen frac_core = EF_core / tot_core
	keep frac*
	gen year = `y'
	duplicates drop
	save temp_frac`y', replace
	}

clear all
forvalues y = 2015/2023 {
	append using temp_frac`y'
	erase temp_frac`y'.dta
	}

collapse (max) frac*, by(year)	

label var frac "All EIPs"
label var frac_erc "ERCs EIPs"
label var frac_core "Core EIPs"

twoway line frac year  || line frac_erc year || line frac_core year ,  ///
	xtitle("Year") ytitle("% EIPs Co-Authored by Ethereum Foundation") ///
	xla(2015(1)2023) xtick(2015(1)2023) legend(ring(0) position(2) cols(1))  ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\eip_ef_by_year.png", as(png) replace

	
use temp_ef, clear
erase temp_ef.dta

********************************************************************************
* Principal Component Analysis

pca log_gh log_tw 
predict pca_social, score 
label var pca_social "Social Influence Index (PCA)"

pca n_author n_contributors_eip total_eip_commit
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


gen success2 = "Finalized" if status =="Final"
replace success2 = "In Progress" if status =="Draft" | status =="Review" |  status =="Last Call" 
replace success2 = "Failed" if status =="Withdrawn" | status =="Stagnant"  
encode success2 , gen (success2_enc)


********************************************************************************
* Summary Statistics


local summary_list = "success implemented time_to_final n_author tf_scale gh_follower total_eip_commit author_commit n_contributors_eip besu_commits erigon_commits geth_commits nethermind_commits client_commits betweenness"

eststo clear	
eststo: estpost summarize `summary_list', detail	
esttab using "analysis\Results\Tables\summstat.tex" , cells("count mean(fmt(%12.3fc)) sd(fmt(%13.3fc)) min(fmt(%12.3gc))  p25(fmt(%12.3gc)) p50(fmt(%12.3gc)) p75(fmt(%12.3gc)) max(fmt(%12.3gc))") ///
	collabels("N." " Mean" "St. Dev." "Min"  "p25" "p50" "p75" "Max" ) ///
	tex replace label nonumbers alignment(rrrrrrrr) noobs


	
********************************************************************************
* Stats on Success and category

generate order =4 if status=="Final"
replace order = 5 if status=="Withdrawn"
replace order = 6 if status=="Stagnant"
replace order = 1 if status=="Draft"
replace order = 2 if status=="Review"
replace order = 3 if status=="Last Call"


graph pie, over(status) sort(order) plabel(_all percent , format(%9.1f) ///
	color(black))  pie(4, explode) plotregion(fcolor(white)) ///
	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\success.png", as(png) replace


graph pie, over(Category) sort(order) plabel(_all percent , format(%9.1f) ///
	color(black))  plotregion(fcolor(white)) ///
	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\eip_by_category.png", as(png) replace




********************************************************************************
* Regressions

*success
eststo clear
eststo one : reg success log_gh log_tw  i.category_encoded cdum_* i.year , robust 
eststo two : reg success n_author n_contributors_eip  i.category_encoded cdum_*  i.year, robust 
eststo three: reg success between client_commits_dum author_commit  i.category_encoded cdum_*  i.year, robust 
eststo four: reg success pca_social  i.category_encoded cdum_* i.year, robust 
eststo five: reg success pca_author  i.category_encoded cdum_* i.year, robust 
eststo six: reg success pca_skill i.category_encoded cdum_* i.year, robust 
eststo seven: reg success pca_social pca_author pca_skill i.category_encoded cdum_* i.year, robust 

unab varlist : cdum_*
foreach cd in `varlist'{
	local var2 = substr("`cd'",6,.)
	label var `cd' "`var2'"
	}
	
test `varlist'
coefplot, drop(_cons) yline(0) vertical keep(cdum_*) xlabel(, angle(45) ///
	labsize(small)) levels(90) ytitle("Likelihood of Success") ///
	plotregion(fcolor(white)) 	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "analysis\results\Figures\cdum_coef.png", as(png) replace


eststo eight: reg success pca_social pca_author pca_skill i.category_encoded cdum_*  i.year if implementation ==., robust 
eststo nine: reg implemented  pca_social pca_author pca_skill  cdum_* i.year , robust 

esttab one two three seven using analysis\Results\Tables\final_all.tex , eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = cdum_*" "Year FE = *year") 

	
	
esttab one two three using analysis\Results\Tables\final_all_alt1.tex , eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = cdum_*" "Year FE = *year") 

esttab four five six seven eight nine using analysis\Results\Tables\final_all_alt2.tex , eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = cdum_*" "Year FE = *year") 
	
	
	
	
* EIP SUCCESS NO IMPL/ IMPL
	

*success
eststo clear
eststo : reg success log_gh log_tw  i.category_encoded cdum_*  i.year if implementation ==., robust 
eststo : reg success n_author n_contributors_eip  i.category_encoded cdum_*   i.year if implementation ==., robust 
eststo : reg success between client_commits_dum author_commit  i.category_encoded cdum_*  i.year  if implementation ==., robust 
eststo : reg success pca_social pca_author pca_skill i.category_encoded cdum_*  i.year if implementation ==., robust 
eststo : reg implemented log_gh log_tw cdum_*  i.year , robust 
eststo : reg implemented  n_author n_contributors_eip  cdum_*  i.year , robust 
eststo : reg implemented between  client_commits_dum author_commit   cdum_* i.year , robust 
eststo : reg implemented  pca_social pca_author pca_skill  cdum_* i.year , robust 


esttab using analysis\Results\Tables\final_noimpl_impl.tex ,  eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("Category FE = *.category_encoded" "Company FE = cdum_*" "Year FE = *year") ///
	mgroups("Finalized ERC EIP" "Implemented Core EIP", pattern(1 0 0 0 1 0 0 0 ) prefix(\multicolumn{@span}{c}{) ///
	suffix(}) span erepeat(\cmidrule(lr){@span})) 
	
	

********************************************************************************
* EVOLUTION OF EIP DEVELOPMENT OVER TIME.


* N. unique vauthors over time
preserve
keep year author*_id eip_number
reshape long author@_id, i(year eip_number) j(n)
keep year author_id
duplicates drop
bys year: egen n_author=count(year)
drop author_*id
duplicates drop
save temp_year_author, replace


* EIP Over time
restore
preserve

merge m:1 year using temp_year_author, keep(1 3)
drop _merge
erase temp_year_author.dta

bys Category year: egen neip = count(eip_number)
keep Category year neip n_author
duplicates drop
reshape wide neip, i(year n_author) j(Category) string

egen Networking = rowtotal(neipCore neipNetworking)
egen ERC = rowtotal(Networking neipERC)
egen Interface = rowtotal(ERC neipInterface) 
rename neipCore Core

 
graph twoway bar Core  year , yaxis(1) barw(0.8) xtitle("Year") ytitle("N. of EIPs") ///
	|| rbar Core Networking year , yaxis(1)  barw(0.8)|| ///
	rbar Networking ERC year , yaxis(1)  barw(0.8) || rbar ERC Interface year  , ///
	yaxis(1)  barw(0.8) || 	scatter  n_author year ,  yaxis(2)  ///
	ytitle("N. of Unique Authors", axis(2)) msymbol(T) mcolor(black)  || ///
	line n_author year ,  yaxis(2)  lcolor(black)  xlabel(2015(1)2023) ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ilcolor(white)) legend(order(1 "Core" 2 "Networking" 3 "ERC" 4 "Interface" 5 "N. Unique Authors")) 
graph export "analysis\results\Figures\neip_by_year.png", as(png) replace


restore 

	

********************************************************************************
* Concentration of EIP Development


*top 10 authors	
keep eip_number author* status implemented Category sdate
drop author author*commit* author*_follo* author*_job* author*comp* author*between* author*close* author*eigen*


foreach var of varlist author*id {
	local newname = "id_" + subinstr("`var'", "_id","", .)
   	rename `var' `newname'	
	}
	
reshape long author id_author , i(eip status sdate) j(id) string
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


graph bar (asis) N_* , over(Category) over(type) asyvars  stack  ///
	ytitle("N. of Authors")  plotregion(fcolor(white)) graphregion(fcolor(white) ///
	lcolor(white) ilcolor(white)) blabel(none)  
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
keep author n_eip* id_author 
duplicates drop
gsort author -n_eip
bys author: keep if _n==1
gsort -n_eip
save "Analysis\Meeting Attendees and Ethereum Community Analysis\eip_by_authors.dta"
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


*% top 10 authors  
di cum_n[10]
di cum_n_final[10]
di cum_n_imp[10]



* GINI COEFFICIENT BY Rolling 2 year
	
use temp, clear
gen gini = .
gen year = .
keep gini year
drop if year==.
save gini, replace

forvalues y = 2016/2023 {

	use temp, clear
	gen year = year(sdate)
	keep if year == `y' | year == `y'-1
	bys eip_number: gen frac = 1/_N
	egen toteip = nvals(eip_number)
	bys id_author: egen n_eip_frac = total(frac)	
	replace n_eip_frac = n_eip_frac/toteip 

	keep author id_author n_eip_frac*

	duplicates drop
	gsort id_author -n_eip_frac
	bys id_author: keep if _n==1
	drop if n_eip_frac ==.
	sort n_eip_frac
	ineqdec0 n_eip_frac
	
	gen gini = r(gini) 
	keep gini
	duplicates drop
	gen year = `y'
	save temp_gini, replace
	use gini, clear
	append using temp_gini
	save gini, replace
	erase temp_gini.dta
	}
	
use gini, clear

graph bar gini, over(year) ytitle("Gini Coefficient")  ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(0) position(4) cols(1))
graph export "analysis\results\Figures\gini_by_year.png", as(png) replace

* Compute Gini Coefficient
	
erase gini.dta
erase temp_final.dta
erase temp3.dta
erase temp.dta
erase temp_imp.dta
