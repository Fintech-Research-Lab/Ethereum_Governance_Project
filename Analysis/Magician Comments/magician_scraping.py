'''
Author: Cesare Fracassi
Date: 1/3/2024
'''


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


#This function scrapes the list of all posssible EIP websites from FEM
def get_list_of_EIP_from_FEM(input_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(input_file, "w", encoding='utf-8', newline="") as file:
        writer_obj = csv.writer(file)
        header = ["Website"]
        writer_obj.writerow(header)
        url = 'https://ethereum-magicians.org/c/eips/5'

        driver.get(url)

        # SCROLLS ALL THE WAY DOWN
        SCROLL_PAUSE_TIME = 0.5
        
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)
        
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        # GET THE SITE ON SOUP< AND PARSE IT    
        soup = BeautifulSoup(driver.page_source.encode('utf-8') , "html.parser")
        
        # FIND EACH LINK, AND STORE IT
        l = len(soup.find_all('td', attrs={'class':'main-link clearfix topic-list-data'}))
        link = [soup.find_all('td', attrs={'class':'main-link clearfix topic-list-data'})[x].find("a", {'class':'title raw-link raw-topic-link'})['href'] for x in range(l)]
        link2 = ['https://ethereum-magicians.org/' + s for s in link]
        for word in link2:
            writer_obj.writerow([word])

   
        
def get_text_or_na(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else 'N/A'

# THIS IS THE MAIN SCRAPING FUNCTION. FOR EACH URL, IT SCRAPES THE DATA WE NEED.
def scrape_and_write_data(urls, output_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(output_file, "w", encoding='utf-8', newline="") as file:
        
        # PREPARE OUTPUT FILE. 
        writer_obj = csv.writer(file)
        header = ["Title", "EIP", "Website", "Category", "Author", "Article Body", "Comments", "Comment Authors", "Replies", "Created at", "Created at2", "Views", "Users", "Likes", "Links"]
        writer_obj.writerow(header)

        # FOR EACH URL, 
        for url in urls:
            driver.get(url)
            print(url + '\n')
            soup = BeautifulSoup(driver.page_source.encode('utf-8') , "html.parser")
            
            # IF THE TITLE DOES NOT HAVE ANY NUMBER, SKIP THE URL
            title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
            try: 
                eip = int(re.search(r'\d+', title)[0])
            except: 
                continue
            
            # IF THE PAGE DOES NOT HAVE ANY CREATED-AT ELEMENT, DO NOT COLLECT THE BAR DATA. OTHERWISE, IT COLLECTS CREATED AT, REPLIES, VIEWS, LIKES, LINKS. 
            if soup.find_all('li', attrs={'class':'created-at'}) != []: 
                created = soup.find_all('li', attrs={'class':'created-at'})[0].select_one("span[class='relative-date']")['title']
                replies = int(soup.find_all('li', attrs={'class':'replies'})[0].select_one("span[class='number']").text.strip())
                try: 
                    views = int(soup.find_all('li', attrs={'class':'secondary views'})[0].find("span", {'class':['number heatmap-high', 'number heatmap-low', 'number heatmap-med', 'number']})['title'])
                except: 
                    views = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary views'})[0], "span[class='number']"))
                users = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary users'})[0], "span[class='number']"))
                try: 
                    likes = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary likes'})[0], "span[class='number']"))
                except: 
                    likes = 0
                try: 
                    links = int(get_text_or_na(soup.find_all('li', attrs={'class':'secondary links'})[0], "span[class='number']"))
                except: 
                    links = 0
            else:
                created = ''
                replies = 0
                views = 0
                users = 0 
                likes = 0
                links = 0
            
            #COLLECT MAIN DATA ABOUT SITE
            category = get_text_or_na(soup, "span[itemprop='name']")
            username = get_text_or_na(soup, "span[itemprop='author']")
            article_body = get_text_or_na(soup, "div[itemprop='articleBody']")
            date_orig = soup.find_all('time', attrs={'itemprop':'datePublished'})[0]['datetime']
            auth = {}
            comm = {}
            
            #NEED TO SCROLL DOWN SLOWLY, ONE COMMENT AT THE TIME, OTHERWISE THE PARSING WILL NOT LOAD ALL COMMENTS UP. 
            maxrep = replies + 2 
            for x in range(maxrep):
                driver.get(url+"/"+str(x))
                page= driver.page_source.encode('utf-8') 
                soup = BeautifulSoup(page , "html.parser")            
                comment_text = soup.find_all("div", itemprop="text")[0:]
                for comment in comment_text:
                   comm.update({str(comment):x})  
                
                # LOAD COMMENTS. TWO TYPES OF AUTHORS: AUTHORS, AND ARIA-LABEL @. WE COLLECT BOTH,A ND THEN APPEND. 
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
            
            #WRITE ON OUTPUT FILE    
            comment_list = list(set(list(comm.keys())))
            info = [title, eip, url, category, username, article_body, comment_list, auth, replies, created, date_orig, views, users, likes, links] 
            writer_obj.writerow(info)

        
def update_dataframe_with_eip(file_name):
    df = pd.read_csv(file_name)
    df['EIP'] = df['Title'].str.extract(r'(?:EIP|ERC)[ -]?(\d+)', expand=False).astype('Int64')
    df.to_csv(file_name, index=False)

# MAIN FILE TO RUN. 
if __name__ == "__main__":
    os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/Analysis/Magician Comments')
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    input_file = 'list_of_FEM_EIP_pages.csv'
    get_list_of_EIP_from_FEM(input_file)
    df = pd.read_csv('list_of_FEM_EIP_pages.csv')
    urls = df['Website'].tolist()
    output_file = "ethereum_magicians_data_scraped.csv"  
    scrape_and_write_data(urls, output_file)
    update_dataframe_with_eip(output_file)
    driver.quit()


