# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 09:11:23 2023

@author: moazz
"""

import pandas as pd
import os as os
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# EVENT DATES get eip list and meeting dates of last time eip was discussed #####################################
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
final = final[['eip_number','status','edate','Category']]
final = final[(final['Category'] != "Informational") & (final['Category'] != "Meta")]

eip = pd.merge(eip,final,left_on = "EIP", right_on = 'eip_number', how = 'inner')
eip['Date'] = pd.to_datetime(eip['Date'])  # Ensure 'Date' is in datetime format
eip_max_date = eip.loc[eip.groupby('eip_number')['Date'].idxmax()]


## GET PRICES

os.chdir('C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/')
# os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/')

          

# convert eth hourly prices to daily price based on 4:00 PM EST close
eth_prices = pd.read_csv("Data/Raw Data/eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')

# Fix missing dates 
maxp_eth = max(eth_prices['START']).to_pydatetime()
minp_eth = min(eth_prices['START']).to_pydatetime()
eth_prices2 = pd.DataFrame(pd.date_range(start=minp_eth, end=maxp_eth, freq = 'H', name = 'START'))
eth_prices2 = pd.merge(eth_prices2,eth_prices, on = 'START', how = 'left')
eth_prices2 = eth_prices2.ffill()

# Keep time = 4pm ET close
eod_eth= eth_prices2[eth_prices2['START'].dt.hour == 15]  # this is because the start is the start date of the period 3-4pm. Hence close price of 3pm period is 4pm. 
np.where(pd.isnull(eod_eth['CLOSE'])) # no missing close price
eod_eth = eod_eth.sort_values('START')
eod_eth = eod_eth.rename(columns = {'START':"date",'CLOSE':'eth_close'})
eth = eod_eth[['date','eth_close']]


###############################################################################
# BTC PRICES
# get btc price data

# convert btc hourly prices to daily price based on 4:00 PM EST close
btc_prices = pd.read_csv("Data/Raw Data/btc_prices.csv")
btc_prices['START'] = pd.to_datetime(btc_prices['START']).dt.tz_convert('US/Eastern')

# Fix missing dates 
maxp_btc = max(btc_prices['START']).to_pydatetime()
minp_btc = min(btc_prices['START']).to_pydatetime()
btc_prices2 = pd.DataFrame(pd.date_range(start=minp_btc, end=maxp_btc, freq = 'H', name = 'START'))
btc_prices2 = pd.merge(btc_prices2,btc_prices, on = 'START', how = 'left')
btc_prices2 = btc_prices2.ffill()

# Keep time = 4pm ET close
eod_btc= btc_prices2[btc_prices2['START'].dt.hour == 15]  # this is because the start is the start date of the period 3-4pm. Hence close price of 3pm period is 4pm. 
np.where(pd.isnull(eod_btc['CLOSE'])) # no missing close price
eod_btc = eod_btc.sort_values('START')
eod_btc = eod_btc.rename(columns = {'START':"date",'CLOSE':'btc_close'})
btc = eod_btc[['date','btc_close']]

###############################################################################
# SPY PRICES
# get spy data from yahoo finance

spy = pd.DataFrame()
spy = yf.Ticker('spy').history(start=minp_eth, end=maxp_eth, auto_adjust=True)
spy['date'] = pd.to_datetime(spy.index).tz_convert('US/Eastern')
spy['date'] = spy['date'] + pd.DateOffset(hours=15)
spy = spy[['date','Close']]
spy = spy.rename(columns = {'Close':'spy_close'})

# merge
dat = pd.merge(spy,eth, on = 'date', how = 'left')
dat = pd.merge(dat,btc, on = 'date', how = 'left')

np.where(pd.isnull(dat['spy_close'])) # no missing close price
np.where(pd.isnull(dat['eth_close'])) # no missing close price
np.where(pd.isnull(dat['btc_close'])) # no missing close price

# calculate returns
dat = dat.sort_values('date')
dat[['eth_ret', 'spy_ret', 'btc_ret']] = dat[['eth_close', 'spy_close', 'btc_close']].apply(lambda x: x.pct_change())

# create abnormal return
dat['AR'] = dat['eth_ret'] - dat['spy_ret']
dat['AR_btc'] = dat['eth_ret'] - dat['btc_ret']


###############################################################################
# create event cumulative returns


# adjust event dates if they occur during non trading days.
eip_max_date['Date'] = pd.to_datetime(eip_max_date['Date']).dt.tz_localize('US/Eastern')  + pd.DateOffset(hours=15)
eip_max_date.sort_values('Date', inplace = True)

 
eip_meeting = pd.merge_asof(left = eip_max_date, right = dat, left_on = 'Date', right_on = 'date', direction = 'backward')
eip_meeting = eip_meeting.loc[eip_meeting['Date'] > minp_eth][['Date', 'EIP', 'Meeting','date','Category']].dropna().reset_index(drop = True)
    
# generate a dataframe with -40 to +10 days around each announcement

df = pd.DataFrame()
for i in range(len(eip_meeting.index)):
    dat_temp = dat.dropna()
    dat_temp.sort_values('date', inplace = True)
    dat_temp.reset_index(drop = True, inplace = True) 
    dat_temp['N'] =  dat_temp.index
    dat_temp = dat_temp.merge(eip_meeting[eip_meeting.index == i], on = 'date', how = 'left')
    dat_temp['diff'] = (dat_temp['N'] - dat_temp.loc[pd.notnull(dat_temp['EIP']) , 'N'].values[0])
    dat_temp['EIP'] = eip_meeting.iloc[i]['EIP']
    dat_temp['Category'] = eip_meeting.iloc[i]['Category']
    dat_temp = dat_temp[(dat_temp['diff']>-41) & (dat_temp['diff']<11)]
    dat_temp['CAR'] = (dat_temp['AR']+1).cumprod()-1
    dat_temp['CAR_btc'] = (dat_temp['AR_btc']+1).cumprod()-1
    df = df.append(dat_temp)

df.sort_values(['EIP','diff'])
df['diff'].value_counts()

###############################################################################
# PLOT

# Filter plots by category



#SPY BENCHMARK
plt.figure()
#df.groupby('diff')['CAR'].mean().plot()
df[(df['Category'] == "Core")|(df['Category'] == "Networking")].groupby('diff')['CAR'].mean().plot()

#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.axvline(x=0, color='red', linestyle='--', label='Final Date')
plt.title("Cumulative Abnormal Returns (SPY) by Last Meeting when Core/Networking EIPs were Discussed")
plt.xlabel('Days to Finalization Announcement Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.show()

#BTC BENCHMARK
plt.figure()
#df.groupby('diff')['CAR_btc'].mean().plot()
df[(df['Category'] == "Core")|(df['Category'] == "Networking")].groupby('diff')['CAR_btc'].mean().plot()

#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.axvline(x=0, color='red', linestyle='--', label='Final Date')
plt.title("Cumulative Abnormal Returns (BTC) by last Meeting when Core/Networking EIPs were Discussed")
plt.xlabel('Days to Finalization Announcement Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.show()

