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
#os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/')

authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv", encoding='latin-1')
clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")
contributors_only = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributorsonly_final.csv")

# get actual author data from cross-sectional file

cs = pd.read_stata('Data/Raw Data/Ethereum_Cross-sectional_Data.dta')
cs = cs[['author1_id','author2_id','author3_id','author4_id','author5_id',
         'author6_id','author7_id','author8_id','author9_id','author10_id',
         'author11_id','author12_id','author13_id','author14_id','author15_id','sdate']]

author_df = cs.melt(id_vars = 'sdate', value_vars = ['author1_id','author2_id','author3_id','author4_id','author5_id',
         'author6_id','author7_id','author8_id','author9_id','author10_id',
         'author11_id','author12_id','author13_id','author14_id','author15_id'], var_name = 'number', value_name = 'Author_id' )

author_df = author_df[pd.notnull(author_df['Author_id'])]
author_df = pd.merge(author_df, authors, left_on = 'Author_id', right_on = 'author_id', how = 'inner')

authors = author_df.groupby('Author_id')['Anonymity_Flag'].mean()



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
ann_top20 = [authors, attendees['Anonymity_Flag'], client_top20['Anonymity_Flag']] 

for series in ann_top20:
    percentage_of_ones = (1- (series.sum() / len(series))) * 100
    percentages.append(percentage_of_ones)


labels = ['EIP \n Authors', 'AllCoreDevs \n Attendees', 'Top Client \n Developers']

# Create a bar graph
plt.bar(labels, percentages, color=['blue', 'green', 'red'])  # Adjust colors as needed
#plt.xlabel('DataFrames')
plt.ylabel('Percentage of People \n Disclosing their Full Names')
#plt.title('Percentage of Anonymous in Different Categories')
plt.ylim(0, 100)  # Set y-axis limit from 0 to 100 for percentage
plt.savefig('Analysis/Anonymity Analysis/Anonymity_Diagram.png')
plt.show()
