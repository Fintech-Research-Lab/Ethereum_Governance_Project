python:
os.chdir("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Meeting Dates Volatility Analysis/")
meeting = pd.read_csv("calls_updated_standardized.csv")
meeting_dates = pd.DataFrame(meeting['Date'], columns = ['Date'])
meeting_dates['Date'].replace('Missing', pd.NaT, inplace=True)
meeting_dates['Date'] = pd.to_datetime(meeting_dates['Date']).dt.strftime('%Y-%m-%d')


# get Eth prices and generate daily hourly volatility
os.chdir ("C:/Users/moazz/Box/Fintech Research Lab/Ethereum_Governance_Project/Analysis/Abnormal Returns/")
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

eth_vols.to_csv("eth_vols.csv")
end

cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum_Governance_Project\Analysis\Meeting Dates Volatility Analysis\"
clear
import delimited "eth_vols.csv"
rename date date1
gen date = date(date1,"YMD")
format date %td
gen dow = dow(date)
gen month = month(date)
gen year = year(date)

reg intra_day_vol meeting i.dow i.month i.year, robust