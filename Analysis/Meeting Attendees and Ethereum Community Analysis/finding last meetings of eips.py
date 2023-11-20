# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 09:11:23 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np

# get meeting dates
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
meeting = pd.read_csv("Analysis/Meeting Dates Volatility Analysis/calls_updated_standardized.csv")
eip = meeting.loc[:,['Date','EIP','Meeting']]
eip_list = eip['EIP'].str.split(',')
eip_list = eip_list.explode()
eip_list = eip_list.str.replace("EIP-","")
eip_list = eip_list.dropna().astype(int)
eip = pd.merge(eip[['Date','Meeting']],eip_list,left_index = True, right_index = True, how = 'outer',indicator = "True")
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-sectional_Data.dta")
final = cs.loc[cs['status'] == "Final"]
final = final[['eip_number','status','edate']]
eip = pd.merge(eip,final,left_on = "EIP", right_on = 'eip_number', how = 'inner')
eip['Date'] = pd.to_datetime(eip['Date'])  # Ensure 'Date' is in datetime format
eip_max_date = eip.loc[eip.groupby('eip_number')['Date'].idxmax()]



