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


os.chdir('C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/')
data = pd.read_csv("Analysis/Magician Comments/ethereum_sentiment.csv")
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-Sectional_Data.dta")
cs = cs[['eip_number','Category']]
comment_author = data[['EIP','Comment Authors']]  
commentator = comment_author['Comment Authors'].dropna()
comment_author = pd.merge(comment_author,cs,left_on = 'EIP',right_on = "eip_number", how = 'left')

# create a list of names and comments and tie them to eips
names = []
comments = []
indexes = []

for index, entry in enumerate(commentator):
    items = entry.split(",")
    for item in items:
        name, comment = item.split(":")
        name = name.strip("' ")
        names.append(name)
        comment = int(comment)
        comments.append(comment)
        indexes.append(index)
        
names = pd.DataFrame(names, columns = ["Names"])
comments = pd.DataFrame(comments, columns = ['comments'])
indexes = pd.DataFrame(indexes, columns = ['Index'])    
commentary = pd.concat([indexes, names, comments], axis=1)
commentary = pd.merge(commentary, comment_author[['EIP','Category']], left_on='Index', right_index=True)

# group by names and eips

unique_names = commentary['Names'].unique()
comments_by_name = commentary.groupby('Names')['comments'].sum().sort_values(ascending = False).reset_index()
comments_by_eip = commentary.groupby('EIP').agg({'comments':'sum','Category':'first'}).reset_index()

# histogram

comments_by_eip_mod = comments_by_eip.copy()
comments_by_eip.loc[comments_by_eip['comments']>100,'comments'] = 100

plt.figure(figsize=(8, 6))
plt.hist(comments_by_eip['comments'], bins=30, alpha=0.7, color='green')  # Adjust bins for granularity
plt.title('Histogram of Comments by EIP')
plt.xlabel('Number of Comments')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()


# plot by eips of comments per eip
plt.figure(figsize=(10, 6))
sns.barplot(data=comments_by_name.head(20), x='Names', y='comments', hue='Category', dodge=False)
plt.title('Frequency of Comments by Names with Categories')
plt.xlabel('Names')
plt.ylabel('Frequency')
plt.xticks(rotation=45)  # Rotating x-axis labels for better readability
plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# lorenze curve with commentators
comments_by_name = pd.DataFrame(comments_by_name)
comments_by_name['cum_comments'] = comments_by_name['comments'].cumsum()
comments_by_name['N_People'] = comments_by_name.index+1

plt.figure(figsize=(10, 6))
plt.plot(comments_by_name['N_People'], comments_by_name['cum_comments'])
plt.title('Lorenz Curve Number of Comments')
plt.xlabel('Commentator')
plt.ylabel('Frequency')
plt.xticks(rotation=45)  # Rotating x-axis labels for better readability
plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# gini coefficient

def gini_coefficient(x):
    # The rest of the values are handled by this line:
    x = np.sort(x) # values must be sorted
    index = np.arange(1, x.shape[0] + 1) # index per array element
    n = x.shape[0] # number of array elements
    return ((np.sum((2 * index - n  - 1) * x)) / (n * np.sum(x))) # Gini coefficient


dat = comments_by_name['comments']
gini_coefficient = gini_coefficient(dat)
