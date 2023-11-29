# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 02:08:12 2023

@author: moazz
"""

import pandas as pd
import os as os
import re

# Read Data
os.chdir("C:/Users/moazz/Downloads/")
dat = pd.read_csv("dev_calls_attendees_standardized.csv", encoding='latin1')


# Function to clean text
def clean_text(text):
    text = re.sub(r'\(.*?\)', '', text)  # Remove everything within ()
    text = re.sub(r'<.*?>', '', text)  # Remove everything within <>
    text = text.strip()  # Remove leading and trailing spaces
    return None if text == '' else text  # Return None for empty strings

# Apply the function to each name in the 'names' column
dat['names'] = dat['Attendees'].str.split(",").apply(lambda x: [i for i in [clean_text(j) for j in x] if i is not None])
names = pd.DataFrame(dat['names'])


# create flt list for names
flat_list = [name for sublist in dat['names'] for name in sublist]
flat_names = pd.DataFrame(flat_list)

# create flat list for meetings
meeting_list = []
for index, row in dat.iterrows():
    meetings = [row['Meeting']] * len(row['names'])
    meeting_list.extend(meetings)   
meetings = pd.DataFrame(meeting_list)

# combine flat meetings and attendees to create a new list
new_list = pd.concat([meetings, flat_names], axis = 1)

new_list.to_csv("flat_list_meeting_attendees.csv")

