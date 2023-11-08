clear
python:
import pandas as pd
import os as os

* Define Directory: 

* Cesare
direc = "C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/"

* Moazzam
direc = "C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/"

os.chdir (direc + "Data/Raw Data/")

commit = pd.read_stata("eip_commit.dta")
commit = commit[commit['Author'] != 'eth-bot']
commit['distance'] = (commit['CommitDate'] - commit['MeetingDate']).dt.total_seconds() / (24 * 60 * 60)
commit['day'] = commit['distance']//1
daily_commits = commit.groupby(["eip_number","day"])['CommitDate'].count().reset_index()
daily_commits2 = daily_commits[(daily_commits['day'] >= -30) & (daily_commits['day'] <= 30)]
daily_commits2 = daily_commits2.rename(columns = {'CommitDate' : 'Commits'})

# create an empty data frame that has 24 0 for commits for each 

unique_eip = daily_commits2['eip_number'].unique()

zero = []
for eip in unique_eip:
    for day in range(-30,31):
        zero.append({'eip_number':eip, 'day' : day, 'Commits' : 0})

zero_df = pd.DataFrame(zero)  

daily_commits3 = pd.merge(zero_df,daily_commits2, on = ['eip_number','day'], how = 'left', indicator = True)
daily_commits3 = daily_commits3.rename(columns = {'Commits_y':'Commits'})
daily_commits3['Commits'].fillna(0, inplace = True)
daily_commits4 = daily_commits3.drop(columns = ['Commits_x', '_merge'])
os.chdir(direc + "Analysis/Commit Analysis Around Meetings/")
daily_commits4.to_stata("daily_commits.dta")
end 

* Cesare
local direc = "C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/"

* Moazzam
*local direc = "C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/"


cd "`direc'Analysis/Commit Analysis Around Meetings/"
use "daily_commits.dta"

bysort eip_number : gen dy = _n

// Run the regression
quietly reg Commits i.dy i.eip_number

// Capture the coefficients
estimates store myModel

matrix b_dy = e(b)[1,1..61]

matrix list b_dy

matrix se = J(1,61,0) // create an empty matrix of size 1x25

forvalues i = 1/61 {
    matrix se[1,`i'] = sqrt(el(e(V),`i',`i')) // fill the matrix with standard errors
}

matrix ci_lower = b_dy - 1.96 * se
matrix ci_upper = b_dy + 1.96 * se


// Create variables for lower and upper confidence intervals and estimates
gen lower = .
gen upper = .
gen estimate = .

// Loop over the elements in the matrices
forvalues i = 1/61 {
    replace lower = ci_lower[1,`i'] in `i'
    replace upper = ci_upper[1,`i'] in `i'
    replace estimate = b_dy[1,`i'] in `i'
}


twoway (rcap lower upper day) (scatter estimate day), xlabel(-30(1)30, labsize(*0.4))



