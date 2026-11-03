"""
fig_fem_engagement.py
========================

Reproduces **Figure 13** (`\\label{fig:FEM}`, "Discussion on Fellowship of Ethereum Magicians") of
the current manuscript, `paper/latex/MS_R2.tex`. Figure numbers shift as the paper is
revised; see `docs/figure_table_index.md` for the current numbering snapshot and its date.

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
    Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: Concentration in EIP Discussion (community engagement on the Fellowship of Ethereum
Magicians -- "FEM" -- forum).

Figure 13 caption (panel (b) is a Lorenz curve of comments-per-user): "the vertical axis is the
percentage of all comments made by the most prolific contributors ... sorted by the most to the
least prolific ones" -- the same most-to-least-prolific (descending) sort convention used by the
paper's other author-concentration Lorenz curves (see `code/utils/inequality.py`'s
`lorenz_curve(..., descending=True)` default). Panel (a) is total FEM forum views by year.

RAW DATA SOURCE -- UPDATED
---------------------------
Originally ported from `Analysis\\Magician Comments\\Magician comment analysis.py`, reading
`ethereum_magicians_data_scraped.csv` (one row per FEM thread, with a `Comment Authors`
dict-literal string column needing `ast.literal_eval` to unpack). That file is kept in
`data/raw/forum/` for provenance but is NO LONGER READ by this script.

This script now reads `data/raw/forum/fem_posts_by_eip.csv` instead -- a comment-level scrape
(one row per COMMENT, with a real `user` column) covering the same forum and the same
collection cutoff (last comment timestamp 2023-06-21, matching the original scrape's stated
June 21, 2023 cutoff almost to the day) but substantially more complete: 463 EIPs matched
here versus 346 from the old file, 1,375 unique commenters versus 1,101, 9,456 comments versus
6,416, 3,554,180 views versus 1,617,301. Spot-checked for the same known-bad-EIP-association
issue the old file had (EIP numbers 75/2/0 mismatched during scraping): none found in this file,
so the old file's `TITLE_DROPS`/`TITLE_EIP_CORRECTIONS` hand-corrections are dropped, not ported
forward -- they were specific fixes for specific rows in the old scrape, not a general cleaning
step, and applying them blind to a different scrape with no matching rows would be a no-op at
best and a wrong title-based match at worst.

One field is lost in the switch: the old file had a `Links` column (per-EIP total forum-post
links); this is NOT present in the new comment-level file. Downstream consumers
(`build_cross_sectional_dataset.py`) already handle a null `links` column in the FEM data if it's
is a column that's entirely null (not malformed-- deliberately left null here, matching
`build_cross_sectional_dataset.py`'s own no-FEM-data fallback at that column) -- not fabricated.

Outputs
-------
    - `data/interim/fem_data_for_regressions.parquet`  -- one row per EIP that has a matching FEM
      forum thread AND a matching row in the cross-sectional dataset: `eip`, `replies`, `views`,
      `likes`, `links`, `createddate`, `users`, `year`. THIS IS A REQUIRED INPUT to two other
      scripts in this package -- see "THE CIRCULAR DEPENDENCY" section below.
    - `output/figures/figure_12a_fem_views_by_year.png`
    - `output/figures/figure_12b_fem_lorenz_comments.png`

THE CIRCULAR DEPENDENCY -- READ THIS BEFORE CHANGING THE TWO-PASS BEHAVIOR
-----------------------------------------------------------------------------
This mirrors the FEM circular dependency already documented in
`code/02_data_preparation/build_cross_sectional_dataset.py`'s module docstring (its "circular
dependency #2"), from the other side:

    - THIS script needs `eip_number` + `Category` from
      `data/processed/ethereum_cross_sectional_data.parquet` (to replicate the original's
      `pd.merge(data, cs[['eip_number','Category']], ..., how='inner')` -- i.e. FEM engagement
      is only computed for EIPs that also appear in the cross-sectional dataset).
    - `build_cross_sectional_dataset.py` needs THIS script's own output
      (`data/interim/fem_data_for_regressions.parquet`) to populate its `replies`/`views`/
      `likes`/`links`/`createddate`/`users` columns.

The `eip_number`/`Category` columns this script needs are produced by
`build_cross_sectional_dataset.py`'s FIRST pass (before centrality/FEM are available -- they come
from the mandatory base-EIP-spine + `eip_implementation.xlsx` merges, entirely independent of the
FEM merge step), so the correct run order is:

    pass 1: clean_eip_authors.py -> build_cross_sectional_dataset.py
            (produces data/processed/ethereum_cross_sectional_data.parquet with
             eip_number/Category populated, but replies/views/likes/links/createddate/users null)
    pass 2: (centrality analysis, independently) and THIS script
            (THIS script reads pass-1's eip_number/Category, produces
             data/interim/fem_data_for_regressions.parquet)
    pass 3: re-run build_cross_sectional_dataset.py
            (now both centrality_all.parquet and fem_data_for_regressions.parquet exist, so the
             FINAL, fully-populated cross-sectional dataset is produced)

Unlike centrality/FEM being *optional* inputs to `build_cross_sectional_dataset.py`, the
cross-sectional dataset is NOT optional here -- there is no way to replicate the original's inner
join without it, so this script raises a clear `FileNotFoundError` (not a fabricated/empty
result) if pass 1 has not been run yet.

RECONCILING THE 3-WAY PATH/CASING CONTRACT (read this if touching any of the 3 scripts below)
-------------------------------------------------------------------------------------------------
Three scripts must agree exactly on path, filename casing, and column names for the FEM
regression dataset:
    1. THIS script (producer)                                          -- writes the file.
    2. `code/02_data_preparation/build_cross_sectional_dataset.py`       -- consumer #1.
    3. `code/03_analysis/regressions/table2_fem_regressions.py`         -- consumer #2.

Given both consumers' expectations, this script writes columns exactly as:
    eip, replies, views, likes, links, createddate, users, year
all already lower-case with no interior spaces.

Conventions followed
---------------------
- Uses Polars throughout (no pandas), zstd-compressed Parquet output.
- Uses `code/utils/inequality.py`'s `gini()` / `lorenz_curve()`.
- The new file is already one row per (topic, comment), so no `ast.literal_eval` dict-unpacking
  step is needed at all -- `load_raw_fem_data()` is the whole of what used to be
  `load_raw_fem_data()` + `explode_comment_authors()` combined, and is simpler as a result.
  `views` and `t_likes` are THREAD-level values repeated on every comment row of that thread, so
  they are deduplicated by `topic` before being summed per EIP (an EIP can have more than one FEM
  thread, e.g. popular standards like ERC-20 accumulate several tangentially-related threads).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_FIGURES, ensure_dirs
from utils.inequality import gini, lorenz_curve

RAW_FEM_CSV = DATA_RAW / "forum" / "fem_posts_by_eip.csv"
CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
OUT_PARQUET = DATA_INTERIM / "fem_data_for_regressions.parquet"

FIG_12A_PATH = OUTPUT_FIGURES / "figure_12a_fem_views_by_year.png"
FIG_12B_PATH = OUTPUT_FIGURES / "figure_12b_fem_lorenz_comments.png"


# ---------------------------------------------------------------------------
# Step 1: load the raw FEM comment-level scrape
# ---------------------------------------------------------------------------
def load_raw_fem_data() -> pl.DataFrame:
    """
    Read `fem_posts_by_eip.csv`: one row per (FEM thread, comment), columns include
    `topic` (thread id), `eip`, `views`/`t_likes` (thread-level, repeated per comment row),
    `user` (commenter), and `t_created` (thread creation timestamp, also repeated per row).
    """
    df = pl.read_csv(RAW_FEM_CSV, encoding="utf8-lossy", infer_schema_length=10_000)
    df = df.filter(pl.col("eip").is_not_null())
    df = df.with_columns(
        pl.col("t_created").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("created_date")
    )
    return df


# ---------------------------------------------------------------------------
# Step 2: bring in the cross-sectional dataset (inner-join filter on eip_number)
# ---------------------------------------------------------------------------
def load_matched_eip_numbers() -> pl.DataFrame:
    """
    Load `eip_number` from the cross-sectional dataset -- FEM engagement is only computed for
    EIPs that also appear in the cross-sectional dataset, exactly as before (see module docstring,
    "THE CIRCULAR DEPENDENCY").
    """
    if not CROSS_SECTIONAL_PATH.exists():
        raise FileNotFoundError(
            f"Required input not found: {CROSS_SECTIONAL_PATH}\n"
            "This script needs eip_number from a FIRST PASS of "
            "code/02_data_preparation/build_cross_sectional_dataset.py. Run that script first, "
            "then re-run this script. See this script's module docstring, 'THE CIRCULAR "
            "DEPENDENCY', for the full 3-pass run order."
        )
    cs = pl.read_parquet(CROSS_SECTIONAL_PATH, columns=["eip_number"])
    return cs.select("eip_number")


# ---------------------------------------------------------------------------
# Step 3: per-EIP aggregation (sum comments/Views/Likes, min thread-creation date, unique Users)
# ---------------------------------------------------------------------------
def build_fem_regression_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Builds the per-EIP FEM engagement dataset (the `fem_data_for_regressions.parquet` contract)
    and, alongside it, the long (EIP, user) comment table needed for the Lorenz curve / Gini.

    Returns
    -------
    (per_eip, exploded) : (pl.DataFrame, pl.DataFrame)
        `per_eip` has one row per EIP that survived the inner join, with columns
        `eip, replies, views, likes, links, createddate, users, year`. `links` is always null
        (not captured by this raw source -- see module docstring).
        `exploded` is the long (EIP, user) comment table -- already the natural shape of the raw
        data here, one row per comment, so no unpacking step is needed (unlike the old
        dict-literal-column source).
    """
    raw = load_raw_fem_data()
    matched_eips = load_matched_eip_numbers()

    # Inner join on eip == eip_number, same restriction as before: only EIPs that are both
    # discussed on FEM and present in the cross-sectional dataset.
    data = raw.join(matched_eips, left_on="eip", right_on="eip_number", how="semi")

    # views/t_likes/created_date are THREAD-level values repeated on every comment row of that
    # thread -- deduplicate by topic before summing across an EIP's (possibly several) threads.
    threads = data.unique(subset=["topic"], keep="first").select(
        ["topic", "eip", "views", "t_likes", "created_date"]
    )
    per_eip = threads.group_by("eip").agg(
        pl.col("views").sum(),
        pl.col("t_likes").sum().alias("likes"),
        pl.col("created_date").min(),
    )

    # replies: one row per comment in the comment-level table (post-join), summed per EIP.
    replies_per_eip = data.group_by("eip").agg(pl.len().alias("replies"))
    users_per_eip = data.group_by("eip").agg(pl.col("user").n_unique().alias("users"))

    per_eip = (
        per_eip.join(replies_per_eip, on="eip", how="left")
        .join(users_per_eip, on="eip", how="left")
        .with_columns(pl.lit(None, dtype=pl.Int64).alias("links"))
    )

    per_eip = per_eip.with_columns(
        pl.col("created_date").dt.year().alias("year"),
        pl.col("created_date").dt.strftime("%d%b%Y").alias("createddate"),
    )

    per_eip = per_eip.select(
        "eip", "replies", "views", "likes", "links", "createddate", "users", "year"
    ).sort("eip")

    exploded = data.select(["eip", "user"]).rename({"eip": "EIP"})
    return per_eip, exploded


def build_user_comment_totals(exploded: pl.DataFrame) -> pl.DataFrame:
    """N. of comments per user, summed across every EIP (and every thread within an EIP) that
    user commented on."""
    return (
        exploded.group_by("user")
        .agg(pl.len().alias("ncomm"))
        .sort("ncomm", descending=True)
    )


# ---------------------------------------------------------------------------
# Figure 13a: total FEM views by year
# ---------------------------------------------------------------------------
def make_figure_12a(per_eip: pl.DataFrame) -> None:
    """Total FEM forum views by (thread creation) year."""
    by_year = per_eip.group_by("year").agg(pl.col("views").sum()).sort("year")
    years = by_year.get_column("year").to_list()
    totals = by_year.get_column("views").to_list()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(range(len(years)), totals)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("Year")
    ax.set_ylabel("Total Views")

    if 2023 in years:
        idx2023 = years.index(2023)
        ax.text(
            idx2023,
            totals[idx2023] + 0.02 * ax.get_ylim()[1],
            "*",
            ha="center",
            va="bottom",
            fontsize=16,
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(FIG_12A_PATH, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 13b: Lorenz curve of comments-per-user + Gini
# ---------------------------------------------------------------------------
def make_figure_12b(user_totals: pl.DataFrame) -> None:
    """Lorenz curve of comments-per-user (descending: most-prolific commenter first)."""
    counts = user_totals.get_column("ncomm")
    lc = lorenz_curve(counts, descending=True)
    g = gini(counts)

    top10_share = (
        counts.sort(descending=True).head(10).sum() / counts.sum() * 100.0
    )
    print(
        f"[fig_fem_engagement] N. unique FEM commenters: {user_totals.height} | "
        f"Top-10 commenters' share of all comments: {top10_share:.1f}% | "
        f"Gini (comments per user): {g:.4f}"
    )

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(lc["pct_population"], lc["cum_pct_value"])
    ax.set_xlabel("Cumulative % of Commentators (sorted most- to least-prolific)")
    ax.set_ylabel("Cumulative % of Total Comments")
    fig.tight_layout()
    fig.savefig(FIG_12B_PATH, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ensure_dirs()

    per_eip, exploded = build_fem_regression_data()
    per_eip.write_parquet(OUT_PARQUET, compression="zstd")
    print(f"[fig_fem_engagement] Wrote {per_eip.height} rows x {per_eip.width} cols to {OUT_PARQUET}")

    print(
        f"[fig_fem_engagement] Overall FEM stats -- "
        f"Likes: {per_eip.get_column('likes').sum()}, "
        f"Views: {per_eip.get_column('views').sum()}, "
        f"Replies: {per_eip.get_column('replies').sum()}"
    )

    make_figure_12a(per_eip)

    user_totals = build_user_comment_totals(exploded)
    make_figure_12b(user_totals)

    print(
        "[fig_fem_engagement] Reminder: re-run "
        "code/02_data_preparation/build_cross_sectional_dataset.py now that "
        f"{OUT_PARQUET} exists, to produce the FINAL, FEM-populated cross-sectional dataset."
    )


if __name__ == "__main__":
    main()
