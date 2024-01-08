# -*- coding: utf-8 -*-
"""
Created on Tue Dec 26 21:22:24 2023

@author: cf8745
"""


import requests
import pandas as pd
import os
from textstat.textstat import textstatistics


os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project')
    
# GitHub API URL for the Ethereum EIPs repository contents
GITHUB_REPO_EIPS_API_URL = "https://api.github.com/repos/ethereum/EIPs/contents/EIPS"
GITHUB_REPO_ERCS_API_URL = "https://api.github.com/repos/ethereum/ERCs/contents/ERCS"


def count_words_in_file(file_url):
    """
    Count the number of words in a file given its URL.
    """
    response = requests.get(file_url)
    if response.status_code == 200:
        content = response.text
        words = content.split()
        return len(words)
    else:
        print(f"Error accessing file: {file_url}")
        return 0
    
def calculate_readability(file_url):
    """ Calculate the readability score of a text. """
    response = requests.get(file_url)
    if response.status_code == 200:
        content = response.text
        return textstatistics().flesch_reading_ease(content)

    else:
        print(f"Error accessing file: {file_url}")
        return 0

def extract_eip_number(filename):
    """
    Extract the EIP number from the filename.
    """
    parts = filename.split('-')
    if parts[1].replace('.md','').isdigit():
        return int(parts[1].replace('.md',''))
    return None

def main():
    eips = []
    response = requests.get(GITHUB_REPO_EIPS_API_URL)
    if response.status_code == 200:
        repo_contents = response.json()
        for file_info in repo_contents:
            if file_info['type'] == 'file':
                eip_number = extract_eip_number(file_info['name'])
                word_count = count_words_in_file(file_info['download_url'])
                readability = calculate_readability(file_info['download_url'])
                eips.append({'EIP Number': eip_number, 'Word Count_EIP': word_count, 'Readability_EIP': readability})
    else:
        print("Error accessing GitHub API.")
    
    # Create a DataFrame
    df = pd.DataFrame(eips)
    print(df)

    eips = []
    response = requests.get(GITHUB_REPO_ERCS_API_URL)
    if response.status_code == 200:
        repo_contents = response.json()
        for file_info in repo_contents:
            if file_info['type'] == 'file':
                eip_number = extract_eip_number(file_info['name'])
                word_count = count_words_in_file(file_info['download_url'])
                readability = calculate_readability(file_info['download_url'])
                eips.append({'EIP Number': eip_number, 'Word Count_ERC': word_count, 'Readability_ERC': readability})
    else:
        print("Error accessing GitHub API.")
    
    # Create a DataFrame
    df2 = pd.DataFrame(eips)
    print(df2)

    return pd.merge(df,df2, on = 'EIP Number', how = 'outer')

df = main()

df['Word Count_EIP']=df['Word Count_EIP'].fillna(0)
df['Word Count_ERC']=df['Word Count_ERC'].fillna(0)

df['Word Count'] = df[['Word Count_EIP', 'Word Count_ERC']].max(axis=1, skipna = True)
df.loc[(df['Word Count_EIP']> df['Word Count_ERC'] ),'Readability'] = df['Readability_EIP']
df.loc[df['Word Count_EIP']<= df['Word Count_ERC'],'Readability'] = df['Readability_ERC']
  
       
       
df[['EIP Number','Word Count','Readability']].to_csv('Data\Raw Data\eip_word_count.csv', index=False)