# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os



# Read Data

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
authors = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_authors_final.csv")
clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")
contributors = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributors_final.csv") 
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")

attendees = pd.DataFrame(attendees['Name'])
attendees = attendees.rename(columns = {"Name":"Attendee_Name"})
contributors = pd.DataFrame(contributors['Name'])
contributors = contributors.rename(columns = {"Name":"Contributor_Name"})



# putting all attendee clasifications together
attendees_and_author = pd.merge(attendees,authors, left_on = 'Name', 
                                              right_on = 'Full_Name',how = 'outer', indicator = True)
attendees_and_author = attendees_and_author.sort_values('_merge', ascending=False)
attendees_and_author = attendees_and_author.rename(columns = {'_merge' : 'merge_att&author'})

attendee_author_and_contributor = pd.merge(attendees_and_author,contributors,left_on = 'Name', 
                                             right_on = 'Name', how = 'outer', indicator = True)
    
attendee_author_and_contributor = attendee_author_and_contributor.sort_values(['_merge','merge_att&author'], ascending=[False, True])
attendee_author_and_contributor  = attendee_author_and_contributor.rename(columns = {'_merge' : 'merge_att,author&contributor'})

everyone = pd.merge(attendee_author_and_contributor, clients, left_on = 'Name', right_on = 'Name',
                    how = 'outer', indicator = True)
everyone = everyone.sort_values(['Name'], na_position = 'last')
everyone_dep = everyone.drop(columns = ['merge_att&author','merge_att,author&contributor','_merge'])

os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Attendees and Ethereum Community Analysis/")
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

###### THIS CODE BELOW CREATES A 3 WAY VENN DIAGRAM #################
# ignore contributors

from matplotlib import pyplot as plt
from matplotlib_venn import venn3


unique_attendees = set(attendee_unique['attendee_name'].unique())
unique_clients = set(client_unique['client_name'].unique())
unique_authors = set(author_unique['author_name'].unique())

venn3([unique_attendees, unique_clients, unique_authors], ('Attendees', 'Clients', 'Authors'))
plt.title('Meeting Attendees, Authors, and Clients Combination')
plt.show()