from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
import csv
from collections import Counter
import os
from selenium.webdriver.chrome.service import Service



def get_text_or_na(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else 'N/A'

def scrape_and_write_data(urls, output_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(output_file, "w", encoding='utf-8', newline="") as file:
        writer_obj = csv.writer(file)
        header = ["Title", "Website", "Category", "Author", "Article Body", "Comments", "Comment Authors"]# "Replies", "Views", "Users", "Likes", "Links", "Last Reply", "Created At"]
        writer_obj.writerow(header)

        for url in urls:
            driver.get(url)
            scroll_page(driver)
            info = extract_info_from_page(driver)
            writer_obj.writerow(info)

def scroll_page(driver):
    wait = WebDriverWait(driver, 2)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            wait.until(lambda d: driver.execute_script("return document.body.scrollHeight") > last_height)
            last_height = driver.execute_script("return document.body.scrollHeight")
        except TimeoutException:
            break  # Break the loop if no new content is loaded

def extract_info_from_page(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
    url = driver.current_url
    category = get_text_or_na(soup, "span[itemprop='name']")
    username = get_text_or_na(soup, "span[itemprop='author']")
    article_body = get_text_or_na(soup, "div[itemprop='articleBody']")

    comments_html = soup.find_all('div', class_='post')
    comments = "##$$##".join(comment.text.strip() for comment in comments_html[1:])

    comment_authors = soup.find_all("span", itemprop="author")[1:]
    list_of_authors = [author.find('span', itemprop="name").text.strip() for author in comment_authors]
    comment_author_count_cleaned = str(Counter(list_of_authors))[9:-2]

    # # Extract additional information
    # replies = get_text_or_na(soup, "section.map li.replies span.number")
    # views = get_text_or_na(soup, "section.map li.views span.number")
    # users = get_text_or_na(soup, "section.map li.users span.number")
    # likes = get_text_or_na(soup, "section.map li.likes span.number")
    # links = get_text_or_na(soup, "section.map li.links span.number")
    # last_reply = get_text_or_na(soup, "section.map li.last-reply span.relative-date")
    # created_at = get_text_or_na(soup, "section.map li.created-at span.relative-date")

    return [title, url, category, username, article_body, comments, comment_author_count_cleaned]#, replies, views, users, likes, links, last_reply, created_at] --< this is removed

def update_dataframe_with_eip(file_name):
    df = pd.read_csv(file_name)
    df['EIP'] = df['Title'].str.extract(r'(?:EIP|ERC)[ -]?(\d+)', expand=False).astype('Int64')
    df.to_csv(file_name, index=False)

if __name__ == "__main__":
    os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project/Analysis/Magician Comments')
    df = pd.read_csv('ethereum_magicians_filtered.csv').head(10)
    urls = df['Website'].tolist()
    output_file = "ethereum_magicians_updated2.csv"
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    scrape_and_write_data(urls, output_file)
    update_dataframe_with_eip(output_file)
    driver.quit()




