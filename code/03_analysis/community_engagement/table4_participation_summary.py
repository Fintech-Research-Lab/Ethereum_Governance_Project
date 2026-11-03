"""
table4_participation_summary.py
=================================

Produces **Table 4** of:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: III.B (community engagement), subsection \\ref{subsec:concentration_EIP_Discussion}
("Concentration in EIP Discussion").

What this table is
-------------------
A three-panel summary-statistics table (Mean, Median, Std. Dev., Min, Max). Panels A and B are
per-EIP, over the paper's full 612-EIP sample; Panel C is per-MEETING, not per-EIP -- see the
note below for why.

    Panel A. Fellowship of Ethereum Magicians (FEM) forum, per EIP -- Comments, Views, Likes,
              Active Participants (unique commenters).
    Panel B. GitHub, per EIP -- Commits, Comment, Reviews (reviews + inline review comments
              combined).
    Panel C. AllCoreDevs calls, per MEETING -- Active Participants per Meeting (unique
              attendees at a call, 2015 onward).

Panels A and B are zero-filled over the full 612-EIP sample (an EIP with no FEM thread or no
GitHub activity is a genuine zero, not a missing value).

Why Panel C is per-meeting, not per-EIP (history)
----------------------------------------------------
This table originally also reported AllCoreDevs participation per EIP (unique attendees across
every meeting that discussed that EIP, zero-filled over all 612 EIPs). That number came out to a
mean of ~7, which looked inconsistent with the paper's own text/Figure 14a ("~20 individuals
actively attend each call on average") -- in fact both were correct, just different populations:
only 132 of 612 EIPs (21.6%) are ever discussed at an AllCoreDevs call at all, so the per-EIP
average was being dragged down by the 78.4% of EIPs that never reach ACD. Per explicit request,
Panel C now reports the per-MEETING statistic directly instead (the same quantity Figure 14a's
"~20 per call" is built from), so it is directly comparable to the text rather than requiring
this caveat every time it's read.

New raw data source: data/raw/github/github_activity_clean.csv
-----------------------------------------------------------------
This script introduces a GitHub PR/issue-comment-and-review dataset that was not previously
part of this package (one row per comment/review/review-comment event, columns `eip`, `source`,
`ref`, `kind`, `user`, `at`; `kind` in {"comment", "review", "review_comment"}). It was explored
first as an off-pipeline side analysis before being promoted into the paper as Table 4 -- see
`PIPELINE_TODO.md` for the full history. Two bot accounts are excluded (`eip-automerger`,
`maxrobot`; confirmed by scanning every unique `user` value for bot-like names -- no others
found). This is a distinct GitHub signal from the existing `data/raw/commits/eip_commit_beg.xlsx`
commit log (used by `fig_commit_timing.py` for Figures 13/15, and reused here unchanged for this
table's "Commits" row): commits are actual code changes, while this new file captures
feedback/review activity with no code change.

AllCoreDevs per-meeting attendee counting
--------------------------------------------
Reuses the SAME cleaned meeting-attendee panel construction as
`fig_commit_timing.py::_build_attendee_meeting_panel()` (flatten
`dev_calls_attendees_standardized_v2.csv`, apply `clean_text()`, then the `Mapping_File.csv`
name-correction map, restricted to meetings from 2015 onward) rather than a naive comma-split, so
this is the exact same per-meeting unique-attendee quantity Figure 14a's
`make_attendees_by_year()` computes (just not broken out by year) -- confirmed to reproduce the
same ~20-per-call magnitude stated in the paper's text (mean 20.82 across 142 meetings).

Output
------
`output/tables/participation_summary.tex` (Table 4), via `utils.reg_tables.format_panel_stats_table`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02_data_preparation"))

from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_TABLES, ensure_dirs  # noqa: E402
from clean_eip_authors import clean_text, _read_latin1_csv_as_utf8  # noqa: E402
from utils.reg_tables import format_panel_stats_table  # noqa: E402

CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
FEM_INTERIM_PATH = DATA_INTERIM / "fem_data_for_regressions.parquet"
GITHUB_COMMIT_XLSX = DATA_RAW / "commits" / "eip_commit_beg.xlsx"
GITHUB_ACTIVITY_CSV = DATA_RAW / "github" / "github_activity_clean.csv"
CALLS_CSV = DATA_RAW / "meetings" / "calls_updated_standardized.csv"
RAW_DEV_CALLS_ATTENDEES_CSV = DATA_RAW / "meetings" / "dev_calls_attendees_standardized_v2.csv"
MAPPING_FILE_CSV = DATA_RAW / "name_cleaning_manual" / "Mapping_File.csv"

GITHUB_BOT_USERS = {"eip-automerger", "maxrobot"}
GITHUB_COMMIT_BOT_USERNAME = "eth-bot"  # same exclusion as fig_commit_timing.py's make_commits_per_eip()


def _eip_pool() -> pl.DataFrame:
    """The paper's 612-EIP sample (one row, column `eip`)."""
    return (
        pl.read_parquet(CROSS_SECTIONAL_PATH)
        .select(pl.col("eip_number").alias("eip"))
        .unique()
    )


# =============================================================================
# Panel A: FEM forum
# =============================================================================
def _fem_panel(pool: pl.DataFrame) -> pl.DataFrame:
    """Reads the already-built FEM interim dataset (one row per EIP with a matching FEM
    thread; see fig_fem_engagement.py) and zero-fills it over the full 612-EIP pool."""
    fem = pl.read_parquet(FEM_INTERIM_PATH).select(
        pl.col("eip"),
        pl.col("replies").alias("fem_comments"),
        pl.col("views").alias("fem_views"),
        pl.col("likes").alias("fem_likes"),
        pl.col("users").alias("fem_users"),
    )
    return (
        pool.join(fem, on="eip", how="left")
        .with_columns(
            pl.col("fem_comments").fill_null(0),
            pl.col("fem_views").fill_null(0),
            pl.col("fem_likes").fill_null(0),
            pl.col("fem_users").fill_null(0),
        )
    )


# =============================================================================
# Panel B: GitHub
# =============================================================================
def _github_commits_panel(pool: pl.DataFrame) -> pl.DataFrame:
    """Per-EIP commit counts from the existing commit log, excluding the `eth-bot` account --
    identical filtering to fig_commit_timing.py::make_commits_per_eip()."""
    commits = pl.read_excel(GITHUB_COMMIT_XLSX)
    commits = commits.rename({"Username": "github_username", "EIP": "eip"})
    commits = commits.filter(pl.col("github_username") != GITHUB_COMMIT_BOT_USERNAME)
    counts = commits.group_by("eip").agg(pl.len().alias("github_commits"))
    return pool.join(counts, on="eip", how="left").with_columns(pl.col("github_commits").fill_null(0))


def _github_activity_panel(pool: pl.DataFrame) -> pl.DataFrame:
    """Per-EIP comment/review counts from the new github_activity_clean.csv source, excluding
    bot accounts. `github_comment` = kind == "comment"; `github_reviews` combines "review" and
    "review_comment" (a review's own verdict plus any inline, line-anchored follow-up comments
    on that review -- see module docstring)."""
    activity = pl.read_csv(GITHUB_ACTIVITY_CSV)
    activity = activity.filter(~pl.col("user").is_in(list(GITHUB_BOT_USERS)))

    comment_counts = (
        activity.filter(pl.col("kind") == "comment")
        .group_by("eip")
        .agg(pl.len().alias("github_comment"))
    )
    review_counts = (
        activity.filter(pl.col("kind").is_in(["review", "review_comment"]))
        .group_by("eip")
        .agg(pl.len().alias("github_reviews"))
    )

    out = pool.join(comment_counts, on="eip", how="left").join(review_counts, on="eip", how="left")
    return out.with_columns(
        pl.col("github_comment").fill_null(0),
        pl.col("github_reviews").fill_null(0),
    )


# =============================================================================
# Panel C: AllCoreDevs (per-meeting, not per-EIP -- see module docstring)
# =============================================================================
def _cleaned_meeting_attendee_panel() -> pl.DataFrame:
    """One row per (meeting, name) appearance, name-cleaned and corrected via Mapping_File.csv --
    the attendee-identity half of fig_commit_timing.py::_build_attendee_meeting_panel(), without
    that function's meeting-date join (not needed here)."""
    dat = _read_latin1_csv_as_utf8(RAW_DEV_CALLS_ATTENDEES_CSV)

    meetings: list[str] = []
    attendees: list[str] = []
    for meeting, attendees_field in zip(dat["Meeting"].to_list(), dat["Attendees"].to_list()):
        if attendees_field is None:
            continue
        for tok in attendees_field.split(","):
            cleaned = clean_text(tok)
            if cleaned is not None:
                meetings.append(meeting)
                attendees.append(cleaned)
    flat = pl.DataFrame({"meeting": meetings, "attendees": attendees})
    flat = flat.filter(pl.col("meeting") != "Meeting Template")

    mapping = pl.read_csv(MAPPING_FILE_CSV)
    mapping = mapping.select(["Original_Name", "Replace_Name"]).rename(
        {"Original_Name": "attendees", "Replace_Name": "replace_name"}
    )
    mapping = mapping.with_columns(
        pl.when(pl.col("attendees") == "ÃÂukasz Rozmej")
        .then(pl.lit("Åukasz Rozmej"))
        .otherwise(pl.col("attendees"))
        .alias("attendees")
    )
    for old, new in [
        ("ÃÂ", "Å"),
        ("ÃÂ³", "Ã³"),
        ("ÃÂ", "Å"),
        ("ÃÂ©", "Ã©"),
        ("ÃÂ¡", "Ã¡"),
        ("ÃÂ¶", "Ã¶"),
    ]:
        mapping = mapping.with_columns(pl.col("attendees").str.replace_all(old, new, literal=True).alias("attendees"))
    mapping = mapping.unique()

    joined = flat.join(mapping, on="attendees", how="left").rename({"replace_name": "name"}).drop("attendees")
    return joined.filter(pl.col("name").is_not_null() & (pl.col("name") != "")).select(["meeting", "name"]).unique()


def _acd_attendees_per_meeting() -> pl.Series:
    """Per-meeting unique-attendee counts, meetings from 2015 onward -- the same quantity
    Figure 14a plots (`fig_commit_timing.py::make_attendees_by_year()`), just not broken out
    by year. Not restricted to meetings that discussed a 612-sample EIP: this describes how
    AllCoreDevs calls themselves are attended, independent of any particular EIP."""
    panel = _cleaned_meeting_attendee_panel()

    calls = pl.read_csv(CALLS_CSV)
    meetdate = calls.select(
        pl.col("Meeting").alias("meeting"),
        pl.col("Date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).dt.year().alias("year"),
    )
    meetdate = meetdate.filter(pl.col("year") >= 2015)

    panel = panel.join(meetdate, on="meeting", how="inner")
    per_meeting = panel.group_by("meeting").agg(pl.col("name").n_unique().alias("n_attendees"))
    return per_meeting.get_column("n_attendees")


def build_participation_data() -> pl.DataFrame:
    """Per-EIP data for Panels A and B (Panel C is per-meeting; see `_acd_attendees_per_meeting()`)."""
    pool = _eip_pool()

    fem = _fem_panel(pool)
    github_commits = _github_commits_panel(pool)
    github_activity = _github_activity_panel(pool)

    data = fem.join(github_commits, on="eip").join(github_activity, on="eip")
    print(f"[table4_participation_summary] Built per-EIP participation data for {data.height} EIPs.")
    return data


def main() -> None:
    ensure_dirs()
    data = build_participation_data()
    acd_per_meeting = _acd_attendees_per_meeting()
    print(f"[table4_participation_summary] Built per-meeting AllCoreDevs data for {acd_per_meeting.len()} meetings.")

    panels: list[tuple[str, dict[str, pl.Series]]] = [
        (
            "Panel A. Fellowship of Ethereum Magicians (FEM)",
            {
                "Comments": data.get_column("fem_comments"),
                "Views": data.get_column("fem_views"),
                "Likes": data.get_column("fem_likes"),
                "Active Participants": data.get_column("fem_users"),
            },
        ),
        (
            "Panel B. GitHub",
            {
                "Commits": data.get_column("github_commits"),
                "Comment": data.get_column("github_comment"),
                "Reviews": data.get_column("github_reviews"),
            },
        ),
        (
            "Panel C. AllCoreDevs",
            {
                "Active Participants per Meeting": acd_per_meeting,
            },
        ),
    ]

    out_path = OUTPUT_TABLES / "participation_summary.tex"
    format_panel_stats_table(panels=panels, out_path=out_path)
    print(f"[table4_participation_summary] Wrote {out_path}")


if __name__ == "__main__":
    main()
