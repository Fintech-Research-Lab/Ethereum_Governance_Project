# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import os as os

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Analysis Code/Data Fixing Codes/")
github = pd.read_csv("author_github_following_raw.csv")
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Old Data WIP/")
gh_old = pd.read_csv("GitHub_Data-old.csv")
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/")
author = pd.read_stata("author.dta")

# check missing github ids in author data

merge = pd.merge(author,github, left_on = "github_username", right_on = "GitHub Username", how = 'outer', indicator = True)
merge = merge.sort_values(["_merge","author_id"])

# check numbers
merge[merge["_merge"]=="left_only"].shape[0] # 164
merge[merge["_merge"]=="both"].shape[0] # 543 
merge[merge["_merge"]=="right_only"].shape[0] # 85

author[author['github_username'] != ""].shape[0] # 547

new = github[~github['GitHub Username'].isin(gh_old['GitHub_Username'])] # new github data that is not in current
newinauthor = author[author['github_username'].isin(new['GitHub Username'])]


# old github data without missing

gh_old_NM = gh_old[gh_old['GitHub_Followers'].notnull()] # 481 not null github followers in current data
notinold = github[~github['GitHub Username'].isin(gh_old_NM['GitHub_Username'])] # 158 names are in new
notinoldwithauthor_id = author[author['github_username'].isin(notinold['GitHub Username'])] # 73 names have author_id that can be added
notinoldwithoutauthor_id = notinold[~notinold['GitHub Username'].isin(notinoldwithauthor_id['github_username'])] # 85 names not with author_id

# create a new github file that contains old and not in old with author id

columns_to_keep = ['author_id', 'Full_Name', 'GitHub_Username', 'URL','GitHub_Followers']
gh_old_NM_ctk = gh_old_NM[columns_to_keep]
new_github_tobeadded = github[github['GitHub Username'].isin(notinoldwithauthor_id['github_username'])]
new_github_tobeadded = pd.merge(new_github_tobeadded,notinoldwithauthor_id, left_on = 'GitHub Username', right_on = 'github_username', how = 'inner')
new_github_tobeadded = new_github_tobeadded.rename(columns = {'GitHub Username' : 'GitHub_Username', 'Full Name' : 'Full_Name', 'GitHub Followers' : 'GitHub_Followers'})
new_github_tobeadded = new_github_tobeadded[columns_to_keep]
new_github_tobeadded_NM = new_github_tobeadded[new_github_tobeadded['GitHub_Followers'].notnull()]

new_github = pd.concat([gh_old_NM_ctk, new_github_tobeadded_NM], axis = 0)
new_github = new_github.sort_values('author_id')