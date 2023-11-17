# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 16:38:09 2023

@author: khojama
"""

import pandas as pd
import os as os
import numpy as np

# get meeting dates
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
meeting = pd.read_csv("/Analysis/Meeting Dates Volatility Analysis/calls_updated_standardized.csv")
meeting_dates = pd.DataFrame(meeting['Date'], columns = ['Date'])
meeting_dates['Date'].replace('Missing', pd.NaT, inplace=True)
meeting_dates['Date'] = pd.to_datetime(meeting_dates['Date']).dt.strftime('%Y-%m-%d')


# get Eth prices and generate daily hourly volatility
os.chdir ("Data/Raw Data/")
eth_prices = pd.read_csv("eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')
eth_prices = eth_prices.sort_values('START')
eth_prices['return'] = eth_prices['CLOSE'].pct_change()
eth_vols = eth_prices.groupby('START_DATE')['return'].std()
eth_vols = pd.DataFrame(eth_vols)
eth_vols['Date'] = eth_vols.index
eth_vols['Date'] = pd.to_datetime(eth_vols['Date']).dt.strftime('%Y-%m-%d')
eth_vols = eth_vols.rename(columns = {'CLOSE':'Intra_day_vol'})

eth_vols['Meeting'] = np.where(eth_vols['Date'].isin(meeting_dates['Date']),1,0)

indices = np.where(~meeting_dates['Date'].isin(eth_vols['Date']))[0]
meetings_not_covered = meeting_dates.loc[indices,'Date']

eth_vols.to_csv("eth_vols.csv")