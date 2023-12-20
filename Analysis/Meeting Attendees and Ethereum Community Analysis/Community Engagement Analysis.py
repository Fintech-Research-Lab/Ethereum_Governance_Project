# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np

#os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project')


# Read Data

authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
clients = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_clients_final.csv")
attendees = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_attendees_final.csv")

attendees = pd.DataFrame(attendees['Name'])
attendees = attendees.rename(columns = {"Name":"Attendee_Name"})
clients = pd.DataFrame(clients['Name'])
clients = clients.rename(columns = {"Name":"Client_Name"})

# This last part of the code further find names on contributor file which may be authors. After complete treatment of name cleaning code above
# this code will see if there are still common names in contribution file that contains authors and remove it. Later on, these will
# be appended for further analysis to find all members of the community

authors = pd.read_csv("Data/Raw Data/unique_author_names_with_id.csv")
cleaned_contributors = pd.read_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributors_final.csv") 

# find authors only contributors only and contributors and authors

eip_commit = pd.read_excel("Data/Commit Data/Eip commit Data/eip_commit_beg.xlsx")
all_contributors = pd.merge(eip_commit,authors, left_on = 'Username', right_on = "GitHub_Username", how = 'left', indicator = True )
all_contributors = pd.unique(all_contributors['Author'])
all_contributors = pd.DataFrame(all_contributors, columns = ['Name'])

authors_and_contributors = pd.merge(authors,cleaned_contributors, left_on = 'Full_Name', right_on = "Name", how = 'outer', indicator = True )
contributors_only = authors_and_contributors[authors_and_contributors['_merge']=='right_only']
missed_authors_in_github = authors_and_contributors[authors_and_contributors['_merge']=='both']

author_contributors = pd.merge(authors,all_contributors, left_on = "Full_Name", right_on = "Name", how = 'inner')


len(np.where(pd.isnull(authors['GitHub_Username']))[0]) #153 usernames with missing github 
contributors_only.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_contributorsonly_final.csv", index = False)



# putting all attendee clasifications together

authors = pd.DataFrame(authors['Full_Name'])
authors = authors.rename(columns = {"Full_Name" : "Author_Name"})
all_contributors = all_contributors.rename(columns = {"Name" : "Contributor_Name"})


attendees_and_author = pd.merge(attendees,authors, left_on = 'Attendee_Name', 
                                              right_on = 'Author_Name',how = 'outer', indicator = True)
attendees_and_author = attendees_and_author.sort_values('_merge', ascending=False)
attendees_and_author = attendees_and_author.rename(columns = {'_merge' : 'merge_att&author'})

attendee_author_and_contributor = pd.merge(attendees_and_author,all_contributors,left_on = 'Author_Name', 
                                             right_on = 'Contributor_Name', how = 'outer', indicator = True)
    
attendee_author_and_contributor = attendee_author_and_contributor.sort_values(['_merge','merge_att&author'], ascending=[False, True])
attendee_author_and_contributor  = attendee_author_and_contributor.rename(columns = {'_merge' : 'merge_att,author&contributor'})

everyone = pd.merge(attendee_author_and_contributor, clients, left_on = 'Author_Name', right_on = 'Client_Name',
                    how = 'outer', indicator = True)
everyone = everyone.sort_values(['Author_Name','Attendee_Name','Contributor_Name','Client_Name'], na_position = 'last')
everyone_dep = everyone.drop(columns = ['merge_att&author','merge_att,author&contributor','_merge'])

# check for duplicates

dup = everyone_dep[everyone_dep.duplicated(keep = False)]
everyone_dep = everyone_dep.drop_duplicates()

everyone_dep.to_csv ("Analysis/Meeting Attendees and Ethereum Community Analysis/unique_names_allplayers.csv", index = False)

# Result of Analysis


Result = pd.DataFrame(columns = ['Issue','Result'])
Result.loc[len(Result)] = ['Attendees', attendees.shape[0]]
Result.loc[len(Result)] = ['Authors', authors.shape[0]]
Result.loc[len(Result)] = ['EIP Contributors', all_contributors.shape[0]]
Result.loc[len(Result)] = ['Client Contributors', clients.shape[0]]

Result.loc[len(Result)] = ['Authors who Attended Meetings', len(np.where(pd.notnull(everyone_dep['Author_Name'])
                                                                         &pd.notnull(everyone_dep['Attendee_Name']))[0])] 

Result.loc[len(Result)] = ['Contributors who Attended Meetings',len(np.where(pd.notnull(everyone_dep['Contributor_Name'])
                                                                         &pd.notnull(everyone_dep['Attendee_Name']))[0])]

Result.loc[len(Result)] = ['Clients who Attended Meetings', len(np.where(pd.notnull(everyone_dep['Client_Name'])
                                                                         &pd.notnull(everyone_dep['Attendee_Name']))[0])]

Result.loc[len(Result)] = ['Authors who are also Contributors', len(np.where(pd.notnull(everyone_dep['Author_Name'])
                                                                             &pd.notnull(everyone_dep['Contributor_Name']))[0])]

Result.loc[len(Result)] = ['Authors who are also Clients', len(np.where(pd.notnull(everyone_dep['Author_Name'])
                                                                        &pd.notnull(everyone_dep['Client_Name']))[0])]

Result.loc[len(Result)] = ['Client who are also Contributors', len(np.where(pd.notnull(everyone_dep['Contributor_Name'])
                                                                        &pd.notnull(everyone_dep['Client_Name']))[0])]

Result.loc[len(Result)] = ['Authors who are Clients and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name']))[0])]

Result.loc[len(Result)] = ['Authors who are Contributors and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Contributor_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name']))[0])]

Result.loc[len(Result)] = ['Authors who are Clients and Contributors', 
                           len(np.where(pd.notnull(everyone_dep['Author_Name'])&pd.notnull(everyone_dep['Contributor_Name'])
                                        &pd.notnull(everyone_dep['Client_Name']))[0])]

Result.loc[len(Result)] = ['Contributors who are Clients and also attended meetings', 
                           len(np.where(pd.notnull(everyone_dep['Contributor_Name'])&pd.notnull(everyone_dep['Attendee_Name'])
                                        &pd.notnull(everyone_dep['Client_Name']))[0])]

Result.loc[len(Result)] = ['People who did everything', 
                           len(np.where(pd.notnull(everyone_dep['Contributor_Name'])&pd.notnull(everyone_dep['Client_Name'])
                                        &pd.notnull(everyone_dep['Attendee_Name'])&pd.notnull(everyone_dep['Author_Name']))[0])]


Result.to_csv("Analysis/Meeting Attendees and Ethereum Community Analysis/Name_Results.csv", index = False)

###### THIS CODE BELOW CREATES A 3 WAY VENN DIAGRAM #################
# ignore contributors


from matplotlib import pyplot as plt
from matplotlib_venn import venn3

unique_attendees = set(attendees['Attendee_Name'].unique())
unique_clients = set(clients['Client_Name'].unique())
unique_authors = set(authors['Author_Name'].unique())

venn3([unique_attendees, unique_clients, unique_authors], ('AllCoreDevs Attendees', 'Client Contributors', 'EIP Authors'))
#plt.title('Meeting Attendees, Authors, and Clients Combination')

# Save the plot as a PNG file
plt.savefig('Analysis/Meeting Attendees and Ethereum Community Analysis/venn_diagram.png')

# Display the plot
plt.show()


















