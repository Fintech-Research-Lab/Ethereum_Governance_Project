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

# get startdates of all eips

os.chdir ("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")
cs = pd.read_stata("Ethereum_Cross-sectional_Data.dta")
cs_dates = cs[['eip_number','sdate','edate']]
meta = [606,607,608,609,779,1013,1679,1716,1716,2387]
end_date = ["2016-02-29","2016-11-18","2016-10-13","2017-10-12",""]
cs_dates = cs_dates[cs_dates['eip_number'].isin(meta)]
cs_dates['sdate'] = pd.to_datetime(cs_dates['sdate']).dt.strftime('%Y-%m-%d')
cs_dates['edate'] = pd.to_datetime(cs_dates['edate']).dt.strftime('%Y-%m-%d')

symbols = ['SPY','ETH-USD']
data = {}
start_date = pd.to_datetime(cs_dates['sdate']).min()-timedelta(days = 40)

for symbol in symbols:
    data[symbol] = yf.Ticker(symbol).history(start=start_date, end=cs['sdate'].max(), auto_adjust=True)
    
for symbol in symbols:
    data[symbol] = data[symbol]['Close']

eth = pd.DataFrame(data['ETH-USD'])
eth['date'] = eth.index
eth['date'] = eth['date'].dt.strftime('%Y-%m-%d')
spy = pd.DataFrame(data['SPY']) 
spy['date'] = spy.index
spy['date'] = spy['date'].dt.strftime('%Y-%m-%d')  

dat = pd.merge(eth,spy, on = 'date', how = 'inner')
dat = dat.rename(columns = {'Close_x' : 'eth_price', 'Close_y':'spy_price'})

# calculate returns

dat = dat.sort_values('date')
dat[['eth_ret', 'spy_ret']] = dat[['eth_price', 'spy_price']].apply(lambda x: x.pct_change())
dat['eth_cumulative'] = (1 + dat['eth_ret']).cumprod() - 1
dat['spy_cumulative'] = (1 + dat['spy_ret']).cumprod() - 1

# create abnormal return

dat['AR'] = dat['eth_cumulative'] - dat['spy_cumulative']


# create markers 

for eip in cs_dates['eip_number']:
    dat[f'{eip}_marker'] = None

emarker = pd.DataFrame()   
for eip in cs_dates['eip_number']:
        dat[f'{eip}_emarker'] = None

    
# create event dates
dates = pd.to_datetime(dat['date'])
dates_arrays = dates.values
event_dates = pd.to_datetime(cs_dates['sdate'])
end_dates = pd.to_datetime(cs_dates['edate'])
end_dates = end_dates[pd.notnull(end_dates)]
event_dates_arrays = event_dates.values
end_dates_arrays = end_dates.values

# create differences in days
day_differences = np.subtract.outer(dates_arrays, event_dates_arrays)
day_differences = (day_differences / np.timedelta64(1, 'D')).astype(int)

# create end day differences
eday_differences = np.subtract.outer(dates_arrays, end_dates_arrays)
eday_differences = (eday_differences / np.timedelta64(1, 'D')).astype(int)

# create marker
mark = (day_differences >= -40) & (day_differences <= 10)
emark = (eday_differences >= -40) & (eday_differences <= 10)
dat.iloc[:,8:] = np.where(emark, eday_differences, np.nan)

# generate return matrix from -40 to +10

ret = pd.DataFrame()
for i in range(-40,11):
    condition = (dat.iloc[:, 8:] == i)
    #ret_mark = np.where(dat.iloc[:,8:] == i,1,0)
    #ret[f'AR{i}'] = dat.loc[np.where(np.any(condition, axis = 1))[0],'AR']
    ret[f'AR{i}'] = np.where(condition.any(axis=1), dat['AR'], np.nan)
    #ret[f'AR{i}'] = (condition).astype(int).any(axis=1).astype(int)
    


# take average returns for all eips

mean_ret = pd.DataFrame(ret.mean()).transpose()
lower_5 = ret.quantile(0.05)
upper_95 = ret.quantile(0.95)

# plot

row = mean_ret.iloc[0]
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
    