# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 12:44:12 2023

@author: moazz
"""

import pandas as pd
import os as os
from fuzzywuzzy import fuzz



os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
attendees = pd.read_csv("flat_list_meeting_attendees.csv", encoding='latin1')

names = attendees['Attendees'].tolist()
unique_attendees1 = list(set(names))

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
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
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
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
names_to_change2.to_csv("names_to_change2.csv")

# create second replacement based on manually corrected names between the threshold of 55 to 75

names_to_change2_mod = pd.read_csv("names_to_change2_post_manual.csv")
right_names2 = names_to_change2_mod['Names_to_Keep'].tolist()
wrong_names2 = names_to_change2_mod['Names_to_Replace'].tolist()
name_dict2 = dict(zip(wrong_names2,right_names2))
names3 = [name_dict2[name] if name in name_dict2 else name for name in names2]
sorted_names3 = sorted(names3, key=lambda x: (isinstance(x, str), x))

# create a third replacement based on manually checked names

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
#unique_attendee4.to_csv("Attendeelist_before_assigning_firstnames_to_multiple_persons.csv")
unique_attendee4.to_csv("Unique_Attendees.csv")


# create mapping file
df1 = pd.DataFrame(names, columns=['Original_Name'])
df2 = pd.DataFrame(names4, columns=['Replace_Name'])

mapping_file = pd.concat([df1, df2], axis=1)

# save mapping file

mapping_file.to_csv("Attendees_Mapping_File.csv")
