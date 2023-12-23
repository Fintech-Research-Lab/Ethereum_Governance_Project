
*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"

********************************************************************************
* ORACLE

insheet using "Analysis\Adoption Analysis\OracleMarketShare.csv", comma clear

* produce lorenz curve for each client

reshape wide activeusers, i(date) j(oracle) string
gen temp = substr(date,1,10)
gen date2 = date(temp,"YMD")
drop date
rename date2 date
format date %td
egen tot = rowtotal(active*)
foreach var of varlist active* {
	replace `var' = 0 if `var' ==.
	gen `var'_perc = `var' / tot
	local var2 =  substr("`var'",12,.)
	rename `var' `var2'
	rename `var'_perc `var2'_perc
	}


gen chain = Chainlink
gen chain2 = chain + Ocean
gen chain3 = chain2 + Band
gen chain4 = chain3 + Api3
	

gen perc_chain = Chainlink_perc
gen perc_chain2 = perc_chain + Ocean_perc
gen perc_chain3 = perc_chain2 + Band_perc
gen perc_chain4 = perc_chain3 + Api3_perc
	
twoway area chain4 chain3 chain2 chain date, 

twoway area perc_chain4 perc_chain3 perc_chain2 perc_chain date,  ///
	yscale(range(0, 1 )) ylabel(#5)  legend( label(1 "Api3") ///
	label(2 "Band") label(3 "Ocean") label(4 "Chainlink")) ///
	xtitle("Date") ytitle("Active Users Market Share") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(1) position(6) cols(4))
graph export "analysis\adoption analysis\oracle.png", as(png) replace




********************************************************************************
* STABLECOIN

	
foreach var in "Analysis\Adoption Analysis\USDC" "Analysis\Adoption Analysis\USDT" "Analysis\Adoption Analysis\DAI" {
	insheet using "`var'_MASTER.csv", comma clear names
	capture drop total 
	ds
	local varlist `r(varlist)'	
	gen total = 0 
	foreach v in `varlist' { 
		capture egen temptotal = rowtotal(total `v')
		capture replace total = temptotal
		capture drop temptotal
	} 
	local var2  = substr("`var'",28,.)
	gen stable = "`var2'"
	save "`var'_temp", replace
	}
clear all
foreach var in "Analysis\Adoption Analysis\USDC" "Analysis\Adoption Analysis\USDT" "Analysis\Adoption Analysis\DAI" {
	append using "`var'_temp"
	erase "`var'_temp.dta"
	}

keep evt_date total stable	
reshape wide total, i(evt_date) j(stable) string
rename totalDAI DAI
rename totalUSDC USDC
rename totalUSDT USDT
egen total = rowtotal(DAI USDC USDT)
replace DAI =  DAI/total
replace USDC =  USDC/total
replace USDT =  USDT/total

egen two =  rowtotal(USDC USDT)
egen three = rowtotal(two DAI)




gen date = dofc(clock(evt_date, "YMD hm"))
format date %td


* MARKETSHARE
*keep if date > date("01-05-2021", "MDY")
keep if date < date("11-18-2023", "MDY")
twoway area three two USDC date,  ///
	yscale(range(0, 1 )) ylabel(#5)  legend( label(1 "DAI") ///
	label(2 "USDT") label(3 "USDC") ) ///
	xtitle("Date") ytitle("TVL Market Share") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(1) position(6) cols(3)) ///
	tlabel(, format(%dm-CY))
graph export "analysis\adoption analysis\stable.png", as(png) replace

* TREND IN TOTAL STABLECOIN MARKET VS TOTAL TVL

keep date total
rename total stable
save temp, replace

insheet using "Analysis\Adoption Analysis\Total_TVL_ETH.csv", clear names

rename protocol date
gen date2 = date(date, "DMY")
drop date
rename date2 date
format date %d
merge 1:1 date using temp, 
drop if _merge==2
egen mindate = min(date) if _merge ==3
drop if date<mindate
drop mindate _merge

gen perc = stable / total

twoway line perc date,  ///
	 ylabel(#5)  legend( label(1 "DAI") ///
	label(2 "USDT") label(3 "USDC") ) ///
	xtitle("Date") ytitle("Total Stablecoin TVL Market Share") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(1) position(6) cols(3)) ///
	tlabel(, format(%dm-CY))
graph export "analysis\adoption analysis\stable_perc.png", as(png) replace




