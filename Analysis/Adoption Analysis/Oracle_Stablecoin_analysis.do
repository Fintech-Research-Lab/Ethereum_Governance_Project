
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



	
