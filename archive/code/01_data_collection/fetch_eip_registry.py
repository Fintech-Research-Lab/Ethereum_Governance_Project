"""
fetch_eip_registry.py
======================

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Replaces
--------
`Data\\Data Gathering Code\\EIP list generating code.py` in the original messy project
(read in full and ported faithfully -- same scrape target, same table-parsing logic, same
column layout).

==================================================================================
HISTORICAL / OPTIONAL -- NOT PART OF THE DEFAULT REPRODUCTION PIPELINE
==================================================================================
This script is provided purely for methodological transparency -- as a documented, working
record of *how* the original EIP registry was scraped -- and is NOT meant to be re-run as
part of a normal reproduction of the paper's numbers.

The point-in-time raw data actually used in the paper is already frozen at
`data/raw/eip_registry/allEIPsandAuthorsv2.csv` (see `data/RAW_DATA_MANIFEST.md` for the
exact provenance/mapping of every raw file). That frozen CSV reflects the state of
https://eips.ethereum.org/all as it existed when the original authors scraped it (circa
late 2023 / June 2023 per the paper's data-collection window).

Re-running THIS script today will pull the CURRENT, live state of eips.ethereum.org --
which now includes EIPs proposed, finalized, or withdrawn after the paper's data-collection
cutoff, and may reflect edits to titles/authors/status of pre-existing EIPs. Running it will
NOT reproduce the paper's exact published numbers. Use it only to understand or audit the
original collection methodology, not as a pipeline input. Its output is therefore written to
`data/interim/` (never to `data/raw/`, which holds the frozen, paper-exact data) so it can
never be confused with, or accidentally overwrite, the authoritative raw file.

Output (if run)
----------------
    data/interim/refetched_eip_registry.parquet

Known fragile assumption (faithfully preserved from the original)
-------------------------------------------------------------------
See the inline comment above the `len(tables) != len(categories)` check below: this script
assumes the page's `<h2>` category headings and `<table>` elements inside the `post-content`
div appear in the same order and count, and zips them together positionally. This is exactly
the assumption the original script made (and is exactly why it can break if the page's
structure changes) -- it is not new fragility introduced by this port.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add code/ to sys.path
from config import DATA_INTERIM, ensure_dirs

import requests
from bs4 import BeautifulSoup
import polars as pl

EIP_ALL_URL = "https://eips.ethereum.org/all"
OUTPUT_PATH = DATA_INTERIM / "refetched_eip_registry.parquet"


def fetch_eip_registry(url: str = EIP_ALL_URL) -> pl.DataFrame:
    """
    Scrape https://eips.ethereum.org/all and return a DataFrame of (EIP, Title, Author,
    Status) rows, one per EIP/ERC/RIP listed on the page, exactly as the original script did.

    Faithful port of the original's logic:
    - Find the single `<div class="post-content">` and raise if absent.
    - Find every `<table>` within it, and every `<h2>` heading within it (the category names,
      e.g. "Core", "Networking", "Interface", "ERC", "Meta", "Informational", "Withdrawn").
    - Zip categories 1:1 against tables in document order (see module docstring for the
      fragile-assumption caveat this carries over from the original).
    - For each table, skip the header row (`rows[1:]`) and, per row:
        * if it has >= 4 `<td>` columns, take columns 0, 2, 3 (EIP number, Title, Author) --
          this is the "Category" layout where column 1 is a link/category column that is
          intentionally NOT captured (only column indices 0, 2, 3 are, mirroring the
          original's `[cols[0], cols[2], cols[3]]` selection exactly);
        * else if it has exactly 3 columns, take all three in order (EIP, Title, Author) --
          the layout used by, e.g., the "Withdrawn" table which lacks the extra column;
        * rows with fewer than 3 `<td>` columns are silently skipped, same as the original.
    - Append the category name as the 4th field ("Status") in both cases.
    """
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    # Scope down to the div where the tables are.
    post_content = soup.find("div", class_="post-content")
    if post_content is None:
        raise ValueError("No post-content div found")

    # Find all tables within the post-content div.
    tables = post_content.find_all("table")
    if not tables:
        raise ValueError("No tables found")

    # Find all category names within the post-content div.
    categories = [header.text.strip() for header in post_content.find_all("h2")]
    print("Categories extracted:", categories)

    # Ensure equal number of tables and categories.
    # FRAGILE ASSUMPTION (faithfully preserved from the original script): this assumes each
    # <h2> category heading is followed by exactly one <table>, in the same order, so that
    # zip(categories, tables) below pairs them up correctly. If eips.ethereum.org ever adds
    # an extra heading or a table-less section, `len(tables) != len(categories)` and this
    # raises -- it does not attempt to recover or re-pair by proximity in the DOM.
    if len(tables) != len(categories):
        raise ValueError("Mismatch in number of categories and tables")

    data: list[list[str]] = []

    for category, table in zip(categories, tables):
        rows = table.find_all("tr")
        if not rows:
            raise ValueError(f"No rows found in {category} table")

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:  # Check if at least 3 columns exist
                # If 4th column exists, take 1st, 3rd and 4th columns
                if len(cols) >= 4:
                    selected_data = [
                        cols[0].text.strip(),
                        cols[2].text.strip(),
                        cols[3].text.strip(),
                        category,
                    ]
                # If 4th column does not exist, take the first three columns
                else:
                    selected_data = [col.text.strip() for col in cols[:3]]
                    selected_data.append(category)
                data.append(selected_data)

    if not data:
        raise ValueError("No data found")

    column_names = ["EIP", "Title", "Author", "Status"]
    return pl.DataFrame(data, schema=column_names, orient="row")


if __name__ == "__main__":
    ensure_dirs()
    df = fetch_eip_registry()
    df.write_parquet(OUTPUT_PATH, compression="zstd")
    print(f"Wrote {df.height} rows to {OUTPUT_PATH}")
