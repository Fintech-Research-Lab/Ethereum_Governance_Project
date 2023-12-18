# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:49:52 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np
from fuzzywuzzy import fuzz

# author list

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
author = pd.read_csv("/Data/Raw Data/unique_author_names_with_id.csv")
author_unique = pd.DataFrame(author, columns = ['Full_Name'])
author_unique.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Unique_Authors.csv")


# Contributor List

# get commit data

eip_commit = pd.read_excel("Data/Commit Data/Eip commit Data/eip_commit_beg.xlsx")
contributors = pd.merge(eip_commit,author, left_on = 'Username', right_on = "GitHub_Username", how = 'left', indicator = True )
contributors = contributors[contributors['_merge'] == 'left_only']
# remove bots
contributors = contributors[contributors['Author'] != 'eth-bot']
#  the following code checks if there are any duplicates author names within a username since usernames are unique
dup = contributors[contributors.duplicated(subset = 'Username', keep = False)]
username_author_counts = dup.groupby('Username')['Author'].nunique().reset_index()
repeats = dup[dup['Username'] == "Unknown"]
repeats = dup[dup['Username'] == "5chdn"]
# the above test showed that only one Unknown usernames have duplicate authors so aggregating by author would be ok

contributors_unique = pd.unique(contributors['Author'])
contributors_unique = pd.DataFrame(contributors_unique, columns = ['Full_name'])

# Manually created a mapping file to replace names 

names = contributors_unique['Full_name'].tolist()
right_names = ['Afri Schoeden','Afri Schoeden','Andrew Ashikhmin','David Bieber','Lucas Cullen','Rai Ratan Sur','Suleman Kardas',"g. nicholas d'andrea"]
wrong_names = ['Afri Schoedon','5chdn','Andrew','David','Lucas','Ratan (Rai) Sur','Süleyman Kardaş',"g. nicholas d'andrea"]
name_dict = dict(zip(wrong_names,right_names))
names2 = [name_dict[name] if name in name_dict else name for name in names]
names3 = set(names2)
contributors_unique = pd.DataFrame(names3, columns = ['Full_Name'])
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
contributors_unique.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Unique_Contributors.csv")

# Client List


geth = pd.read_stata("Data/Commit Data/client_commit/commitsgeth.dta")
besu = pd.read_stata("Data/Commit Data/client_commit/commitsbesu.dta")
erigon = pd.read_stata("Data/Commit Data/client_commit/commitserigon.dta")
nethermind = pd.read_stata("Data/Commit Data/client_commit/commitsnethermind.dta")

clients = pd.concat([geth,besu,erigon,nethermind])
client_unique = pd.unique(clients ['author'])
client_unique = pd.DataFrame(client_unique, columns = ['full_name'])
np.where(client_unique['full_name'].str.contains('bot'))
# remove dependabot[bot] and github-actions[bot]
client_unique = client_unique[(client_unique['full_name'] != 'dependabot[bot]') & (client_unique['full_name'] != 'github-actions[bot]' )]

# apply fuzzywuzzy to find similar client names

client_list = list(set(client_unique['full_name'].tolist()))

similarity_score =  []
for i in range(len(client_list)):
               for j in range(i+1,len(client_list)):
                   score = fuzz.ratio(client_list[i],client_list[j])
                   similarity_score.append((i,j,client_list[i],client_list[j],score))
                   
threshold = 76 # after manually iterating 76 seems to be the best first cutoff

high_similarity_score1 = [score for score in similarity_score if score[4] > threshold]
#name_check = [score for score in high_similarity_score1 if (score[4]>74 and score[4]<80)] # to manually check

name_to_replace = [row[3] for row in high_similarity_score1]
name_to_replace_with = [row[2] for row in high_similarity_score1]

names_to_change = pd.concat([pd.DataFrame(name_to_replace_with),pd.DataFrame(name_to_replace)], axis = 1)
names_to_change.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/clients_name_to_change.csv")

names_to_change_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/clients_name_to_change_post_manual.csv")
right_names = names_to_change_mod['Names_to_Keep'].tolist()
wrong_names = names_to_change_mod['Names_to_Replace'].tolist()
name_dict = dict(zip(wrong_names,right_names))
names2 = [name_dict[name] if name in name_dict else name for name in client_list]

high_similarity_score2 = [score for score in similarity_score if score[4] > 54 and score[4] < 76]
name_to_replace2 = [row[3] for row in high_similarity_score2]
name_to_replace_with2 = [row[2] for row in high_similarity_score2]
names_to_change2 = pd.concat([pd.DataFrame(name_to_replace_with2),pd.DataFrame(name_to_replace2)], axis = 1)
names_to_change2.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/client_names_to_change2.csv")

names_to_change2_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/client_names_to_change2_post_manual.csv")
right_names2 = names_to_change2_mod['Names_to_Keep'].tolist()
wrong_names2 = names_to_change2_mod['Names_to_Replace'].tolist()
name_dict2 = dict(zip(wrong_names2,right_names2))
names3 = [name_dict2[name] if name in name_dict2 else name for name in names2]
sorted_names3 = sorted(names3, key=lambda x: (isinstance(x, str), x))

unique_client_list = set(names3)
unique_client2 = pd.DataFrame(unique_client_list , columns = ['full_name'])
# manual check and fixing last time without similarity scores
unique_client2.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/client_names_to_change3.csv")

# manual check last time without fuzzy logic

names_to_change3_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/client_names_to_change3_post_manual.csv")
right_names3 = names_to_change3_mod['Names_to_Keep'].tolist()
wrong_names3 = names_to_change3_mod['Names_to_Replace'].tolist()
name_dict3 = dict(zip(wrong_names3,right_names3))
names4 = [name_dict3[name] if name in name_dict3 else name for name in names3]

# create a dataframe

unique_client_list = set(names4)
unique_clients3 = pd.DataFrame(unique_client_list, columns = ['full_name'])
unique_clients4 = unique_clients3[(pd.notnull(unique_clients3['full_name'])) & (unique_clients3['full_name'] != "NONE")]

unique_clients4.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Unique_Clients.csv")

# create mapping file
df1 = pd.DataFrame(client_list, columns=['Original_Name'])
df2 = pd.DataFrame(names4, columns=['Replace_Name'])

mapping_file = pd.concat([df1, df2], axis=1)

# save mapping file

mapping_file.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/Client_Mapping_File.csv")
