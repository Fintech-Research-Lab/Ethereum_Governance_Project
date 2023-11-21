# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 16:38:09 2023

@author: khojama
"""

import pandas as pd
import os as os
import numpy as np

# get meeting dates
#os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/")
os.chdir("C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/")

meeting = pd.read_csv("Analysis/Meeting Dates Volatility Analysis/calls_updated_standardized.csv")
meeting_dates = pd.DataFrame(meeting['Date'], columns = ['Date'])
meeting_dates['Date'].replace('Missing', pd.NaT, inplace=True)
meeting_dates['Date'] = pd.to_datetime(meeting_dates['Date']).dt.strftime('%Y-%m-%d')
meeting_dates['begin'] = pd.to_datetime(meeting_dates['Date']) + pd.to_timedelta('14h')
meeting_dates['end'] = pd.to_datetime(meeting_dates['Date']) + pd.to_timedelta("15h")
meeting_dates['begin'] = meeting_dates['begin'].dt.tz_localize('UTC')
meeting_dates['end'] = meeting_dates['end'].dt.tz_localize('UTC')


# get Eth prices and generate daily hourly volatility
eth_prices = pd.read_csv("Data/Raw Data/eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START'], format='%Y-%m-%d %H:%M:%S') 
# Fix missing dates 
maxp_eth = max(eth_prices['START']).to_pydatetime()
minp_eth = min(eth_prices['START']).to_pydatetime()
eth_prices2 = pd.DataFrame(pd.date_range(start=minp_eth, end=maxp_eth, freq = 'H', name = 'START'))
eth_prices2 = pd.merge(eth_prices2,eth_prices, on = 'START', how = 'left')
eth_prices = eth_prices2.ffill()
eth_prices = eth_prices.sort_values('START')
eth_prices['return'] = eth_prices['CLOSE'].pct_change()
eth_prices['vol_rol'] = eth_prices['return'].rolling(12).std()
eth_prices['Meeting'] = np.where(eth_prices['START'].isin(meeting_dates['begin']),1,0)
eth_prices['Meeting'] = eth_prices['Meeting'] + np.where(eth_prices['START'].isin(meeting_dates['end']),1,0)

eth_prices.to_csv("Analysis/Meeting Dates Volatility Analysis/eth_vols2.csv")