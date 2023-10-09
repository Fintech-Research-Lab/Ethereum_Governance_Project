# -*- coding: utf-8 -*-
"""
Created on Sun Oct  1 10:40:00 2023

@author: moazz
"""

import pandas as pd
import os as os
import re

# Read Data
os.chdir("C:/Users/khojama/Downloads/")
dat = pd.read_csv("allEIPsandAuthorsv2.csv", encoding='latin1')
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Ethereum Project Data/")
author = pd.read_csv("unique_author_names_with_id.csv")

# drop unnamed column

dat.drop("Unnamed: 6", axis = 1, inplace = True)

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
               'Tomasz Stanczak','Zainan Zhou','fubuloubu','Christian Reitwießner','Süleyman Karda?','Tomá Jan?a',
               'tefan imec','Jessica','Roy']
Right_Names = ['Christian Reitwiessner','Matt Garnett','Marius Van Der Wijden','Muhammed Emin Aydın','Mücahit Büyükyılmaz',
               'Pawel Bylica','Piotr Kosinski','Sergio Demian Lerner',"g. nicholas d'andrea",'Arran Schlosberg','Piotr Kosiński',
               'Ben Hauser','Bryant Eisenbach','Felix Lange','Gavin John', 'Martin Holst Swende','Matt Garnett','Matt Garnett',
               'Qi Zhou','Tomasz Kajetan Stanczak','Zainan Victor Zhou','Bryant Eisenbach','Christian ReitwieBner',
               'Suleman Kardas','Tomas Jansa','Stefan Simec','Jessica Zheng','Roy Shang']

name_dict = dict(zip(wrong_names,Right_Names))

# replace change names in the list of author nmes
corrected_names = [[name_dict[name] if name in name_dict else name for name in sublist] for sublist in names]
corrected_names_df = pd.DataFrame(corrected_names)
corrected_names_df.columns = ["Author1","Author2","Author3","Author4","Author5","Author6","Author7","Author8","Author9","Author10","Author11","Author12","Author13","Author14", "Author15"]
dat = pd.concat([dat,corrected_names_df], axis = 1)

author_dict = pd.Series(author.author_id.values, index = author.Full_Name).to_dict()


for i in range(1, 16):
    dat[f'author{i}_id'] = dat[f'Author{i}'].map(author_dict)
    
# rename Number to eip_number

dat = dat.rename(columns = {'Number' : 'eip_number'})    
 
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum Governance Project/Analysis Code/")
dat.to_csv("Ethereum_Cross-sectional_Data.csv", encoding='utf-8', index = False)