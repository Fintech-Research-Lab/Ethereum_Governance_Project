# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np



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
clients = pd.DataFrame(clients['Name'])
clients = clients.rename(columns = {"Name":"Client_Name"})
authors = pd.DataFrame(authors['Full_Name'])
authors = authors.rename(columns = {"Full_Name":"Author_Name"})


# our contributors file currently misses all contributor-authors, this file only contains non-author contributors
# the following code will add author-contributors to this list

eip_commit = pd.read_excel("Data/Commit Data/Eip commit Data/eip_commit_beg.xlsx")
author_contributors = pd.merge(eip_commit,authors, left_on = 'Username', right_on = "GitHub_Username", how = 'outer', indicator = True )
author_contributors = author_contributors[author_contributors['_merge'] == 'both']
author_contributors = author_contributors['Full_Name']
author_contributors = pd.unique(author_contributors)
author_contributors = pd.DataFrame(author_contributors, columns = ["Contributor_Name"])

# add author_contributors to contributors

contributors = pd.concat([contributors,author_contributors], axis = 0)



# putting all attendee clasifications together
attendees_and_author = pd.merge(attendees,authors, left_on = 'Attendee_Name', 
                                              right_on = 'Author_Name',how = 'outer', indicator = True)
attendees_and_author = attendees_and_author.sort_values('_merge', ascending=False)
attendees_and_author = attendees_and_author.rename(columns = {'_merge' : 'merge_att&author'})

attendee_author_and_contributor = pd.merge(attendees_and_author,contributors,left_on = 'Author_Name', 
                                             right_on = 'Contributor_Name', how = 'outer', indicator = True)
    
attendee_author_and_contributor = attendee_author_and_contributor.sort_values(['_merge','merge_att&author'], ascending=[False, True])
attendee_author_and_contributor  = attendee_author_and_contributor.rename(columns = {'_merge' : 'merge_att,author&contributor'})

everyone = pd.merge(attendee_author_and_contributor, clients, left_on = 'Author_Name', right_on = 'Client_Name',
                    how = 'outer', indicator = True)
everyone = everyone.sort_values(['Author_Name','Attendee_Name','Contributor_Name','Client_Name'], na_position = 'last')
everyone_dep = everyone.drop(columns = ['merge_att&author','merge_att,author&contributor','_merge'])

everyone_dep.to_csv ("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_names_allplayers.csv", index = False)

# Result of Analysis


Result = pd.DataFrame(columns = ['Issue','Result'])
Result.loc[len(Result)] = ['Attendees', attendees.shape[0]]
Result.loc[len(Result)] = ['Authors', authors.shape[0]]
Result.loc[len(Result)] = ['EIP Contributors', contributors.shape[0]]
Result.loc[len(Result)] = ['Client Contributors', clients.shape[0]]
Result.loc[len(Result)] = ['Authors who Attended Meetings', len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Attendee_Name']))[0])] 
Result.loc[len(Result)] = ['Contributors who Attended Meetings',len(np.where(pd.notnull(everyone_dep['Contributor_Name'])&pd.notnull(everyone_dep['Attendee_Name']))[0])]
Result.loc[len(Result)] = ['Clients who Attended Meetings', len(np.where(pd.notnull(everyone_dep['Client_Name'])&pd.notnull(everyone_dep['Attendee_Name']))[0])]
Result.loc[len(Result)] = ['Authors who are also Contributors', len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Contributor_Name']))[0])]
Result.loc[len(Result)] = ['Authors who are also Clients', len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Client_Name']))[0])]
Result.loc[len(Result)] = ['Client who are also Contributors', len(np.where(pd.notnull(everyone_dep['Client_Name'])&pd.notnull(everyone_dep['Contributor_Name']))[0])]
Result.loc[len(Result)] = ['Authors who are Clients and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name']))[0])]
Result.loc[len(Result)] = ['Authors who are Contributors and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Contributor_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name']))[0])]
Result.loc[len(Result)] = ['Authors who are Clients and Contributors', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Contributor_Name']))[0])]
Result.loc[len(Result)] = ['Contributors who are Clients and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Contributor_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name']))[0])]
Result.loc[len(Result)] = ['People who did everything', 
                           len(np.where(pd.notnull(everyone_dep['Contributor_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name'])&pd.notnull(everyone_dep['Author_Name']))[0])]


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