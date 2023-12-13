# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:49:52 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np

# get attendee list

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
attendees_unique = pd.read_csv("Unique_attendee_list.csv", encoding='latin1')

# get author list

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")
cs = pd.read_csv("Ethereum_Cross-sectional_Data_beg.csv")
author_values = cs.loc[:,'Author1':'Author15'].values.tolist()
author = set([item for sublist in author_values for item in sublist])
author = pd.DataFrame(author, columns = ['full_name'])
author_unique = author[pd.notnull(author['full_name']) & (author['full_name'] != 'et al.')]

# Get Client List

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/client_commit/")
geth = pd.read_stata("commitsgeth.dta")
besu = pd.read_stata("commitsbesu.dta")
erigon = pd.read_stata("commitserigon.dta")
nethermind = pd.read_stata("commitsnethermind.dta")

clients = pd.concat([geth,besu,erigon,nethermind])
client_unique = pd.unique(clients ['author'])
client_unique = pd.DataFrame(client_unique, columns = ['full_name'])
np.where(client_unique['full_name'].str.contains('bot'))
# remove dependabot[bot] and github-actions[bot]
client_unique = client_unique[(client_unique['full_name'] != 'dependabot[bot]') & (client_unique['full_name'] != 'github-actions[bot]' )]

# Get Contributor List

# get commit data
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/Eip commit Data/")
eip_commit = pd.read_excel("eip_commit_beg.xlsx")
contributors = eip_commit[pd.isnull(eip_commit['Author_Id'])]
# remove bots
contributors = contributors[contributors['Author'] != 'eth-bot']
#  the following code checks if there are any duplicates author names within a username since usernames are unique
dup = contributors[contributors.duplicated(subset = 'Username', keep = False)]
username_author_counts = dup.groupby('Username')['Author'].nunique().reset_index()
repeats = dup[dup['Username'] == "Unknown"]
# the above test showed that only one Unknown usernames have duplicate authors so aggregating by author would be ok

contributors_unique = pd.unique(contributors['Author'])
contributors_unique = pd.DataFrame(contributors_unique, columns = ['full_name'])