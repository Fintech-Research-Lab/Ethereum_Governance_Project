"""
scrape_fem_forum.py
====================

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Replaces
--------
`Analysis\\Magician Comments\\magician_scraping.py` in the original messy project (read in
full and ported faithfully -- same Selenium + BeautifulSoup scrape of the Ethereum
Magicians (FEM) forum, same two-stage save points, same comment/author extraction logic).

==================================================================================
HISTORICAL / OPTIONAL -- NOT PART OF THE DEFAULT REPRODUCTION PIPELINE
==================================================================================
This script is provided purely for methodological transparency -- as a documented, working
reference for *how* the original Ethereum Magicians forum data was scraped -- and is NOT
meant to be re-run as part of a normal reproduction of the paper's numbers.

The point-in-time raw data actually used in the paper is already frozen at
`data/raw/forum/list_of_FEM_EIP_pages.csv` and `data/raw/forum/ethereum_magicians_data_scraped.csv`
(see `data/RAW_DATA_MANIFEST.md`). Those frozen CSVs reflect the exact state of
https://ethereum-magicians.org/c/eips/5 (topics, comments, view/like/reply counts) as it
existed when the original authors scraped it (circa the paper's data-collection window,
early 2024 per the original file's authorship date of 1/3/2024).

Re-running THIS script today would NOT reproduce the paper's exact published numbers, for
two independent reasons:
  1. The live forum has almost certainly changed: new topics/comments have been posted,
     view/like/reply counters have moved on, and old topics may have been edited or removed.
  2. Ethereum Magicians runs on the Discourse forum platform, whose HTML structure (CSS
     class names, DOM layout of comment/metadata elements) can and does change across
     Discourse version upgrades. Every CSS-class-based selector below (e.g.
     `'main-link clearfix topic-list-data'`, `'created-at'`, `itemprop='articleBody'`) was
     accurate for the Discourse version running on the site at scrape time in
     early 2024, but is NOT guaranteed to still match the live site's current markup.

Running this script today is therefore best-effort, not guaranteed -- it may need selector
updates to work at all against the current site, and even if it runs cleanly, its output
will reflect today's forum state, not the paper's. Use it only to understand or audit the
original scraping methodology, not as a pipeline input. Its output is written to
`data/interim/` (never to `data/raw/`) so it can never be confused with, or accidentally
overwrite, the frozen, paper-exact raw files.

Requirements to run this script at all
----------------------------------------
Requires Selenium with a local Google Chrome install AND a matching ChromeDriver binary on
PATH (or resolvable by Selenium Manager, bundled with modern `selenium` releases). Neither
is installed by this package's default dependencies -- install `selenium` and Chrome
yourself before attempting to run this script.

Output (if run)
----------------
    data/interim/refetched_fem_list_of_pages.parquet   (topic-list equivalent of the
        original's `list_of_FEM_EIP_pages.csv` save point)
    data/interim/refetched_fem_scrape.parquet          (full scraped-data equivalent of the
        original's `ethereum_magicians_data_scraped.csv` save point)

Faithfully-preserved original quirk
-------------------------------------
The original's `if __name__ == "__main__":` block instantiates a *third*, non-headless
Chrome driver (`driver = webdriver.Chrome(service=service, options=options)`) that is never
actually used for any scraping -- both `get_list_of_EIP_from_FEM` and `scrape_and_write_data`
each open and manage their own separate *headless* Chrome instance internally via a `with
webdriver.Chrome(...) as driver:` context manager. The outer `driver` therefore just sits
open (as a visible window) for the entire run and is closed with `driver.quit()` at the very
end. This is harmless (aside from wasting a browser instance) and is preserved here exactly
as in the original, rather than "fixed", per this port's faithfulness requirement.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add code/ to sys.path
from config import DATA_INTERIM, ensure_dirs

import csv
import re
import time

import polars as pl
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

FEM_EIPS_CATEGORY_URL = "https://ethereum-magicians.org/c/eips/5"

LIST_OUTPUT_PATH = DATA_INTERIM / "refetched_fem_list_of_pages.parquet"
SCRAPE_OUTPUT_PATH = DATA_INTERIM / "refetched_fem_scrape.parquet"

# Intermediate CSVs, written incrementally during the scrape (mirroring the original's
# row-by-row `csv.writer` behavior) so that a crash partway through a long scrape does not
# lose all progress. Converted to the final parquet outputs above once scraping completes.
_LIST_CSV_TMP = DATA_INTERIM / "_refetched_fem_list_of_pages.tmp.csv"
_SCRAPE_CSV_TMP = DATA_INTERIM / "_refetched_fem_scrape.tmp.csv"


# This function scrapes the list of all possible EIP topic pages from the FEM forum.
def get_list_of_EIP_from_FEM(input_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(
        input_file, "w", encoding="utf-8", newline=""
    ) as file:
        writer_obj = csv.writer(file)
        header = ["Website"]
        writer_obj.writerow(header)
        url = FEM_EIPS_CATEGORY_URL

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

        # GET THE SITE ON SOUP, AND PARSE IT
        soup = BeautifulSoup(driver.page_source.encode("utf-8"), "html.parser")

        # FIND EACH LINK, AND STORE IT
        l = len(
            soup.find_all("td", attrs={"class": "main-link clearfix topic-list-data"})
        )
        link = [
            soup.find_all("td", attrs={"class": "main-link clearfix topic-list-data"})[
                x
            ].find("a", {"class": "title raw-link raw-topic-link"})["href"]
            for x in range(l)
        ]
        link2 = ["https://ethereum-magicians.org/" + s for s in link]
        for word in link2:
            writer_obj.writerow([word])


def get_text_or_na(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else "N/A"


# THIS IS THE MAIN SCRAPING FUNCTION. FOR EACH URL, IT SCRAPES THE DATA WE NEED.
def scrape_and_write_data(urls, output_file):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    with webdriver.Chrome(options=options) as driver, open(
        output_file, "w", encoding="utf-8", newline=""
    ) as file:

        # PREPARE OUTPUT FILE.
        writer_obj = csv.writer(file)
        header = [
            "Title",
            "EIP",
            "Website",
            "Category",
            "Author",
            "Article Body",
            "Comments",
            "Comment Authors",
            "Replies",
            "Created at",
            "Created at2",
            "Views",
            "Users",
            "Likes",
            "Links",
        ]
        writer_obj.writerow(header)

        # FOR EACH URL,
        for url in urls:
            driver.get(url)
            print(url + "\n")
            soup = BeautifulSoup(driver.page_source.encode("utf-8"), "html.parser")

            # IF THE TITLE DOES NOT HAVE ANY NUMBER, SKIP THE URL
            title = soup.find("h1").text.strip() if soup.find("h1") else "N/A"
            try:
                eip = int(re.search(r"\d+", title)[0])
            except Exception:
                continue

            # IF THE PAGE DOES NOT HAVE ANY CREATED-AT ELEMENT, DO NOT COLLECT THE BAR
            # DATA. OTHERWISE, IT COLLECTS CREATED AT, REPLIES, VIEWS, LIKES, LINKS.
            if soup.find_all("li", attrs={"class": "created-at"}) != []:
                created = (
                    soup.find_all("li", attrs={"class": "created-at"})[0]
                    .select_one("span[class='relative-date']")["title"]
                )
                replies = int(
                    soup.find_all("li", attrs={"class": "replies"})[0]
                    .select_one("span[class='number']")
                    .text.strip()
                )
                try:
                    views = int(
                        soup.find_all("li", attrs={"class": "secondary views"})[0].find(
                            "span",
                            {
                                "class": [
                                    "number heatmap-high",
                                    "number heatmap-low",
                                    "number heatmap-med",
                                    "number",
                                ]
                            },
                        )["title"]
                    )
                except Exception:
                    views = int(
                        get_text_or_na(
                            soup.find_all("li", attrs={"class": "secondary views"})[0],
                            "span[class='number']",
                        )
                    )
                users = int(
                    get_text_or_na(
                        soup.find_all("li", attrs={"class": "secondary users"})[0],
                        "span[class='number']",
                    )
                )
                try:
                    likes = int(
                        get_text_or_na(
                            soup.find_all("li", attrs={"class": "secondary likes"})[0],
                            "span[class='number']",
                        )
                    )
                except Exception:
                    likes = 0
                try:
                    links = int(
                        get_text_or_na(
                            soup.find_all("li", attrs={"class": "secondary links"})[0],
                            "span[class='number']",
                        )
                    )
                except Exception:
                    links = 0
            else:
                created = ""
                replies = 0
                views = 0
                users = 0
                likes = 0
                links = 0

            # COLLECT MAIN DATA ABOUT SITE
            category = get_text_or_na(soup, "span[itemprop='name']")
            username = get_text_or_na(soup, "span[itemprop='author']")
            article_body = get_text_or_na(soup, "div[itemprop='articleBody']")
            date_orig = soup.find_all("time", attrs={"itemprop": "datePublished"})[0][
                "datetime"
            ]
            auth = {}
            comm = {}

            # NEED TO SCROLL DOWN SLOWLY, ONE COMMENT AT A TIME, OTHERWISE THE PARSING
            # WILL NOT LOAD ALL COMMENTS UP.
            maxrep = replies + 2
            for x in range(maxrep):
                driver.get(url + "/" + str(x))
                page = driver.page_source.encode("utf-8")
                soup = BeautifulSoup(page, "html.parser")
                comment_text = soup.find_all("div", itemprop="text")[0:]
                for comment in comment_text:
                    comm.update({str(comment): x})

                # LOAD COMMENTS. TWO TYPES OF AUTHORS: AUTHORS, AND ARIA-LABEL @. WE
                # COLLECT BOTH, AND THEN APPEND.
                comment_authors = soup.find_all("span", itemprop="author")[0:]
                comment_authors2 = soup.find_all(
                    "div", {"id": True, "class": "topic-body crawler-post"}
                )[0:]
                comment_authors3 = soup.find_all("article", {"aria-label": True})[0:]

                list_of_authors = [
                    author.find("span", itemprop="name").text.strip()
                    for author in comment_authors
                ]
                list_of_posts = [
                    int(author["id"][author["id"].find("post_") + 5 :])
                    for author in comment_authors2
                ]

                list_of_authors3 = [
                    author["aria-label"][author["aria-label"].find("@") + 1 :]
                    for author in comment_authors3
                ]
                list_of_posts3 = [
                    int(
                        re.compile(r"(\d+)")
                        .match(
                            author["aria-label"][
                                author["aria-label"].find("post #")
                                + 6 : author["aria-label"].find("post #")
                                + 9 : 1
                            ]
                        )
                        .group(1)
                    )
                    for author in comment_authors3
                ]

                auth1 = dict(zip(list_of_posts, list_of_authors))
                auth2 = dict(zip(list_of_posts3, list_of_authors3))

                auth.update(auth2)
                auth.update(auth1)

            # WRITE ON OUTPUT FILE
            comment_list = list(set(list(comm.keys())))
            info = [
                title,
                eip,
                url,
                category,
                username,
                article_body,
                comment_list,
                auth,
                replies,
                created,
                date_orig,
                views,
                users,
                likes,
                links,
            ]
            writer_obj.writerow(info)


def update_dataframe_with_eip(file_name):
    df = pl.read_csv(file_name)
    df = df.with_columns(
        df["Title"]
        .str.extract(r"(?:EIP|ERC)[ -]?(\d+)", 1)
        .cast(pl.Int64)
        .alias("EIP")
    )
    df.write_csv(file_name)


# MAIN FILE TO RUN.
if __name__ == "__main__":
    ensure_dirs()

    # Faithfully-preserved original quirk (see module docstring): this driver is opened but
    # never actually used for scraping -- both scraping functions below open their own,
    # separate headless Chrome instances. It is closed at the very end via `driver.quit()`.
    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    input_file = str(_LIST_CSV_TMP)
    get_list_of_EIP_from_FEM(input_file)

    list_df = pl.read_csv(input_file)
    urls = list_df["Website"].to_list()

    output_file = str(_SCRAPE_CSV_TMP)
    scrape_and_write_data(urls, output_file)
    update_dataframe_with_eip(output_file)

    driver.quit()

    # Convert the two incremental-write CSV save points to the final parquet outputs.
    list_df.write_parquet(LIST_OUTPUT_PATH, compression="zstd")
    print(f"Wrote {list_df.height} rows to {LIST_OUTPUT_PATH}")

    scrape_df = pl.read_csv(output_file)
    scrape_df.write_parquet(SCRAPE_OUTPUT_PATH, compression="zstd")
    print(f"Wrote {scrape_df.height} rows to {SCRAPE_OUTPUT_PATH}")

    # Clean up the temporary intermediate CSVs now that the parquet outputs are written.
    Path(input_file).unlink(missing_ok=True)
    Path(output_file).unlink(missing_ok=True)
