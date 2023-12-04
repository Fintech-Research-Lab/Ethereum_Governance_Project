
*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"

* Put all client commit together

local files : dir "Data\Commit Data\client_commit" files "comm*.dta"
foreach file in `files' {
	local cdfile = "Data\Commit Data\client_commit\" + "`file'"
	use "`cdfile'" , clear
	local cl = subinstr(substr("`file'",8,.),".dta","",.)
	gen client = "`cl'"
	save "Data\Commit Data\client_commit\temp_`file'", replace
	}

clear all	
local files : dir "Data\Commit Data\client_commit" files "comm*.dta"
foreach file in `files' {
	local cdfile = "Data\Commit Data\client_commit\" + "temp_`file'"
	append using "`cdfile'" 
	erase "Data\Commit Data\client_commit\temp_`file'"
	}

* get summary stats
	
drop if login ==""

gen ncomm = 1
bys client login: egen ncomm2 = count(ncomm)
bys client login: keep if _n==1
collapse (count) ncomm , by(client login) 

unique(login), by(client)
preserve
collapse (sum) ncomm, by(login)
sum , d
restore


* Compute gini coefficient

gen gini_av = 0
foreach var in besu erigon geth nethermind {
	di "`var'"
	gsort -ncomm
	ineqdec0 ncomm if client =="`var'"
	replace gini_av = gini_av + r(gini)
	}

replace gini_av = gini_av /4
sum gini_av	
* produce lorenz curve for each client
	
	
gsort client -ncomm login
by client: egen N = total(ncomm) 
by client: gen client_cont = _n 
by client: gen client_cont_tot = _N 
gen client_cont_perc = client_cont / client_cont_tot
gsort client -ncomm login
by client: gen ncomm_cum = sum(ncomm)
replace ncomm_cum = ncomm_cum/N

foreach var in besu erigon geth nethermind {
	insobs 1, before(1)
	replace ncomm_cum =0 if client_cont ==.
	replace client_cont =0 if client_cont ==.
	replace client_cont_perc =0 if client_cont_perc ==.
	replace client = "`var'" if client ==""
	}


* Plot loren curve	

twoway line ncomm_cum client_cont if client == "besu" & client_cont<100,  ytitle("% of Commits") ///
	||  line ncomm_cum client_cont if client == "erigon" & client_cont<100,  ytitle("% of Commits")  ///
	||  line ncomm_cum client_cont if client == "geth" & client_cont<100,  ytitle("% of Commits")  ///
	||  line ncomm_cum client_cont if client == "nethermind" & client_cont<100,  ytitle("% of Commits")  ///
	xtitle("N. of Developers") plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(0) position(4) cols(1) label(1 "Besu") label(2 "Erigon") label(3 "Geth") label(4 "Nethermind"))
graph export "Analysis\Client Analysis\lorenz_commits.png", as(png) replace


********************************************************************************
* CLIENT EMPLOYMENT ANALYSIS

insheet using "Data\Raw Data\Client_Employment.csv", clear names


egen found = count(Name) if company ~=""
replace found = found / _N
sum found

drop if company ==""
gen one = 1

collapse (count) one, by(company client)

gsort -one

gen company2 = company
replace company2 = "Others" if one <6
graph bar one , over(company2) over(client) asyvars stack percentages ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) ytitle("% of Client Developers")
graph export "Analysis\Client Analysis\client_company.png", as(png) replace
	

