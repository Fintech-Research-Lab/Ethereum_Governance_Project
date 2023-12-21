# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 12:14:05 2023

@author: moazz
"""
import pandas as pd
import os as os
import numpy as np
import matplotlib.pyplot as plt


# get data
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv", encoding='latin-1')
clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")
contributors_only = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributorsonly_final.csv")

# get actual author data from cross-sectional file

cs = pd.read_stata('Data/Raw Data/Ethereum_Cross-sectional_Data.dta')
cs = cs[['author1','author2','author3','author4','author5',
         'author6','author7','author8','author9','author10',
         'author11','author12','author13','author14','author15', 'sdate']]

author_df = cs.melt(id_vars = 'sdate', value_vars = ['author1','author2','author3','author4','author5',
         'author6','author7','author8','author9','author10',
         'author11','author12','author13','author14','author15'], var_name = 'number', value_name = 'Author' )

author_df = author_df[author_df['Author'] != ""]
author_df = pd.merge(author_df, authors, left_on = 'Author', right_on = 'Full_Name', how = 'outer', indicator = True)
authors2 = author_df.loc[author_df['_merge'] == 'both', ['Full_Name','Anonymity_Flag']]
authors = authors2.groupby('Full_Name')['Anonymity_Flag'].mean()



# some clean up
clients = clients.drop(columns = "Unnamed: 0")
contributors_only = contributors_only[['Name','Anonymity_Flag_y']]
contributors_only = contributors_only.rename(columns = {'Anonymity_Flag_y' : 'Anonymity_Flag'})

# clients top 20 analysis

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

geth_top20 = geth.groupby('author')['date'].count().sort_values(ascending = False).head(20)
besu_top20 = besu.groupby('author')['date'].count().sort_values(ascending = False).head(20)
erigon_top20 = erigon.groupby('author')['date'].count().sort_values(ascending = False).head(20)
nethermind_top20 = nethermind[nethermind['author'] != ''].groupby('author')['date'].count().sort_values(ascending = False).head(20)

# create anonymity flag and make adjustments
geth_top20_AF = np.where(geth_top20.index.str.contains(' '),0,1)
geth_top20_AF[16] = 0
geth_top20_AF = pd.Series(geth_top20_AF)


besu_top20_AF = np.where(besu_top20.index.str.contains(' '),0,1)
besu_top20_AF[3] = 0
besu_top20_AF[4] = 0
besu_top20_AF[9] = 0
besu_top20_AF[17] = 0
besu_top20_AF = pd.Series(besu_top20_AF)

erigon_top20_AF = np.where(erigon_top20.index.str.contains(' '),0,1)
erigon_top20_AF = pd.Series(erigon_top20_AF)


nethermind_top20_AF = np.where(nethermind_top20.index.str.contains(' '),0,1)
nethermind_top20_AF[12] = 0
nethermind_top20_AF = pd.Series(nethermind_top20_AF)

client_top20 = pd.concat([geth_top20_AF,besu_top20_AF,erigon_top20_AF,nethermind_top20_AF], axis = 0)
client_top20 = pd.DataFrame(client_top20, columns = ['Anonymity_Flag'])

# create graphs

percentages = []
ann = [authors, attendees['Anonymity_Flag'], clients['Anonymity_Flag'], contributors_only['Anonymity_Flag']] 
ann_top20 = [authors, attendees['Anonymity_Flag'], client_top20['Anonymity_Flag'], contributors_only['Anonymity_Flag']] 

for series in ann_top20:
    percentage_of_ones = (series.sum() / len(series)) * 100
    percentages.append(percentage_of_ones)


labels = ['Authors', 'Attendees', 'Clients(20)', 'EIP-Contributors-only']

# Create a bar graph
plt.bar(labels, percentages, color=['blue', 'green', 'red', 'orange'])  # Adjust colors as needed
plt.xlabel('DataFrames')
plt.ylabel('Percentage')
plt.title('Percentage of Anonymous in Different Categories')
plt.ylim(0, 100)  # Set y-axis limit from 0 to 100 for percentage
plt.savefig('Analysis/Anonymity Analysis/Anonymity_Diagram.png')
plt.show()

## eip author trend analysis not used in the analysis

os.chdir('C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project')

author_df['year'] = author_df['sdate'].dt.year
author_df = author_df.drop(columns = ['sdate','number'])
author_by_year =author_df.groupby(author_df['year'])['Anonymity_Flag'].apply(list)

percentages = []
for series in author_by_year:
    ones_count = sum(series)  # Count the number of ones in the list
    percentage_of_ones = (ones_count / len(series)) * 100  # Calculate the percentage
    percentages.append(percentage_of_ones)
    
labels = ['2015', '2016', '2017', '2018','2019','2020','2021','2022','2023']
colors = ['blue', 'green', 'red', 'orange', 'magenta', 'cyan', 'yellow']

# Create a bar graph
plt.bar(labels, percentages, color=colors)
plt.xlabel('Labels')
plt.ylabel('Percentages')
plt.title('Percentage of Anonymous Authors for Each Year')
plt.show()    
