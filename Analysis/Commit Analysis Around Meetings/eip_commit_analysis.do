
*cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\"

cd "C:\Users\cf8745\Box\Research\Ethereum Governance\Ethereum_Governance_Project\"


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
