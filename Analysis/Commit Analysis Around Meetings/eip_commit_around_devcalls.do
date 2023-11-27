* THIS CODE CREATES A FILE WITH THE EIP COMMITS AROUND A TIME WHEN THE EIP IS DISCUSSED IN A ALL DEVS CALL. 


*cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"

********************************************************************************
* NUMBER OF COMMITS BY EIP, BROKEN DOWN BY AUTHORS AND CONTRIBUTORS

// first we import updated commit file which contains the raw data of commitment and convert it into an stata file
import excel "Data\Commit Data\Eip Commit Data\eip_commit_beg.xlsx", sheet("Sheet1") firstrow clear
rename Username github_username
rename EIP eip_n

drop if github_username == "eth-bot"

gen author_dum = (Author_Id ~=.)

gen ncommit = 1
collapse (count) ncommit , by(eip_n author_dum)
reshape wide ncommit, i(eip_n) j(author_dum)
replace ncommit0 = 0 if ncommit0 ==.
replace ncommit1 = 0 if ncommit1 ==.
egen ncommit_tot = rowtotal(ncommit0 ncommit1)

gen frac = ncommit1/ncommit_tot

replace ncommit_tot = 30 if ncommit_tot > 30
bys ncommit_tot: egen mean_frac = mean(frac)
collapse (percent) eip_n,  by(ncommit_tot mean_frac)
gen eip_n1 = eip_n * mean_frac / 100
gen eip_n0 = eip_n * (1-mean_frac) /100

tostring ncommit_tot, gen(ncom_str)
replace ncom_str = "30+" if ncom_str =="30"
graph bar eip_n1 eip_n0 , stack over(ncom_str, sort(ncommit_tot) ///
	label(labsize(small))) ytitle("% of EIPs") ///
	 b1title("Number of Commits") legend(label(1 "EIP Authors") label(2 "EIP Contributors" )) plotregion(fcolor(white)) ///
	graphregion(fcolor(white) lcolor(white) ilcolor(white))
graph export "Analysis\Commit Analysis Around Meetings\commit_total.png", as(png) replace


********************************************************************************
* ANALYSIS OF DEV CALLS ATTENDEES


insheet using "Analysis\Meeting Attendees and Ethereum Community Analysis\Mapping_File.csv", names clear
rename original_name full_name
replace full_name = "Åukasz Rozmej" if full_name == "ÃÂukasz Rozmej"
replace full_name = subinstr(full_name,"ÃÂ", "Å",.)
replace full_name = subinstr(full_name,"ÃÂ³", "Ã³",.)
replace full_name = subinstr(full_name,"ÃÂ", "Å",.)
replace full_name = subinstr(full_name,"ÃÂ©", "Ã©",.)
replace full_name = subinstr(full_name,"ÃÂ¡", "Ã¡",.)
replace full_name = subinstr(full_name,"ÃÂ¶", "Ã¶",.)
 
drop v1
duplicates drop
save temp_names, replace

insheet using "Analysis\Meeting Attendees and Ethereum Community Analysis\flat_list_meeting_attendees.csv", names clear
merge m:1 full_name using temp_names, 

*unique(meeting)

rename replace_name name
drop full_name _merge
drop if name ==""

gen one = 1
collapse (count) one, by(name)
gsort -one

erase temp_names.dta

rename name attendee_name

save attendee_names, replace
// now bring eip authorship
import delimited "Analysis\Meeting Attendees and Ethereum Community Analysis\unique_names_allplayers.csv", varnames(1)  clear
merge m:m attendee_name using attendee_names
keep if attendee_name !="" & author_name != ""
drop contributor_name client_name _merge
rename one meetings_attended
save attendee_names, replace

use "Analysis\Meeting Attendees and Ethereum Community Analysis\eip_by_authors.dta"
rename author author_name
merge m:m author_name using attendee_names
keep if _merge == 3
gen label = author_name if meetings_attended > 40 | n_eip > 40


twoway scatter meetings_attended n_eip, xtitle("EIPs Co-Authored") ytitle("Meetings Attended") title("Dev Call Attendees and EIP Authorship") mlabel(label) mlabsize(1.5)

graph save "meetings attended and co-authorship graph.png", replace

erase attendee_names.dta

********************************************************************************
* EVENT STUDY OF N. COMMITS AROUND DEV CALL


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



