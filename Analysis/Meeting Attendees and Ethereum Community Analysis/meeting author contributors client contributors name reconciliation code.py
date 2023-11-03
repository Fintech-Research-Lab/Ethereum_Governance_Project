# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os
from fuzzywuzzy import fuzz
import numpy as np


# Read Data

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
attendees = pd.read_csv("flat_list_meeting_attendees.csv", encoding='latin1')


# get author data and remove nan and et al. from the author list
os.chdir ("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")
cs = pd.read_csv("Ethereum_Cross-sectional_Data.csv")
author_values = cs.loc[:,'Author1':'Author15'].values.tolist()
author = set([item for sublist in author_values for item in sublist])
author = pd.DataFrame(author, columns = ['full_name'])
author = author[pd.notnull(author['full_name']) & (author['full_name'] != 'et al.')]

# get commit data
eip_commit = pd.read_stata("eip_Commit.dta")

# get client data
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Commit Data/client_commit/")
geth = pd.read_stata("commitsgeth.dta")
besu = pd.read_stata("commitsbesu.dta")
erigon = pd.read_stata("commitserigon.dta")
nethermind = pd.read_stata("commitsnethermind.dta")

clients = pd.concat([geth,besu,erigon,nethermind])


# creare an attendee list which we will use to replace names

names = attendees['full_name'].tolist()
unique_attendees1 = list(set(names))

# Create a unique list of authors, contributors, attendee and clitnts

author_unique = author['full_name']
author_unique = pd.DataFrame(author_unique, columns = ['full_name'])
contributor_unique = pd.unique(eip_commit['Author'])
contributor_unique = pd.DataFrame(contributor_unique, columns = ['full_name'])
# remove eth-bot from contributor_unique
contributor_unique = contributor_unique[contributor_unique['full_name'] != 'eth-bot']
client_unique = pd.unique(clients ['author'])
client_unique = pd.DataFrame(client_unique, columns = ['full_name'])
np.where(client_unique['full_name'].str.contains('bot'))
# remove dependabot[bot] and github-actions[bot]
client_unique = client_unique[(client_unique['full_name'] != 'dependabot[bot]') & (client_unique['full_name'] != 'github-actions[bot]' )]



# create similarity score within attendees list to remove similar name

similarity_score =  []
for i in range(len(unique_attendees1)):
               for j in range(i+1,len(unique_attendees1)):
                   score = fuzz.ratio(unique_attendees1[i],unique_attendees1[j])
                   similarity_score.append((i,j,unique_attendees1[i],unique_attendees1[j],score))

threshold = 76 # after manually iterating 76 seems to be the best first cutoff

high_similarity_score1 = [score for score in similarity_score if score[4] > threshold]
#name_check = [score for score in high_similarity_score1 if (score[4]>74 and score[4]<80)] # to manually check

name_to_replace = [row[3] for row in high_similarity_score1]
name_to_replace_with = [row[2] for row in high_similarity_score1]

# manually change the list. This process is better done in a spreadsheet manually

names_to_change = pd.concat([pd.DataFrame(name_to_replace_with),pd.DataFrame(name_to_replace)], axis = 1)
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
names_to_change.to_csv("names_to_change.csv")

# There was a manual process to map names to replace and names_to_replace_with

names_to_change_mod = pd.read_csv("names_to_change_post_manual.csv")
right_names = names_to_change_mod['Names_to_Keep'].tolist()
wrong_names = names_to_change_mod['Names_to_Replace'].tolist()
name_dict = dict(zip(wrong_names,right_names))
names2 = [name_dict[name] if name in name_dict else name for name in names]

# manually check from threshold between 55 to 75
high_similarity_score2 = [score for score in similarity_score if score[4] > 54 and score[4] < 76]
name_to_replace2 = [row[3] for row in high_similarity_score2]
name_to_replace_with2 = [row[2] for row in high_similarity_score2]
names_to_change2 = pd.concat([pd.DataFrame(name_to_replace_with2),pd.DataFrame(name_to_replace2)], axis = 1)
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
names_to_change2.to_csv("names_to_change2.csv")

# create second replacement based on manually corrected names between the threshold of 55 to 75

names_to_change2_mod = pd.read_csv("names_to_change2_post_manual.csv")
right_names2 = names_to_change2_mod['Names_to_Keep'].tolist()
wrong_names2 = names_to_change2_mod['Names_to_Replace'].tolist()
name_dict2 = dict(zip(wrong_names2,right_names2))
names3 = [name_dict2[name] if name in name_dict2 else name for name in names2]
sorted_names3 = sorted(names3, key=lambda x: (isinstance(x, str), x))

# create a unique list

unique_attendees_list = set(names3)
unique_attendeee2 = pd.DataFrame(unique_attendees_list , columns = ['full_name'])
# manual check and fixing last time without similarity scores
unique_attendeee2.to_csv("names_to_change3.csv")

# last manual check and last corrections that might were missed in similarity scores

names_to_change3_mod = pd.read_csv("names_to_change3_post_manual.csv")
right_names3 = names_to_change3_mod['Names_to_Keep'].tolist()
wrong_names3 = names_to_change3_mod['Names_to_Replace'].tolist()
name_dict3 = dict(zip(wrong_names3,right_names3))
names4 = [name_dict3[name] if name in name_dict3 else name for name in names3]

# create a dataframe

unique_attendee3 = pd.DataFrame(pd.Series(names4).unique(), columns = ['full_name'])
unique_attendee4 = unique_attendee3[(pd.notnull(unique_attendee3['full_name'])) & (unique_attendee3['full_name'] != "NONE")]


# Now the code will do cross-list check of names with Contributors Client, and Author Lists
# reassign attendee_unique3 as attendee_unique for further coding

attendee_unique = unique_attendee4
attendee_unique.to_csv("Unique_Attendee_List.csv", index = False)
  
# merge documents to run cross-table similarity score

attendees_with_author = pd.merge(attendee_unique,author_unique, on = 'full_name', how = 'outer', indicator = True) 
unreconciled_attendees_with_author = attendees_with_author[(attendees_with_author['_merge'] == 'left_only') | (attendees_with_author['_merge'] == 'right_only')]
attendees_notreconciled_with_authors = unreconciled_attendees_with_author[unreconciled_attendees_with_author['_merge'] == 'left_only']
authors_notreconciled_with_attendees = unreconciled_attendees_with_author[unreconciled_attendees_with_author['_merge'] == 'right_only']

# apply fuzzywuzzy to unreconciled list of attendees


similarity_scores = []
for name1 in attendees_notreconciled_with_authors['full_name']:
    for name2 in authors_notreconciled_with_attendees['full_name']:
        score = fuzz.ratio(name1,name2)
        similarity_scores.append(score)

threshold = 55 

attendees_author_similar_pairs = [
    (name1, name2, score)
    for name1, name2, score in zip(attendees_notreconciled_with_authors['full_name'], authors_notreconciled_with_attendees['full_name'], similarity_scores)
    if score >= threshold
]      

# no similar names in unreconcilable

author_attendees = attendees_with_author[attendees_with_author['_merge'] == 'both'] # 78 attendees are authors

# run the test with eip_contributors

attendees_with_contributors = pd.merge(attendee_unique,contributor_unique, on = 'full_name', how = 'outer', indicator = True) 
unreconciled_attendees_with_contributor = attendees_with_contributors[(attendees_with_contributors['_merge'] == 'left_only') | (attendees_with_contributors['_merge'] == 'right_only')]
attendees_notreconciled_with_contributors = unreconciled_attendees_with_contributor[unreconciled_attendees_with_contributor['_merge'] == 'left_only']
contributors_notreconciled_with_attendees = unreconciled_attendees_with_contributor[unreconciled_attendees_with_contributor['_merge'] == 'right_only']

# apply fuzzywuzzy to unreconciled list of attendees


similarity_scores = []
for name1 in attendees_notreconciled_with_contributors['full_name']:
    for name2 in contributors_notreconciled_with_attendees['full_name']:
        score = fuzz.ratio(name1,name2)
        similarity_scores.append(score)

threshold = 55

attendee_contribuitor_similar_pairs = [
    (name1, name2, score)
    for name1, name2, score in zip(attendees_notreconciled_with_contributors['full_name'], contributors_notreconciled_with_attendees['full_name'], similarity_scores)
    if score >= threshold
]      
 
# no similar names in unreconciled attendee contributor pair 

contributor_attendees = attendees_with_contributors[attendees_with_contributors['_merge'] == 'both'] # 63 contributor attendees


# apply the test on client contributors

attendees_with_client = pd.merge(attendee_unique,client_unique, on = 'full_name', how = 'outer', indicator = True) 
unreconciled_attendees_with_client = attendees_with_client[(attendees_with_client['_merge'] == 'left_only') | (attendees_with_client['_merge'] == 'right_only')]
attendees_notreconciled_with_clients = unreconciled_attendees_with_client[unreconciled_attendees_with_client['_merge'] == 'left_only']
clients_notreconciled_with_attendees = unreconciled_attendees_with_client[unreconciled_attendees_with_client['_merge'] == 'right_only']

# apply fuzzywuzzy to unreconciled list of attendees


similarity_scores = []
for name1 in attendees_notreconciled_with_clients['full_name']:
    for name2 in clients_notreconciled_with_attendees['full_name']:
        score = fuzz.ratio(name1,name2)
        similarity_scores.append(score)

threshold = 55

attendee_client_similar_pairs = [
    (name1, name2, score)
    for name1, name2, score in zip(attendees_notreconciled_with_clients['full_name'], clients_notreconciled_with_attendees['full_name'], similarity_scores)
    if score >= threshold
]      


# no similar names in unreconciled attendees client pair

client_attendees =  attendees_with_client[attendees_with_client['_merge'] == 'both'] # 62 contributor attendees  


# putting all attendee clasifications together
attendee_unique = attendee_unique.rename(columns = {'full_name' : 'attendee_name'})
author_unique = author_unique.rename(columns = {'full_name' : 'author_name'})
contributor_unique = contributor_unique.rename(columns = {'full_name' : 'contributor_name'})
client_unique = client_unique.rename(columns = {'full_name' : 'client_name'})

attendees_and_author = pd.merge(attendee_unique,author_unique, left_on = 'attendee_name', 
                                              right_on = 'author_name',how = 'outer', indicator = True)
attendees_and_author = attendees_and_author.sort_values('_merge', ascending=False)
attendees_and_author = attendees_and_author.rename(columns = {'_merge' : 'merge_att&author'})

attendee_author_and_contributor = pd.merge(attendees_and_author,contributor_unique,left_on = 'attendee_name', 
                                             right_on = 'contributor_name', how = 'outer', indicator = True)

attendee_author_and_contributor = attendee_author_and_contributor.sort_values(['_merge','merge_att&author'], ascending=[False, True])
attendee_author_and_contributor  = attendee_author_and_contributor.rename(columns = {'_merge' : 'merge_att,author&contributor'})

everyone = pd.merge(attendee_author_and_contributor, client_unique, left_on = 'attendee_name', right_on = 'client_name',
                    how = 'outer', indicator = True)
everyone = everyone.sort_values(['attendee_name','author_name','contributor_name','client_name'], na_position = 'last')
everyone_dep = everyone.drop(columns = ['merge_att&author','merge_att,author&contributor','_merge'])

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
everyone_dep.to_csv ("unique_names_allplayers.csv", index = False)

# Result of Analysis


Result = pd.DataFrame(columns = ['Issue','Result'])
Result.loc[len(Result)] = ['Unique Attendees', attendee_unique.shape[0]]
Result.loc[len(Result)] = ['Unique Authors', author_unique.shape[0]]
Result.loc[len(Result)] = ['Unique Eip Contributors', contributor_unique.shape[0]]
Result.loc[len(Result)] = ['Unique Client Contributors', client_unique.shape[0]]
Result.loc[len(Result)] = ['Authors who Attended Meetings', author_attendees.shape[0]] 
Result.loc[len(Result)] = ['Contributors who Attended Meetings', contributor_attendees.shape[0]]
Result.loc[len(Result)] = ['Clients who Attended Meetings', client_attendees.shape[0]]
Result.loc[len(Result)] = ['Authors who are also Contributors', author_unique[author_unique['author_name'].isin(contributor_unique['contributor_name'])].shape[0]]
Result.loc[len(Result)] = ['Authors who are also Clients', author_unique[author_unique['author_name'].isin(client_unique['client_name'])].shape[0]]
Result.loc[len(Result)] = ['Client who are also Contributors', client_unique[client_unique['client_name'].isin(contributor_unique['contributor_name'])].shape[0]]
Result.loc[len(Result)] = ['Authors who are Clients and also attended meetings', 
                           author_unique[author_unique['author_name'].isin(client_unique['client_name'])
                                                                                              & author_unique['author_name'].isin(attendee_unique['attendee_name'])].shape[0]]
Result.loc[len(Result)] = ['Authors who are Contributors and also attended meetings', 
                           author_unique[author_unique['author_name'].isin(contributor_unique['contributor_name'])
                                                                                              & author_unique['author_name'].isin(attendee_unique['attendee_name'])].shape[0]]
Result.loc[len(Result)] = ['Authors who are Clients and Contributors', 
                           author_unique[author_unique['author_name'].isin(client_unique['client_name'])
                                                                                              & author_unique['author_name'].isin(contributor_unique['contributor_name'])].shape[0]]

Result.loc[len(Result)] = ['Contributors who are Clients and also attended meetings', 
                           contributor_unique[contributor_unique['contributor_name'].isin(client_unique['client_name'])
                                                                                              & contributor_unique['contributor_name'].isin(attendee_unique['attendee_name'])].shape[0]]
Result.loc[len(Result)] = ['People who did everything', 
                           attendee_unique[attendee_unique['attendee_name'].isin(client_unique['client_name'])
                                                                                              & attendee_unique['attendee_name'].isin(author_unique['author_name'])
                                                                                              & attendee_unique['attendee_name'].isin(contributor_unique['contributor_name'])].shape[0]]


Result.to_csv("Name_Results.csv", index = False)