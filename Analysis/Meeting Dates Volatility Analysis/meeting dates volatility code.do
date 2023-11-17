python:

import pandas as pd
import os as os
import numpy as np

# get meeting dates
os.chdir("C:/Users/khojama/Box/Fintech Research Lab/Ethereum_Governance_Project/")
meeting = pd.read_csv("Analysis/Meeting Dates Volatility Analysis/calls_updated_standardized.csv")
meeting_dates = pd.DataFrame(meeting['Date'], columns = ['Date'])
meeting_dates['Date'].replace('Missing', pd.NaT, inplace=True)
meeting_dates['Date'] = pd.to_datetime(meeting_dates['Date']).dt.strftime('%Y-%m-%d')


# get Eth prices and generate daily hourly volatility
eth_prices = pd.read_csv("Data/Raw Data/eth_prices.csv")
eth_prices['START'] = pd.to_datetime(eth_prices['START']).dt.tz_convert('US/Eastern')
eth_prices = eth_prices.sort_values('START')
eth_prices['return'] = eth_prices['CLOSE'].pct_change()
eth_vols = eth_prices.groupby('START_DATE')['return'].std()
eth_vols = pd.DataFrame(eth_vols)
eth_vols['Date'] = eth_vols.index
eth_vols['Date'] = pd.to_datetime(eth_vols['Date']).dt.strftime('%Y-%m-%d')
eth_vols = eth_vols.rename(columns = {'return':'intra_day_vol'})

eth_vols['Meeting'] = np.where(eth_vols['Date'].isin(meeting_dates['Date']),1,0)

eth_vols.to_csv("Analysis/Meeting Dates Volatility Analysis/eth_vols.csv")
end

cd "C:\Users\khojama\Box\Fintech Research Lab\Ethereum_Governance_Project\Analysis\Meeting Dates Volatility Analysis\"
clear
import delimited "eth_vols.csv"
rename date date1
gen date = date(date1,"YMD")
format date %td
gen dow = dow(date)
gen month = month(date)
gen year = year(date)

erase "eth_vols.csv"

save "intraday volatility analysis.dta"

reg intra_day_vol meeting i.dow i.month i.year, robust