
*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"

********************************************************************************
* ORACLE

insheet using "Analysis\Adoption Analysis\Oracle_Data.csv", comma clear

insobs 1
gen small = (tvl < 150000000 | tvl ==.)
bys small: egen tvl2 = total(tvl)
replace oracle = "others" if oracle ==""
replace tvl = tvl2 if tvl==.
replace small = 0 if v1 ==.


gsort -tvl
graph pie tvl if small == 0, over(oracle) sort desc ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(1) position(6) cols(4))
graph export "analysis\adoption analysis\oracle_pie.png", as(png) replace

graph bar num* if small == 0 & oracle ~="others", over(oracle) ///
	ytitle("Number of Protocols") ///
	plotregion(fcolor(white)) graphregion(fcolor(white) lcolor(white) ///
	ilcolor(white) ifcolor(white)) legend(ring(1) position(6) cols(4))
graph export "analysis\adoption analysis\oracle_bar.png", as(png) replace



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




