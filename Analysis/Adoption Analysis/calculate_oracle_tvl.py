from pymongo import MongoClient
import pandas as pd

from database import get_tvl

client = MongoClient('localhost', 27017)
db = client['eth']
collection = db['oracle_protocols']

projection = {'_id': False}
cursor = collection.find({}, projection)

documents = list(cursor)
df = pd.DataFrame(documents)
oracles = df['oracle'].unique().tolist()


def add_tvl(row):
    slug = row['protocol']
    return get_tvl(slug)


# Add tvl column by looking at DB or API
df = df.assign(tvl=df.apply(add_tvl, axis=1))

df.to_csv('oracle_eth_tvl.csv')

aggregated = df.groupby('oracle').apply(lambda x: pd.Series({
    'tvl': x['tvl'].sum(),
    'num_protocols_with_tvl_gt_0': (x['tvl'] > 0).sum()
})).reset_index()
aggregated['num_protocols_with_tvl_gt_0'] = aggregated['num_protocols_with_tvl_gt_0'].astype(int)
aggregated = aggregated.sort_values(by='tvl', ascending=False).reset_index(drop=True)

aggregated.to_csv('oracle_eth_tvl_aggregated.csv')
