import requests
from bs4 import BeautifulSoup
from lxml import html
from database import insert_protocol

# Website is not really scrapable due to JIT loading, had to do it step by step with this script
# All scraped data is loaded into a database, export of DB is attached


def extract_with_xpath(source, xpath_query):
    tree = html.fromstring(source)
    results = tree.xpath(xpath_query)

    for result in results:
        href = result.get('href')
        slug = href.split('/')[-1]
        if slug is not None:
            return slug


with open('source.html', 'r') as file:
    source = file.read()


for i in range(1, 1000):
    xpath = f'div[2]/div[{i}]/div[1]/span/span[2]/a'
    slug = extract_with_xpath(source, xpath)
    if slug is None:
        break
    print(slug)
    insert_protocol('band', slug)
