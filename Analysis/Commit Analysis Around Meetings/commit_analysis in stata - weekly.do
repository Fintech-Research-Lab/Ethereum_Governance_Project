clear
python:
import pandas as pd
import os as os


os.chdir ("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/")

commit = pd.read_stata("Ethereum_Commit.dta")
commit['week'] = commit['distance']//7
weekly_commits = commit.groupby(["eip_number","week"])['CommitDate'].count().reset_index()
weekly_commits2 = weekly_commits[(weekly_commits['week'] >= -12) & (weekly_commits['week'] <= 12)]
weekly_commits2 = weekly_commits2.rename(columns = {'CommitDate' : 'Commits'})

# create an empty data frame that has 24 0 for commits for each 

unique_eip = weekly_commits2['eip_number'].unique()

zero = []
for eip in unique_eip:
    for week in range(-12,13):
        zero.append({'eip_number':eip, 'week' : week, 'Commits' : 0})

zero_df = pd.DataFrame(zero)  

weekly_commits3 = pd.merge(zero_df,weekly_commits2, on = ['eip_number','week'], how = 'left', indicator = True)
weekly_commits3 = weekly_commits3.rename(columns = {'Commits_y':'Commits'})
weekly_commits3['Commits'].fillna(0, inplace = True)
weekly_commits4 = weekly_commits3.drop(columns = ['Commits_x', '_merge'])

weekly_commits4.to_stata("weekly_commits.dta")
end 

cd "C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/"
use "weekly_commits.dta"

bysort eip_number : gen wk = _n

// Run the regression
quietly reg Commits i.wk i.eip_number

// Capture the coefficients
estimates store myModel

matrix b_wk = e(b)[1,1..25]

matrix list b_wk

matrix se = J(1,25,0) // create an empty matrix of size 1x25

forvalues i = 1/25 {
    matrix se[1,`i'] = sqrt(el(e(V),`i',`i')) // fill the matrix with standard errors
}

matrix ci_lower = b_wk - 1.96 * se
matrix ci_upper = b_wk + 1.96 * se


// Create variables for lower and upper confidence intervals and estimates
gen lower = .
gen upper = .
gen estimate = .

// Loop over the elements in the matrices
forvalues i = 1/25 {
    replace lower = ci_lower[1,`i'] in `i'
    replace upper = ci_upper[1,`i'] in `i'
    replace estimate = b_wk[1,`i'] in `i'
}


twoway (rcap lower upper week) (scatter estimate week), xlabel(-12(1)12)


//set trace on
// Loop through the weeks from 2 to 22
forvalues week = 2/22 {
    // Calculate the percentiles and the average of the coefficient variable for each value of wk
    //_pctile myest[coef] if wk == `week', p(5 95) mean
    
    // Store the results in the matrix
    matrix results[`week'-1, 1] = `week'
    matrix results[`week'-1, 2] = scalar(p5)
    matrix results[`week'-1, 3] = r(p95)
    matrix results[`week'-1, 4] = r(mean)
}
matrix list results
//set trace off

// Convert the matrix to a DataFrame
svmat results
reshape long p5 p95 mean, i(week) j(percentile) string

// Create a dot chart that shows the percentiles and the average for each value of wk
graph dot (p5) p5_* (p95) p95_* (mean) mean_*, over(week)


// Convert the matrix to a DataFrame
svmat results
reshape long p5 p95 mean, i(week) j(percentile) string

// Create a dot chart that shows the percentiles and the average for each value of wk
graph dot (p5) p5_* (p95) p95_* (mean) mean_*, over(week)
