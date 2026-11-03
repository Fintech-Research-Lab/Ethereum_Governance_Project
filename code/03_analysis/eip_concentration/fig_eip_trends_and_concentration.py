"""
fig_eip_trends_and_concentration.py
======================================

Reproduces **Figures 2, 7, 8, 10, and 11** (`\\label`s `fig:neip_year`, `n_author_by_stage`,
`top10_author`, `lorenz_authorship`, `fig:gini_year`) of the current manuscript,
`paper/latex/MS_R2.tex`. Figure numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date. The `\\label`s are
the stable identifiers.

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: EIP volume over time and author-level concentration of EIP output (the "how
concentrated is EIP authorship" empirical section).

Ported from: `Analysis\\Regression Code\\Regression Code.do`, the "ETHEREUM TIME TRENDS" (partial --
only the EIP-count-by-year piece; the Ethereum-Foundation-share piece is
`fig_company_concentration.py`'s `eip_ef_by_year.png`), "EVOLUTION OF EIP DEVELOPMENT OVER TIME", and
"Concentration of EIP Development" sections.

Output produced by this script (`\\label` -> file(s); code-level comments and variable names below
still use this script's own historical "Figure 2/6/7/8/9" numbering, which predates the paper's
current, renumbered section order -- the mapping to the CURRENT numbers is only in this header and
in `docs/figure_table_index.md`):

    fig:neip_year (Figure 2):        neip_by_year.png            -- EIP count by year (stacked by
                                      category) + unique-author overlay
    n_author_by_stage (Figure 7):    n_authors_by_stage.png       -- fractional author counts by
                                      category x stage (All / Finalized ERC-Interface / Implemented)
    top10_author (Figure 8):         neip_top10author.png         -- top-10 authors by raw N. of EIPs
                                      neip_final_top10author.png   -- top-10 authors by raw N. of
                                      Finalized ERC/Interface EIPs
                                      neip_imp_top10author.png     -- top-10 authors by raw N. of
                                      Implemented EIPs
    lorenz_authorship (Figure 10):   neip_by_author.png           -- Lorenz curve, EIP-authorship
                                      concentration (by author count, x-axis)
                                      npeip_by_author.png          -- same Lorenz curves, x-axis
                                      re-expressed as % of authors
    fig:gini_year (Figure 11):       gini_by_year.png             -- rolling 2-year-window Gini of
                                      EIP-authorship concentration, 2016-2023

Also saves `data/interim/eip_by_authors.parquet` (author, id_author, n_eip, n_eip_final, n_eip_imp;
one row per author), replicating the original's
`save "Analysis\\Meeting Attendees...\\eip_by_authors.dta"`, which a sibling script (Figure 15,
commits-around-meetings) is being written to consume.

Data source
-----------
`DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"` (see `table3_finalization_regressions.py`'s
docstring for the full expected column list). This script additionally needs the raw `Category`
(string) column -- capitalized `Category`, confirmed against the actual columns produced by
`code/02_data_preparation/build_cross_sectional_dataset.py` (aliased to lowercase `category`
internally in this file's own long-format panel for convenience), `status`, `implemented`
(derived the same way as in Table 3 -- reproduced locally rather than imported, since this script must
be runnable even if the `regressions/` package is not on the path) `sdate`, and the wide
`author{n}` / `author{n}_id` (n=1..15) columns.

Sort convention for the per-author collapse steps
-----------------------------------------------------
`_stata_keep_first_desc` collapses each author down to one row via a descending sort on a count
column, keeping the top row per author. Missing values (an author with zero qualifying EIPs, e.g.
zero Finalized-ERC EIPs) sort as smallest by default here (`missing_sorts_first=False`) -- verified
against the published figures: this reproduces the paper's Figure 8/9 Gini values (0.499/0.589) and
Figure 7's Implemented-EIPs top 10 (Buterin=20, Swende=6, Beregszaszi=6, Bylica=5, Reitwiessner=5,
...) exactly. The "All EIPs"/"Finalized EIPs" collapses are indifferent to this setting, since their
sort key (an author's total unconditional EIP count) is never missing for any author with at least
one EIP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_INTERIM, DATA_PROCESSED, OUTPUT_FIGURES, ensure_dirs
from utils.inequality import gini, lorenz_curve, rolling_window_gini

CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
N_AUTHOR_SLOTS = 15


# ---------------------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------------------
def add_implemented_column(df: pl.DataFrame) -> pl.DataFrame:
    """Same derivation as `table3_finalization_regressions.add_implemented_column`, duplicated here
    (rather than cross-imported) so this figure script has no dependency on the `regressions/`
    folder. See that function's docstring for the exact Stata logic being replicated."""
    non_terminal = pl.col("status").is_in(["Draft", "Final", "Last Call", "Living", "Review"])
    return df.with_columns(
        pl.when(non_terminal & (pl.col("implementation") != 1))
        .then(None)
        .otherwise(pl.col("implementation"))
        .alias("implemented")
    )


def _stata_keep_first_desc(
    df: pl.DataFrame, group_cols: list[str], sort_col: str, missing_sorts_first: bool = False
) -> pl.DataFrame:
    """
    For each group in `group_cols`, keep only the row with the largest `sort_col` value (a
    descending sort followed by a keep-first-per-group collapse).

    Parameters
    ----------
    missing_sorts_first : bool, default False
        Whether a null `sort_col` value should be treated as the largest possible value (sorting
        first, `True`) or the smallest (sorting last, `False`, the default -- so a group's real,
        non-missing value is always kept over a missing one when both exist).
    """
    df = df.with_row_index("__rid")
    sentinel = float("inf") if missing_sorts_first else float("-inf")
    df = df.with_columns(
        pl.when(pl.col(sort_col).is_null()).then(sentinel).otherwise(pl.col(sort_col)).alias("__key")
    )
    df = df.sort(group_cols + ["__key", "__rid"], descending=[False] * len(group_cols) + [True, False])
    out = df.group_by(group_cols, maintain_order=True).first()
    return out.drop(["__key", "__rid"])


def _build_eip_author_long(df: pl.DataFrame) -> pl.DataFrame:
    """
    Replicates the "temp" dataset built at the top of the "Concentration of EIP Development" section:
    one row per (eip_number, author-slot) pair, with per-eip status/category/sdate carried along, and
    per-author `n_eip` / `n_eip_final` / `n_eip_imp` computed group-wise.

        reshape long author id_author, i(eip status sdate) j(id) string
        drop if id_author ==.
        bys id_author: egen n_eip = count(id)
        bys id_author: egen n_eip_final = count(id) if status=="Final" & (Category in ERC/Interface)
        bys id_author: egen n_eip_imp = count(id) if implemented==1
    """
    frames = []
    for a in range(1, N_AUTHOR_SLOTS + 1):
        name_col, id_col = f"author{a}", f"author{a}_id"
        if name_col not in df.columns or id_col not in df.columns:
            continue
        frames.append(
            df.select(
                pl.col("eip_number"),
                pl.col("status"),
                pl.col("Category").alias("category"),  # source column is capitalized "Category";
                # aliased to lowercase "category" here once so every downstream helper in this file
                # can use one consistent internal name.
                pl.col("sdate"),
                pl.col("implemented"),
                pl.col(name_col).alias("author"),
                pl.col(id_col).alias("id_author"),
            )
        )
    long_df = pl.concat(frames, how="vertical").filter(pl.col("id_author").is_not_null())

    qualifies_final = (pl.col("status") == "Final") & pl.col("category").is_in(["ERC", "Interface"])
    qualifies_imp = pl.col("implemented") == 1

    long_df = long_df.with_columns(
        pl.len().over("id_author").alias("n_eip"),
        qualifies_final.alias("__qual_final"),
        qualifies_imp.alias("__qual_imp"),
    )

    # `egen n_eip_X = count(id) if <condition>` in Stata: count rows per id_author RESTRICTED to
    # rows meeting <condition>, with that count assigned only on the qualifying rows (missing
    # elsewhere) -- replicated here as: count within the (id_author, qualifying-subset) group, then
    # explicitly null out the non-qualifying rows.
    long_df = long_df.with_columns(
        pl.when(pl.col("__qual_final"))
        .then(pl.len().over(["id_author", "__qual_final"]))
        .otherwise(None)
        .alias("n_eip_final"),
        pl.when(pl.col("__qual_imp"))
        .then(pl.len().over(["id_author", "__qual_imp"]))
        .otherwise(None)
        .alias("n_eip_imp"),
    ).drop(["__qual_final", "__qual_imp"])
    return long_df


# ---------------------------------------------------------------------------------------
# Figure 2: neip_by_year.png
# ---------------------------------------------------------------------------------------
def make_neip_by_year(df: pl.DataFrame) -> None:
    """
    Replicates the "N. unique authors over time" + "EIP Over time" blocks: a stacked bar of EIP
    counts by (Core / Networking / ERC / Interface) category per year, overlaid with a line/marker
    series of the count of distinct authors active that year.
    """
    # -- unique authors per year --------------------------------------------------------------
    author_year_frames = []
    for a in range(1, N_AUTHOR_SLOTS + 1):
        id_col = f"author{a}_id"
        if id_col not in df.columns:
            continue
        author_year_frames.append(
            df.select(pl.col("sdate").dt.year().alias("year"), pl.col(id_col).alias("author_id"))
        )
    author_year_long = pl.concat(author_year_frames, how="vertical").filter(pl.col("author_id").is_not_null())
    n_author_by_year = (
        author_year_long.select(["year", "author_id"]).unique().group_by("year").agg(pl.len().alias("n_author"))
    )

    # -- EIP counts by category and year ------------------------------------------------------
    # Source column is capitalized "Category"; aliased to lowercase "category" for local use.
    eip_year = df.with_columns(
        pl.col("sdate").dt.year().alias("year"), pl.col("Category").alias("category")
    )
    neip_by_cat_year = (
        eip_year.group_by(["category", "year"]).agg(pl.col("eip_number").n_unique().alias("neip"))
        .pivot(values="neip", index="year", columns="category")
        .fill_null(0)
    )

    for col in ("Core", "Networking", "ERC", "Interface"):
        if col not in neip_by_cat_year.columns:
            neip_by_cat_year = neip_by_cat_year.with_columns(pl.lit(0).alias(col))

    neip_by_cat_year = neip_by_cat_year.with_columns(
        pl.col("Core").alias("core_top"),
        (pl.col("Core") + pl.col("Networking")).alias("networking_top"),
    ).with_columns(
        (pl.col("networking_top") + pl.col("ERC")).alias("erc_top"),
    ).with_columns(
        (pl.col("erc_top") + pl.col("Interface")).alias("interface_top"),
    )

    plot_df = neip_by_cat_year.join(n_author_by_year, on="year", how="left").sort("year")

    years = plot_df.get_column("year").to_list()
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(years, plot_df.get_column("core_top").to_list(), width=0.8, label="Core")
    ax1.bar(
        years,
        plot_df.get_column("Networking").to_list(),
        bottom=plot_df.get_column("core_top").to_list(),
        width=0.8,
        label="Networking",
    )
    ax1.bar(
        years,
        plot_df.get_column("ERC").to_list(),
        bottom=plot_df.get_column("networking_top").to_list(),
        width=0.8,
        label="ERC",
    )
    ax1.bar(
        years,
        plot_df.get_column("Interface").to_list(),
        bottom=plot_df.get_column("erc_top").to_list(),
        width=0.8,
        label="Interface",
    )
    ax1.set_xlabel("Year")
    ax1.set_ylabel("N. of EIPs")
    ax1.set_xticks(years)

    ax2 = ax1.twinx()
    n_author_series = plot_df.get_column("n_author").to_list()
    ax2.plot(years, n_author_series, color="black", marker="^")
    ax2.set_ylabel("N. of Unique Authors")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2 + ["N. Unique Authors"][: len(lines2)])

    if 2023 in years:
        idx2023 = years.index(2023)
        stack_top = plot_df.get_column("interface_top").to_list()[idx2023]
        ax1.text(
            2023,
            stack_top + 0.02 * ax1.get_ylim()[1],
            "*",
            ha="center",
            va="bottom",
            fontsize=16,
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "neip_by_year.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Figure 6: n_authors_by_stage.png
# ---------------------------------------------------------------------------------------
def _fractional_author_counts_by_category(long_df: pl.DataFrame) -> pl.DataFrame:
    """
    Replicates the "Number of authors working on EIPs" block: for the given subset of `long_df`,
    each author's activity is split fractionally across the categories they've worked in (so an
    author touching 2 categories contributes 0.5 to each), then summed within category. This avoids
    double-counting authors who work across categories.
    """
    counts = long_df.group_by(["id_author", "category"]).agg(pl.len().alias("one"))
    counts = counts.with_columns((pl.col("one") / pl.col("one").sum().over("id_author")).alias("one"))
    return counts.group_by("category").agg(pl.col("one").sum().alias("n"))


def make_n_authors_by_stage(long_df: pl.DataFrame) -> None:
    all_counts = _fractional_author_counts_by_category(long_df).rename({"n": "All EIPs"})
    final_counts = _fractional_author_counts_by_category(
        long_df.filter((pl.col("status") == "Final") & pl.col("category").is_in(["ERC", "Interface"]))
    ).rename({"n": "Finalized ERC/Interf."})
    imp_counts = _fractional_author_counts_by_category(
        long_df.filter(pl.col("implemented") == 1)
    ).rename({"n": "Implemented Core/Network EIP"})

    merged = all_counts.join(final_counts, on="category", how="outer", coalesce=True).join(
        imp_counts, on="category", how="outer", coalesce=True
    )
    merged = merged.fill_null(0.0).sort("category")

    categories = merged.get_column("category").to_list()
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(categories))
    width = 0.25
    for i, col in enumerate(["All EIPs", "Finalized ERC/Interf.", "Implemented Core/Network EIP"]):
        ax.bar([xi + i * width for xi in x], merged.get_column(col).to_list(), width=width, label=col)
    ax.set_xticks([xi + width for xi in x])
    ax.set_xticklabels(categories)
    ax.set_ylabel("N. of Authors")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "n_authors_by_stage.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Figure 7: top-10 author bar charts
# ---------------------------------------------------------------------------------------
def make_top10_author_charts(long_df: pl.DataFrame) -> None:
    """
    Collapses `long_df` to one row per author, independently per measure (`n_eip`, `n_eip_final`,
    `n_eip_imp` each get their own `_stata_keep_first_desc` collapse -- matching
    `make_eip_author_lorenz_curves`'s pattern), and bar-charts the top 10 by each. Also saves the
    "All EIPs" collapse to `data/interim/eip_by_authors.parquet` for the sibling Figure 15 script.

    Collapsing independently per measure matters: an author has one row per EIP they appear on,
    and `n_eip_final`/`n_eip_imp` are null on any row for an EIP that doesn't qualify for that
    measure. `n_eip` (an author's total EIP count) is identical across all of an author's rows, so
    collapsing on `n_eip` alone leaves a tie between an author's qualifying and non-qualifying
    rows -- which one survives is then undefined and can vary from run to run (a real
    non-determinism this fix removes; it does not depend on `long_df`'s row order at all).
    """
    per_author = long_df.select(["author", "id_author", "n_eip", "n_eip_final", "n_eip_imp"]).unique()

    def _top10(measure_col: str, out_path: Path, ylabel: str) -> pl.DataFrame:
        collapsed = _stata_keep_first_desc(
            per_author.select(["author", "id_author", measure_col]).unique(),
            group_cols=["author"],
            sort_col=measure_col,
        )
        top10 = collapsed.filter(pl.col(measure_col).is_not_null()).sort(measure_col, descending=True).head(10)
        _hbar(top10.get_column("author").to_list(), top10.get_column(measure_col).to_list(), ylabel, out_path)
        return collapsed

    all_collapsed = _top10("n_eip", OUTPUT_FIGURES / "neip_top10author.png", "N. of EIPs")
    _top10("n_eip_final", OUTPUT_FIGURES / "neip_final_top10author.png", "N. of Finalized ERCs/Inter.")
    _top10("n_eip_imp", OUTPUT_FIGURES / "neip_imp_top10author.png", "N. of Implemented Core/Network. EIPs")

    # eip_by_authors.parquet needs all three measures on one row per author (Figure 15's own
    # consumer joins on author name), so re-join the three independent per-measure collapses.
    final_by_author = per_author.select(["author", "n_eip_final"]).unique().drop_nulls("n_eip_final")
    imp_by_author = per_author.select(["author", "n_eip_imp"]).unique().drop_nulls("n_eip_imp")
    eip_by_authors = (
        all_collapsed.select(["author", "id_author", "n_eip"])
        .join(final_by_author, on="author", how="left")
        .join(imp_by_author, on="author", how="left")
    )
    eip_by_authors.write_parquet(DATA_INTERIM / "eip_by_authors.parquet", compression="zstd")


def _hbar(labels: list[str], values: list[float], ylabel: str, out_path: Path) -> None:
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.4 * len(labels))))
    ax.barh(range(len(labels)), values)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(ylabel)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Figure 8: Lorenz curves (neip_by_author.png, npeip_by_author.png)
# ---------------------------------------------------------------------------------------
def _build_frac_table(long_df: pl.DataFrame) -> pl.DataFrame:
    """
    Replicates the "temp3"-equivalent table built at eip-author row granularity (i.e. NOT yet
    collapsed to one row per author -- each measure's own collapse, and its associated bug, is
    applied separately by `_collapse_frac_measure` below, exactly mirroring how the original .do
    file builds one shared `temp3.dta` and then runs three independent collapses against it):

        bys eip_number: gen frac = 1/_N
        egen toteip = nvals(eip_number)
        bys id_author: egen n_eip_frac = total(frac)
        replace n_eip_frac = n_eip_frac / toteip
        ... identically for n_eip_frac_final (status=="Final" & Category in ERC/Interface) and
            n_eip_frac_imp (implemented==1), each restricted to its own qualifying subset first ...
        keep author id_author n_eip_frac*
        duplicates drop
    """
    qualifies_final = (pl.col("status") == "Final") & pl.col("category").is_in(["ERC", "Interface"])
    qualifies_imp = pl.col("implemented") == 1

    base = long_df.with_columns(
        (1.0 / pl.len().over("eip_number")).alias("frac"),
        qualifies_final.alias("__qual_final"),
        qualifies_imp.alias("__qual_imp"),
    )

    toteip_all = base.get_column("eip_number").n_unique()
    toteip_final = base.filter(pl.col("__qual_final")).get_column("eip_number").n_unique()
    toteip_imp = base.filter(pl.col("__qual_imp")).get_column("eip_number").n_unique()

    n_eip_frac = base.group_by("id_author").agg(pl.col("frac").sum().alias("n_eip_frac")).with_columns(
        (pl.col("n_eip_frac") / toteip_all).alias("n_eip_frac")
    )
    n_eip_frac_final = (
        base.filter(pl.col("__qual_final"))
        .group_by("id_author")
        .agg(pl.col("frac").sum().alias("n_eip_frac_final"))
        .with_columns((pl.col("n_eip_frac_final") / toteip_final).alias("n_eip_frac_final"))
    )
    n_eip_frac_imp = (
        base.filter(pl.col("__qual_imp"))
        .group_by("id_author")
        .agg(pl.col("frac").sum().alias("n_eip_frac_imp"))
        .with_columns((pl.col("n_eip_frac_imp") / toteip_imp).alias("n_eip_frac_imp"))
    )

    per_row = (
        base.select(["author", "id_author", "__qual_final", "__qual_imp"])
        .join(n_eip_frac, on="id_author", how="left")
        .join(n_eip_frac_final, on="id_author", how="left")
        .join(n_eip_frac_imp, on="id_author", how="left")
    )
    # Stamp missing on non-qualifying rows for the two conditional measures, mirroring Stata's
    # `egen ... if condition` (real value on qualifying rows only, missing elsewhere) -- this is
    # what lets an author's later per-measure collapse land on a mix of real/missing rows.
    per_row = per_row.with_columns(
        pl.when(pl.col("__qual_final")).then(pl.col("n_eip_frac_final")).otherwise(None).alias(
            "n_eip_frac_final"
        ),
        pl.when(pl.col("__qual_imp")).then(pl.col("n_eip_frac_imp")).otherwise(None).alias("n_eip_frac_imp"),
    )
    return per_row.select(["author", "id_author", "n_eip_frac", "n_eip_frac_final", "n_eip_frac_imp"]).unique()


def _collapse_frac_measure(temp3: pl.DataFrame, measure_col: str) -> pl.Series:
    """
    For one of `n_eip_frac` / `n_eip_frac_final` / `n_eip_frac_imp`: collapse to one row per
    author, keeping each author's largest (i.e. real, non-missing, over missing) value on that
    measure, then drop authors left with a missing value (i.e. authors who never qualify on this
    measure at all).
    """
    narrow = temp3.select(["author", "id_author", measure_col]).unique()
    collapsed = _stata_keep_first_desc(
        narrow, group_cols=["id_author"], sort_col=measure_col, missing_sorts_first=False
    )
    return collapsed.filter(pl.col(measure_col).is_not_null()).get_column(measure_col)


def make_eip_author_lorenz_curves(long_df: pl.DataFrame) -> None:
    temp3 = _build_frac_table(long_df)
    all_shares = _collapse_frac_measure(temp3, "n_eip_frac")
    final_shares = _collapse_frac_measure(temp3, "n_eip_frac_final")
    imp_shares = _collapse_frac_measure(temp3, "n_eip_frac_imp")

    lc_all = lorenz_curve(all_shares, descending=True)
    lc_final = lorenz_curve(final_shares, descending=True) if final_shares.len() else None
    lc_imp = lorenz_curve(imp_shares, descending=True) if imp_shares.len() else None

    gini_all = gini(all_shares)
    gini_final = gini(final_shares) if final_shares.len() else float("nan")
    gini_imp = gini(imp_shares) if imp_shares.len() else float("nan")
    print(
        f"[fig_eip_trends_and_concentration] Author-concentration Gini -- "
        f"All EIPs: {gini_all:.4f}, Finalized ERC/Interface: {gini_final:.4f}, "
        f"Implemented: {gini_imp:.4f}"
    )

    # neip_by_author.png: x-axis = rank (n), by construction of lorenz_curve this is pct_population
    # (0-100); the original x-axis is a raw author rank (n), which is a monotone rescaling of
    # pct_population and produces an identical-shaped curve.
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(lc_all["pct_population"], lc_all["cum_pct_value"], label="All EIPs")
    if lc_final is not None:
        ax.plot(lc_final["pct_population"], lc_final["cum_pct_value"], label="Finalized ERCs/Inter.")
    if lc_imp is not None:
        ax.plot(lc_imp["pct_population"], lc_imp["cum_pct_value"], label="Implemented Core/Network. EIPs")
    ax.set_xlabel("N. Authors, sorted from most- to least-prolific (%)")
    ax.set_ylabel("% of EIPs")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "neip_by_author.png", dpi=200)
    plt.close(fig)

    # npeip_by_author.png: same curves, x-axis explicitly labeled "% of Authors" (already what
    # pct_population is, so this is the same data as neip_by_author.png with an explicit axis label).
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(lc_all["pct_population"], lc_all["cum_pct_value"], label="All EIPs")
    if lc_final is not None:
        ax.plot(lc_final["pct_population"], lc_final["cum_pct_value"], label="Finalized ERCs/Inter.")
    if lc_imp is not None:
        ax.plot(lc_imp["pct_population"], lc_imp["cum_pct_value"], label="Implemented Core/Network. EIPs")
    ax.set_xlabel("% of Authors")
    ax.set_ylabel("% of EIPs")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "npeip_by_author.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Figure 9: gini_by_year.png
# ---------------------------------------------------------------------------------------
def make_gini_by_year(long_df: pl.DataFrame) -> None:
    """
    Replicates the "GINI COEFFICIENT BY Rolling 2 year" loop (`forvalues y = 2016/2023`) via
    `rolling_window_gini`, using each (eip_number, author) pair's fractional credit (1/n_coauthors)
    as the per-window-summed value.
    """
    panel = long_df.with_columns(
        (1.0 / pl.len().over("eip_number")).alias("frac"),
        pl.col("sdate").dt.year().alias("year"),
    ).select(["id_author", "year", "frac"])

    rolling = rolling_window_gini(panel, value_col="frac", id_col="id_author", year_col="year", window_years=2)
    # The original loop explicitly runs `forvalues y = 2016/2023` -- restrict to that exact range
    # rather than whatever full year span happens to be in the data.
    rolling = rolling.filter((pl.col("window_end_year") >= 2016) & (pl.col("window_end_year") <= 2023)).sort(
        "window_end_year"
    )

    years = rolling.get_column("window_end_year").to_list()
    ginis = rolling.get_column("gini").to_list()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(years, ginis)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gini Coefficient")

    if 2023 in years:
        idx2023 = years.index(2023)
        ax.text(
            2023,
            ginis[idx2023] + 0.02 * ax.get_ylim()[1],
            "*",
            ha="center",
            va="bottom",
            fontsize=16,
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "gini_by_year.png", dpi=200)
    plt.close(fig)


def main() -> None:
    ensure_dirs()

    df = pl.read_parquet(CROSS_SECTIONAL_PATH)
    df = add_implemented_column(df)

    make_neip_by_year(df)

    long_df = _build_eip_author_long(df)
    make_n_authors_by_stage(long_df)
    make_top10_author_charts(long_df)
    make_eip_author_lorenz_curves(long_df)
    make_gini_by_year(long_df)


if __name__ == "__main__":
    main()
