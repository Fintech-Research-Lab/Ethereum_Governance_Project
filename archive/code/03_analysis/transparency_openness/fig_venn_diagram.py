"""
fig_venn_diagram.py
======================

Reproduces **Figure 5** of:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: **Section III**. Figure 5 caption: "Venn diagram of the individuals involved in
EIP production, AllCoreDevs meetings, and client implementation."

Ported from (both read in full):
  1. `Analysis\\Meeting Attendees and Ethereum Community Analysis\\Community Engagement
     Analysis.py` -- builds the `contributors_only` / `everyone` overlap tables, the
     ~15-row "Result" overlap-count table, and the 3-set Venn diagram itself.
  2. `Analysis\\Meeting Attendees and Ethereum Community Analysis\\Top10_in_community.py` --
     supplementary top-10-most-active-people overlap statistics (not a numbered figure/table on
     its own, but the source of several concentration statistics referenced in the paper's text,
     e.g. the share of implemented Core/Networking EIPs attributable to top-10-author
     concentration).

Outputs
-------
- `output/figures/figure_05_venn_diagram.png` -- the Figure 5 Venn diagram.
- `data/interim/unique_names_allplayers.parquet` -- the `everyone_dep` overlap table (one row
  per distinct name appearing in any of the four roles; `Attendee_Name`/`Author_Name`/
  `Contributor_Name`/`Client_Name`, null where that role doesn't apply to that row).
- `data/interim/unique_contributorsonly_final.parquet` -- contributors who are NOT also EIP
  authors (`Name`, `Anonymity_Flag`). This is the file `code/02_data_preparation/
  name_cleaning_pipeline.py`'s docstring explicitly flags as "not produced here -- built later
  by Community Engagement Analysis.py ... a future 'community engagement' conversion task" --
  i.e. this script.
- `data/interim/community_overlap_stats.parquet` -- the ~15-row "Result" overlap-count table.
- `data/interim/top10_community_overlap.parquet` -- the 22-row "Common" top-10-overlap
  percentage table from `Top10_in_community.py`.
- `data/interim/top10_by_category.parquet` -- the original's `top10.csv`: top-10
  clients/attendees/authors placed side by side, POSITIONALLY (see "Known issue" #4 below).

Design notes
-------------
1. **Client commit data.** The Top-10 client-committer section loads each client's own commit
   history via `load_client_commits()` (see `utils/client_commits.py`) -- no cross-client
   substitution. The Venn-diagram / overlap-table half of this script never reads a client-commit
   file directly at all; it consumes the already-name-cleaned `unique_clients_final`
   (`name_cleaning_pipeline.py::build_unique_clients()`), which is built from the same correct,
   per-client data.
2. **`top10.csv` (`top10_by_category.parquet`) intentionally holds three independent rankings
   side by side, not a join.** The top-10 clients / attendees / authors lists are three separate
   rankings of different sizes and populations; concatenating them horizontally (keeping each
   list's columns distinctly named) juxtaposes them for the reader without implying that row *i*
   of one ranking corresponds to row *i* of another.

Not computed (would have no effect on any published output)
----------------------------------------------------------------
Two supplementary lookups are not computed here since nothing downstream references them:
`missed_authors_in_github` (authors present in the roster but absent from the cleaned contributor
list -- the complement of `contributors_only`) and `author_contributors` (authors who are also in
the raw EIP-commit-log contributor list). Similarly, `fig_anonymity.py` does not read this
script's `unique_contributorsonly_final` output back, since Figure 4 does not need it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from matplotlib_venn import venn3

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # add this folder for the sibling import

from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_FIGURES, ensure_dirs  # noqa: E402
from utils.client_commits import load_client_commits  # noqa: E402

# Reused, not duplicated, per this package's established sibling-import precedent (e.g.
# code/03_analysis/regressions/table1_summary_stats.py importing from table3_finalization_regressions.py).
from fig_anonymity import _read_latin1_csv_as_utf8, _row_wide_scalar_assign, _top_n_by_count  # noqa: E402

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
RAW_AUTHOR_ROSTER_CSV = DATA_RAW / "eip_registry" / "unique_author_names_with_id.csv"
RAW_EIP_COMMIT_XLSX = DATA_RAW / "commits" / "eip_commit_beg.xlsx"
RAW_DEV_CALLS_ATTENDEES_CSV = DATA_RAW / "meetings" / "dev_calls_attendees_standardized_v2.csv"
CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"

ATTENDEES_FINAL_PATH = DATA_INTERIM / "unique_attendees_final.parquet"
CLIENTS_FINAL_PATH = DATA_INTERIM / "unique_clients_final.parquet"
CONTRIBUTORS_FINAL_PATH = DATA_INTERIM / "unique_contributors_final.parquet"

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
OUTPUT_FIGURE_PATH = OUTPUT_FIGURES / "figure_05_venn_diagram.png"
OUTPUT_EVERYONE_PATH = DATA_INTERIM / "unique_names_allplayers.parquet"
OUTPUT_CONTRIBUTORSONLY_PATH = DATA_INTERIM / "unique_contributorsonly_final.parquet"
OUTPUT_RESULT_STATS_PATH = DATA_INTERIM / "community_overlap_stats.parquet"
OUTPUT_TOP10_OVERLAP_PATH = DATA_INTERIM / "top10_community_overlap.parquet"
OUTPUT_TOP10_TABLE_PATH = DATA_INTERIM / "top10_by_category.parquet"

AUTHOR_ID_COLS = [f"author{i}_id" for i in range(1, 16)]
AUTHOR_NAME_COLS = [f"author{i}" for i in range(1, 16)]


# ---------------------------------------------------------------------------
# Small local helpers
# ---------------------------------------------------------------------------
def _unique_preserve_order(values: list) -> list:
    """Faithful port of pandas' `Series.unique()` / `pd.unique()`: de-duplicate while preserving
    FIRST-OCCURRENCE order (deterministic, unlike a `set()`-based dedup)."""
    seen = set()
    out = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _clean_text(text: str) -> str | None:
    """Local duplicate of `code/02_data_preparation/clean_eip_authors.py::clean_text` (see that
    module for the canonical version; duplicated here per this package's established
    small-helper-duplication convention rather than a cross-stage import)."""
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.strip()
    return None if text == "" else text


def _flatten_meeting_attendees() -> list[str]:
    """
    Local duplicate of `name_cleaning_pipeline.py::flatten_meeting_attendees()`, reproducing the
    RAW (uncleaned) per-mention attendee list that `Top10_in_community.py`'s original reads from
    `flat_list_meeting_attendees.csv` -- i.e. BEFORE the fuzzy-match name-cleaning cascade, so
    the same person appearing under two slightly different spellings across meetings is counted
    as two different "top 10 attendee" candidates here. This is not a bug we are introducing --
    it is what the original script actually reads (the raw flat list, not `unique_attendees_final`).
    """
    dat = _read_latin1_csv_as_utf8(RAW_DEV_CALLS_ATTENDEES_CSV)
    flat_names: list[str] = []
    for attendees_field in dat["Attendees"].to_list():
        if attendees_field is None:
            continue
        tokens = attendees_field.split(",")
        cleaned = [_clean_text(tok) for tok in tokens]
        flat_names.extend(c for c in cleaned if c is not None)
    return flat_names


def _load_top20_style_client_commits() -> dict[str, pl.DataFrame]:
    """
    Load and name-normalize all four clients' commit histories, matching
    `fig_anonymity.py::compute_client_top20_anonymity_flags`'s loading section (minus the
    Anonymity_Flag computation, which isn't needed for the Top-10 community-overlap stats).
    """
    geth = load_client_commits("geth")
    besu = load_client_commits("besu")
    erigon = load_client_commits("erigon")
    nethermind = load_client_commits("nethermind")

    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "Tomasz Kajetan Sta?czak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "Tomasz K. Stanczak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "tkstanczak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "github-actions[bot]", "")
    erigon = _row_wide_scalar_assign(erigon, pl.col("author") == "alex.sharov", "Alex Sharov")

    return {"geth": geth, "besu": besu, "erigon": erigon, "nethermind": nethermind.filter(pl.col("author") != "")}


# ===========================================================================
# Part A -- Community Engagement Analysis.py (Venn diagram + overlap "Result" table)
# ===========================================================================
def compute_all_contributors(eip_commit: pl.DataFrame, author_roster: pl.DataFrame) -> pl.DataFrame:
    """
    Port of:
        all_contributors = pd.merge(eip_commit, authors, left_on='Username',
                                     right_on='GitHub_Username', how='left', indicator=True)
        all_contributors = pd.unique(all_contributors['Author'])

    The merge's `indicator=True` result is never actually used to filter anything in the
    original (a left join preserves every `eip_commit` row regardless), so this is functionally
    just "the unique `Author` values in the EIP commit log, order-preserving" -- ported as such,
    but via the same left-join shape for structural fidelity.
    """
    joined = eip_commit.join(
        author_roster.select(["Full_Name", "GitHub_Username"]),
        left_on="Username",
        right_on="GitHub_Username",
        how="left",
    )
    names = _unique_preserve_order(joined["Author"].to_list())
    return pl.DataFrame({"Name": names})


def compute_contributors_only(author_roster: pl.DataFrame, cleaned_contributors: pl.DataFrame) -> pl.DataFrame:
    """
    Port of:
        authors_and_contributors = pd.merge(authors, cleaned_contributors, left_on='Full_Name',
                                             right_on='Name', how='outer', indicator=True)
        contributors_only = authors_and_contributors[authors_and_contributors['_merge']=='right_only']
        contributors_only.to_csv(".../unique_contributorsonly_final.csv", index=False)

    `_merge=='right_only'` == present in `cleaned_contributors` but with no matching `Full_Name`
    in the author roster, i.e. "a contributor who is not already an EIP author" -- reproduced
    here as `pl.col('Full_Name').is_null()` after an outer join (Polars keeps both `Full_Name`
    and `Name` when the join keys have different names, so a right-only row has `Full_Name` null
    and `Name` populated -- confirmed empirically).
    """
    joined = author_roster.join(
        cleaned_contributors.select(["Name", "Anonymity_Flag"]),
        left_on="Full_Name",
        right_on="Name",
        how="outer",
        suffix="_contrib",
    )
    contributors_only = joined.filter(pl.col("Full_Name").is_null())
    return contributors_only.select(["Name", "Anonymity_Flag_contrib"]).rename({"Anonymity_Flag_contrib": "Anonymity_Flag"})


def compute_authors_from_cross_sectional(author_roster: pl.DataFrame) -> pl.DataFrame:
    """
    Port of:
        cs = cs[[author1_id..author15_id, sdate]]
        author_df = cs.melt(...)
        author_df = author_df[pd.notnull(author_df['Author_id'])]
        author_df = pd.merge(author_df, authors, left_on='Author_id', right_on='author_id', how='left')
        authors = author_df['Full_Name'].unique()
        authors = pd.DataFrame(authors, columns=['Author_Name'])

    Note the LEFT join here (unlike `fig_anonymity.py`'s INNER join for the same melt): if any
    `Author_id` fails to match the roster, `Full_Name` is null for that row, and `.unique()`
    would include that null as one more "unique" value -- preserved faithfully (a null can end
    up inside the Venn-diagram's `unique_authors` set below, inflating its cardinality by at
    most one; harmless in practice since every observed Author_id here matches the roster, but
    not fixed away in case future data ever has an unmatched author_id).
    """
    cs = pl.read_parquet(CROSS_SECTIONAL_PATH).select([*AUTHOR_ID_COLS, "sdate"])
    melted = cs.melt(id_vars="sdate", value_vars=AUTHOR_ID_COLS, variable_name="number", value_name="Author_id")
    melted = melted.filter(pl.col("Author_id").is_not_null())
    joined = melted.join(
        author_roster.select(["author_id", "Full_Name"]), left_on="Author_id", right_on="author_id", how="left"
    )
    names = _unique_preserve_order(joined["Full_Name"].to_list())
    return pl.DataFrame({"Author_Name": names})


def build_everyone(attendees: pl.DataFrame, authors_cs: pl.DataFrame, all_contributors: pl.DataFrame, clients: pl.DataFrame) -> pl.DataFrame:
    """
    Port of the three successive outer joins building `everyone_dep`:
        attendees_and_author = merge(attendees, authors, Attendee_Name==Author_Name, outer)
        attendee_author_and_contributor = merge(attendees_and_author, all_contributors,
                                                  Author_Name==Contributor_Name, outer)
        everyone = merge(attendee_author_and_contributor, clients, Author_Name==Client_Name, outer)
        everyone_dep = everyone.drop(columns=[the pandas merge-indicator columns])

    (The original also `.sort_values(...)`s after each merge and drops the `_merge` indicator
    columns; row ORDER is cosmetic only for a CSV a human might skim, and has zero effect on any
    downstream count/statistic, so this port does not reproduce that specific sort order.)
    """
    contributor_renamed = all_contributors.rename({"Name": "Contributor_Name"})

    step1 = attendees.join(authors_cs, left_on="Attendee_Name", right_on="Author_Name", how="outer")
    step1 = step1.with_columns(pl.coalesce(["Author_Name", "Author_Name_right"]).alias("Author_Name")) if "Author_Name_right" in step1.columns else step1
    # NOTE: with distinct join-key names (Attendee_Name vs Author_Name), Polars keeps both
    # columns as-is (no "_right" suffix is created) -- the conditional coalesce above is a no-op
    # safety net, confirmed empirically not to trigger, kept only for robustness across Polars
    # versions.

    step2 = step1.join(contributor_renamed, left_on="Author_Name", right_on="Contributor_Name", how="outer")
    everyone = step2.join(clients, left_on="Author_Name", right_on="Client_Name", how="outer")

    return everyone.select(["Attendee_Name", "Author_Name", "Contributor_Name", "Client_Name"])


def compute_result_stats(everyone_dep: pl.DataFrame, attendees: pl.DataFrame, authors_cs: pl.DataFrame, all_contributors: pl.DataFrame, clients: pl.DataFrame) -> pl.DataFrame:
    """Port of the 15-row `Result` DataFrame (original lines 96-137)."""

    def _both_notnull(*cols: str) -> int:
        expr = pl.col(cols[0]).is_not_null()
        for c in cols[1:]:
            expr = expr & pl.col(c).is_not_null()
        return everyone_dep.filter(expr).height

    rows: list[tuple[str, int]] = [
        ("Attendees", attendees.height),
        ("Authors", authors_cs.height),
        ("EIP Contributors", all_contributors.height),
        ("Client Contributors", clients.height),
        ("Authors who Attended Meetings", _both_notnull("Author_Name", "Attendee_Name")),
        ("Contributors who Attended Meetings", _both_notnull("Contributor_Name", "Attendee_Name")),
        ("Clients who Attended Meetings", _both_notnull("Client_Name", "Attendee_Name")),
        ("Authors who are also Contributors", _both_notnull("Author_Name", "Contributor_Name")),
        ("Authors who are also Clients", _both_notnull("Author_Name", "Client_Name")),
        ("Client who are also Contributors", _both_notnull("Contributor_Name", "Client_Name")),
        ("Authors who are Clients and also attended meetings", _both_notnull("Author_Name", "Client_Name", "Attendee_Name")),
        ("Authors who are Contributors and also attended meetings", _both_notnull("Author_Name", "Contributor_Name", "Attendee_Name")),
        ("Authors who are Clients and Contributors", _both_notnull("Author_Name", "Contributor_Name", "Client_Name")),
        ("Contributors who are Clients and also attended meetings", _both_notnull("Contributor_Name", "Client_Name", "Attendee_Name")),
        ("People who did everything", _both_notnull("Contributor_Name", "Client_Name", "Attendee_Name", "Author_Name")),
    ]
    return pl.DataFrame({"Issue": [r[0] for r in rows], "Result": [r[1] for r in rows]})


def make_venn_figure(attendees: pl.DataFrame, clients: pl.DataFrame, authors_cs: pl.DataFrame) -> None:
    """Port of the `venn3([unique_attendees, unique_clients, unique_authors], (...))` call."""
    unique_attendees = set(attendees["Attendee_Name"].to_list())
    unique_clients = set(clients["Client_Name"].to_list())
    unique_authors = set(authors_cs["Author_Name"].to_list())  # may include a null; see docstring above

    fig, ax = plt.subplots(figsize=(7, 7))
    venn3([unique_attendees, unique_clients, unique_authors], ("AllCoreDevs Attendees", "Client Contributors", "EIP Authors"), ax=ax)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURE_PATH)
    plt.close(fig)


# ===========================================================================
# Part B -- Top10_in_community.py (supplementary top-10 overlap statistics)
# ===========================================================================
def compute_top10_authors() -> pl.DataFrame:
    """Port of: `authors = cs.loc[:,'author1':'author15'].values.flatten(); authors =
    authors[authors != '']; top10_authors = authors.groupby(...).size().sort_values(...).head(10)`."""
    cs = pl.read_parquet(CROSS_SECTIONAL_PATH)
    names: list[str] = []
    for col in AUTHOR_NAME_COLS:
        names.extend(v for v in cs[col].to_list() if v not in (None, ""))
    counts = (
        pl.DataFrame({"Author_Name": names})
        .group_by("Author_Name")
        .agg(pl.len().alias("n"))
        .sort("Author_Name")
        .sort("n", descending=True, maintain_order=True)
        .head(10)
    )
    return counts.rename({"n": "EIP_Authored"})


def compute_top10_attendees() -> pl.DataFrame:
    """Port of: `attendees = pd.read_csv(".../flat_list_meeting_attendees.csv"); top10_attendees =
    attendees.groupby("Attendees").size().sort_values(...).head(10)`."""
    flat_names = _flatten_meeting_attendees()
    counts = (
        pl.DataFrame({"Attendees": flat_names})
        .group_by("Attendees")
        .agg(pl.len().alias("n"))
        .sort("Attendees")
        .sort("n", descending=True, maintain_order=True)
        .head(10)
    )
    return counts.rename({"n": "Meetings_Attended"})


def compute_top10_clients() -> pl.DataFrame:
    """
    Port of the geth/besu/erigon/nethermind top-10-per-client commit counts, re-aggregated by
    summing across clients (`clients.groupby('Client_Name')['date'].sum()`) before re-ranking --
    i.e. if the same committer name appears in more than one client's own top-10, their counts
    are SUMMED before the final top-10-overall cut. See module docstring, "Confirmed bugs" #1-#2
    (this function reproduces both).
    """
    commits = _load_top20_style_client_commits()
    per_client_top10 = [
        _top_n_by_count(commits[client], 10).rename({"author": "Client_Name"}) for client in ("geth", "besu", "erigon", "nethermind")
    ]
    combined = pl.concat(per_client_top10)
    return (
        combined.group_by("Client_Name")
        .agg(pl.col("n").sum().alias("Total_Commits"))
        .sort("Client_Name")
        .sort("Total_Commits", descending=True, maintain_order=True)
        .head(10)
    )


def compute_common_stats(everyone_dep: pl.DataFrame, top10_authors: pl.DataFrame, top10_attendees: pl.DataFrame, top10_clients: pl.DataFrame) -> pl.DataFrame:
    """
    Port of the 22-row `Common` DataFrame (original lines 74-96), including the confirmed
    label/formula mismatch on row 21 (see module docstring, "Confirmed bugs" #3).
    """

    def _pool(*cols: str) -> tuple[set, int]:
        filtered = everyone_dep.filter(pl.all_horizontal([pl.col(c).is_not_null() for c in cols]))
        names: set = set()
        for c in cols:
            names.update(filtered[c].to_list())
        names.discard(None)
        return names, len(names)

    all_three, all_three_n = _pool("Attendee_Name", "Author_Name", "Client_Name")
    clients_and_authors, clients_and_authors_n = _pool("Client_Name", "Author_Name")
    attendees_and_authors, attendees_and_authors_n = _pool("Attendee_Name", "Author_Name")
    clients_and_attendees, clients_and_attendees_n = _pool("Client_Name", "Attendee_Name")

    t10_authors = top10_authors["Author_Name"].to_list()
    t10_attendees = top10_attendees["Attendees"].to_list()
    t10_clients = top10_clients["Client_Name"].to_list()

    def _isin_sum(names: list, pool: set) -> int:
        return sum(1 for n in names if n in pool)

    rows: list[tuple[str, float]] = [
        ("What percent of people who do everything are top 10 authors", _isin_sum(t10_authors, all_three) / all_three_n),
        ("What percent of people who do everything are top 10 attendees", _isin_sum(t10_attendees, all_three) / all_three_n),
        ("What percent of people who do everything are top 10 clients", _isin_sum(t10_clients, all_three) / all_three_n),
        ("What percent of people who are clients and authors are top 10 authors", _isin_sum(t10_authors, clients_and_authors) / clients_and_authors_n),
        ("What percent of people who are clients and authors are top 10 clients", _isin_sum(t10_clients, clients_and_authors) / clients_and_authors_n),
        ("What percent of people who are attendees and authors are top 10 authors", _isin_sum(t10_authors, attendees_and_authors) / attendees_and_authors_n),
        ("What percent of people who are attendees and authors are top 10 attendees", _isin_sum(t10_attendees, attendees_and_authors) / attendees_and_authors_n),
        ("What percent of people who are clients and attendees are top 10 attendees", _isin_sum(t10_attendees, clients_and_attendees) / clients_and_attendees_n),
        ("What percent of people who are clients and attendees are top 10 clients", _isin_sum(t10_clients, clients_and_attendees) / clients_and_attendees_n),
        ("Percent of top 10 authors who do everything", _isin_sum(t10_authors, all_three) / len(t10_authors)),
        ("Percent of top 10 clients who do everything", _isin_sum(t10_clients, all_three) / len(t10_clients)),
        ("Percent of top 10 attendees who do everything", _isin_sum(t10_attendees, all_three) / len(t10_attendees)),
        ("Percent of top 10 authors who are also clients", _isin_sum(t10_authors, clients_and_authors) / len(t10_authors)),
        ("Percent of top 10 clients who are also authors", _isin_sum(t10_clients, clients_and_authors) / len(t10_clients)),
        ("Percent of top 10 attendees who are also authors", _isin_sum(t10_attendees, attendees_and_authors) / len(t10_attendees)),
        ("Percent of top 10 authors who are also attendees", _isin_sum(t10_authors, attendees_and_authors) / len(t10_authors)),
        ("Percent of top 10 attendees who are also clients", _isin_sum(t10_attendees, clients_and_attendees) / len(t10_attendees)),
        ("Percent of top 10 clients who are also attendees", _isin_sum(t10_clients, clients_and_attendees) / len(t10_clients)),
        (
            "Percent of people who do everything that are either top 10 clients or authors or attendees",
            sum(1 for n in all_three if (n in t10_clients) or (n in t10_authors) or (n in t10_attendees)) / all_three_n,
        ),
        (
            "Percent of authors and clients that are either top 10 clients or top 10 authors",
            sum(1 for n in clients_and_authors if (n in t10_clients) or (n in t10_authors)) / clients_and_authors_n,
        ),
        (
            "Percent of attendees and clients that are either top 10 clients or top 10 authors",
            sum(1 for n in clients_and_attendees if (n in t10_clients) or (n in t10_authors)) / clients_and_attendees_n,
        ),
        (
            "Percent of authors and attendees that are either top 10 authors or top 10 attendees",
            sum(1 for n in attendees_and_authors if (n in t10_authors) or (n in t10_attendees)) / attendees_and_authors_n,
        ),
    ]
    return pl.DataFrame({"Common": [r[0] for r in rows], "Result": [r[1] for r in rows]})


def build_top10_table(top10_clients: pl.DataFrame, top10_attendees: pl.DataFrame, top10_authors: pl.DataFrame) -> pl.DataFrame:
    """
    Place the three independent top-10 rankings (clients, attendees, authors) side by side in
    one table for easy side-by-side reading. This is a juxtaposition, not a join: row *i* of the
    client ranking has no relationship to row *i* of the attendee or author ranking. Each
    category's columns keep distinct names so this is never mistaken for a join downstream.
    """
    for name, df in (("clients", top10_clients), ("attendees", top10_attendees), ("authors", top10_authors)):
        if df.height != 10:
            raise ValueError(
                f"build_top10_table: expected exactly 10 rows for top10_{name}, got {df.height}. "
                "The original's positional pd.concat(axis=1) assumes all three lists are the same "
                "length; this port raises rather than silently padding/misaligning."
            )
    return pl.concat([top10_clients, top10_attendees, top10_authors], how="horizontal")


def main() -> None:
    ensure_dirs()

    clients = pl.read_parquet(CLIENTS_FINAL_PATH).select("Name").rename({"Name": "Client_Name"})
    attendees = pl.read_parquet(ATTENDEES_FINAL_PATH).select("Name").rename({"Name": "Attendee_Name"})
    # Plain (default utf-8) read, matching Community Engagement Analysis.py's own encoding
    # choice for this file -- see module docstring's "Encoding inconsistency" section.
    author_roster = pl.read_csv(RAW_AUTHOR_ROSTER_CSV)
    cleaned_contributors = pl.read_parquet(CONTRIBUTORS_FINAL_PATH)
    eip_commit = pl.read_excel(RAW_EIP_COMMIT_XLSX)

    all_contributors = compute_all_contributors(eip_commit, author_roster)
    contributors_only = compute_contributors_only(author_roster, cleaned_contributors)
    authors_cs = compute_authors_from_cross_sectional(author_roster)

    everyone_dep = build_everyone(attendees, authors_cs, all_contributors, clients)
    result_stats = compute_result_stats(everyone_dep, attendees, authors_cs, all_contributors, clients)
    make_venn_figure(attendees, clients, authors_cs)

    top10_authors = compute_top10_authors()
    top10_attendees = compute_top10_attendees()
    top10_clients = compute_top10_clients()
    common_stats = compute_common_stats(everyone_dep, top10_authors, top10_attendees, top10_clients)
    top10_table = build_top10_table(top10_clients, top10_attendees, top10_authors)

    everyone_dep.write_parquet(OUTPUT_EVERYONE_PATH, compression="zstd")
    contributors_only.write_parquet(OUTPUT_CONTRIBUTORSONLY_PATH, compression="zstd")
    result_stats.write_parquet(OUTPUT_RESULT_STATS_PATH, compression="zstd")
    common_stats.write_parquet(OUTPUT_TOP10_OVERLAP_PATH, compression="zstd")
    top10_table.write_parquet(OUTPUT_TOP10_TABLE_PATH, compression="zstd")

    print(f"Wrote {OUTPUT_FIGURE_PATH}")
    print(f"Wrote {OUTPUT_EVERYONE_PATH} ({everyone_dep.height} rows)")
    print(f"Wrote {OUTPUT_CONTRIBUTORSONLY_PATH} ({contributors_only.height} rows)")
    print(f"Wrote {OUTPUT_RESULT_STATS_PATH} ({result_stats.height} rows)")
    print(f"Wrote {OUTPUT_TOP10_OVERLAP_PATH} ({common_stats.height} rows)")
    print(f"Wrote {OUTPUT_TOP10_TABLE_PATH} ({top10_table.height} rows)")


if __name__ == "__main__":
    main()
