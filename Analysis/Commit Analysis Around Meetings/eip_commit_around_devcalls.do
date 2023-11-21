* THIS CODE CREATES A FILE WITH THE EIP COMMITS AROUND A TIME WHEN THE EIP IS DISCUSSED IN A ALL DEVS CALL. 


*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"


* Import list of EIPS without living, and meta

use "Data\Raw Data\Ethereum_Cross-sectional_Data", clear
keep if Category ~= "Meta" & Category ~="Informational"
keep eip_number 
rename eip_number eip_n
save temp_eip, replace

// Import call list with dates EIP are discussed, and clean/reshape it.
insheet using "Data\Commit Data\Eip Commit Data\Calls_Updated_standardized.csv", clear comma names
keep if eip_mention == "TRUE"
replace eip = subinstr(eip, "EIP-","",.)
split eip , parse(,) generate(eip_n)

keep meeting date eip_n*
destring eip_n*, replace

reshape long eip_n , i(meeting date) j(eip)
drop eip
drop if eip_n == .

merge m:1 eip_n using temp_eip  , keep(3)
drop _merge
duplicates drop

save temp_call_eip, replace
erase temp_eip.dta

// first we import updated commit file which contains the raw data of commitment and convert it into an stata file
import excel "Data\Commit Data\Eip Commit Data\eip_commit_beg.xlsx", sheet("Sheet1") firstrow clear
rename Username github_username
rename EIP eip_n

drop if github_username == "eth-bot"
keep eip_n CommitDate

* joinby with call dates and eip discussed. 
count
joinby eip_n using temp_call_eip, unmatched(none)
count

* now we have a row unique each eip, commit, and meeting

* Find distance between dates

gen meet_date = date(date, "MDY")
drop date
format meet_date %td
gen call_date = dofc(CommitDate)
format call_date %td
drop CommitDate
gen distance = meet_date - call_date

gen one = 1
collapse (sum) one, by(eip_n meeting meet_date call_date distance) 
keep if distance > -183 & distance < 189

tostring eip_n, replace
gen id = meeting + eip_n
encode id, generate(eip_meeting)
xtset eip_meeting distance
tsfill, full
replace one = 0 if one ==. 
keep eip_meeting one distance
gen dw = floor(distance/7)

collapse(sum) one, by(dw eip_meeting)
tabulate dw, generate(week)

foreach v of varlist week* {
	local x : variable label `v'
	local y = substr("`x'",6,5)
	label var `v' "`y'"
	}

eststo clear
xtreg one week2-week53 i.eip_meeting, cluster(eip_meeting)
esttab using analysis\Results\Tables\commit_call.tex , eform unstack varwidth(35)  ///
	b(4) nobaselevels noomitted interaction(" X ") label ar2(2)  ///
	star (* .1 ** .05 *** .01) replace nodepvars nomtitles mlabels(none) nonotes noconstant ///
	indicate("EIP FE = *.eip_meeting") 


coefplot, vertical drop(_cons *eip_meet*) xline(26) levels(90) xlabel(, angle(45) ///
	labsize(small)) ytitle("Number of Commits") xtitle("Weeks from Dev Call") ///
	omitted plotregion(fcolor(white)) ///
	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "Analysis\Commit Analysis Around Meetings\commit_call.png", as(png) replace


erase temp_call_eip.dta



