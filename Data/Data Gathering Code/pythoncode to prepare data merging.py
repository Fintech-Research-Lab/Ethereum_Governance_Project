# -*- coding: utf-8 -*-
"""
Created on Sun Oct  1 10:40:00 2023

@author: moazz
"""

import pandas as pd
import os as os
import re

# Read Data
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")
dat = pd.read_csv("allEIPsandAuthorsv2.csv", encoding='latin1')
author = pd.read_csv("unique_author_names_with_id.csv")

# drop unnamed column

#dat.drop("Unnamed: 6", axis = 1, inplace = True)

# Function to clean text
def clean_text(text):
    text = re.sub(r'\(.*?\)', '', text)  # Remove everything within ()
    text = re.sub(r'<.*?>', '', text)  # Remove everything within <>
    text = text.strip()  # Remove leading and trailing spaces
    return None if text == '' else text  # Return None for empty strings

# Apply the function to each name in the 'names' column
names = dat['Author'].str.split(",").apply(lambda x: [i for i in [clean_text(j) for j in x] if i is not None])

wrong_names = ['Christian ReitwieÃŸner','Lightclient','Marius van der Wijden','Muhammed Emin Ayd?n','Mücahit Büyüky?lmaz',
               'Pawe? Bylica','Piotr Kosi?ski','Sergio D. Lerner','g. nicholas dandrea','and Arran Schlosberg','Piotr KosiÅ„ski',
               'Benjamin Hauser','Señor Doggo','Felix J Lange','Pandapip1','Martin Swende','lightclient','lightclient','qizhou',
               'Tomasz Stanczak','Zainan Zhou','fubuloubu','Süleyman Karda?','Tomá Jan?a',
               'tefan imec','Jessica','Roy','Christian ReitwieBner','Agustín Aguilar','Joel Torstensson','Michael D. Carter','PhD',
               'et al.','Christian Reitwießner']
Right_Names = ['Christian Reitwiessner','Matt Garnett','Marius Van Der Wijden','Muhammed Emin Aydın','Mücahit Büyükyılmaz',
               'Pawel Bylica','Piotr Kosinski','Sergio Demian Lerner',"g. nicholas d'andrea",'Arran Schlosberg','Piotr Kosiński',
               'Ben Hauser','Bryant Eisenbach','Felix Lange','Gavin John', 'Martin Holst Swende','Matt Garnett','Matt Garnett',
               'Qi Zhou','Tomasz Kajetan Stanczak','Zainan Victor Zhou','Bryant Eisenbach',
               'Suleman Kardas','Tomas Jansa','Stefan Simec','Jessica Zheng','Roy Shang','c','Agustin Aguilar'
               ,'Joel Thorstensson','Michael Carter','','','Christian Reitwiessner']

name_dict = dict(zip(wrong_names,Right_Names))

# replace change names in the list of author nmes
corrected_names = [[name_dict[name] if name in name_dict else name for name in sublist] for sublist in names]
corrected_names_df = pd.DataFrame(corrected_names)
corrected_names_df.columns = ["Author1","Author2","Author3","Author4","Author5","Author6","Author7","Author8","Author9","Author10","Author11","Author12","Author13","Author14", "Author15"]
dat = pd.concat([dat,corrected_names_df], axis = 1)


# fixing duplicates (some author names are duplicated in certain eips)

def rearrange_authors(row):
    seen_authors = set()
    rearranged_authors = []
    
    for col in row.index[3:]:
        author = row[col]
        if author not in seen_authors:
            rearranged_authors.append(author)
            seen_authors.add(author)
    
    return pd.Series(rearranged_authors)

# Apply the rearrange_authors function to each row
dat_rearranged = dat.apply(rearrange_authors, axis=1)
dat_rearranged.columns =  ["Author1","Author2","Author3","Author4","Author5","Author6","Author7","Author8","Author9","Author10","Author11","Author12","Author13","Author14", "Author15"]
dat = pd.concat([dat.iloc[:,0:3],dat_rearranged], axis = 1)

# remove authors that are modified

new_author = dat.iloc[:, 3:].stack().dropna().unique()
new_author_in_author = author[author['Full_Name'].isin(new_author)]
new_author_notin_author = author[~author['Full_Name'].isin(new_author)]

author_dict = pd.Series(new_author_in_author.author_id.values, index = new_author_in_author.Full_Name).to_dict()


for i in range(1, 16):
    dat[f'author{i}_id'] = dat[f'Author{i}'].map(author_dict)
    
# rename Number to eip_number

dat = dat.rename(columns = {'Number' : 'eip_number'})    
 
# save the Cross Sectional and Author files
dat.to_csv("Ethereum_Cross-sectional_Data.csv", encoding='utf-8', index = False)
new_author_in_author.to_csv("unique_author_names_with_id") # saving new author list after modifications