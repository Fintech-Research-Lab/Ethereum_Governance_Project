# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 12:14:05 2023

@author: moazz
"""
import pandas as pd
import os as os
import numpy as np
import matplotlib.pyplot as plt

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")
contributors_only = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributorsonly_final.csv")

# some clean up
attendees = attendees.drop(columns = "Unnamed: 0")
authors = authors[['Full_Name','Anonymity_Flag']]
clients = clients.drop(columns = "Unnamed: 0")
contributors_only = contributors_only[['Name','Anonymity_Flag_y']]
contributors_only = contributors_only.rename(columns = {'Anonymity_Flag_y' : 'Anonymity_Flag'})

# clients top 20 analysis

geth = pd.read_stata("Data/Commit Data/client_commit/commitsgeth.dta")
besu = pd.read_stata("Data/Commit Data/client_commit/commitsbesu.dta")
erigon = pd.read_stata("Data/Commit Data/client_commit/commitserigon.dta")
nethermind = pd.read_stata("Data/Commit Data/client_commit/commitsnethermind.dta")

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
ann = [authors['Anonymity_Flag'], attendees['Anonymity_Flag'], clients['Anonymity_Flag'], contributors_only['Anonymity_Flag']] 
ann_top20 = [authors['Anonymity_Flag'], attendees['Anonymity_Flag'], client_top20['Anonymity_Flag'], contributors_only['Anonymity_Flag']] 

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

