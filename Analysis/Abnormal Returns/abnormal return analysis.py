# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 13:41:38 2023

@author: moazz
"""

import pandas as pd
import os as os
import yfinance as yf
import numpy as np
import math
import matplotlib.pyplot as plt
from datetime import datetime 

###############################################################################
# ETH PRICES
# get eth price data

#os.chdir('C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/')
os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/')

          

# convert eth hourly prices to daily price based on 4:00 PM EST close
eth_prices = pd.read_csv("Analysis/Abnormal Returns/eth_prices.csv")
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
btc_prices = pd.read_csv("Analysis/Abnormal Returns/btc_prices.csv")
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
# EVENT LIST

# create event_dates and eip list for finalized eips
eip = pd.read_csv("Data/Raw Data/finaleip_enddates.csv", encoding = 'latin1')
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-sectional_Data.dta")
eip = pd.merge(eip,cs[['eip_number','Category']], left_on = 'Number', right_on = 'eip_number', how = 'inner')
eip = eip[eip['Status']=='Final'][['Number','End','Category']]
eip = eip.rename(columns = {'Number':'eip_number','End':'ann_date'})
eip['ann_date'] = pd.to_datetime(eip['ann_date']).dt.tz_localize('US/Eastern')  + pd.DateOffset(hours=15)
eip.sort_values('ann_date', inplace = True)
# adjust event dates if they occur during non trading days. 
eip = pd.merge_asof(left = eip, right = dat, left_on = 'ann_date', right_on = 'date', direction = 'backward')
eip = eip.loc[eip['date'] > minp_eth][['eip_number', 'ann_date', 'date','Category']].dropna().reset_index(drop = True)
eip = eip.rename(columns = {'eip_number' : "EIP"})

# create event_dates and fork list for implemented forks

fork = pd.read_csv("Data/Raw Data/Fork_announcement.csv", encoding = 'latin1')
fork['ann_date'] = pd.to_datetime(fork['ann_date']).dt.tz_localize('US/Eastern')  + pd.DateOffset(hours=15)
fork.sort_values('ann_date', inplace = True)
# adjust event dates if they occur during non trading days. 
fork = pd.merge_asof(left = fork, right = dat, left_on = 'ann_date', right_on = 'date', direction = 'backward')
fork = fork.rename(columns = {'date' : 'ann_date2'})

fork['block_date'] = pd.to_datetime(fork['block_date'], format='%b-%d-%Y %I:%M:%S %p +UTC').dt.tz_localize('UTC').dt.tz_convert('US/Eastern') 
fork.sort_values('block_date', inplace = True)
# adjust event dates if they occur during non trading days. 
fork = pd.merge_asof(left = fork, right = dat, left_on = 'block_date', right_on = 'date', direction = 'backward')
fork = fork.rename(columns = {'date' : 'block_date2'})
fork = fork.loc[fork['ann_date'] > minp_eth][['release', 'ann_date', 'block_date', 'ann_date2', 'block_date2']].dropna().reset_index(drop = True)

fork = fork.loc[~fork['release'].str.contains("Glacier", na=False)].reset_index(drop = True)

# generate event dates based on last meeting date when eip was discussed

# adjust event dates if they occur during non trading days.
meeting = pd.read_csv("Analysis/Meeting Dates Volatility Analysis/calls_updated_standardized.csv")
eip2 = meeting.loc[:,['Date','EIP','Meeting']]
eip_list = eip2['EIP'].str.split(',')
eip_list = eip_list.explode()
eip_list = eip_list.str.replace("EIP-","")
eip_list = eip_list.dropna().astype(int)
eip2 = pd.merge(eip2[['Date','Meeting']],eip_list,left_index = True, right_index = True, how = 'outer',indicator = "True")
cs = pd.read_stata("Data/Raw Data/Ethereum_Cross-sectional_Data.dta")
final = cs.loc[cs['status'] == "Final"]
final = final[['eip_number','status','edate','Category']]
final = final[(final['Category'] != "Informational") & (final['Category'] != "Meta")]
eip2 = pd.merge(eip2,final,left_on = "EIP", right_on = 'eip_number', how = 'inner')
eip2['Date'] = pd.to_datetime(eip2['Date'])  # Ensure 'Date' is in datetime format
eip_max_date = eip2.loc[eip2.groupby('eip_number')['Date'].idxmax()]
eip_max_date['Date'] = pd.to_datetime(eip_max_date['Date']).dt.tz_localize('US/Eastern')  + pd.DateOffset(hours=15)
eip_max_date.sort_values('Date', inplace = True)
eip_meeting = pd.merge_asof(left = eip_max_date, right = dat, left_on = 'Date', right_on = 'date', direction = 'backward')
eip_meeting = eip_meeting.loc[eip_meeting['Date'] > minp_eth][['Date', 'EIP', 'Meeting','date','Category']].dropna().reset_index(drop = True)


#################################################################################################################   
# generate a dataframe with -40 to +10 days around each announcement

# Use this code for eip and eip_meeting

# create event PICK ONE FOR THE ANALYSIS

#event = eip
event = eip_meeting
 
df = pd.DataFrame()
for i in range(len(event.index)):
    dat_temp = dat.dropna()
    dat_temp.sort_values('date', inplace = True)
    dat_temp.reset_index(drop = True, inplace = True) 
    dat_temp['N'] =  dat_temp.index
    dat_temp = dat_temp.merge(event[event.index == i], on = 'date', how = 'left')
    dat_temp['diff'] = (dat_temp['N'] - dat_temp.loc[dat_temp['EIP']>0 , 'N'].values[0])
    #dat_temp['diff'] = (dat_temp['N'] - dat_temp.loc[pd.notnull(dat_temp['release']) , 'N'].values[0])
    dat_temp['eip'] = event.iloc[i]['EIP'] # For EIP Finalization Dates
    dat_temp['Category'] = event.iloc[i]['Category'] # To Add Category
    dat_temp = dat_temp[(dat_temp['diff']>-61) & (dat_temp['diff']<61)]
    dat_temp['CAR'] = (dat_temp['AR']+1).cumprod()-1
    dat_temp['CAR_btc'] = (dat_temp['AR_btc']+1).cumprod()-1
    df = pd.concat([df,dat_temp], axis = 0)

df.sort_values(['eip','diff'])
df['diff'].value_counts()

###############################################################################
# PLOT for EIP and EIP_Meeting

#SPY BENCHMARK
fig, ax = plt.subplots(figsize=(8,6))

df1 = df[(df['Category'] == "Core")|(df['Category'] == "Networking")]
df1_grouped = df1.groupby('diff')['CAR'].mean().rename('mean')
df1_grouped = pd.concat([df1_grouped, (1.645 * df1.groupby('diff')['CAR'].std() / np.sqrt(  df1.groupby('diff')['CAR'].count())).rename('ci') ], axis = 1)
df1_grouped['ci_lower'] = df1_grouped['mean'] - df1_grouped['ci']
df1_grouped['ci_upper'] = df1_grouped['mean'] + df1_grouped['ci']

df1_grouped['mean'].plot(ax = ax)



x = df1_grouped.index
ax.plot(x, df1_grouped['mean'])
ax.fill_between(
    x, df1_grouped['ci_lower'], df1_grouped['ci_upper'], color='b', alpha=.15)
fig.autofmt_xdate(rotation=45)
plt.gca().yaxis.grid(True)
plt.axvline(x=0, color='red', linestyle='--', label='Final Discussion Date')
#plt.title("Cumulative Abnormal Returns (SPY) by Last AllDevCore Meeting Date of Core/Networking EIPs")
plt.xlabel('Days to AllDevCore Meeting Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.savefig('Analysis/Abnormal Returns/CAR_SPY.png', bbox_inches="tight")
plt.show()


#BTC BENCHMARK
fig, ax = plt.subplots(figsize=(8,6))

df1 = df[(df['Category'] == "Core")|(df['Category'] == "Networking")]
df1_grouped = df1.groupby('diff')['CAR_btc'].mean().rename('mean')
df1_grouped = pd.concat([df1_grouped, (1.645 * df1.groupby('diff')['CAR_btc'].std() / np.sqrt(  df1.groupby('diff')['CAR_btc'].count())).rename('ci') ], axis = 1)
df1_grouped['ci_lower'] = df1_grouped['mean'] - df1_grouped['ci']
df1_grouped['ci_upper'] = df1_grouped['mean'] + df1_grouped['ci']

df1_grouped['mean'].plot(ax = ax)



x = df1_grouped.index
ax.plot(x, df1_grouped['mean'])
ax.fill_between(
    x, df1_grouped['ci_lower'], df1_grouped['ci_upper'], color='b', alpha=.15)
fig.autofmt_xdate(rotation=45)
plt.gca().yaxis.grid(True)
plt.axvline(x=0, color='red', linestyle='--', label='Final Discussion Date')
#plt.title("Cumulative Abnormal Returns (SPY) by Last AllDevCore Meeting Date of Core/Networking EIPs")
plt.xlabel('Days to AllDevCore Meeting Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.savefig('Analysis/Abnormal Returns/CAR_BTC.png', bbox_inches="tight")
plt.show()


###############################################################################
# Use this code for FORK Analysis

df = pd.DataFrame()
for i in range(len(fork.index)):
    dat_temp = dat.dropna()
    dat_temp.sort_values('date', inplace = True)
    dat_temp.reset_index(drop = True, inplace = True) 
    dat_temp['N'] =  dat_temp.index
    dat_temp = dat_temp.merge(fork[fork.index == i], left_on = 'date', right_on = 'block_date2', how = 'left')
    dat_temp['diff'] = (dat_temp['N'] - dat_temp.loc[pd.notnull(dat_temp['release']) , 'N'].values[0])
    dat_temp['release'] = fork.iloc[i]['release']
    dat_temp = dat_temp[(dat_temp['diff']>-61) & (dat_temp['diff']<61)]
    dat_temp['CAR'] = (dat_temp['AR']+1).cumprod()-1
    dat_temp['CAR_btc'] = (dat_temp['AR_btc']+1).cumprod()-1
    df = pd.concat([df,dat_temp], axis = 0)

df.sort_values(['release','diff'])
df['diff'].value_counts()


# Plot for Fork Analysis


#SPY BENCHMARK
plt.figure()
df.groupby('diff')['CAR'].mean().plot()

#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.axvline(x=0, color='red', linestyle='--', label='Final Date')
plt.title("Cumulative Abnormal Returns (SPY) by Fork Release")
plt.xlabel('Days to Fork Announcement Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.show()


#BTC BENCHMARK
plt.figure()
df.groupby('diff')['CAR_btc'].mean().plot()

#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.axvline(x=0, color='red', linestyle='--', label='Final Date')
plt.title("Cumulative Abnormal Returns (BTC) by Fork Release")
plt.xlabel('Days to Finalization Announcement Date')
plt.ylabel('Cumulative Abnormal Returns')
plt.show()

