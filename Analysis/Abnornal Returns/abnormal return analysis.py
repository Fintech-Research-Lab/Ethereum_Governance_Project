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


# get eth price data

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")

# convert eth hourly prices to daily price based on 4:00 PM EST close
eth_prices = pd.read_csv("eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')
eod_eth= eth_prices[eth_prices['START'].dt.hour == 15]
np.where(pd.isnull(eod_eth['CLOSE'])) # no missing close price
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
    
# create event_dates  from forks

fork = pd.read_csv("Fork_announcement.csv")
ann_dates = fork['ann_date']


# merge
dat = pd.merge(eth,spy, on = 'date', how = 'inner')
dat = dat.rename(columns = {'close_x' : 'eth_price', 'close_y':'spy_price'})


# calculate returns

dat = dat.sort_values('date')
dat[['eth_ret', 'spy_ret']] = dat[['eth_price', 'spy_price']].apply(lambda x: x.pct_change())

# create abnormal return

dat['AR'] = dat['eth_ret'] - dat['spy_ret']



    
# generate differences in days from the announcement days

dates = dat['date']
dates = pd.to_datetime(dates)
dates = dates.sort_values()
dates_arrays = dates.values

ann_dates = pd.to_datetime(ann_dates)  # Convert 'ann_dates' to datetime
ann_dates = ann_dates.sort_values()

# Find indices in dates where ann_dates and dates are common
indices = np.full((len(ann_dates),), fill_value=np.nan, dtype=np.float64)
common_dates_mask = np.isin(ann_dates, dates)
indices[common_dates_mask] = np.searchsorted(dates, ann_dates[common_dates_mask], side='right')


# Create a 1877x 15 matrix of days difference between announcement date and trading dates
day_differences = np.arange(len(dates)) - indices[:, None]
day_differences = day_differences.reshape(len(ann_dates), -1).T

# insert date difference markers in dat

# create columns ind dat to place -40 to 10 markers on dates 
for frk in fork['release']:
    dat[f'{frk}_marker'] = None

# filter day differences between 40 and 10 and then add them into dat at the right place
mark = (day_differences > -41) & (day_differences < 11) 
columns_to_update = dat.columns[6:] 
dat[columns_to_update] = np.where(mark, day_differences, np.nan)

# generate return matrix from -40 to +10 for all forks
ret = pd.DataFrame()
for frk in dat.columns[6:]:
    for i in range(-40,11):
        condition = (dat[frk] == i)
        ret[f'AR{i}_{frk}'] = np.where(condition, dat['AR'], np.nan)

             

# take average returns for all forks

mean_ret = pd.DataFrame(ret.mean()).transpose()
cumulative_returns = (1+mean_ret.iloc[0,:]).cumprod() - 1
mean_ret = mean_ret.append(cumulative_returns, ignore_index=True)
# remove null
mean_ret_notnull = mean_ret.iloc[:2].dropna(how = 'all', axis = 1)


# Assuming 'frk' contains at least 16 items for the 4x4 grid
frk = fork['release'][1:]

fig, axs = plt.subplots(4, 4, figsize=(15, 15))  # Creating a 4x4 grid of subplots

for i, frk_word in enumerate(frk):
    row = i // 4  # Row index for subplot
    col = i % 4   # Column index for subplot

    selected_columns = [col for col in mean_ret_notnull.columns if f'_{frk_word}_' in col]
    
    if not selected_columns:  # Skip if selected_columns is empty
        continue
    
    row_data = mean_ret_notnull.iloc[1][selected_columns]
    
    x_axis_values = []
    for column in selected_columns:
        numeric_part = ''.join(filter(lambda x: x.isdigit() or x == '-', column.split('_')[0]))
        x_axis_values.append(numeric_part)
    
    # Plotting in each subplot
    axs[row, col].plot(x_axis_values, row_data, marker='o', label="Mean")
    axs[row, col].set_xlabel('Days to Release Date')
    axs[row, col].set_ylabel('Abnormal Returns')
    axs[row, col].set_title(f"Abnormal Returns - {frk_word}")

    if '0' in x_axis_values:
        zero_index = x_axis_values.index('0')
        axs[row, col].axvline(x=zero_index, color='red', linestyle='--', label='x=0')

plt.tight_layout()  # Automatically adjust subplot parameters to give specified padding
plt.show()





    
    