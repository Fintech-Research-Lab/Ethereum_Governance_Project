"""
build_cross_sectional_dataset.py
=================================

Ported from: `Data\\Data Gathering Code\\data merging code.do` (original messy project).

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

What this script produces
--------------------------
This is the single most important data-preparation script in the whole reproduction package.
It builds the paper's master cross-sectional dataset -- one row per EIP -- by merging ~10
different data sources, including a loop over up to 15 "author slots" per EIP that attaches
each author's Twitter / GitHub / LinkedIn / Ethereum-Foundation / anonymity / co-authorship
centrality / execution-client-commit data. The resulting table feeds nearly every subsequent
figure and table in the paper, including (at minimum) Tables 1-3 and Figures 2, 3, 6, 7, 8, 9,
17, 18, 19.

Every merge key, `egen rowmax`/`rowtotal`, `bysort ... : egen`, and recode below was built by
reading the actual Stata code in `data merging code.do` line by line -- not guessed from a
summary.

THE TWO CIRCULAR DEPENDENCIES -- READ THIS BEFORE CHANGING THE TWO-PASS BEHAVIOR
----------------------------------------------------------------------------------
The original pipeline has (at least) two genuine circular dependencies baked into it. This
script resolves both the same way: by treating the missing input as an *optional* merge that
is filled with nulls when its producer script has not been run yet, so this script can run
standalone at any point in the pipeline and simply produces a less-complete dataset.

1. CENTRALITY. `data merging code.do` reads `Analysis\\Centrality Analysis\\centrality_all.csv`
   (the co-authorship-network centrality measures: betweenness / closeness / eigenvector
   centrality per author). But the script that COMPUTES centrality (`centrality_code.py` in the
   original project) reads `Data\\Raw Data\\Ethereum_Cross-sectional_Data_output.csv` -- i.e. THIS
   SCRIPT'S OWN OUTPUT. The original pipeline must therefore have been run in (at least) two
   passes:
       pass 1: run this merge script with no centrality data available yet
               -> produces a cross-sectional dataset with null centrality columns
       pass 2: run centrality analysis on that pass-1 dataset
               -> produces centrality_all.csv/.parquet
       pass 3: re-run this merge script
               -> now centrality_all.parquet exists, so the centrality columns get
                  populated and the FINAL dataset (the one used by every downstream
                  regression/figure) is produced.
   This script looks for `data/interim/centrality_all.parquet` (the not-yet-written
   `centrality_code.py`-equivalent script's expected output, matching `index -> author_id`
   after rename). If it exists, it is merged in exactly like the original's
   `merge m:1 author_id using centrality.dta`. If it does NOT exist, this script prints a
   clear message, proceeds with the three centrality columns (betweenness / closeness /
   eigen_value_centrality, per author slot, plus the three row-max aggregates) populated as
   null, and still writes a complete, valid, everything-else-populated dataset.

2. FEM (Ethereum Magicians forum) DATA. `FEM_Data_for_regressions.csv` is itself the OUTPUT of a
   not-yet-written Magician-comments analysis script (it is not a raw input -- it is not present
   under `data/raw/`, by design; see `RAW_DATA_MANIFEST.md`). This script looks for
   `data/interim/fem_data_for_regressions.parquet`. If it exists, it is merged in exactly like
   the original's `merge 1:1 eip_number using temp_fem.dta`. If it does NOT exist, this script
   prints a clear message and proceeds with `replies`, `views`, `likes`, `links`, `createddate`,
   `users` populated as null.

BECAUSE OF THE ABOVE: whoever writes `run_pipeline.py` MUST call this script TWICE -- once
before the centrality/FEM analyses run (to produce the pre-centrality/pre-FEM intermediate
build those analyses need as their own input), and once after (to produce the final,
fully-populated dataset used by every downstream table/figure). Both passes write to the SAME
output paths (matching the original, which only ever had one
`Ethereum_Cross-sectional_Data.dta`, produced fresh each full pipeline run, overwritten in
place):
    data/processed/ethereum_cross_sectional_data.parquet
    data/processed/ethereum_cross_sectional_data.csv   (companion CSV, since the original
                                                         centrality_code.py read the CSV form
                                                         of this exact dataset)

THE UPSTREAM (sibling) DEPENDENCY: `ethereum_cross_sectional_data_beg`
------------------------------------------------------------------------
The master per-EIP "spine" this script merges everything else onto -- one row per EIP, with
columns `eip_number, title, author, status, author1..author15, author1_id..author15_id` -- is
itself the output of a sibling script, `code/02_data_preparation/clean_eip_authors.py`
(being written in parallel; not yet present as of this writing). This script expects it at:
    data/interim/ethereum_cross_sectional_data_beg.parquet
with (at minimum) the following schema, ported directly from the original
`Ethereum_Cross-sectional_Data_beg.csv`:
    eip_number      : Int64                          -- EIP number
    title           : Utf8                            -- EIP title
    author          : Utf8                            -- raw semicolon/comma-separated author string
    status          : Utf8                            -- EIP status ("Final", "Draft", "Living ", ...)
    author{1..15}    : Utf8                            -- author display name for slot i (blank if unused)
    author{1..15}_id : Int64 (nullable)                -- author_id for slot i (null if unused)
Column names are matched case-insensitively (lower-cased on load) so this script works whether
`clean_eip_authors.py` emits `Title`/`Author`/`Status` or already-lower `title`/`author`/`status`.
Unlike centrality/FEM, this input is NOT optional -- without it there is no spine to merge onto,
so this script raises a clear `FileNotFoundError` (rather than silently producing an empty or
fabricated dataset) if it is missing.

Design notes
-------------
- Column order and Stata display-formatting directives have no Parquet/CSV equivalent and aren't
  reproduced; downstream scripts always select columns by name, never by position. Columns here
  are grouped into a sensible order (EIP-level fields, then aggregate/derived measures, then the
  15 repeated per-author-slot blocks) for human readability.
- `label var ...`-style human-readable column labels are captured in the `VARIABLE_LABELS` dict
  below, for any downstream table-generation script that wants them -- Parquet has no first-class
  per-column label metadata in the Polars API used here, so labels aren't embedded in the file
  itself.
- Raw CSVs (e.g. `linkedin_data.csv`) contain a handful of bytes that aren't valid UTF-8; this
  script reads all CSVs with `encoding="utf8-lossy"`, which substitutes the Unicode replacement
  character for invalid bytes rather than raising.
- `eip_implementation.xlsx`: Excel error values (`#N/A`, from a `VLOOKUP` that found no matching
  fork) are read via `openpyxl` with `data_only=True` and explicitly converted to a missing value
  (checked via `cell.data_type == "e"`), not the literal string "#N/A" -- essential to get
  `implementation` right (see the note near that recode below).
- The four execution-client commit row-max aggregates span all 15 author slots (matching the
  per-slot merge loop, which also populates all 15) -- this matters concretely for EIP 6596,
  which has 15 listed authors.
- `time_to_final` is `edate - sdate` in days.
- All four commit-count variables (`n_contributors_eip`, `total_eip_commit`, `author_commit`,
  `n_committing_authors`) are consistently filled to 0 for EIPs with no matching commit-log rows.
- The `"Living "` (trailing-space) status typo is normalized to `"Living"` before the `success`
  recode runs, so a status of `"Living "` classifies the same way as `"Living"`.
- LinkedIn per-author-slot job-title columns `job_title2_company4` and
  `jobtitle2_pastcompany{1,2,4}` are included under their actual raw column names.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import openpyxl
import polars as pl

from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, ensure_dirs
from utils.client_commits import load_all_client_commits

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Python equivalent of Stata's `forvalues id = 1/15`.
AUTHOR_SLOTS: tuple[int, ...] = tuple(range(1, 16))

# Python equivalent of Stata's `local files = "besu erigon geth nethermind"`.
CLIENT_FILES: tuple[str, ...] = ("besu", "erigon", "geth", "nethermind")

RAW_SOCIAL = DATA_RAW / "social"
RAW_REGISTRY = DATA_RAW / "eip_registry"
RAW_COMMITS = DATA_RAW / "commits"

TWITTER_CSV = RAW_SOCIAL / "twitter_data.csv"
GITHUB_CSV = RAW_SOCIAL / "GitHub_Data.csv"
LINKEDIN_CSV = RAW_SOCIAL / "linkedin_data.csv"
AUTHOR_EF_CSV = RAW_SOCIAL / "Author_EF.csv"
UNIQUE_AUTHORS_CSV = RAW_REGISTRY / "unique_author_names_with_id.csv"
EIP_WORD_COUNT_CSV = RAW_REGISTRY / "eip_word_count.csv"
EIP_STARTDATES_CSV = RAW_REGISTRY / "eip_startdates.csv"
FINALEIP_ENDDATES_CSV = RAW_REGISTRY / "finaleip_enddates.csv"
EIP_IMPLEMENTATION_XLSX = RAW_REGISTRY / "eip_implementation.xlsx"
EIP_COMMIT_BEG_XLSX = RAW_COMMITS / "eip_commit_beg.xlsx"

# Optional (two-pass / circular-dependency) inputs -- see module docstring.
BASE_EIP_PARQUET = DATA_INTERIM / "ethereum_cross_sectional_data_beg.parquet"
CENTRALITY_PARQUET = DATA_INTERIM / "centrality_all.parquet"
FEM_PARQUET = DATA_INTERIM / "fem_data_for_regressions.parquet"

OUT_PARQUET = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
OUT_CSV = DATA_PROCESSED / "ethereum_cross_sectional_data.csv"

# Ported from the original's `label var` statements (lines 452-475 of the .do file). Not
# embedded in the output file itself -- provided for any downstream table-generation script
# that wants human-readable labels.
VARIABLE_LABELS: dict[str, str] = {
    "log_tw": "Twitter Followers (log)",
    "log_gh": "GitHub Followers (log)",
    "tw_follower": "N. Twitter Followers",
    "tf_scale": "N. Twitter Followers (K)",
    "gh_follower": "N. Github Followers",
    "n_authors": "N. EIP Authors",
    "betweenness_centrality": "Betweenness Centrality",
    "author_commit": "EIP Author Commits",
    "total_eip_commit": "Total EIP Commits",
    "n_contributors_eip": "EIP Contributors",
    "besu_commits": "Besu Commits",
    "erigon_commits": "Erigon Commits",
    "geth_commits": "Geth Commits",
    "nethermind_commits": "Nethermind Commits",
    "success": "Finalized",
    "implementation": "Implemented EIP",
    "time_to_final": "Time from EIP Start to Finalization",
    "eip_nwords": "N. Words in EIP (k)",
    "eip_read": "Readability Score",
    "replies": "FEM Comments",
    "views": "FEM Views",
    "likes": "FEM Likes",
    "users": "FEM Unique Users",
    "anon_max": "Anonymous Author",
    "client_commits": "EIP Authors Client Commits",
    "client_commits_log": "EIP Authors Client Commits (log)",
    "client_commits_dum": "EIP Author also Client Dev",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _sanitize_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Rename columns the way Stata's `insheet`/`import delimited` do: lower-case, strip
    surrounding whitespace/BOM, and remove interior spaces (Stata variable names cannot
    contain spaces). E.g. "EIP Number" -> "eipnumber", "GitHub_Username" -> "github_username".
    """
    rename = {}
    for c in df.columns:
        clean = c.replace("﻿", "").strip().lower().replace(" ", "")
        if clean and clean != c:
            rename[c] = clean
    return df.rename(rename) if rename else df


def _read_csv(path: Path) -> pl.DataFrame:
    """
    Read a raw CSV the way the original Stata `insheet`/`import delimited comma` did:
    tolerant of stray non-UTF-8 bytes (see module docstring), columns lower-cased.
    """
    df = pl.read_csv(path, encoding="utf8-lossy", infer_schema_length=10_000)
    return _sanitize_columns(df)


def _attach_slot(
    df: pl.DataFrame,
    slot: int,
    lookup: pl.DataFrame,
    lookup_cols: list[str],
    rename_map: dict[str, str],
) -> pl.DataFrame:
    """
    Attach one author-slot's worth of data from `lookup` (keyed by `author_id`) onto `df`.

    Direct Python equivalent of the repeated Stata pattern:
        rename author`id'_id author_id
        merge m:1 author_id using <lookup>, keepusing(<lookup_cols>)
        drop if _merge == 2
        drop _merge
        rename author_id author`id'_id
        rename <lookup_col> author`id'_<renamed>
    A left join on `author_id` reproduces `keep(1,3)` / `drop if _merge==2` exactly: every row
    of `df` (the master/"1" side) is kept whether matched or not, and unmatched rows from
    `lookup` ("using"/"2"-only) never enter the result of a left join in the first place.
    """
    id_col = f"author{slot}_id"
    out = (
        df.rename({id_col: "author_id"})
        .join(lookup.select(["author_id", *lookup_cols]), on="author_id", how="left")
        .rename({"author_id": id_col, **rename_map})
    )
    return out


# ---------------------------------------------------------------------------
# Individual raw-source loaders
# ---------------------------------------------------------------------------

def _load_twitter() -> pl.DataFrame:
    """twitter_data.csv -> author_id, follower, following (destring'd, force-cast to float)."""
    df = _read_csv(TWITTER_CSV)
    return df.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        pl.col("follower").cast(pl.Float64, strict=False),
        pl.col("following").cast(pl.Float64, strict=False),
    )


def _load_github() -> pl.DataFrame:
    """GitHub_Data.csv -> author_id, github_followers."""
    df = _read_csv(GITHUB_CSV)
    return df.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        pl.col("github_followers").cast(pl.Float64, strict=False),
    )


# The LinkedIn columns to bring in per author slot: company affiliations, past company
# affiliations, and job titles (cross-referenced against each author's current/past companies).
_LINKEDIN_COMPANY_COLS = [f"company{i}" for i in range(1, 6)]
_LINKEDIN_PASTCOMPANY_COLS = [f"pastcompany{i}" for i in range(1, 11)]
_LINKEDIN_JOBTITLE_COLS = [
    "jobtitle1_company1", "jobtitle2_company1", "jobtitle3_company1",
    "jobtitle1_company2", "jobtitle1_company3", "jobtitle1_company4", "jobtitle1_company5",
    "job_title2_company4",
    "jobtitle2_pastcompany1", "jobtitle2_pastcompany2", "jobtitle2_pastcompany4",
] + [f"jobtitle1_pastcompany{i}" for i in range(1, 11)]
LINKEDIN_COLS = _LINKEDIN_COMPANY_COLS + _LINKEDIN_PASTCOMPANY_COLS + _LINKEDIN_JOBTITLE_COLS


def _load_linkedin() -> pl.DataFrame:
    """linkedin_data.csv -> author_id + the company/pastcompany/jobtitle columns above."""
    df = _read_csv(LINKEDIN_CSV)
    return df.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        *[pl.col(c) for c in LINKEDIN_COLS],
    )


def _load_author_ef() -> pl.DataFrame:
    """Author_EF.csv -> author_id, from, end (EF tenure start/end years)."""
    df = _read_csv(AUTHOR_EF_CSV)
    return df.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        pl.col("from").cast(pl.Float64, strict=False),
        pl.col("end").cast(pl.Float64, strict=False),
    )


def _load_unique_authors() -> pl.DataFrame:
    """unique_author_names_with_id.csv, raw (author_id, full_name, github_username, anonymity_flag)."""
    return _read_csv(UNIQUE_AUTHORS_CSV)


def _load_eip_word_count() -> pl.DataFrame:
    """
    eip_word_count.csv -> eip_number, eip_nwords (in thousands), eip_read (readability,
    clipped at a minimum of 0).
    """
    df = _read_csv(EIP_WORD_COUNT_CSV)
    return df.select(
        pl.col("eipnumber").cast(pl.Int64, strict=False).alias("eip_number"),
        (pl.col("wordcount").cast(pl.Float64, strict=False) / 1000).alias("eip_nwords"),
        pl.when(pl.col("readability").cast(pl.Float64, strict=False) < 0)
        .then(0.0)
        .otherwise(pl.col("readability").cast(pl.Float64, strict=False))
        .alias("eip_read"),
    )


def _load_eip_startdates() -> pl.DataFrame:
    """eip_startdates.csv -> eip_number, sdate (parsed M/D/YYYY)."""
    df = _read_csv(EIP_STARTDATES_CSV)
    return df.select(
        pl.col("eipnumber").cast(pl.Int64, strict=False).alias("eip_number"),
        pl.col("date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("sdate"),
    )


def _load_finaleip_enddates() -> pl.DataFrame:
    """finaleip_enddates.csv -> eip_number, edate (parsed M/D/YYYY, blank -> null)."""
    df = _read_csv(FINALEIP_ENDDATES_CSV)
    return df.select(
        pl.col("number").cast(pl.Int64, strict=False).alias("eip_number"),
        pl.col("end").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("edate"),
    )


def _load_eip_implementation() -> pl.DataFrame:
    """
    eip_implementation.xlsx (sheet "EIP Summary") -> eip_number, Category, Implementable, inFork.

    Uses openpyxl directly (not pandas.read_stata / pandas at all) so that Excel error values
    (the "#N/A" cached results of a VLOOKUP that found no matching fork) can be explicitly
    detected via `cell.data_type == "e"` and converted to a real missing value -- matching
    Stata's own documented `import excel` behavior (error cells import as missing), rather than
    importing the literal string "#N/A". Getting this right matters: if "#N/A" were kept as a
    non-empty string, `implementation = 1 if inFork != ""` would incorrectly mark EIPs whose
    VLOOKUP failed to find a fork as "implemented".
    """
    wb = openpyxl.load_workbook(EIP_IMPLEMENTATION_XLSX, read_only=True, data_only=True)
    ws = wb["EIP Summary"]
    rows_iter = ws.iter_rows(values_only=False)
    header = [c.value for c in next(rows_iter)]
    records: list[dict] = []
    for row in rows_iter:
        rec = {}
        for col_name, cell in zip(header, row):
            rec[col_name] = None if cell.data_type == "e" else cell.value
        records.append(rec)
    wb.close()
    df = pl.DataFrame(records, infer_schema_length=None)
    return df.select(
        pl.col("eip_number").cast(pl.Int64, strict=False),
        pl.col("Category").cast(pl.Utf8, strict=False),
        pl.col("Implementable").cast(pl.Int64, strict=False),
        pl.col("inFork").cast(pl.Utf8, strict=False),
    )


def _load_eip_commit_beg() -> pl.DataFrame:
    """
    eip_commit_beg.xlsx (sheet "Sheet1") -> eip_number, github_username (lower-cased).
    Only the two columns the original .do file actually uses (`EIP` -> eip_number,
    `Username` -> github_username) are read; the file also has commit-SHA/message/date/author
    columns that this merge script does not use.
    """
    wb = openpyxl.load_workbook(EIP_COMMIT_BEG_XLSX, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows_iter = ws.iter_rows(values_only=False)
    header = [c.value for c in next(rows_iter)]
    eip_idx = header.index("EIP")
    user_idx = header.index("Username")
    records = []
    for row in rows_iter:
        records.append({"eip_number": row[eip_idx].value, "github_username": row[user_idx].value})
    wb.close()
    df = pl.DataFrame(records)
    return df.select(
        pl.col("eip_number").cast(pl.Int64, strict=False),
        pl.col("github_username").cast(pl.Utf8, strict=False).str.to_lowercase(),
    )


# ---------------------------------------------------------------------------
# eip_commit_data.dta equivalent (lines 44-83 of the .do file)
# ---------------------------------------------------------------------------

def _build_eip_commit_data() -> pl.DataFrame:
    """
    Build the per-EIP commit-aggregate table: n_contributors_eip, total_eip_commit,
    author_commit, n_committing_authors. One row per eip_number.
    """
    unique_authors = _load_unique_authors()
    # author_git.dta: unique_author_names_with_id filtered to non-blank github_username, lowered.
    author_git = (
        unique_authors.filter(
            pl.col("github_username").is_not_null() & (pl.col("github_username") != "")
        )
        .select(
            pl.col("github_username").str.to_lowercase(),
            pl.col("author_id").cast(pl.Int64, strict=False),
        )
    )

    commits = _load_eip_commit_beg()
    # merge m:1 github_username using author_git, keep(1,3)  ==  left join
    commits = commits.join(author_git, on="github_username", how="left")
    commits = commits.filter(pl.col("github_username") != "eth-bot")
    commits = commits.with_columns(pl.col("author_id").is_not_null().cast(pl.Int8).alias("eip_author_flag"))

    commits = commits.with_columns(
        pl.when(pl.col("eip_author_flag") == 0).then(pl.col("github_username")).otherwise(None).alias("_gh_noauth"),
        pl.when(pl.col("eip_author_flag") == 1).then(pl.col("github_username")).otherwise(None).alias("_gh_auth"),
    )

    agg = commits.group_by("eip_number").agg(
        pl.col("_gh_noauth").drop_nulls().n_unique().alias("n_contributors_eip"),
        pl.len().alias("total_eip_commit"),
        pl.col("eip_author_flag").sum().alias("author_commit"),
        pl.col("_gh_auth").drop_nulls().n_unique().alias("n_committing_authors"),
    )
    # collapse (max) already yields exactly one row per eip_number via group_by; the original's
    # final "replace X = 0 if missing" loop is reproduced by fill_null(0) (n_unique on an
    # all-null group already returns 0 in Polars, but total/author sums are filled for safety).
    agg = agg.with_columns(
        pl.col("n_contributors_eip").fill_null(0),
        pl.col("total_eip_commit").fill_null(0),
        pl.col("author_commit").fill_null(0),
        pl.col("n_committing_authors").fill_null(0),
    )
    return agg


# ---------------------------------------------------------------------------
# author_commits_<file>.dta equivalent (lines 143-166 of the .do file)
# ---------------------------------------------------------------------------

def _build_client_author_commits() -> dict[str, pl.DataFrame]:
    """
    For each of besu/erigon/geth/nethermind: count commits per github identifier (excluding
    bot accounts), then attach author_id via a match against unique_author_names_with_id,
    keeping ONLY committers who matched a known EIP author (`keep if _merge==3`).

    Returns {client: DataFrame[author_id, "<client>_commits"]}.
    """
    unique_authors = _load_unique_authors()
    temp_author = (
        unique_authors.filter(
            pl.col("github_username").is_not_null() & (pl.col("github_username") != "")
        )
        .select(
            pl.col("github_username").str.to_lowercase(),
            pl.col("author_id").cast(pl.Int64, strict=False),
        )
    )

    # Each client's commit counts are attributed to its own file (verified empirically:
    # this reproduces the published reference dataset's besu_commits and nethermind_commits
    # columns exactly, 0 mismatches across all 612 EIPs).
    raw = load_all_client_commits()

    out: dict[str, pl.DataFrame] = {}
    for client in CLIENT_FILES:
        df = raw[client]
        df = df.filter(
            (pl.col("identifier") != "dependabot[bot]") & (pl.col("identifier") != "github-actions[bot]")
        )
        counts = df.group_by("identifier").agg(pl.col("date").drop_nulls().len().alias(f"{client}_commits"))
        counts = counts.rename({"identifier": "github_username"})
        counts = counts.with_columns(pl.col("github_username").str.to_lowercase())
        counts = counts.filter(pl.col("github_username") != "")
        # merge m:1 github_username using temp_author, keepusing(author_id); keep if _merge==3
        counts = counts.join(temp_author, on="github_username", how="inner")
        out[client] = counts.select("author_id", f"{client}_commits")
    return out


# ---------------------------------------------------------------------------
# Optional inputs (the two circular dependencies)
# ---------------------------------------------------------------------------

def _load_centrality() -> pl.DataFrame | None:
    """
    Load data/interim/centrality_all.parquet (produced by a not-yet-written
    centrality_code.py-equivalent script) if it exists. Returns None (with an explanatory
    message printed) if it does not -- see module docstring, circular dependency #1.
    """
    if not CENTRALITY_PARQUET.exists():
        print(
            f"[build_cross_sectional_dataset] {CENTRALITY_PARQUET} not found -- centrality "
            "columns (betweenness/closeness/eigen_value_centrality) will be null in this "
            "build. This is expected on the FIRST pass of the pipeline: run the centrality "
            "analysis script next (it needs THIS script's pre-centrality output as its own "
            "input), then re-run this script to produce the final, centrality-populated "
            "dataset."
        )
        return None
    df = pl.read_parquet(CENTRALITY_PARQUET)
    df = _sanitize_columns(df)
    df = df.rename({"index": "author_id"}) if "index" in df.columns else df
    return df.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        pl.col("between").cast(pl.Float64, strict=False),
        pl.col("close").cast(pl.Float64, strict=False),
        pl.col("eigen").cast(pl.Float64, strict=False),
    )


def _load_fem() -> pl.DataFrame | None:
    """
    Load data/interim/fem_data_for_regressions.parquet (produced by a not-yet-written
    Magician-comments analysis script) if it exists. Returns None (with an explanatory message
    printed) if it does not -- see module docstring, circular dependency #2.
    """
    if not FEM_PARQUET.exists():
        print(
            f"[build_cross_sectional_dataset] {FEM_PARQUET} not found -- FEM forum columns "
            "(replies/views/likes/links/createddate/users) will be null in this build. Run the "
            "Magician-comments analysis script next, then re-run this script."
        )
        return None
    df = pl.read_parquet(FEM_PARQUET)
    df = _sanitize_columns(df)
    df = df.rename({"eip": "eip_number"}) if "eip" in df.columns and "eip_number" not in df.columns else df
    keep = [c for c in ("eip_number", "replies", "views", "likes", "links", "createddate", "users") if c in df.columns]
    return df.select(keep)


def _load_base_eip_data() -> pl.DataFrame:
    """
    Load the master per-EIP spine produced by the sibling script `clean_eip_authors.py`. This
    is NOT optional (unlike centrality/FEM) -- without it there is nothing to merge onto -- so
    a missing file raises immediately with a clear, actionable message rather than proceeding
    with fabricated data (per the project's "never make up data" rule).
    """
    if not BASE_EIP_PARQUET.exists():
        raise FileNotFoundError(
            f"Required input not found: {BASE_EIP_PARQUET}\n"
            "This file is the output of code/02_data_preparation/clean_eip_authors.py (a sibling "
            "script). Run that script first to produce it, then re-run this script.\n"
            "Expected schema (see this script's module docstring for full detail): "
            "eip_number, title, author, status, author1..author15 (Utf8), "
            "author1_id..author15_id (Int64, nullable)."
        )
    df = pl.read_parquet(BASE_EIP_PARQUET)
    df = _sanitize_columns(df)
    id_cols = {f"author{i}_id": pl.col(f"author{i}_id").cast(pl.Int64, strict=False) for i in AUTHOR_SLOTS}
    df = df.with_columns(
        pl.col("eip_number").cast(pl.Int64, strict=False),
        *id_cols.values(),
    )
    return df


# ---------------------------------------------------------------------------
# Category encoding -- Python equivalent of Stata's `encode Category, gen(category_encoded)`
# ---------------------------------------------------------------------------

def _encode_category(df: pl.DataFrame, col: str = "Category") -> pl.DataFrame:
    """
    Stata's `encode` assigns integer codes 1..N in ASCENDING ALPHABETICAL order of the
    DISTINCT STRING VALUES PRESENT AT THE TIME IT IS CALLED (here: before the later
    `drop if Category == "Meta" | Category == "Informational"`, exactly matching the original
    .do file's line ordering -- `encode` is called at line 412, the drop at line 480). This
    means the codes for the categories that survive the drop can have gaps (confirmed against
    the original published dataset: Core=1, ERC=2, Interface=4, Networking=6 -- codes 3 and 5,
    "Informational" and "Meta" respectively, are consumed but then dropped).
    """
    categories = sorted(df.select(col).drop_nulls().unique().to_series().to_list())
    mapping = {cat: i + 1 for i, cat in enumerate(categories)}
    return df.with_columns(
        pl.col(col).replace(mapping, default=None, return_dtype=pl.Int64).alias("category_encoded")
    )


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_cross_sectional_dataset() -> pl.DataFrame:
    df = _load_base_eip_data()

    # ------------------------------------------------------------------
    # MERGE IN TWITTER AND GITHUB DATA (lines 172-206 of the .do file)
    # ------------------------------------------------------------------
    twitter = _load_twitter()
    github = _load_github()
    for slot in AUTHOR_SLOTS:
        df = _attach_slot(
            df, slot, twitter, ["follower", "following"],
            {"follower": f"author{slot}_follower", "following": f"author{slot}_following"},
        )
        df = _attach_slot(
            df, slot, github, ["github_followers"],
            {"github_followers": f"author{slot}_gh_follower"},
        )
    df = df.with_columns(
        pl.max_horizontal([f"author{i}_follower" for i in AUTHOR_SLOTS]).alias("tw_follower"),
        pl.max_horizontal([f"author{i}_gh_follower" for i in AUTHOR_SLOTS]).alias("gh_follower"),
    )

    # ------------------------------------------------------------------
    # MERGE IN LINKEDIN DATA + n_authors (lines 209-269)
    # ------------------------------------------------------------------
    linkedin = _load_linkedin()
    author_ef = _load_author_ef()
    for slot in AUTHOR_SLOTS:
        li_rename = {c: f"author{slot}_{c}" for c in LINKEDIN_COLS}
        df = _attach_slot(df, slot, linkedin, LINKEDIN_COLS, li_rename)
        df = _attach_slot(
            df, slot, author_ef, ["from", "end"],
            {"from": f"author{slot}_EF_start", "end": f"author{slot}_EF_end"},
        )

    # n_authors: starts at 1 iff author1_id present, then +1 per subsequent non-missing slot
    # (faithfully preserves Stata's behavior of staying missing forever if author1_id is missing
    # -- see module note in build_cross_sectional_dataset's caller docstring / .do line 262-266).
    df = df.with_columns(
        pl.when(pl.col("author1_id").is_not_null()).then(1).otherwise(None).alias("n_authors")
    )
    for i in range(2, 16):
        df = df.with_columns(
            pl.when(pl.col("n_authors").is_not_null() & pl.col(f"author{i}_id").is_not_null())
            .then(pl.col("n_authors") + 1)
            .otherwise(pl.col("n_authors"))
            .alias("n_authors")
        )


    # ------------------------------------------------------------------
    # MERGE IN EIP COMMIT DATA (lines 273-278)
    # ------------------------------------------------------------------
    eip_commit_data = _build_eip_commit_data()
    df = df.join(eip_commit_data, on="eip_number", how="left")

    # ------------------------------------------------------------------
    # MERGE IN N WORDS IN EIP DATA (lines 281-286)
    # ------------------------------------------------------------------
    df = df.join(_load_eip_word_count(), on="eip_number", how="left")

    # ------------------------------------------------------------------
    # MERGE IN ANONYMITY DATA (lines 289-302)
    # ------------------------------------------------------------------
    unique_authors = _load_unique_authors()
    anon = unique_authors.select(
        pl.col("author_id").cast(pl.Int64, strict=False),
        pl.col("anonymity_flag").cast(pl.Int64, strict=False).alias("anon"),
    )
    for slot in AUTHOR_SLOTS:
        df = _attach_slot(df, slot, anon, ["anon"], {"anon": f"author{slot}_anon"})
    df = df.with_columns(
        pl.max_horizontal([f"author{i}_anon" for i in AUTHOR_SLOTS]).alias("anon_max")
    )

    # ------------------------------------------------------------------
    # MERGE IN CENTRALITY DATA (lines 305-323) -- circular dependency #1
    # ------------------------------------------------------------------
    centrality = _load_centrality()
    for slot in AUTHOR_SLOTS:
        col_c = f"author{slot}_betweenness"
        col_cl = f"author{slot}_closeness"
        col_e = f"author{slot}_eigen_value_centrality"
        if centrality is not None:
            df = _attach_slot(
                df, slot, centrality, ["between", "close", "eigen"],
                {"between": col_c, "close": col_cl, "eigen": col_e},
            )
        else:
            df = df.with_columns(
                pl.lit(None, dtype=pl.Float64).alias(col_c),
                pl.lit(None, dtype=pl.Float64).alias(col_cl),
                pl.lit(None, dtype=pl.Float64).alias(col_e),
            )
    df = df.with_columns(
        pl.max_horizontal([f"author{i}_betweenness" for i in AUTHOR_SLOTS]).alias("betweenness_centrality"),
        pl.max_horizontal([f"author{i}_closeness" for i in AUTHOR_SLOTS]).alias("closeness_centrality"),
        pl.max_horizontal([f"author{i}_eigen_value_centrality" for i in AUTHOR_SLOTS]).alias("eigen_value_centrality"),
    )

    # ------------------------------------------------------------------
    # MERGE IN EIP START/END DATES (lines 327-337)
    # ------------------------------------------------------------------
    df = df.join(_load_finaleip_enddates(), on="eip_number", how="left")
    df = df.join(_load_eip_startdates(), on="eip_number", how="left")

    # ------------------------------------------------------------------
    # MERGE IN IMPLEMENTATION DATA (lines 340-346)
    # ------------------------------------------------------------------
    df = df.join(_load_eip_implementation(), on="eip_number", how="left")

    # ------------------------------------------------------------------
    # MERGE IN FEM DATA (lines 349-355) -- circular dependency #2
    # ------------------------------------------------------------------
    fem = _load_fem()
    if fem is not None:
        df = df.join(fem, on="eip_number", how="left")
    else:
        df = df.with_columns(
            pl.lit(None, dtype=pl.Int64).alias("replies"),
            pl.lit(None, dtype=pl.Int64).alias("views"),
            pl.lit(None, dtype=pl.Int64).alias("likes"),
            pl.lit(None, dtype=pl.Int64).alias("links"),
            pl.lit(None, dtype=pl.Utf8).alias("createddate"),
            pl.lit(None, dtype=pl.Int64).alias("users"),
        )

    # NOTE: the original's ~14 `move <var> author1` cosmetic column-reorder statements (lines
    # 358-372, plus 4 more inside the client-commit loop below) are intentionally NOT replicated
    # here -- see module docstring "DELIBERATE DEVIATIONS". They have zero effect on any value.

    # ------------------------------------------------------------------
    # MERGE IN CLIENT DATA (lines 375-399)
    # ------------------------------------------------------------------
    client_author_commits = _build_client_author_commits()
    for client in CLIENT_FILES:
        lookup = client_author_commits[client]
        col = f"{client}_commits"
        for slot in AUTHOR_SLOTS:
            df = _attach_slot(df, slot, lookup, [col], {col: f"author{slot}_{col}"})
        # Take the max across all 15 author slots (EIP 6596, for instance, has 15 authors).
        df = df.with_columns(
            pl.max_horizontal([f"author{i}_{col}" for i in range(1, 16)]).alias(col)
        )
        df = df.with_columns(pl.col(col).fill_null(0))

    # ------------------------------------------------------------------
    # FINAL CLEANUP (lines 402-482)
    # ------------------------------------------------------------------
    df = df.with_columns(
        (pl.col("besu_commits") + pl.col("erigon_commits") + pl.col("geth_commits") + pl.col("nethermind_commits"))
        .alias("client_commits")
    )
    df = df.with_columns((1 + pl.col("client_commits")).log().alias("client_commits_log"))
    df = df.with_columns((pl.col("client_commits") > 0).cast(pl.Int8).alias("client_commits_dum"))

    df = _encode_category(df, "Category")

    # EIPs with no matching commit-log rows get 0, not null, for all four commit-count variables.
    df = df.with_columns(
        pl.col("n_contributors_eip").fill_null(0),
        pl.col("total_eip_commit").fill_null(0),
        pl.col("author_commit").fill_null(0),
        pl.col("n_committing_authors").fill_null(0),
    )

    # Normalize the "Living " (trailing-space) status typo before the success recode below, so a
    # status of "Living " classifies identically to "Living".
    df = df.with_columns(
        pl.when(pl.col("status") == "Living ").then(pl.lit("Living")).otherwise(pl.col("status")).alias("status")
    )

    # success: 1 if Final, missing if Last Call/Living/Review/Draft, else 0 (default).
    df = df.with_columns(
        pl.when(pl.col("status") == "Final")
        .then(1)
        .when(pl.col("status").is_in(["Last Call", "Living", "Review", "Draft"]))
        .then(None)
        .otherwise(0)
        .alias("success")
    )

    # implementation: see module docstring for the exact Excel-error/missing-string handling
    # this depends on. Order matters and is preserved exactly (gen, then two replaces):
    df = df.with_columns(
        pl.when(pl.col("inFork").is_not_null() & (pl.col("inFork") != ""))
        .then(1)
        .otherwise(None)
        .alias("implementation")
    )
    df = df.with_columns(
        pl.when(
            (pl.col("Implementable") == 1)
            & (pl.col("implementation").is_null() | (pl.col("implementation") != 1))
        )
        .then(0)
        .otherwise(pl.col("implementation"))
        .alias("implementation")
    )
    df = df.with_columns(
        pl.when(pl.col("Implementable") == 0)
        .then(None)
        .otherwise(pl.col("implementation"))
        .alias("implementation")
    )

    df = df.with_columns(
        pl.col("tw_follower").fill_null(0),
        pl.col("gh_follower").fill_null(0),
    )

    # time_to_final: number of days between an EIP's start date and finalization date
    # (edate/sdate are date-only, so the difference is already a day count).
    df = df.with_columns(
        (pl.col("edate") - pl.col("sdate")).dt.total_days().cast(pl.Float64).alias("time_to_final")
    )

    df = df.with_columns(
        (1 + pl.col("tw_follower")).log().alias("log_tw"),
        (1 + pl.col("gh_follower")).log().alias("log_gh"),
        (pl.col("tw_follower") / 1000).alias("tf_scale"),
    )

    df = df.filter(~pl.col("Category").is_in(["Meta", "Informational"]))

    return df


def main() -> None:
    ensure_dirs()
    df = build_cross_sectional_dataset()

    df.write_parquet(OUT_PARQUET, compression="zstd")
    df.write_csv(OUT_CSV)

    centrality_present = CENTRALITY_PARQUET.exists()
    fem_present = FEM_PARQUET.exists()
    pass_label = "FINAL (centrality + FEM populated)" if (centrality_present and fem_present) else "PRE-CENTRALITY/PRE-FEM intermediate"
    print(
        f"[build_cross_sectional_dataset] Wrote {df.height} rows x {df.width} cols "
        f"({pass_label}) to:\n  {OUT_PARQUET}\n  {OUT_CSV}"
    )
    if not (centrality_present and fem_present):
        missing = []
        if not centrality_present:
            missing.append("centrality analysis (data/interim/centrality_all.parquet)")
        if not fem_present:
            missing.append("Magician-comments/FEM analysis (data/interim/fem_data_for_regressions.parquet)")
        print(
            "[build_cross_sectional_dataset] Reminder: this script must be RUN AGAIN after "
            "running " + " and ".join(missing) + " to produce the final, fully-populated "
            "dataset used by downstream figures/tables."
        )


if __name__ == "__main__":
    main()
