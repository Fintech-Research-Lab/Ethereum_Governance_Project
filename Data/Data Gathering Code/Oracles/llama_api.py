import requests


def query_api(slug):
    url = f"https://api.llama.fi/protocol/{slug}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"


def query_tvl(slug):
    result = query_api(slug)
    try:
        ethereum_tvls = result['chainTvls']['Ethereum']['tvl']
        latest_eth_tvl = ethereum_tvls[-1]['totalLiquidityUSD']
    except:
        # Usually when the protocol is not on Ethereum
        return 0
    return latest_eth_tvl


if __name__ == "__main__":
    # Example usage
    slug = "aave"
    latest_eth_tvl = query_tvl(slug)
    print(latest_eth_tvl)
