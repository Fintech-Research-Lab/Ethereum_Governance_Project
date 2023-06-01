# Ethereum_Governance_Project
Ethereum Governance Project is designed to store codes associated with a finance research project to find governance process in Ethereum. Specifically, the initial code is designed to find how Ethereum Improvement Protocols (EIPs) are created. 
# DATA GATHERING
The process starts with the data gathering. As a first step we begin with a file called ALLEIPS2.csv 
This file is created by taking all EIPS that have been initiated. By initiated we mean that an EIP number has been established and an EIP has been created using proper format and procedures. This file contains 553 EIPs that were created as of May 2023. The file contains a unique EIP Number, Title, Author(s), and status which tells you whether EIP is final, withdrawn, in review ,etc
We download this file. The code "Authot Name Matching.R" is designed to create a unique author ID and then match the author names to separaterly created files which contains data on twiiter followers and gitHub
followers

Author Name Matching.R does the follwing
  a) Splits Author Columns into multiple columns so that co-authors of specific EIPs can be split into separate names
  b) Since names may have formatting issues, we "treat" the names to do the following three steps
    bi) We remove space between names or in some cases spaces exists before the first name
    bii) we apply a filter to remove all special characters like Latic ASICS (enunciations in names)
    biii) We lower the case
    
After treatment we call these names mod_names (as in modified names). We asign a sequence of numbers to create unique "author_id" so that we can merge documents that contain twitter, github followers, and comapny information. 

We create columns in the ALLEIPS file that add 11 author_id columns e.g. author1_id, author2_id....

We then apply R's fuzzy logic package called stringdist to match twitter names with our author names. Twitter file contain manual gathering of twitter followers and followings. This file contains 588 observations.
We find all but 15 names using name matching, we assign author_ids to all matched names. 26 names in twitter file are not in our author list. These could be due to formating of names in twitter
This process will be followed by manual matching and checks to ensure that twitter file contains matched names, author_id and content information like twiiter follower and following data

The same process is applied to a separate file that contains gitHub follower data which has 537 observations. This file has 139 "unmatched" names and 91 names that are in the gitHub follower file but not present in our file. This file will also be manually checked
