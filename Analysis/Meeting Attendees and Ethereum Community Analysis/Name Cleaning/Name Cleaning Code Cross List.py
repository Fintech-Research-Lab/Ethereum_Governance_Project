# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 10:08:48 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np
from fuzzywuzzy import fuzz

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")

# get all lists

clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/Unique_Clients.csv")
contributors = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/Unique_Contributors.csv")
authors = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/Unique_Authors.csv")
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/Unique_Attendees.csv")
authors = authors.rename(columns = {'Full_Name' : "Name"})
authors = authors.drop(columns = 'Unnamed: 0')
contributors = contributors.rename(columns = {'Full_Name' : "Name"})
contributors = contributors.drop(columns = 'Unnamed: 0')
clients = clients.rename(columns = {'full_name' : "Name"})
clients = clients.drop(columns = 'Unnamed: 0')
attendees = attendees.rename(columns = {'full_name' : "Name"})
attendees = attendees.drop(columns = 'Unnamed: 0')


clients['list'] = "client"
contributors['list'] = "contributor"
authors['list'] = "author"
attendees['list'] = "attendee"

total = pd.concat([clients,contributors,authors,attendees], ignore_index = True)

names = total['Name'].tolist()
unique_names = list(set(names))

# create similarity score within attendees list to remove similar name

similarity_score =  []
for i in range(len(unique_names)):
               for j in range(i+1,len(unique_names)):
                   score = fuzz.ratio(unique_names[i],unique_names[j])
                   similarity_score.append((i,j,unique_names[i],unique_names[j],score))

threshold = 76 # after manually iterating 76 seems to be the best first cutoff

high_similarity_score1 = [score for score in similarity_score if score[4] > threshold]
#name_check = [score for score in high_similarity_score1 if (score[4]>74 and score[4]<80)] # to manually check

name_to_replace = [row[3] for row in high_similarity_score1]
name_to_replace_with = [row[2] for row in high_similarity_score1]

names_to_change = pd.concat([pd.DataFrame(name_to_replace_with),pd.DataFrame(name_to_replace)], axis = 1)
names_to_change.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change.csv", index = False)

names_to_change_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change_post_manual.csv")
right_names = names_to_change_mod['Names_to_Keep'].tolist()
wrong_names = names_to_change_mod['Names_to_Replace'].tolist()
name_dict = dict(zip(wrong_names,right_names))
names2 = [name_dict[name] if name in name_dict else name for name in names]

high_similarity_score2 = [score for score in similarity_score if score[4] > 54 and score[4] < 76]
name_to_replace2 = [row[3] for row in high_similarity_score2]
name_to_replace_with2 = [row[2] for row in high_similarity_score2]
names_to_change2 = pd.concat([pd.DataFrame(name_to_replace_with2),pd.DataFrame(name_to_replace2)], axis = 1)
names_to_change2.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change2.csv", index = False)

names_to_change2_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change2_post_manual.csv")
right_names2 = names_to_change2_mod['Names_to_Keep'].tolist()
wrong_names2 = names_to_change2_mod['Names_to_Replace'].tolist()
name_dict2 = dict(zip(wrong_names2,right_names2))
names3 = [name_dict2[name] if name in name_dict2 else name for name in names2]
sorted_names3 = sorted(names3, key=lambda x: (isinstance(x, str), x))

# create a third replacement based on manually checked names

total_list2 = set(names3)
total2 = pd.DataFrame(total_list2 , columns = ['Name'])
# manual check and fixing last time without similarity scores
total2.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change3.csv", index = False)

names_to_change3_mod = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/total_names_to_change3_post_manual.csv")
right_names3 = names_to_change3_mod['Names_to_Keep'].tolist()
wrong_names3 = names_to_change3_mod['Names_to_Replace'].tolist()
name_dict3 = dict(zip(wrong_names3,right_names3))
names4 = [name_dict3[name] if name in name_dict3 else name for name in names3]

# create mapping file
df1 = pd.DataFrame(names, columns=['Original_Name'])
df2 = pd.DataFrame(names4, columns=['Replace_Name'])

mapping_file = pd.concat([df1, df2], axis=1)

mapping_file.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/all_Mapping_File.csv")

# create separate unique lists

total_mod = total
total_mod['Name'] = pd.DataFrame(names4)


attendees_mod = total_mod.loc[total_mod['list'] == "attendee", "Name"]
clients_mod = total_mod.loc[total_mod['list'] == "client","Name"]
contributors_mod = total_mod.loc[total_mod['list'] == "contributor","Name"]

# generate unique (Note that we used a method that when someone signs up as an attendee, contributor, or client only with the first name
# but does there are two people with the same first name but different last name to avoid over-counting we deployed a rule that we assign
# the last name which is highest in alphabatic order to the person with only the last name. This may avoid overcounting
# however we do not apply this rule to authors list)

attendees_unique_mod = pd.DataFrame(attendees_mod.unique(), columns = ["Name"])
clients_unique_mod = pd.DataFrame(clients_mod.unique(), columns = ["Name"])
contributors_unique_mod = pd.DataFrame(contributors_mod.unique(), columns = ["Name"])

# apply the test for anonymity and create anonymity flag

authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
authors['Anonymity_Flag'] = np.where(authors['Full_Name'].str.contains(" "),0,1)
authors.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name Cleaning/author_anonymity_flag.csv") 
authors.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_authors_final.csv") 

contributors_unique_mod['Anonymity_Flag'] = np.where(contributors_unique_mod['Name'].str.contains(" "),0,1)
# after manual checking
contributors_unique_mod.loc[4,'Anonymity_Flag'] = 1
contributors_unique_mod.loc[229,'Anonymity_Flag'] = 1

contributors_unique_mod.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributors_final.csv")

clients_unique_mod['Anonymity_Flag'] = np.where(clients_unique_mod['Name'].str.contains(" "),0,1)
# after manual checking make following changes
clients_unique_mod.loc[4,'Anonymity_Flag'] = 1
clients_unique_mod.loc[229,'Anonymity_Flag'] = 1
clients_unique_mod.loc[509,'Anonymity_Flag'] = 1
clients_unique_mod.loc[603,'Anonymity_Flag'] = 1
clients_unique_mod.loc[609,'Anonymity_Flag'] = 1
clients_unique_mod.loc[361,'Anonymity_Flag'] = 0
clients_unique_mod.loc[571,'Anonymity_Flag'] = 0
clients_unique_mod.loc[1047,'Anonymity_Flag'] = 0

clients_unique_mod.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")

attendees_unique_mod['Anonymity_Flag'] = np.where(attendees_unique_mod['Name'].str.contains(" "),0,1)

# after manual checking make following changes
index_to_0 = [347,361,402,416,431,446,705,769,775,802,806,835,844,848,902,937,938,939,1027,1033,1079,1101]
attendees_unique_mod.loc[index_to_0,'Anonymity_Flag'] = 0
index_to_1 = [4,195,229,386,669,936,1091]
attendees_unique_mod.loc[index_to_1,'Anonymity_Flag'] = 1

attendees_unique_mod.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")
