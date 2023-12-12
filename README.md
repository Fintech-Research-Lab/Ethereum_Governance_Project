This document describes how to replicate the data and the results of the paper "Ethereum Governance". 

# Data Collection Process.

## EIP DATA
1. *EIP List*: The data collection process begins with scraping the list of EIPs and related authors from the [Ethereum EIP page](https://eips.ethereum.org/all). This website contains information of all EIPs, their status and their authors. This data is collected using a web-scrapping code as of **06/21/2023**. The code *EIP list generating code.py* scrapes EIP Number, Authors, Status, and Title, and stores it into the file allEIPsandAuthorsv2_beg.csv. (Note that the code was run on 6/21/2023. Rerunnign the code now would produce a different set of EIPs, as new EIPS have been added since then). 
2. *EIP Author ID*: The same EIP author name is sometime spelled differently in the EIP list. We thus take the EIP author list, and manually assign a unique author identidier (*Author id*) to each author and the related github handle. The file *unique_author_names_with_id.csv* includes the list of authors and id.   
3. *EIP List and Standardized Authors*: The python code *pythoncode to prepare data merging* takes the EIP list, and adds the author id to each author, saving the file as *Ethereum_Cross-sectional_Data.csv*.
4. *EIP Implementation*. We manually went throguh all EIPs, and classified them on whether Whether an EIP requires a client implementation or not, and in which fork it was implemented. The information is saved in *eip_implementation.csv*
5. *EIP Start Date*: *startdate_scraping.py* collect start date of all eips and stores it into *eip_startdates.csv*  
6. *EIP End Date*: end date of all EIPs that have reached final stage stored in file *finaleip_enddates.csv*
7. *EIP Authorship betweenness*. we use python code *??????.py* to create a betweenness centrality measure amongs all co-authors of EIPs. The code takes file *Ethereum_Cross-Sectional_Data.csv* and create a betweenness centrality measure for each EIP based on author_ids. We merge the betweenness_centrality measure in the Ethereum_Cross-sectional_Date.dta using eip_number.

## SOCIAL DATA
8. *Github Followers*: *Github Follower Extract.py* scrapes the github followers for each EIP authors with a github handle. The code generates an interim file which is stored in *author_github_following_raw.csv*. We apply python code *github data reconciliation* to reconcile an older version of this data and match it with author_ids in this code to create a final github data stored in *GitHub_Data.csv*  
9. *Twitter Data*: We manually collected information on the authors' Twitter following and Twitter followers, if available. This data is in *Twitter_Data.csv*.
10. *LinkedIn Data:* We also manually collected data from LinkedIn, capturing details of up to four current companies where the authors are presently employed, along with their job titles. Additionally, we gathered information on up to the last 10 companies where they had previously worked, including their past job titles. This is in *LinkedIn_Data.csv*

## COMMIT DATA
11. *EIP Commit*. Each EIP has a github repository. We collect all commitments made by any contributor to the EIP, whether they are an author or a contributor who may not be an author. This collection is done through a python code *???????.py* the output of this code is a file *updated_commits.xlsx*
    - We use a stata code *eip commit data creation code.do* which takes this data and merge it with *author.dta*. If the merged value matches author.dta we flag the github_username *eip_author = 0/1*. If the github_usernames does not exists in the author.dta (_merge == 1) then we consider it as whether the github username that contributes to EIP is part of the author list or not. If it is a part of the author list we create a flag *eip_author = 1/0* indicating whether commitor is an eip author or not. We then aggregate this data to create cross-sectional equivalent based on eip_number to get the following three values:
    - Total number of commits to each EIP and merge it with the cross-sectional data in the *data merging code.do* and call it *total_commits*
    - Author Commits which is number of commits made by EIP Authors and merge it with the cross-sectional data in the *data merging code.do* and call it *author_commits*
    - Unique number of participants that are commiting to the eip github for each eip. We call this variable *contributors* and merge this with the cross-sectional data in the *data merging code.do*
12. *Client Commit*. We also download all commit to the 4 largest client repositories: besu, erigon, geth, and nethermind. *???????.py* scrapes the data, and stores it into four stata files *commitsbesu.dta*,*commitserigon.dta*,*commitsgeth.dta*, and "commitnethermind.dta".
  - We then aggregate all commits by each github username
  - We match github usernames with authors to see how many commits are done by eip authors
  - We then merge this to the cross-sectional data for each author 1 to 11
  - We create a maximum of all authors for eip. This process is repeated for 4 clients so we get *geth_commits*, *besu_commits*, *erigon_commits*, and *nethermind_commits* as four variables in the cross-sectional data. The process is included in the *data merging code.do*

## Merge and Prepare files for regressions
13. *Merge all files* We use a stata code called *data merging code.do* to create the cross-sectional data organized by EIP_Number. The following steps describe the process:
* The cross-sectional data is generated by first importing *Ethereum_Crossectional_Data.csv*. This is the output of running python code *pythoncode to prepare data merging*
* After downloading the above csv file and converting into stata, we merge the following data:
  - twitter data for each author and create a tw_follower variable which is the maximum twitter follower of any of the authors listed in the EIP.
  - Github Follower data on each author and create a gh_follower variable which is the maximum github follower of any of the authors listed in the EIP.
  - Linkedin data for each author which includes, upto 4 companies in which author may be working and 10 past companies where authors might have worked along with their job titles
  - create a variable n_authors which represents the number of authors for each EIP
  - merge the total commits on eip's github for each eip. Eip commit data is described below
  - merge the number of unique authors who commit to the eip
  - merge the number of unique contributors who are not eip authors that commit to the eips
  - merge betweenness centrality measure of co-authors which is generated through a python code *????????.py*
  - merge manually collected end dates (variable named edate) for all finalized EIPs
  - merge scrapped start dates of all eips (Variable named sdate)
  - merge implementation data
  - rearrange variables
  - Add *client* commit data for each author, that is each author's contribution to client repository of github. There are four clients Besu, Erigon, Geth, and Nethermind.
  - Create 4 variables called geth_commits, besu_commits, erigon_commits, and nethermind_commits that represent the maximum commitment by each author in the eip for each of the client commits
13. *Preparing Data for Regression* Final step is to prepare the cross-sectional data for regression. This is done using the stata code *Preparing Regression Data.do* . The following steps are taken:
    - Finding top 10 companies represented by authors in the Cross-sectional data. We count just the company1 where authors work and find the frequency of authors by each company. We then sort it and create dummy variables for top 10 companies. In addition to using company dummies, the preparation code also create a success variable that uses 0 and 1 for eips in progress and finalized.
    - create success variable which takes a value of 1 if eip is finalized and a value of 0 if it is withdrawn or stagnant and a value of NA(.) if it is Living, Last Call or Review
    - create a variable called "Implementation" which takes the value of 1 if eip has been implemented in a Fork and the value of 0 for all eips that have either a 1 or 0 in the "Implentable" column. These are eips that are deemed implementable through a client code. 
14. *Replication Steps*
    - Make sure you have all the files in the correct directory
    - Assign proper directory to the *data merging code.do*
    - Run *data merging code.do*
    - Run *Preparing Regression Data.do*
