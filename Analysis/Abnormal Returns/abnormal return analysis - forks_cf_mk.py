# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 13:41:38 2023

@author: moazz
"""

import pandas as pd
import os as os
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt


###############################################################################
# ETH PRICES
# get eth price data

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
# EVENT LIST

# create event_dates from finalized eips
fork = pd.read_csv("Data/Raw Data/Fork_announcement.csv", encoding = 'latin1')
fork['ann_date'] = pd.to_datetime(fork['ann_date']).dt.tz_localize('US/Eastern')  + pd.DateOffset(hours=15)
fork.sort_values('ann_date', inplace = True)
# adjust event dates if they occur during non trading days. 
fork = pd.merge_asof(left = fork, right = dat, left_on = 'ann_date', right_on = 'date', direction = 'backward')
fork = fork.loc[fork['date'] > minp_eth][['release', 'ann_date', 'date']].dropna().reset_index(drop = True)
    
# generate a dataframe with -40 to +10 days around each announcement

df = pd.DataFrame()
for i in range(len(fork.index)):
    dat_temp = dat.dropna()
    dat_temp.sort_values('date', inplace = True)
    dat_temp.reset_index(drop = True, inplace = True) 
    dat_temp['N'] =  dat_temp.index
    dat_temp = dat_temp.merge(fork[fork.index == i], on = 'date', how = 'left')
    dat_temp['diff'] = (dat_temp['N'] - dat_temp.loc[pd.notnull(dat_temp['release']) , 'N'].values[0])
    dat_temp['release'] = fork.iloc[i]['release']
    dat_temp = dat_temp[(dat_temp['diff']>-41) & (dat_temp['diff']<11)]
    dat_temp['CAR'] = (dat_temp['AR']+1).cumprod()-1
    dat_temp['CAR_btc'] = (dat_temp['AR_btc']+1).cumprod()-1
    df = df.append(dat_temp)

df.sort_values(['release','diff'])
df['diff'].value_counts()


###############################################################################
# PLOT

#SPY BENCHMARK
plt.figure()
df.groupby('diff')['CAR'].mean().plot()

#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.axvline(x=0, color='red', linestyle='--', label='Final Date')
plt.title("Cumulative Abnormal Returns (SPY) by Fork Release")
plt.xlabel('Days to Finalization Announcement Date')
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





