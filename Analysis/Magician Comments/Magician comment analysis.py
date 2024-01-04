# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 15:20:10 2023

@author: moazz
"""

import os
import pandas as pd
import numpy as np  # Import numpy for NaN handling
import matplotlib.pyplot as plt
import seaborn as sns
import re
import ast



def gini(x):
    total = 0
    for i, xi in enumerate(x[:-1], 1):
        total += np.sum(np.abs(xi - x[i:]))
    return total / (len(x)**2 * np.mean(x))




#os.chdir('C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/')
os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/')


data = pd.read_csv("Analysis/Magician Comments/ethereum_magicians_data_scraped.csv")

#DROP WRONG EIP ASSOCIATIONS
data = data.loc[(data['EIP']!=75) | (data['EIP']!=2) | (data['EIP']!=0) ]
data = data.loc[data['Title']!='Hierarchical Deterministic Wallet for Computation Integrity Proof (CIP) Layer-2']
data = data.loc[data['Title']!='EIP-0000 ERC-721 Merkle-Provable Ownership Extension']
data = data.loc[data['Title']!='EIP 75xx: Reserve Precompile Address range for RIPs/L2s']
data.loc[data['Title']=='EIP: 7265 - Circuit Breaker Standard','EIP'] = 7265
data.loc[data['Title']=='ERC - 7537 - Soulbound tokens - DAOS and Web3 Games','EIP'] = 7537
data.loc[data['Title']=='Eip-3712: Standard for Multiple Types of Fungible-Tokens','EIP'] = 3712
data.loc[data['Title']=='Eip-3198: basefeeopcode','EIP'] = 3198
data.loc[data['Title']=='Eip-1283 / 1706 AMA','EIP'] = 1283

# Format date
data['Created Date']= pd.to_datetime(data['Created at2']).dt.strftime('%d%b%Y')

# BRING IN CROSS SECTIONAL DATA TO GET THE CATEGORIES. 
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-Sectional_Data.dta")
cs = cs[['eip_number','Category']]

data = pd.merge(data,cs,left_on = 'EIP',right_on = "eip_number", how = 'inner') # PLS NOTE THAT THIS ONLY KEEPS EIPS THAT ARE BOTH IN FEM AND CS


# Aggregate per EIP (few EIPs have multiple pages. See EIP 20)
df = data[['EIP', 'Replies', 'Views', 'Likes', 'Links']].groupby(['EIP']).sum()
df = pd.merge(df, data[['EIP','Created Date']].groupby(['EIP']).min(), on = 'EIP', how = 'left')

# Aggregate Users (issue. We have multiple sites for some EIPs. So we first have to aggregate site users, and then take unique count)
df['Users'] = 0
comment_author = data[['Comment Authors', 'EIP']]  

ncomm = pd.DataFrame(columns = ['user','ncomm', 'EIP'])
ncomm.index.rename('user', inplace = True)
for eip in df.index.to_list() :
    df_eip = pd.DataFrame(columns = ['user'])
    for subeip in comment_author.loc[comment_author['EIP'] == eip].index.to_list() :
        dict_authors = pd.DataFrame.from_dict(ast.literal_eval(comment_author['Comment Authors'][subeip]), orient='index', columns = ['user'])
        df_eip = pd.concat([df_eip,dict_authors], axis=0, join='outer')
    df.at[eip, 'Users'] = len(pd.unique(df_eip['user']))
    
    # THIS AGGREGATES USERS COMMENTS ACROSS EIPS
    df_eip['ncomm'] = 1
    temp = df_eip.groupby('user').count().reset_index()
    temp['EIP']= eip
    ncomm = pd.concat([ncomm, temp], axis = 0).reset_index(drop = True)

df['year'] = pd.to_datetime(df['Created Date']).dt.year

# EXPORT DF FILE
df.to_csv('Analysis/Magician Comments/FEM_Data_for_regressions.csv')

# NCOMM_UNIQUE IS N. OF COMMENTS PER USER ACROSS PLATFORMS. 
ncomm_unique = ncomm.groupby('user')['ncomm'].sum()
# lorenz curve with users
ncomm_unique.sort_values(ascending = False, inplace = True)
tot = ncomm_unique.sum()
ncomm_unique = ncomm_unique.to_frame()
ncomm_unique['perc']=ncomm_unique['ncomm']/tot
ncomm_unique.reset_index(inplace = True)
ncomm_unique['cumperc']=ncomm_unique['perc'].cumsum()

fig, ax = plt.subplots()
ncomm_unique['cumperc'].plot(ax = ax)
plt.xlabel('N. of Commentators')
plt.ylabel('Percentage of Total Comments')
plt.savefig('Analysis/Magician Comments/FEM_Lorenz_Comments', bbox_inches="tight")
fig.show()


# % of TOP 10 CONTRIBUTORS: 24.8%
ncomm_unique['cumperc'][9]

# Compute Gini coeff: 0.7158
gini(ncomm_unique['perc'])


## OVERALL STATS ON FEM
# N OF UNIQUE USERS ON PLATFORM: 1101
print(len(ncomm_unique))
# N. OF TOTAL LIKES: 4675
print(df['Likes'].sum())
# N. OF TOTAL VIEWS: 1,617,301
print(df['Views'].sum())
# N. OF TOTAL COMMENTS: 6416
print(df['Replies'].sum())

# N. OF TOTAL VIEWS BY YEAR

fig, ax = plt.subplots()
df.groupby(['year'])['Views'].sum().plot.bar(ax = ax)
ax.text(5, .25, '*', fontsize=12, transform=ax.get_xaxis_transform())
plt.xlabel('Year')
plt.ylabel('Total Views')
plt.savefig('Analysis/Magician Comments/FEM_Views_year', bbox_inches="tight")
fig.show()


# histograms

# REPLIES
df = df.reset_index()
df.loc[df['Replies']>100,'Replies'] = 100

plt.figure(figsize=(8, 6))
plt.hist(df['Replies'], bins=30, alpha=0.7, color='green')  # Adjust bins for granularity
plt.title('Distribution of Comments per EIP')
plt.xlabel('Number of Comments')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

# VIEWS
plt.figure(figsize=(8, 6))
plt.hist(df['Views'], bins=30, alpha=0.7, color='green')  # Adjust bins for granularity
plt.title('Distribution of Views per EIP')
plt.xlabel('Number of Views')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()


# USERS
plt.figure(figsize=(8, 6))
plt.hist(df['Users'], bins=30, alpha=0.7, color='green')  # Adjust bins for granularity
plt.title('Distribution of Unique Users Commenting on a EIP')
plt.xlabel('Number of Users')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

# LIKES
plt.figure(figsize=(8, 6))
plt.hist(df['Likes'], bins=30, alpha=0.7, color='green')  # Adjust bins for granularity
plt.title('Distribution of Likes per EIP')
plt.xlabel('Number of Likes')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

