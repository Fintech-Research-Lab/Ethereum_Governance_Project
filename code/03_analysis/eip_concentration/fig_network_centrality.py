"""
fig_network_centrality.py
==========================

Reproduces **Figure 9** (`\\label{fig:between}`, "EIP Co-Authorship Network") and **Figure 12**
(`\\label{fig:clustering_trends}`, "Decentralization of EIP Co-Authorship over Time") of the
current manuscript, `paper/latex/MS_R2.tex`. Figure numbers shift as the paper is
revised; see `docs/figure_table_index.md` for the current numbering snapshot and its date, and
that file (or `MS_R2.tex` directly) for the current, up-to-date figure captions -- the network
figure's caption in particular has changed since this module was first written (it now describes
a giant-component-only layout with community coloring; see `plot_network_figure()` below).

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: Concentration in EIP Proposals, "Influential Authors in EIP Production."

Ported from: `Analysis\\Centrality Analysis\\centrality_code.py` (original messy project).

Scope note: only ONE network-figure variant is published in the paper (the betweenness-sized,
"all EIPs" graph, `eip_between_all.png` -> Figure 9 / `fig:between`). The original
`centrality_code.py` additionally computed and saved 8 more network PNGs that never made it into
the paper: a closeness-sized and an eigenvector-sized version of the SAME "all EIPs" graph, plus
all three centrality-sized versions for each of the "Finalized ERC/Interface" and "Implemented
Core/Networking" subsets (9 PNGs total across 3 subsets x 3 centrality measures; all 9 are
preserved read-only for reference under `data/reference/original_figures/eip_{between,close,
eigen}_{all,final,imp}.png`). This port reproduces exactly the 3 PNGs the task's deliverable list
calls for -- one betweenness-sized network figure PER SUBSET (all / finalized / implemented),
matching what the paper actually publishes as "Figure 9" for the all-EIPs case, extended in the
same style to the other two subsets for symmetry. The redundant closeness-/eigenvector-sized
PNGs (6 more files, never referenced by any figure/table in the paper) are NOT re-plotted here --
this is a deliberate scope decision, not a bug, exactly analogous to the "dynamics" scope
reduction below. All three centrality MEASURES (betweenness, closeness, eigenvector) are still
computed and written to the `centrality_*.parquet` tables for every subset regardless, since the
downstream `build_cross_sectional_dataset.py` merge needs all three.

Scope reduction: the "DYNAMICS OF ALL EIP NETWORK" section (approved, out of scope)
--------------------------------------------------------------------------------------
The original script's final section, `for x in range(100, len(data.index)): ...`, rebuilds the
co-authorship graph from scratch at every row increment from row 100 to the last row and
re-plots + re-saves a PNG each time (potentially hundreds of images, one betweenness-centrality
network snapshot per additional EIP). It is not tied to any specific published paper figure or
table -- it looks like an exploratory/diagnostic scratch feature the original author used while
developing the "Figure 9" network plot, never cleaned up or wired to a caption. Per the approved
conversion plan, this section is OUT OF SCOPE and is NOT ported here. It remains available,
unmodified, in the original (read-only) project at `Analysis\\Centrality Analysis\\
centrality_code.py` for anyone who wants to regenerate it.

Two-pass circular dependency -- READ THIS BEFORE CHANGING INPUT/OUTPUT PATHS
------------------------------------------------------------------------------
This script has a real circular dependency with `code/02_data_preparation/
build_cross_sectional_dataset.py` (see that script's own module docstring, "circular dependency
#1", for the full writeup from the other side). In short:

    PASS 1: `build_cross_sectional_dataset.py` is run with no centrality data available yet
            (`data/interim/centrality_all.parquet` does not exist). It writes
            `data/processed/ethereum_cross_sectional_data.parquet` (+ a companion `.csv`) with
            all three centrality columns (betweenness_centrality / closeness_centrality /
            eigen_value_centrality) populated as null.
    PASS 2: THIS script reads that PASS-1 output as its own input (the original
            `centrality_code.py` read the CSV form of the exact same dataset,
            `Ethereum_Cross-sectional_Data_output.csv`; this port reads the equivalent, already
            zstd-compressed `data/processed/ethereum_cross_sectional_data.parquet`), builds the
            EIP co-authorship network, computes betweenness/closeness/eigenvector centrality per
            author, and writes `data/interim/centrality_all.parquet` (+ `_final.parquet` /
            `_imp.parquet` for transparency -- see "Output files" below).
    PASS 3: `build_cross_sectional_dataset.py` is re-run. It now finds
            `data/interim/centrality_all.parquet`, merges it in by `author_id` (exactly like the
            original's `merge m:1 author_id using centrality.dta`), and produces the FINAL,
            centrality-populated cross-sectional dataset used by every downstream figure/table
            that needs `betweenness_centrality` / `closeness_centrality` /
            `eigen_value_centrality` (e.g. the Table 3 regressions).

This script can therefore only be run AFTER `build_cross_sectional_dataset.py`'s pass 1, and
`build_cross_sectional_dataset.py` must be run AGAIN after this script for the final dataset to
be produced. Whoever writes `run_pipeline.py` must sequence these three passes in this exact
order.

Merge-key contract with `build_cross_sectional_dataset.py`
--------------------------------------------------------------
Confirmed by reading that script's source (`_load_centrality()`): it reads
`data/interim/centrality_all.parquet`, optionally renames an `"index"` column to `"author_id"`
(a compatibility shim for the original CSV's column name -- see "Output files" below), then
selects exactly `author_id`, `between`, `close`, `eigen` and joins them onto its own per-author-
slot columns via a left join keyed on `author_id`. This script therefore writes
`centrality_all.parquet` with a column literally named `author_id` (an `Int64`, matching the
`author{n}_id` columns it will be joined against slot-by-slot) plus `between` / `close` / `eigen`
(all `Float64`) -- no `"index"`-to-`"author_id"` rename is needed on the consumer side since this
script names the column correctly from the start.

Output files
-------------
- `output/figures/figure_10a_eip_network_all.png`          -- Figure 9 (all EIPs, betweenness-sized)
- `output/figures/figure_10b_eip_network_final.png`        -- same, Finalized ERC/Interface EIPs subset
- `output/figures/figure_10c_eip_network_implemented.png`  -- same, Implemented Core/Networking EIPs subset
- `output/figures/figure_11_clustering_coefficient_over_time.png` -- Figure 12
- `data/interim/centrality_all.parquet`    -- REQUIRED downstream input (see above). Columns:
      author_id (Int64), name (Utf8), n_eip (Int64), between (Float64), close (Float64),
      eigen (Float64). One row per author who appears in at least one of the 15 author slots of
      at least one (non-Meta/Informational) EIP.
- `data/interim/centrality_final.parquet`, `data/interim/centrality_imp.parquet` -- same schema,
  restricted to the Finalized-ERC/Interface and Implemented-Core/Networking subsets respectively.
  Not consumed by any other script in this package; written purely for transparency, matching the
  original's `centrality_final.csv` / `centrality_imp.csv`.

Data source
-----------
`DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"` (PASS-1 output of
`build_cross_sectional_dataset.py` -- see above). Needs (at minimum): `eip_number`, `Category`
(capitalized, matching `build_cross_sectional_dataset.py`'s raw column -- consistent with
`fig_eip_trends_and_concentration.py`'s convention of the same name), `status`, `implementation`
(the RAW column, NOT the `add_implemented_column()`-derived `implemented` used elsewhere in this
package -- see "Filters" below), `sdate` (already a proper `pl.Date`, unlike the original's raw
CSV string that needed `pd.to_datetime()`), and the wide `author{n}` / `author{n}_id` (n=1..15)
columns.

Filters (faithfully ported from `centrality_code.py`)
--------------------------------------------------------
- All EIPs: `Category not in ("Meta", "Informational")`. This is expected to be a NO-OP against
  the current input, since `build_cross_sectional_dataset.py` already applies this exact filter
  as its own final step -- kept here anyway for fidelity with the original script (which read a
  pre-filter raw CSV) and as a defensive no-op if this script is ever pointed at a differently
  filtered input.
- Finalized ERC/Interface EIPs: `status == "Final"` AND `Category in ("ERC", "Interface")`.
- Implemented Core/Networking EIPs: `implementation == 1` -- the RAW `implementation` column
  (from the Excel `inFork`/`Implementable` recode in `build_cross_sectional_dataset.py`), exactly
  as the original used, NOT the `implemented` column that `fig_eip_trends_and_concentration.py`
  derives via `add_implemented_column()` (which additionally nulls out non-terminal-status rows).

Refactor vs. the original (pure refactor -- identical computed values, cleaner code)
----------------------------------------------------------------------------------------
The original script copy-pastes the co-authorship-graph-building block and the
author-id -> name/EIP-count lookup-building block FOUR times: once each for the "all EIPs",
"Finalized ERC/Interface EIPs", and "Implemented Core/Networking EIPs" subsets, plus a fourth
copy inside the out-of-scope "dynamics" loop. This port factors both blocks into two shared
helpers, `build_coauthorship_graph()` and `build_author_lookup()`, called once per subset in
`process_variant()`. No computed value changes as a result of this refactor.

Name/EIP-count lookup covers all 15 author slots
----------------------------------------------------
`NAME_LOOKUP_SLOTS` matches `AUTHOR_SLOTS` (all 15 slots), consistent with the co-authorship graph
itself, which is also built from all 15 slots -- so every author with a real centrality value is
represented in the name/EIP-count lookup too. This matters concretely for `author_id` 639, the
15th listed author on EIP 6596.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import networkx.algorithms.community as nx_comm
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_INTERIM, DATA_PROCESSED, OUTPUT_FIGURES, ensure_dirs

# ---------------------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------------------
INPUT_PARQUET = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"

# All 15 author slots -- used for graph construction and the co-author-count computation.
AUTHOR_SLOTS: tuple[int, ...] = tuple(range(1, 16))

# Slots to scan when building the author_id -> name/EIP-count lookup (matches AUTHOR_SLOTS, so
# every author with a graph-based centrality value also gets a name/EIP-count entry).
NAME_LOOKUP_SLOTS: tuple[int, ...] = AUTHOR_SLOTS

FIG_NETWORK_ALL = OUTPUT_FIGURES / "figure_10a_eip_network_all.png"
FIG_NETWORK_FINAL = OUTPUT_FIGURES / "figure_10b_eip_network_final.png"
FIG_NETWORK_IMP = OUTPUT_FIGURES / "figure_10c_eip_network_implemented.png"
FIG_CLUSTERING = OUTPUT_FIGURES / "figure_11_clustering_coefficient_over_time.png"

CENTRALITY_ALL_PARQUET = DATA_INTERIM / "centrality_all.parquet"
CENTRALITY_FINAL_PARQUET = DATA_INTERIM / "centrality_final.parquet"
CENTRALITY_IMP_PARQUET = DATA_INTERIM / "centrality_imp.parquet"

# Rolling-window range for Figure 12, matching the original's `for y in range(2016, 2024)`.
CLUSTERING_YEAR_START = 2016
CLUSTERING_YEAR_END = 2023


# ---------------------------------------------------------------------------------------
# Input loading / cleaning
# ---------------------------------------------------------------------------------------
def _load_input_dataset() -> pl.DataFrame:
    """
    Load the PASS-1 output of `build_cross_sectional_dataset.py` -- see module docstring,
    "Two-pass circular dependency". This input is NOT optional: without it there is nothing to
    build a co-authorship network from, so a missing file raises immediately with a clear,
    actionable message (per the project's "never make up data" rule), rather than the
    null-fill-and-continue pattern used for centrality/FEM in `build_cross_sectional_dataset.py`
    itself (those two are optional there because a dataset without them is still useful; a
    missing input here has nothing for this script to do at all).
    """
    if not INPUT_PARQUET.exists():
        raise FileNotFoundError(
            f"Required input not found: {INPUT_PARQUET}\n"
            "This file is produced by code/02_data_preparation/build_cross_sectional_dataset.py "
            "(its PASS-1 run, i.e. before centrality is available -- see this script's own "
            "module docstring, 'Two-pass circular dependency', for the full explanation). Run "
            "that script first, then re-run this one."
        )
    df = pl.read_parquet(INPUT_PARQUET)
    # Defensive re-cast: guarantees author{n}_id are nullable Int64 regardless of how they were
    # written, so `int(v)` in build_coauthorship_graph() below never sees a float/string.
    id_casts = {f"author{i}_id": pl.col(f"author{i}_id").cast(pl.Int64, strict=False) for i in AUTHOR_SLOTS}
    return df.with_columns(*id_casts.values())


def _clean_et_al(df: pl.DataFrame) -> pl.DataFrame:
    """
    Faithful port of the original's `data.loc[data['author3'] == 'et al.', 'author3'] = np.NaN`.

    Only the author3 NAME is blanked here -- `author3_id` (and every other author-slot column)
    is left untouched, exactly as in the original. In practice this has no effect on the graph or
    centrality values (co-authorship edges are built from the `author{n}_id` columns only, never
    from the name columns), and only matters for the `name` column of the eventual output table,
    for the one specific row/slot where the substitution applies -- preserved here purely for
    exact fidelity with the original's data-cleaning step.
    """
    if "author3" not in df.columns:
        return df
    return df.with_columns(
        pl.when(pl.col("author3") == "et al.").then(None).otherwise(pl.col("author3")).alias("author3")
    )


# ---------------------------------------------------------------------------------------
# Shared helpers (replacing the original's 4x copy-pasted blocks)
# ---------------------------------------------------------------------------------------
def build_coauthorship_graph(df: pl.DataFrame, author_slots: tuple[int, ...] = AUTHOR_SLOTS) -> nx.Graph:
    """
    Build the undirected, weighted EIP co-authorship graph for the given (already-filtered) EIP
    subset: one node per `author_id` (as a string, matching the original's `str(int(...))` keys),
    one edge per co-authoring pair, with edge weight = the number of EIPs (rows of `df`) that pair
    co-authored together. Self-loops (an id appearing twice in the same row, which should not
    normally happen but is not asserted against) are removed at the end, matching the original's
    `G.remove_edges_from(nx.selfloop_edges(G))`.

    This is the shared version of the co-authorship-graph-building block that the original
    `centrality_code.py` copy-pastes four times (all/final/imp variants + the out-of-scope
    dynamics loop) -- a pure refactor, not a behavior change.
    """
    id_cols = [f"author{i}_id" for i in author_slots]
    G = nx.Graph()
    for row in df.select(id_cols).iter_rows():
        author_ids = [str(int(v)) for v in row if v is not None]
        for a in author_ids:
            if a not in G:
                G.add_node(a)
        for i in range(len(author_ids)):
            for j in range(i + 1, len(author_ids)):
                a, b = author_ids[i], author_ids[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    G.remove_edges_from(nx.selfloop_edges(G))
    return G


def build_author_lookup(
    df: pl.DataFrame, name_slots: tuple[int, ...] = NAME_LOOKUP_SLOTS
) -> tuple[dict[str, str], dict[str, int]]:
    """
    Build {author_id_str: display_name} and {author_id_str: n_eip} lookup dicts for the given
    (already-filtered) EIP subset, scanning all `name_slots`.

    Iteration order is: outer loop over slot number ascending, inner loop over rows -- so for an
    author_id appearing in multiple slots/rows, the last-visited row's `name` wins.
    """
    names: dict[str, str] = {}
    counts: dict[str, int] = {}
    for i in name_slots:
        id_col, name_col = f"author{i}_id", f"author{i}"
        for author_id, name in df.select(id_col, name_col).iter_rows():
            if author_id is None:
                continue
            key = str(int(author_id))
            names[key] = name
            counts[key] = counts.get(key, 0) + 1
    return names, counts


def _get_last_name(full_name: str) -> str:
    """Faithful port of the original's `get_last_name`: extract the last whitespace-separated
    token of a full name (used for network-graph node labels)."""
    parts = full_name.split()
    return parts[-1] if parts else full_name


def plot_network_figure(
    G: nx.Graph, centrality: dict[str, float], name_lookup: dict[str, str], out_path: Path
) -> None:
    """
    Network plot restricted to the graph's largest connected component (the full graph includes
    many authors with only one or two co-authorship ties, which -- across all ~685 authors in the
    "all EIPs" variant -- produced an unreadable hairball with most nodes flung to the margins).
    Node size is scaled linearly by `centrality` (betweenness), matching the original design.
    Node color now encodes community membership, detected via greedy modularity maximization
    (Clauset-Newman-Moore) on the largest component, weighted by co-authorship count -- this
    directly addresses referee R1.5's request to "investigate communities or factions" and R1.m4's
    request to improve the layout / reduce clutter. Node attraction in the spring layout is now
    weighted by co-authorship count (`weight="weight"`), so repeat collaborators are pulled
    together more strongly than one-off co-authors, which was not the case before (the original
    `spring_layout` call ignored edge weights entirely). Labels (last name only) are shown for
    nodes above the 95th percentile of `centrality` computed over ALL authors (matching the
    paper's Figure 9 caption, "top 5 percentile of authors"), restricted to those actually
    plotted in the largest component.
    """
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    giant = G.subgraph(components[0]).copy()
    n_dropped = G.number_of_nodes() - giant.number_of_nodes()

    comms = nx_comm.greedy_modularity_communities(giant, weight="weight")
    comm_of = {author_id: i for i, c in enumerate(comms) for author_id in c}
    cmap = plt.get_cmap("tab20")

    m95 = float(np.percentile(list(centrality.values()), 95))
    labels = {
        author_id: _get_last_name(name_lookup[author_id])
        for author_id in giant.nodes()
        if centrality.get(author_id) is not None and centrality[author_id] > m95
    }

    values = np.asarray([centrality[n] for n in giant.nodes()], dtype=float)
    node_size = (values - values.min()) * 990 / (values.max() - values.min()) + 10
    node_color = [cmap(comm_of[n] % 20) for n in giant.nodes()]

    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(giant, k=0.25, iterations=200, weight="weight", seed=10)
    nx.draw_networkx_nodes(giant, pos, node_size=node_size, node_color=node_color, edgecolors="black", linewidths=0.4)
    nx.draw_networkx_edges(giant, pos, alpha=0.15)
    nx.draw_networkx_labels(giant, pos, labels, font_size=10, font_weight="bold")
    plt.axis("off")
    plt.box(False)  # removes the surrounding axes box, matching the original
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()

    print(
        f"[fig_network_centrality] plot_network_figure({out_path.name}): plotted "
        f"{giant.number_of_nodes()} of {G.number_of_nodes()} authors in the largest connected "
        f"component ({n_dropped} authors in smaller/isolated components not shown), "
        f"{len(comms)} communities detected."
    )


# ---------------------------------------------------------------------------------------
# Figure 9: per-subset network + centrality table
# ---------------------------------------------------------------------------------------
def process_variant(df: pl.DataFrame, network_fig_path: Path) -> pl.DataFrame:
    """
    For one (already-filtered) EIP subset: build the co-authorship graph and author lookup,
    compute betweenness/closeness/eigenvector centrality per author, save the betweenness-sized
    network-graph figure, and return the per-author centrality table (author_id, name, n_eip,
    between, close, eigen) -- one row per key in the (KNOWN-ISSUE-affected, slots-1-14-only)
    author lookup, exactly matching the original's inner-merge-restricted `eip_bc_df`.
    """
    G = build_coauthorship_graph(df)
    names, counts = build_author_lookup(df)

    betweenness = nx.betweenness_centrality(G, weight="weight")
    closeness = nx.closeness_centrality(G)
    eigen = nx.eigenvector_centrality(G, weight="weight")

    # Only the betweenness-sized network figure is plotted per subset -- see module docstring
    # "Scope note" for why the closeness-/eigenvector-sized variants are not re-plotted here.
    plot_network_figure(G, betweenness, names, network_fig_path)

    records = [
        {
            "author_id": int(author_id),
            "name": name,
            "n_eip": counts[author_id],
            "between": betweenness[author_id],
            "close": closeness[author_id],
            "eigen": eigen[author_id],
        }
        for author_id, name in names.items()
    ]
    return pl.DataFrame(
        records,
        schema={
            "author_id": pl.Int64,
            "name": pl.Utf8,
            "n_eip": pl.Int64,
            "between": pl.Float64,
            "close": pl.Float64,
            "eigen": pl.Float64,
        },
    )


# ---------------------------------------------------------------------------------------
# Figure 12: clustering coefficient over time (2-year rolling window)
# ---------------------------------------------------------------------------------------
def compute_clustering_by_year(
    df: pl.DataFrame, start_year: int = CLUSTERING_YEAR_START, end_year: int = CLUSTERING_YEAR_END
) -> pl.DataFrame:
    """
    2-year trailing-window average clustering coefficient of the all-EIPs co-authorship graph,
    plus the average number of co-authors per EIP in that same window. Faithful port of the
    original's `for y in range(2016, 2024): datax = data[(data['year']==y) | (data['year']==y-1)]`
    loop.

    The "average number of co-authors per EIP" is recomputed directly from the author-id columns
    here (a straight count of non-null `author{n}_id` slots per row, matching the original's own
    `len(authorids)` computed from its freshly-built `allid` column) -- deliberately NOT read from
    this dataset's own `n_authors` column, which (per `build_cross_sectional_dataset.py`'s
    module docstring) can be null whenever `author1_id` itself is null, a different semantic than
    a plain per-row author-slot count.
    """
    df = df.with_columns(pl.col("sdate").dt.year().alias("__year"))
    n_coauthors = pl.sum_horizontal(
        [pl.col(f"author{i}_id").is_not_null().cast(pl.Int64) for i in AUTHOR_SLOTS]
    ).alias("__n_coauthors")
    df = df.with_columns(n_coauthors)

    records: list[dict] = []
    for y in range(start_year, end_year + 1):
        window = df.filter(pl.col("__year").is_in([y - 1, y]))
        if window.is_empty():
            continue
        G_year = build_coauthorship_graph(window)
        records.append(
            {
                "year": y,
                "clustering": nx.average_clustering(G_year),
                "avg_coauthors": window.get_column("__n_coauthors").mean(),
            }
        )
    return pl.DataFrame(records)


def plot_clustering_over_time(clus_year: pl.DataFrame, out_path: Path) -> None:
    """
    Dual-axis bar chart: clustering coefficient (red, left axis) and average number of
    co-authors per EIP (blue, right axis) by rolling-window end-year. Faithful in VALUES to the
    original's pandas-`.plot(kind='bar', position=...)` dual-axis chart.

    DELIBERATE DEVIATION (cosmetic only, zero effect on plotted values): the original positions
    its two bar series via pandas' internal `position=0`/`position=1` bar-plot machinery on a
    categorical (year-indexed) x-axis. This port achieves the same visual side-by-side grouped-bar
    layout directly in matplotlib (explicit +/- width/2 x-offsets) rather than depending on
    pandas' bar-plot internals -- purely a rendering-mechanics substitution; the underlying
    clustering/avg_coauthors values plotted are unchanged.
    """
    years = clus_year.get_column("year").to_list()
    clustering = clus_year.get_column("clustering").to_list()
    avg_coauthors = clus_year.get_column("avg_coauthors").to_list()

    x = np.arange(len(years))
    width = 0.4

    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    ax.bar(x + width / 2, clustering, width=width, color="red", label="Clustering Coefficient")
    ax2.bar(x - width / 2, avg_coauthors, width=width, color="blue", label="Avg Number of Co-authors")

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("Year")
    ax.set_ylabel("Clustering Coefficient")
    ax2.set_ylabel("Avg. N. of Authors per EIP")
    ax.set_ylim(ymin=0.4)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(lines1 + lines2, labels1 + labels2, loc="upper center", ncols=2)

    if 2023 in years:
        idx2023 = years.index(2023)
        ax.text(
            x[idx2023],
            0.97,
            "*",
            ha="center",
            va="top",
            fontsize=16,
            fontweight="bold",
            transform=ax.get_xaxis_transform(),
        )

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------
def main() -> None:
    ensure_dirs()

    df = _load_input_dataset()
    # Expected to be a no-op given the input's provenance -- see module docstring "Filters".
    df = df.filter(~pl.col("Category").is_in(["Meta", "Informational"]))
    df = _clean_et_al(df)

    df_final = df.filter((pl.col("status") == "Final") & pl.col("Category").is_in(["ERC", "Interface"]))
    df_imp = df.filter(pl.col("implementation") == 1)

    all_table = process_variant(df, FIG_NETWORK_ALL)
    final_table = process_variant(df_final, FIG_NETWORK_FINAL)
    imp_table = process_variant(df_imp, FIG_NETWORK_IMP)

    all_table.write_parquet(CENTRALITY_ALL_PARQUET, compression="zstd")
    final_table.write_parquet(CENTRALITY_FINAL_PARQUET, compression="zstd")
    imp_table.write_parquet(CENTRALITY_IMP_PARQUET, compression="zstd")

    print(
        "[fig_network_centrality] Wrote centrality tables:\n"
        f"  all EIPs:       {all_table.height} authors -> {CENTRALITY_ALL_PARQUET}\n"
        f"  finalized ERC/Interface: {final_table.height} authors -> {CENTRALITY_FINAL_PARQUET}\n"
        f"  implemented Core/Networking: {imp_table.height} authors -> {CENTRALITY_IMP_PARQUET}"
    )

    clus_year = compute_clustering_by_year(df)
    plot_clustering_over_time(clus_year, FIG_CLUSTERING)

    overall_clustering = nx.average_clustering(build_coauthorship_graph(df))
    print(
        f"[fig_network_centrality] Overall (full-period) clustering coefficient of the all-EIPs "
        f"co-authorship network: {overall_clustering:.4f} (paper text reports ~0.6 for this figure)."
    )
    print(
        "[fig_network_centrality] Reminder: re-run code/02_data_preparation/"
        "build_cross_sectional_dataset.py now that data/interim/centrality_all.parquet exists, "
        "to produce the FINAL, centrality-populated cross-sectional dataset (see this script's "
        "module docstring, 'Two-pass circular dependency')."
    )


if __name__ == "__main__":
    main()
