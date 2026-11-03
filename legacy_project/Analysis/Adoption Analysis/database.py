from pymongo import MongoClient
from llama_api import query_tvl

# A local database is used to prevent re-querying the API and to ensure uniqueness of oracle <-> protocol links

client = MongoClient('localhost', 27017)
db = client['eth']


def get_tvl(protocol_slug):
    """ Read from database if possible, otherwise query API and write to database """
    collection = db['defillama']
    tvl = collection.find_one({'slug': protocol_slug})
    if tvl is None:
        tvl = query_tvl(protocol_slug)
        data = {
            "slug": protocol_slug,
            "tvl": tvl
        }
        collection.insert_one(data)
    else:
        # print('loaded')
        tvl = tvl['tvl']
    return tvl


def insert_protocol(oracle, protocol):
    collection = db['oracle_protocols']
    data = {
        "oracle": oracle,
        "protocol": protocol
    }
    criteria = {"oracle": data["oracle"], "protocol": data["protocol"]}

    # upsert to ensure uniqueness
    collection.update_one(criteria, {"$set": data}, upsert=True)


if __name__ == '__main__':
    # Example usage
    insert_protocol('chainlink', 'aave-v3')
