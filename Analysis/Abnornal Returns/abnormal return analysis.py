# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 13:41:38 2023

@author: moazz
"""

import pandas as pd
import os as os
import yfinance as yf
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
from pytz import timezone

# get startdates of all eips

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")

# convert eth hourly prices to daily price based on 4:00 PM EST close
eth_prices = pd.read_csv("eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')
eod_eth= eth_prices[eth_prices['START'].dt.hour == 16]
eod_eth = eod_eth.sort_values('START')
eod_eth = eod_eth.rename(columns = {'START':"date",'CLOSE':'close'})
eth = eod_eth[['date','close']]
eth['date'] = eth['date'].dt.strftime('%Y-%m-%d')



# get spy data from yahoo finance

spy = pd.DataFrame()
spy = yf.Ticker('spy').history(start=eth['date'].min(), end=eth['date'].max(), auto_adjust=True)
spy['date'] = spy.index
spy = spy[['date','Close']]
spy['date'] = pd.to_datetime(spy['date']).dt.strftime('%Y-%m-%d')
spy = spy.rename(columns = {'Close':'close'})
    
# create event_dates

fork = pd.read_csv("Fork_announcement.csv")
ann_dates = fork['ann_date']
ann_dates = pd.to_datetime(ann_dates)  # Convert 'ann_dates' to datetime


# merge
dat = pd.merge(eth,spy, on = 'date', how = 'inner')
dat = dat.rename(columns = {'close_x' : 'eth_price', 'close_y':'spy_price'})


# calculate returns

dat = dat.sort_values('date')
dat[['eth_ret', 'spy_ret']] = dat[['eth_price', 'spy_price']].apply(lambda x: x.pct_change())

# create abnormal return

dat['AR'] = dat['eth_ret'] - dat['spy_ret']


# create markers 

for fork in fork['release']:
    dat[f'{fork}_marker'] = None

    
# create event dates
dates = dat['date']
dates = pd.to_datetime(dates)
dates_arrays = dates.values
ann_dates_arrays = ann_dates.values

# create differences in days
day_differences = np.subtract.outer(dates_arrays, ann_dates_arrays)
day_differences = (day_differences / np.timedelta64(1, 'D')).astype(int)


# create marker
day_differences_int = day_differences.astype(int)
mark = (day_differences_int >= -40) & (day_differences_int <= 10)
columns_to_update = dat.columns[6:]
dat[columns_to_update] = np.where(mark, day_differences_int, np.nan)

# generate return matrix from -40 to +10

ret = pd.DataFrame()
for i in range(-40,11):
    condition = (dat.iloc[:, 6:] == i)
    #ret_mark = np.where(dat.iloc[:,8:] == i,1,0)
    #ret[f'AR{i}'] = dat.loc[np.where(np.any(condition, axis = 1))[0],'AR']
    ret[f'AR{i}'] = np.where(condition.any(axis=1), dat['AR'], np.nan)
    #ret[f'AR{i}'] = (condition).astype(int).any(axis=1).astype(int)
    


# take average returns for all eips

mean_ret = pd.DataFrame(ret.mean()).transpose()
cumulative_returns = mean_ret.iloc[0,:].cumsum()
mean_ret = mean_ret.append(cumulative_returns, ignore_index=True)

# plot

row = mean_ret.iloc[1]
plt.plot(row, marker = 'o', label = "Mean")
#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.xlabel('Days to Start Date')
plt.ylabel('Abnormal Returns')
plt.title("Abnormal Returns Start Dates")
labels = [column.replace('AR','') for column in mean_ret.columns]
plt.xticks(range(len(labels)), labels, rotation=0, fontsize = 4)
plt.axvline(x=mean_ret.columns.get_loc('AR0'), color='red', linestyle='--', label='Start Date')
plt.show()
    