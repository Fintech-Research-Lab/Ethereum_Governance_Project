# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 16:38:09 2023

@author: khojama
"""

import pandas as pd
import os as os
import numpy as np

# get meeting dates
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Dates Volatility Analysis/")
meeting = pd.read_csv("calls_updated_standardized.csv")
meeting_dates = meeting['Date']
meeting_dates['Date'].replace('Missing', pd.NaT, inplace=True)
eth['Meeting_Dates'] = pd.to_datetime(eth['']).dt.strftime('%Y-%m-%d')


# get Eth prices and generate daily hourly volatility
os.chdir ("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Abnormal Returns/")
eth_prices = pd.read_csv("eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')
eth_vols = eth_prices.groupby('START_DATE')['CLOSE'].std()
eth_vols = pd.DataFrame(eth_vols)
eth_vols['Date'] = eth_vols.index


eth = pd.merge(eth_vols,meeting_dates, left_on = "START_DATE", right_on = 'Date', how = 'outer', indicator = True)
eth = eth.rename(columns = {'Date_x' : 'Date','Date_y':'Meeting_Dates', 'CLOSE':'Hourly_vol'})
eth['Date'] = pd.to_datetime(eth['Date']).dt.strftime('%Y-%m-%d')


eth = eth.sort_values(["Date","Meeting_Dates"])