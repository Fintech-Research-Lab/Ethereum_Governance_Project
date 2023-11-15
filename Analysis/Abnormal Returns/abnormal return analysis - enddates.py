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


# get eth price data

os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Abnormal Returns/")

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

# Fix missing dates 

missing = spy[~spy['date'].isin(eth['date'])]
missing['date'] = pd.to_datetime(missing['date']).dt.strftime('%Y-%m-%d') 
eth_prices['START_DATE'] = pd.to_datetime(eth_prices['START_DATE']).dt.strftime('%Y-%m-%d') 
missing_dates_list = missing['date'].tolist()
eth_dates_list = eth_prices['START_DATE'].tolist()
fill = eth_prices[eth_prices['START_DATE'].isin(missing_dates_list)]
fill['START_DATE'] = pd.to_datetime(fill['START_DATE'])
fill = fill.sort_values('START')
close = fill[fill['START'].dt.hour < 13].groupby('START_DATE').agg({'START': 'last', 'CLOSE': 'last'}).reset_index()
close = close[['START_DATE','CLOSE']]
close = close.rename(columns = {'START_DATE' : 'date','CLOSE' : 'close'})
eth = eth.append(close)
eth['date'] = pd.to_datetime(eth['date']).dt.strftime('%Y-%m-%d')
eth = eth.sort_values('date')


# create event_dates  from finalized eips
os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Data/Raw Data/")
eip = pd.read_csv("finaleip_enddates.csv", encoding = 'latin1')
eip = eip[eip['Status']=='Final'][['Number','End']]
eip = eip.rename(columns = {'Number':'eip_number','End':'ann_date'})
ann_dates = eip['ann_date']


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
for e in eip['eip_number']:
    dat[f'{e}_marker'] = None

# filter day differences between 40 and 10 and then add them into dat at the right place
mark = (day_differences > -41) & (day_differences < 11) 
columns_to_update = dat.columns[6:] 
dat[columns_to_update] = np.where(mark, day_differences, np.nan)


# Use the following to plot aggregate mean cumulative returns plot of all finalized eips

ret = pd.DataFrame()
for i in range(-40,11):
    condition = dat.iloc[:,6:] == i
    ret[f'AR{i}'] = dat.loc[np.where(np.any(condition, axis = 1))[0],'AR']

mean_ret = pd.DataFrame(ret.mean()).transpose()  
cumulative_returns = (1+mean_ret.iloc[0,:]).cumprod() -1
mean_ret = mean_ret.append(cumulative_returns, ignore_index=True)

# plot for aggregate cumulative return

row = mean_ret.iloc[1]
plt.plot(row, marker = 'o', label = "Mean")
#plt.plot(lower_5, color = 'red', label = '5th Percentile CI')
#plt.plot(upper_95, color = 'red', label = '5th Percentile CI')
plt.xlabel('Days to Start Date')
plt.ylabel('Abnormal Returns')
plt.title("Abnormal Returns End Dates for All Finalized EIPs")
labels = [column.replace('AR','') for column in mean_ret.columns]
plt.xticks(range(len(labels)), labels, rotation=0, fontsize = 4)
plt.axvline(x=mean_ret.columns.get_loc('AR0'), color='red', linestyle='--', label='Start Date')
plt.show()




# generate abnormal return matrix from -40 to +10 for eips
ret = pd.DataFrame()
for e in dat.columns[6:]:
    conditions = [(dat[e] == i) for i in range(-40, 11)]
    columns = [f'AR{i}_{e}' for i in range(-40,11)]
    ret = pd.concat([ret, pd.DataFrame({col: np.where(cond, dat['AR'], np.nan) for col, cond in zip(columns, conditions)})], axis=1)

             

# take average abnormal returns for individual eips

mean_ret = pd.DataFrame(ret.mean()).transpose()


for e in eip['eip_number'][1:]:
    e_str = str(e)
    columns = mean_ret[mean_ret.columns[mean_ret.columns.astype(str).str.contains(e_str)]].iloc[0].dropna()
    columns = columns.index
    if not mean_ret.loc[0, columns].isnull().all():
        cumulative_returns = (1 + mean_ret.loc[0, columns]).cumprod() - 1
        mean_ret.loc[1, columns] = cumulative_returns.values



    
# remove null
mean_ret_notnull = mean_ret.iloc[:2].dropna(how = 'all', axis = 1)

# summary stats 
describe = mean_ret_notnull.iloc[1].filter(like="-40").describe()






## grid view


# Assuming len(eip['eip_number']) is the total number of elements
total_elements = len(eip['eip_number'])
elements_per_page = 16  # Adjust this based on the number of subplots you want per page

# Calculate the total number of pages needed
total_pages = math.ceil(total_elements / elements_per_page)

for page in range(total_pages):
    start_index = page * elements_per_page
    end_index = min((page + 1) * elements_per_page, total_elements)

    # Calculate the grid size for the current page
    grid_size = math.ceil(math.sqrt(end_index - start_index))

    fig, axs = plt.subplots(grid_size, grid_size, figsize=(15, 15))  # Creating a dynamically sized grid of subplots

    for i, e_word in enumerate(eip['eip_number'][start_index:end_index]):
        row = i // grid_size  # Row index for subplot
        col = i % grid_size   # Column index for subplot

        selected_columns = [col for col in mean_ret_notnull.columns if f'_{e_word}_' in col]

        if not selected_columns:  # Skip if selected_columns is empty
            continue

        row_data = mean_ret_notnull.iloc[1][selected_columns]

        x_axis_values = [int(''.join(filter(lambda x: x.isdigit() or x == '-', col.split('_')[0]))) for col in selected_columns]

        # Plotting in each subplot
        axs[row, col].plot(x_axis_values, row_data, marker='o', label="Mean")
        axs[row, col].set_xlabel('Days to Release Date')
        axs[row, col].set_ylabel('Abnormal Returns')
        axs[row, col].set_title(f"Abnormal Returns - {e_word}")

        if 0 in x_axis_values:
            zero_index = x_axis_values.index(0)
            axs[row, col].axvline(x=x_axis_values[zero_index], color='red', linestyle='--', label='x=0')

    plt.tight_layout()  # Automatically adjust subplot parameters to give specified padding
    plt.show()






