# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 11:38:38 2024

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")


###### This is a further analysis on all participants that are common, how many of them are in top 10 in their respective field? ##

# top 10 authors
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-sectional_Data.dta")
authors = cs.loc[:,'author1':'author15'].values.flatten()
authors = pd.DataFrame(authors[authors != ""], columns = ["Author_Name"])
top10_authors = authors.groupby("Author_Name").size().sort_values(ascending = False).head(10)

# top 10 attendees

attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/flat_list_meeting_attendees.csv")
top10_attendees = attendees.groupby("Attendees").size().sort_values(ascending = False).head(10)

# top 10 clients in each

geth = pd.read_stata("Data/Commit Data/client_commit/geth_commits.dta")
besu = pd.read_stata("Data/Commit Data/client_commit/besu_commits.dta")
erigon = pd.read_stata("Data/Commit Data/client_commit/besu_commits.dta")
nethermind = pd.read_stata("Data/Commit Data/client_commit/nethermind_commits.dta")

# cleanup nethermind names

nethermind[nethermind['author'] == 'Tomasz Kajetan Sta?czak' ] = 'Tomasz Kajetan Stanczak'
nethermind[nethermind['author'] == 'Tomasz K. Stanczak' ] = 'Tomasz Kajetan Stanczak'
nethermind[nethermind['author'] == 'tkstanczak' ] = 'Tomasz Kajetan Stanczak'
nethermind[nethermind['author'] == 'github-actions[bot]' ] = ''
erigon[erigon['author'] == 'alex.sharov' ] = 'Alex Sharov'

geth_top10 = geth.groupby('author')['date'].count().sort_values(ascending = False).head(10)
besu_top10 = besu.groupby('author')['date'].count().sort_values(ascending = False).head(10)
erigon_top10 = erigon.groupby('author')['date'].count().sort_values(ascending = False).head(10)
nethermind_top10 = nethermind[nethermind['author'] != ''].groupby('author')['date'].count().sort_values(ascending = False).head(10)

clients = pd.concat([geth_top10,besu_top10,erigon_top10,nethermind_top10], axis = 0)
clients = pd.DataFrame(clients)
clients['Client_Name'] = clients.index
top10_clients = clients.groupby('Client_Name')['date'].sum().sort_values(ascending = False).head(10)

# overlaps
dat = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_names_allplayers.csv")

all_three = dat[pd.notnull(dat['Attendee_Name'])&pd.notnull(dat['Author_Name'])&pd.notnull(dat['Client_Name'])]
all_three = all_three.loc[:,["Attendee_Name",'Client_Name','Author_Name']]
all_three = pd.Series(all_three.values.flatten()).unique()

clients_and_authors = dat[pd.notnull(dat['Client_Name'])&pd.notnull(dat['Author_Name'])]
clients_and_authors = clients_and_authors.loc[:,['Client_Name','Author_Name']]
clients_and_authors = pd.Series(clients_and_authors.values.flatten()).unique()

attendees_and_authors = dat[pd.notnull(dat['Attendee_Name'])&pd.notnull(dat['Author_Name'])]
attendees_and_authors = attendees_and_authors.loc[:,['Attendee_Name','Author_Name']]
attendees_and_authors = pd.Series(attendees_and_authors.values.flatten()).unique()

clients_and_attendees = dat[pd.notnull(dat['Client_Name'])&pd.notnull(dat['Attendee_Name'])]
clients_and_attendees = clients_and_attendees.loc[:,['Client_Name','Attendee_Name']]
clients_and_attendees = pd.Series(clients_and_attendees.values.flatten()).unique()

# Collating Analysis 

Common = pd.DataFrame(columns = ['Common','Result'])
Common.loc[len(Common)] = ['What percent of people who do everything are top 10 authors',np.sum(top10_authors.index.isin(all_three))/all_three.size]
Common.loc[len(Common)] = ['What percent of people who do everything are top 10 attendees',np.sum(top10_attendees.index.isin(all_three))/all_three.size] 
Common.loc[len(Common)] = ['What percent of people who do everything are top 10 clients',np.sum(top10_clients.index.isin(all_three))/all_three.size] 
Common.loc[len(Common)] = ['What percent of people who are clients and authors are top 10 authors',np.sum(top10_authors.index.isin(clients_and_authors))/clients_and_authors.size]
Common.loc[len(Common)] = ['What percent of people who are clients and authors are top 10 clients',np.sum(top10_clients.index.isin(clients_and_authors))/clients_and_authors.size] 
Common.loc[len(Common)] = ['What percent of people who are attendees and authors are top 10 authors',np.sum(top10_authors.index.isin(attendees_and_authors))/attendees_and_authors.size]
Common.loc[len(Common)] = ['What percent of people who are attendees and authors are top 10 attendees',np.sum(top10_attendees.index.isin(attendees_and_authors))/attendees_and_authors.size] 
Common.loc[len(Common)] = ['What percent of people who are clients and attendees are top 10 attendees',np.sum(top10_attendees.index.isin(clients_and_attendees))/clients_and_attendees.size]
Common.loc[len(Common)] = ['What percent of people who are clients and attendees are top 10 clients',np.sum(top10_clients.index.isin(clients_and_attendees))/clients_and_attendees.size] 
Common.loc[len(Common)] = ['Percent of top 10 authors who do everything',np.sum(top10_authors.index.isin(all_three))/top10_authors.size] 
Common.loc[len(Common)] = ['Percent of top 10 clients who do everything',np.sum(top10_clients.index.isin(all_three))/top10_clients.size] 
Common.loc[len(Common)] = ['Percent of top 10 attendees who do everything',np.sum(top10_attendees.index.isin(all_three))/top10_attendees.size] 
Common.loc[len(Common)] = ['Percent of top 10 authors who are also clients',np.sum(top10_authors.index.isin(clients_and_authors))/top10_authors.size] 
Common.loc[len(Common)] = ['Percent of top 10 clients who are also authors',np.sum(top10_clients.index.isin(clients_and_authors))/top10_clients.size] 
Common.loc[len(Common)] = ['Percent of top 10 attendees who are also authors',np.sum(top10_attendees.index.isin(attendees_and_authors))/top10_attendees.size] 
Common.loc[len(Common)] = ['Percent of top 10 authors who are also attendees',np.sum(top10_authors.index.isin(attendees_and_authors))/top10_authors.size] 
Common.loc[len(Common)] = ['Percent of top 10 attendees who are also clients',np.sum(top10_attendees.index.isin(clients_and_attendees))/top10_attendees.size] 
Common.loc[len(Common)] = ['Percent of top 10 clients who are also attendees',np.sum(top10_clients.index.isin(clients_and_attendees))/top10_clients.size] 
Common.loc[len(Common)] = ['Percent of people who do everything that are either top 10 clients or authors or attendees',np.sum((top10_clients.index.isin(all_three))|(top10_authors.index.isin(all_three))|(top10_attendees.index.isin(all_three)))/all_three.size] 
Common.loc[len(Common)] = ['Percent of authors and clients that are either top 10 clients or top 10 authors',np.sum((top10_clients.index.isin(clients_and_authors))|(top10_authors.index.isin(clients_and_authors)))/clients_and_authors.size] 
Common.loc[len(Common)] = ['Percent of attendees and clients that are either top 10 clients or top 10 attendees',np.sum((top10_clients.index.isin(clients_and_attendees))|(top10_authors.index.isin(clients_and_attendees)))/clients_and_attendees.size] 
Common.loc[len(Common)] = ['Percent of authors and attendees that are either top 10 authors or top 10 attendees',np.sum((top10_authors.index.isin(attendees_and_authors))|(top10_attendees.index.isin(attendees_and_authors)))/attendees_and_authors.size] 

Common.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/top10_communityengagement.csv", index = False)

# create a data frame of top 10

top10_attendees = pd.DataFrame(top10_attendees, columns = ['Meetings_Attended'])
top10_attendees = top10_attendees.reset_index()

top10_clients = pd.DataFrame(top10_clients, columns = ["date"])
top10_clients = top10_clients.reset_index()
top10_clients = top10_clients.rename(columns = {'date' : 'Total_Commits'})

top10_authors = pd.DataFrame(top10_authors, columns = ['EIP_Authored'])
top10_authors = top10_authors.reset_index()

top10 = pd.concat([top10_clients,top10_attendees,top10_authors], axis = 1)

top10.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/top10.csv", index = False, encoding = 'latin-1')

all_three = pd.DataFrame(all_three, columns = ['Name'])
all_three.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/everything.csv", index = False)