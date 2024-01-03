from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
import csv
from collections import Counter
import collections.abc
import os
from selenium.webdriver.chrome.service import Service
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

def get_text_or_na(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else 'N/A'

def scrape_and_write_data(urls, output_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(output_file, "w", encoding='utf-8', newline="") as file:
        writer_obj = csv.writer(file)
        header = ["Title", "Website", "Category", "Author", "Article Body", "Comments", "Comment Authors", "Replies", "Created at", "Views", "Users", "Likes", "Links"]
        writer_obj.writerow(header)

        for url in urls:
            driver.get(url)
            soup = BeautifulSoup(driver.page_source.encode('utf-8') , "html.parser")
            created = soup.find_all('li', attrs={'class':'created-at'})[0].select_one("span[class='relative-date']")['title']
            replies = int(soup.find_all('li', attrs={'class':'replies'})[0].select_one("span[class='number']").text.strip())
            views = int(soup.find_all('li', attrs={'class':'secondary views'})[0].find("span", {'class':'number heatmap-high', 'class':'number heatmap-low'})['title'])
            users = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary users'})[0], "span[class='number']"))
            likes = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary likes'})[0], "span[class='number']"))
            links = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary links'})[0], "span[class='number']"))
            title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
            category = get_text_or_na(soup, "span[itemprop='name']")
            username = get_text_or_na(soup, "span[itemprop='author']")
            article_body = get_text_or_na(soup, "div[itemprop='articleBody']")
            auth = {}
            comm = {}
            maxrep = replies + 2 
            for x in range(maxrep):
                driver.get(url+"/"+str(x))
                page= driver.page_source.encode('utf-8') 
                soup = BeautifulSoup(page , "html.parser")            
                comment_text = soup.find_all("div", itemprop="text")[0:]
                for comment in comment_text:
                   comm.update({str(comment):x})  
                
                comment_authors = soup.find_all("span", itemprop="author")[0:]
                comment_authors2 = soup.find_all("div", {'id': True, 'class':'topic-body crawler-post'} )[0:]
                comment_authors3 = soup.find_all('article', {'aria-label':True})[0:]
                
                list_of_authors = [author.find('span', itemprop="name").text.strip() for author in comment_authors]
                list_of_posts = [int(author['id'][author['id'].find('post_')+5:]) for author in comment_authors2]
                
                list_of_authors3 = [author['aria-label'][author['aria-label'].find('@')+1:]   for author in comment_authors3]
                list_of_posts3 = [int(re.compile("(\d+)").match(author['aria-label'][author['aria-label'].find('post #')+6:author['aria-label'].find('post #')+9:1]).group(1))   for author in comment_authors3]
                
                auth1 = dict(zip(list_of_posts, list_of_authors))
                auth2 = dict(zip(list_of_posts3, list_of_authors3))
                
                auth.update(auth2)
                auth.update(auth1)
                
            comment_list = list(set(list(comm.keys())))
            info = [title, url, category, username, article_body, comment_list, auth, replies, created, views, users, likes, links] 
            writer_obj.writerow(info)

        
def update_dataframe_with_eip(file_name):
    df = pd.read_csv(file_name)
    df['EIP'] = df['Title'].str.extract(r'(?:EIP|ERC)[ -]?(\d+)', expand=False).astype('Int64')
    df.to_csv(file_name, index=False)

if __name__ == "__main__":
    os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/Analysis/Magician Comments')
    df = pd.read_csv('ethereum_magicians_filtered.csv').head(2) 
    urls = df['Website'].tolist()
    output_file = "ethereum_magicians_updated2.csv"
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    scrape_and_write_data(urls, output_file)
    update_dataframe_with_eip(output_file)
   # driver.quit()



'''
from selenium.webdriver.common.keys import Keys


with webdriver.Chrome(options=options) as driver, open(output_file, "w", encoding='utf-8', newline="") as file:
    writer_obj = csv.writer(file)
    header = ["Title", "Website", "Category", "Author", "Article Body", "Comments", "Comment Authors", "Replies", "Views", "Users", "Likes", "Links", "Last Reply", "Created At"]
    writer_obj.writerow(header)

    for url in urls:
        auth = {}
        comm = {}
        driver.get(url)
        page= driver.page_source.encode('utf-8') 
        soup = BeautifulSoup(page , "html.parser")
        replies = get_text_or_na(soup.find_all('li', attrs={'class':'replies'})[0], "span[class='number']")
        created = soup.find_all('li', attrs={'class':'created-at'})[0].select_one("span[class='relative-date']")['title']
        views = soup.find_all('li', attrs={'class':'secondary views'})[0].select_one("span[class='number heatmap-high']")['title']
        users = get_text_or_na(soup.find_all('li', attrs={'class':'secondary users'})[0], "span[class='number']")
        likes = get_text_or_na(soup.find_all('li', attrs={'class':'secondary likes'})[0], "span[class='number']")
        links = get_text_or_na(soup.find_all('li', attrs={'class':'secondary links'})[0], "span[class='number']")
                 
        for x in range(replies+2):
            driver.get(url+"/"+str(x))
            page= driver.page_source.encode('utf-8') 
            soup = BeautifulSoup(page , "html.parser")

            if x == 0: 
                title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
                category = get_text_or_na(soup, "span[itemprop='name']")
                username = get_text_or_na(soup, "span[itemprop='author']")
                article_body = get_text_or_na(soup, "div[itemprop='articleBody']")
                
            comment_text = soup.find_all("div", itemprop="text")[0:]
            for comment in comment_text:
               comm.update({str(comment):x})  
            
            comment_authors = soup.find_all("span", itemprop="author")[0:]
            comment_authors2 = soup.find_all("div", {'id': True, 'class':'topic-body crawler-post'} )[0:]
            comment_authors3 = soup.find_all('article', {'aria-label':True})[0:]
            
            list_of_authors = [author.find('span', itemprop="name").text.strip() for author in comment_authors]
            list_of_posts = [int(author['id'][author['id'].find('post_')+5:]) for author in comment_authors2]
            
            list_of_authors3 = [author['aria-label'][author['aria-label'].find('@')+1:]   for author in comment_authors3]
            list_of_posts3 = [int(re.compile("(\d+)").match(author['aria-label'][author['aria-label'].find('post #')+6:author['aria-label'].find('post #')+9:1]).group(1))   for author in comment_authors3]
            
            auth1 = dict(zip(list_of_posts, list_of_authors))
            auth2 = dict(zip(list_of_posts3, list_of_authors3))
            
            auth.update(auth2)
            auth.update(auth1)
            
        comment_list = list(set(list(comm.keys())))

'''