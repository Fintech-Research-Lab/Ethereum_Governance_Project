# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 12:26:50 2023

## This code will create summary stats information that will go in the Ethereum Governance Paper

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np

# hhi function

def hhi(data):
    # Handle the case where data is a float
    total = data.sum()
    weights = data / total
    hhi = (weights ** 2).sum()
    return hhi

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")

# Load data from Stata into a pandas DataFrame
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-sectional_Data.dta")
eip_commit_data = pd.read_excel("Data/Commit Data/Eip Commit Data/eip_commit_beg.xlsx")
contributors_only = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributorsonly_final.csv")
authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")


cs1 = cs[['author1_id','author2_id','author3_id','author4_id','author5_id',
         'author6_id','author7_id','author8_id','author9_id','author10_id',
         'author11_id','author12_id','author13_id','author14_id','author15_id','eip_number']]

cs2 = cs[[
         'author1_company1','author2_company1','author2_company1','author3_company1','author4_company1','author5_company1',
         'author6_company1','author7_company1','author8_company1','author9_company1','author10_company1',
         'author11_company1','author12_company1','author13_company1','author14_company1','author15_company1','eip_number']]


author_df = cs1.melt(id_vars = 'eip_number', value_vars = ['author1_id','author2_id','author3_id','author4_id','author5_id',
         'author6_id','author7_id','author8_id','author9_id','author10_id',
         'author11_id','author12_id','author13_id','author14_id','author15_id'], var_name = 'number', value_name = 'Author_id' )


company_df = cs2.melt(id_vars = 'eip_number', value_vars = [
         'author1_company1','author2_company1','author2_company1','author3_company1','author4_company1','author5_company1',
         'author6_company1','author7_company1','author8_company1','author9_company1','author10_company1',
         'author11_company1','author12_company1','author13_company1','author14_company1','author15_company1','eip_number'], 
          var_name = 'number', value_name = 'Company' )


linkedin_df = pd.concat([author_df[['eip_number','Author_id']],company_df['Company']], axis = 1)
linkedin_df = linkedin_df[pd.notnull(linkedin_df['Author_id'])]
linkedin_df_missing = linkedin_df[linkedin_df['Company'] == ""]
linkedin_df_missing = linkedin_df_missing['Author_id']
linkedin_df_missing = linkedin_df_missing.unique()
linkedin_df_missing = pd.Series(linkedin_df_missing)

linkedin = pd.read_csv("Data/Raw Data/linkedIn_data.csv")
not_searched = linkedin_df_missing[~linkedin_df_missing.isin(linkedin['author_id'])]
not_searched = pd.DataFrame(not_searched, columns = ['author_id'])
authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
not_searched = pd.merge(not_searched,authors, on = 'author_id', how = 'inner')
not_searched.to_csv("Names_to_search_linkedin.csv")

# Find not included Twitter

cs3 = cs[[
         'author1_follower','author2_follower','author3_follower','author4_follower','author5_follower','author6_follower',
         'author7_follower','author8_follower','author9_follower','author10_follower','author11_follower',
         'author12_follower','author13_follower','author14_follower','author15_follower','eip_number']]


tw_df = cs3.melt(id_vars = 'eip_number', value_vars = [
         'author1_follower','author2_follower','author3_follower','author4_follower','author5_follower','author6_follower',
         'author7_follower','author8_follower','author9_follower','author10_follower','author11_follower',
         'author12_follower','author13_follower','author14_follower','author15_follower','eip_number'], 
          var_name = 'number', value_name = 'Company' )


linkedin_df = pd.concat([author_df[['eip_number','Author_id']],company_df['Company']], axis = 1)
linkedin_df = linkedin_df[pd.notnull(linkedin_df['Author_id'])]
linkedin_df_missing = linkedin_df[linkedin_df['Company'] == ""]
linkedin_df_missing = linkedin_df_missing['Author_id']
linkedin_df_missing = linkedin_df_missing.unique()
linkedin_df_missing = pd.Series(linkedin_df_missing)

linkedin = pd.read_csv("Data/Raw Data/linkedIn_data.csv")
not_searched = linkedin_df_missing[~linkedin_df_missing.isin(linkedin['author_id'])]
not_searched = pd.DataFrame(not_searched, columns = ['author_id'])
authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
not_searched = pd.merge(not_searched,authors, on = 'author_id', how = 'inner')
not_searched.to_csv("Names_to_search_linkedin.csv")



# for further analysis of author 

author_df = author_df[pd.notnull(author_df['Author_id'])]
author_df = pd.merge(author_df, authors, left_on = 'Author_id', right_on = 'author_id', how = 'inner')
authors = author_df['Full_Name'].unique()
authors = pd.DataFrame(authors, columns = ['Author_Name'])

#author_ref = pd.read_stata("author.dta")


# remove eth-bot from eip commit Data
eip_commit_data = eip_commit_data[eip_commit_data['Author'] != 'eth-bot']

# client commit data
geth = pd.read_stata("Data/Commit Data/client_commit/geth_commits.dta")
besu = pd.read_stata("Data/Commit Data/client_commit/besu_commits.dta")
erigon = pd.read_stata("Data/Commit Data/client_commit/besu_commits.dta")
nethermind = pd.read_stata("Data/Commit Data/client_commit/nethermind_commits.dta")

clients = pd.concat([geth,besu,erigon,nethermind])

# Remove bots from clients

clients = clients[(clients['author'] != 'dependabot[bot]') & (clients['author'] != 'github-actions[bot]' )]


# create a shell for results

summary_stats = pd.DataFrame(columns = ['stats','Value'])
summary_stats.loc[len(summary_stats)] = ['Number of Total EIPs', cs['eip_number'].count()]
summary_stats.loc[len(summary_stats)] = ['Number of Unique Authors', len(pd.unique(cs.loc[:, "author1_id":"author15_id"]
                                                                      .values[~np.isnan(cs.loc[:,
                                                                      "author1_id":"author15_id"].values)]))]                   
summary_stats.loc[len(summary_stats)] = ['Average Number of Authors per EIP', cs['n_authors'].mean()]
summary_stats.loc[len(summary_stats)] = ['Percent of EIPs by Top 10 Authors', cs.loc[:,'author1_id':'author15_id']
                                         .apply(pd.value_counts).sum(axis = 1)
                                         .sort_values(ascending = False)
                                         .head(10).sum(axis=0)/cs['eip_number'].count()]
summary_stats.loc[len(summary_stats)] = ['Percent of  Finalized EIPs by Top 10 Authors', cs.loc[cs['status'] == "Final",'author1_id':'author15_id']
                                         .apply(pd.value_counts).sum(axis = 1)
                                         .sort_values(ascending = False).head(10)
                                         .sum(axis=0)/len(cs.loc[cs['status'] == "Final"])]

summary_stats.loc[len(summary_stats)] = ['HHI of Authorship', hhi(cs.loc[:,'author1_id':'author15_id']
                                                                                             .apply(pd.value_counts)
                                                                                             .sum(axis =1))]


summary_stats.loc[len(summary_stats)] = ['HHI of Authors for Finalized EIPs', hhi(cs.loc[cs['status'] == "Final",'author1_id':'author15_id']
                                                                                             .apply(pd.value_counts)
                                                                                             .sum(axis =1))]
               
summary_stats.loc[len(summary_stats)] = ['Number of Unique non-author Contributors to EIP Repository', 
                                         cs['n_contributors_eip'].sum()]                 

summary_stats.loc[len(summary_stats)] = ['Average Unique non-author Contributor per EIP', 
                                         cs['n_contributors_eip'].sum()/cs['eip_number'].count()]                 


summary_stats.loc[len(summary_stats)] = ['Percent of  Commits by Top 10 contributors', eip_commit_data.groupby('Author').size()
                                         .sort_values(ascending = False).head(10).sum()
                                         /
                                         eip_commit_data.groupby('Author').size().sum()]
                                         
summary_stats.loc[len(summary_stats)] = ['HHI of EIP Github Contributors', hhi(eip_commit_data.groupby('Author').size())]
                                                                               

summary_stats.loc[len(summary_stats)] = ['Number of Final EIPs', cs.loc[cs['status'] == "Final"].shape[0]]

summary_stats.loc[len(summary_stats)] = ['Number of Failed EIPs', cs[(cs['status'] == "Stagnant") | 
                                                                            (cs['status'] == "Withdrawn")|
                                                                            (cs['status'] == "Draft")].shape[0]]

summary_stats.loc[len(summary_stats)] = ['Number of In-Progress EIPs', cs[(cs['status'] == "Review") | 
                                                                            (cs['status'] == "Last Call")].shape[0]]

summary_stats.loc[len(summary_stats)] = ['Number Authors for which we have Company Data', linkedin[pd.notnull(linkedin['company1'])].shape[0]]

summary_stats.loc[len(summary_stats)] = ['No Company Boasts more than this authors', linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size().sort_values(ascending = False).head(1).iloc[0]]
                                                                            
summary_stats.loc[len(summary_stats)] = ['Followed by this many authors', linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size().sort_values(ascending = False).head(2).iloc[1]]

summary_stats.loc[len(summary_stats)] = ['HHI of Companies', hhi(linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size())]

summary_stats.loc[len(summary_stats)] = ['HHI of All Clients Contributors', hhi(clients.groupby('identifier').size().value_counts())]

summary_stats.loc[len(summary_stats)] = ['Average Clients Commits per Day', clients.groupby('date').size().mean()]

summary_stats.loc[len(summary_stats)] = ['Top 10 Client Contributors as a Percent of Total', clients.groupby('identifier')
                                         .size().sort_values(ascending = False).head(10).sum()
                                         /
                                         clients.groupby('identifier').size().sort_values(ascending = False).sum()]

summary_stats.loc[len(summary_stats)] = ['HHI of Client Contributors', hhi(clients.groupby('identifier').size())]

# use name analysis file to complete the following summary stats

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")

name_analysis = pd.read_csv("Name_Results.csv")
 
# percent of eip authors who are clients

summary_stats.loc[len(summary_stats)] = ['Percent of EIP Authors that are clients', name_analysis.loc[8,"Result"]/name_analysis.loc[1,"Result"]]


# percent of eip contrubutors who are clients

summary_stats.loc[len(summary_stats)] = ['Percent of EIP Contributors that are clients', name_analysis.loc[7,"Result"]/name_analysis.loc[1,"Result"]]

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Summary Stats/")
summary_stats.to_csv("Summary_Stats.csv")

