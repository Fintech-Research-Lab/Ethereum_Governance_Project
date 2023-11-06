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

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")

# Load data from Stata into a pandas DataFrame
cs = pd.read_stata("Ethereum_Cross-sectional_Data.dta")
eip_commit_data = pd.read_stata("eip_commit.dta")
author_ref = pd.read_stata("author.dta")
linkedin = pd.read_stata("linkedIn_data.dta")

# remove eth-bot from eip commit Data
eip_commit_data = eip_commit_data[eip_commit_data['Author'] != 'eth-bot']

# client commit data
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/client_commit/")
geth = pd.read_stata("commitsgeth.dta")
besu = pd.read_stata("commitsbesu.dta")
erigon = pd.read_stata("commitserigon.dta")
nethermind = pd.read_stata("commitsnethermind.dta")

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
                                         cs['eip_contributors'].sum()]                 

summary_stats.loc[len(summary_stats)] = ['Average Unique non-author Contributor per EIP', 
                                         cs['eip_contributors'].sum()/cs['eip_number'].count()]                 


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

summary_stats.loc[len(summary_stats)] = ['Number Authors for which we have Company Data', linkedin[linkedin['company1'] != ""].shape[0]]

summary_stats.loc[len(summary_stats)] = ['No Company Boasts more than this authors', linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size().sort_values(ascending = False).head(1).iloc[0]]
                                                                            
summary_stats.loc[len(summary_stats)] = ['Followed by this many authors', linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size().sort_values(ascending = False).head(2).iloc[1]]

summary_stats.loc[len(summary_stats)] = ['HHI of Companies', hhi(linkedin[linkedin['company1'] != ""]
                                         .groupby('company1').size())]

summary_stats.loc[len(summary_stats)] = ['HHI of All Clients Contributors', hhi(clients.groupby('login').size().value_counts())]

summary_stats.loc[len(summary_stats)] = ['Average Clients Commits per Day', clients.groupby('date').size().mean()]

summary_stats.loc[len(summary_stats)] = ['Top 10 Client Contributors as a Percent of Total', clients.groupby('login')
                                         .size().sort_values(ascending = False).head(10).sum()
                                         /
                                         clients.groupby('login').size().sort_values(ascending = False).sum()]

summary_stats.loc[len(summary_stats)] = ['HHI of Client Contributors', hhi(clients.groupby('login').size())]

# analysis on eip commit and client commit data

eip_contributors = eip_commit[eip_commit['github_username'] != ""].groupby('github_username').size().reset_index(name='count')
eip_contributor_clients = pd.merge(clients,eip_contributors, left_on = 'login', right_on = 'github_username', how = 'inner')
eip_contributors_clients_agg = eip_contributor_clients.groupby('login').size().reset_index(name = 'count')
 
# percent of eip authors who are clients

summary_stats.loc[len(summary_stats)] = ['Percent of EIP Authors that are clients', 
                                         eip_contributor_clients[eip_contributor_clients['login'].isin(author_ref['github_username'])].groupby('github_username').size().shape[0]
                                         /
                                         eip_contributors.shape[0]]


# percent of eip contrubutors who are clients

summary_stats.loc[len(summary_stats)] = ['Percent of EIP Contributors that are clients', eip_contributors_clients_agg.shape[0]
                                         /
                                         eip_contributors.shape[0]]

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Analysis Code/")
summary_stats.to_csv("Summary_Stats.csv")