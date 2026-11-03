"""
fetch_eip_word_readability.py
==============================

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Replaces
--------
`Data\\Data Gathering Code\\count_eip_words.py` in the original messy project (read in full
and ported faithfully -- same GitHub Contents API calls, same word-count/readability
computation, same EIP-vs-ERC "pick the larger" merge logic).

==================================================================================
HISTORICAL / OPTIONAL -- NOT PART OF THE DEFAULT REPRODUCTION PIPELINE
==================================================================================
This script is provided purely for methodological transparency -- as a documented, working
record of *how* the original per-EIP word counts and Flesch reading-ease scores were
computed -- and is NOT meant to be re-run as part of a normal reproduction of the paper's
numbers.

The point-in-time raw data actually used in the paper is already frozen at
`data/raw/eip_registry/eip_word_count.csv` (see `data/RAW_DATA_MANIFEST.md`). That frozen
CSV reflects the exact state of the `ethereum/EIPs` and `ethereum/ERCs` GitHub repositories
as they existed when the original authors pulled them (circa the paper's data-collection
window).

Re-running THIS script today will hit the CURRENT, live `EIPS`/`ERCS` directories on GitHub
-- which now include files added, edited, or moved after the paper's cutoff -- and will NOT
reproduce the paper's exact published word counts or readability scores. Use it only to
understand or audit the original collection methodology, not as a pipeline input. Its output
is written to `data/interim/` (never to `data/raw/`) so it can never be confused with, or
accidentally overwrite, the frozen, paper-exact raw file.

Output (if run)
----------------
    data/interim/refetched_eip_word_count.parquet

Infrastructure fixes applied during this port (pure plumbing fixes, no effect on the
computed word-count/readability values)
----------------------------------------------------------------------------------------
(a) The original imported the deprecated `textstat.textstat.textstatistics` class
    (`from textstat.textstat import textstatistics`, then `textstatistics().flesch_reading_ease(...)`).
    That submodule/class no longer exists in modern `textstat` releases. This port uses the
    modern top-level API instead: `import textstat; textstat.flesch_reading_ease(text)`.
    The underlying Flesch reading-ease formula/algorithm is unchanged -- only the import path
    changed.
(b) The original made fully unauthenticated GitHub API requests, capped at 60 requests/hour
    -- easy to exhaust given there are hundreds of EIP/ERC files, each requiring up to 2
    requests (word count + readability) on top of the 2 directory-listing calls. This port
    adds optional `GITHUB_TOKEN` environment-variable support (sent as
    `Authorization: token <token>`, raising the cap to 5,000/hour) with a graceful fallback
    to unauthenticated requests (with a printed warning) if the variable is unset, plus
    basic retry-with-backoff on HTTP 403/429 (rate-limit) responses.

Everything else below -- the word-counting method (`content.split()`), the readability
method (`flesch_reading_ease` on the raw file text), the EIP-number-from-filename parsing,
and the "pick whichever of (EIP file, ERC file) has more words, and use ITS readability
score" merge logic -- is a faithful, unmodified port of the original algorithm.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add code/ to sys.path
from config import DATA_INTERIM, ensure_dirs

import os
import time

import requests
import textstat
import polars as pl

# GitHub API URLs for the Ethereum EIPs / ERCs repository contents.
GITHUB_REPO_EIPS_API_URL = "https://api.github.com/repos/ethereum/EIPs/contents/EIPS"
GITHUB_REPO_ERCS_API_URL = "https://api.github.com/repos/ethereum/ERCs/contents/ERCS"

OUTPUT_PATH = DATA_INTERIM / "refetched_eip_word_count.parquet"


def _github_headers() -> dict:
    """
    Build the request headers for GitHub API calls. Uses the optional `GITHUB_TOKEN`
    environment variable if set (raises the rate limit from 60/hour to 5,000/hour);
    otherwise falls back to unauthenticated requests with a printed warning.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"token {token}"}
    print(
        "WARNING: GITHUB_TOKEN environment variable not set. Falling back to "
        "unauthenticated GitHub API requests, which are rate-limited to 60 requests/hour. "
        "Set GITHUB_TOKEN (a GitHub personal access token) to raise this to 5,000/hour."
    )
    return {}


def _request_with_retry(
    url: str, headers: dict, max_retries: int = 5, backoff_base: float = 2.0
) -> requests.Response:
    """
    GET `url` with basic retry-with-backoff on rate-limit responses (HTTP 403/429).

    This is purely an infrastructure addition (see module docstring, fix (b)): the original
    script had no retry logic whatsoever and simply branched on `status_code == 200` at each
    call site, printing an error and returning 0 (word count) / 0 (readability) / skipping
    the file otherwise. That branching is preserved unchanged in the calling functions below
    -- this wrapper only adds resilience against transient 403/429 responses before handing
    control back to that same original branching logic.
    """
    response = requests.get(url, headers=headers)
    for attempt in range(max_retries):
        if response.status_code in (403, 429):
            wait = backoff_base**attempt
            print(
                f"Rate-limited (status {response.status_code}) on {url}; retrying in "
                f"{wait:.0f}s (attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(wait)
            response = requests.get(url, headers=headers)
            continue
        break
    return response


def count_words_in_file(file_url: str, headers: dict) -> int:
    """
    Count the number of words in a file given its URL.
    """
    response = _request_with_retry(file_url, headers)
    if response.status_code == 200:
        content = response.text
        words = content.split()
        return len(words)
    else:
        print(f"Error accessing file: {file_url}")
        return 0


def calculate_readability(file_url: str, headers: dict):
    """
    Calculate the readability score of a text (Flesch reading-ease).
    """
    response = _request_with_retry(file_url, headers)
    if response.status_code == 200:
        content = response.text
        return textstat.flesch_reading_ease(content)
    else:
        print(f"Error accessing file: {file_url}")
        return 0


def extract_eip_number(filename: str):
    """
    Extract the EIP number from the filename.

    Faithful port: splits on '-' and inspects the second element (index 1), stripping a
    trailing '.md' and checking it is all-digits. If it is not, returns None implicitly (no
    explicit `else` branch, matching the original). Note this is a direct, unguarded port --
    a filename with no '-' at all (so `parts` has only one element) would raise IndexError
    here exactly as it would have in the original.
    """
    parts = filename.split("-")
    if parts[1].replace(".md", "").isdigit():
        return int(parts[1].replace(".md", ""))
    return None


def _fetch_repo_word_counts(
    api_url: str, headers: dict, word_count_col: str, readability_col: str
) -> pl.DataFrame:
    """
    Shared helper for the EIPS and ERCS repo passes (the original duplicated this loop body
    twice, once per repo, with only the output column names differing -- consolidated here
    without changing the per-file logic).
    """
    rows = []
    response = _request_with_retry(api_url, headers)
    if response.status_code == 200:
        repo_contents = response.json()
        for file_info in repo_contents:
            if file_info["type"] == "file":
                eip_number = extract_eip_number(file_info["name"])
                word_count = count_words_in_file(file_info["download_url"], headers)
                readability = calculate_readability(file_info["download_url"], headers)
                rows.append(
                    {
                        "EIP Number": eip_number,
                        word_count_col: word_count,
                        readability_col: readability,
                    }
                )
    else:
        print("Error accessing GitHub API.")

    if not rows:
        return pl.DataFrame(
            schema={
                "EIP Number": pl.Int64,
                word_count_col: pl.Int64,
                readability_col: pl.Float64,
            }
        )
    return pl.DataFrame(rows)


def main() -> pl.DataFrame:
    headers = _github_headers()

    df_eip = _fetch_repo_word_counts(
        GITHUB_REPO_EIPS_API_URL, headers, "Word Count_EIP", "Readability_EIP"
    )
    print(df_eip)

    df_erc = _fetch_repo_word_counts(
        GITHUB_REPO_ERCS_API_URL, headers, "Word Count_ERC", "Readability_ERC"
    )
    print(df_erc)

    # Outer merge on EIP Number, same as the original `pd.merge(df, df2, on='EIP Number',
    # how='outer')`. `coalesce=True` keeps a single "EIP Number" column instead of
    # duplicating it, matching pandas' outer-merge-on-shared-key behavior.
    return df_eip.join(df_erc, on="EIP Number", how="full", coalesce=True)


if __name__ == "__main__":
    ensure_dirs()

    df = main()

    df = df.with_columns(
        pl.col("Word Count_EIP").fill_null(0),
        pl.col("Word Count_ERC").fill_null(0),
    )

    df = df.with_columns(
        pl.max_horizontal("Word Count_EIP", "Word Count_ERC").alias("Word Count")
    )

    # Faithful port of the original's row-wise logic:
    #   df.loc[df['Word Count_EIP'] >  df['Word Count_ERC'], 'Readability'] = df['Readability_EIP']
    #   df.loc[df['Word Count_EIP'] <= df['Word Count_ERC'], 'Readability'] = df['Readability_ERC']
    # i.e. ties (equal word counts, including the 0-vs-0 case) resolve to the ERC score.
    df = df.with_columns(
        pl.when(pl.col("Word Count_EIP") > pl.col("Word Count_ERC"))
        .then(pl.col("Readability_EIP"))
        .otherwise(pl.col("Readability_ERC"))
        .alias("Readability")
    )

    out = df.select(["EIP Number", "Word Count", "Readability"])
    out.write_parquet(OUTPUT_PATH, compression="zstd")
    print(f"Wrote {out.height} rows to {OUTPUT_PATH}")
