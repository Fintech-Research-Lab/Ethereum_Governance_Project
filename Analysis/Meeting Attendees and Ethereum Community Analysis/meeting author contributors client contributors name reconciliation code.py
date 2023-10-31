# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os
from fuzzywuzzy import fuzz


# Read Data
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Analysis Code/Data Fixing Codes/")
attendees = pd.read_csv("flat_list_meeting_attendees.csv", encoding='latin1')


# get author data and remove nan and et al. from the author list
os.chdir ("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/")
cs = pd.read_csv("Ethereum_Cross-sectional_Data.csv")
author_values = cs.loc[:,'Author1':'Author15'].values.tolist()
author = set([item for sublist in author_values for item in sublist])
author = pd.DataFrame(author, columns = ['full_name'])
author = author[pd.notnull(author['full_name']) & (author['full_name'] != 'et al.')]

# get commit data
eip_commit = pd.read_stata("Ethereum_Commit.dta")

# get client data
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/client_commit")
geth = pd.read_stata("commitsgeth.dta")
besu = pd.read_stata("commitsbesu.dta")
erigon = pd.read_stata("commitserigon.dta")
nethermind = pd.read_stata("commitsnethermind.dta")

clients = pd.concat([geth,besu,erigon,nethermind])


# Create a unique list of authors, contributors, attendee and clitnts

author_unique = author['full_name']
author_unique = pd.DataFrame(author_unique, columns = ['full_name'])
contributor_unique = pd.unique(eip_commit['Author'])
contributor_unique = pd.DataFrame(contributor_unique, columns = ['full_name'])
# remove eth-bot from contributor_unique
contributor_unique = contributor_unique[contributor_unique['full_name'] != 'eth-bot']
client_unique = pd.unique(clients ['author'])
client_unique = pd.DataFrame(client_unique, columns = ['full_name'])
attendee_unique1 = pd.unique(attendees['full_name'])
attendee_unique1 = pd.DataFrame(attendee_unique1, columns = ['full_name'])


# create similarity score within attendees list to remove similar name

similarity_score =  []
names = attendee_unique1['full_name'].tolist()
for i in range(len(names)):
               for j in range(i+1,len(names)):
                   score = fuzz.ratio(names[i],names[j])
                   similarity_score.append((i,j,names[i],names[j],score))

threshold = 76 # after manually iterating 76 seems to be the best first cutoff

high_similarity_score1 = [score for score in similarity_score if score[4] > threshold]
name_check = [score for score in high_similarity_score1 if (score[4]>74 and score[4]<80)] # to manually check

# remove similar names
indices_to_remove1 = [score[1] for score in high_similarity_score1]
name2 = [name for i, name in enumerate(names) if i not in indices_to_remove1]

attendee_unique2 = attendee_unique1[attendee_unique1['full_name'].isin(name2)]

# the second phase of prunning with require some manual cleanup. In this phase, I will manually check between thresholds of 55 and 75
# and manually create a list of indicies by manually looking at similar names that should be further pruned
# in order to not use old indexing, we create new similarity scores

similarity_score =  []
names = attendee_unique2['full_name'].tolist()
for i in range(len(names)):
               for j in range(i+1,len(names)):
                   score = fuzz.ratio(names[i],names[j])
                   similarity_score.append((i,j,names[i],names[j],score))



threshold = 55 # after manually iterating 55seems to be the best second cutoff

high_similarity_score2 = [score for score in similarity_score if score[4] > threshold]
name_check = [score for score in high_similarity_score2 if (score[4]>54 and score[4]<76)] # to manually check

# create manual list of indices to remove. After manual examination the following appears to be duplicate names with slight
# variations
indices_to_remove2 = [44,188,49,81,238,108,134,148,232,105,307,97,114,340,209,456,67,125,103,229,389,59,283,425,233,277,
                      415,216,369,437,457]


name3 = [name for i, name in enumerate(name2) if i not in indices_to_remove2]


attendee_unique3 = attendee_unique1[attendee_unique1['full_name'].isin(name3)]

# reassign attendee_unique3 as attendee_unique for further coding

attendee_unique = attendee_unique3
  
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

author_attendees = attendees_with_author[attendees_with_author['_merge'] == 'both'] # 76 attendees are authors

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

os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Analysis Code/Data Fixing Codes/")
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