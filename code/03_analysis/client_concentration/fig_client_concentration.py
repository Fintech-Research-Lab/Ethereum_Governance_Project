"""
fig_client_concentration.py
==============================

Reproduces **Figure 16** (`\\label{fig:lorenz_commits}`, "Client Implementation Concentration")
and **Figure 20, panel d** (`\\label{fig:ncomp}`) of the current manuscript,
`paper/latex/MS_R2.tex`. Figure numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date.

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper sections
--------------
- Figure 16 (Concentration in Client Development): Lorenz curves of git-commit concentration for
  each of the four Ethereum execution-client codebases (Geth, Besu, Erigon, Nethermind), plus the
  average Gini coefficient across all four clients.
- Figure 20, panel d: stacked percentage bar chart of client developers' company/employer
  affiliation, broken out by client codebase. Panels a-c of Figure 20 (top-10 companies by
  EIP-author count/EIP count, and the company-level Lorenz curve) are produced by the sibling
  script `code/03_analysis/company_influence/fig_company_concentration.py` -- this script's
  `make_client_company_bar` follows that script's plotting conventions (matplotlib, dpi=200,
  horizontal-bar / stacked-bar style, `output/figures/` destination) so panel d reads as part of the
  same figure family.

Ported from: `Analysis\\Client Analysis\\Client_analysis.do` (read in full).

Data sources
------------
- `data/raw/commits/client_commit/{besu,erigon,geth,nethermind}_commits.parquet`, via
  `utils.client_commits.load_all_client_commits` (columns: `author`, `identifier`, `date`, `message`
  per `RAW_DATA_MANIFEST.md`; `identifier` is the commit author's GitHub login, matching the original's
  `identifier` -> `login` rename).
- `data/raw/social/client_employment.csv` (per `RAW_DATA_MANIFEST.md`: "Author<->employer (client)
  mapping. Feeds Client Analysis (Lorenz, company figures)."), columns `Name`, `Github_Username`,
  `Company`, `Job _Title`, `Client`, `Past_company`, `Job_title_Pastcompany1` -- only `Company` and
  `Client` are used here, matching the original's `company`/`client` usage.

Outputs
-------
- `output/figures/figure_20_client_lorenz.png`
- `output/figures/figure_16d_client_company.png`
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_RAW, OUTPUT_FIGURES, ensure_dirs
from utils.client_commits import VALID_CLIENTS, load_all_client_commits
from utils.inequality import gini, lorenz_curve

CLIENT_EMPLOYMENT_CSV = DATA_RAW / "social" / "client_employment.csv"

# Original plots in this exact order (besu, erigon, geth, nethermind -- matching the `.do` file's
# `foreach var in besu erigon geth nethermind` loop and its four `twoway line` series/legend labels).
CLIENT_ORDER: tuple[str, ...] = ("besu", "erigon", "geth", "nethermind")
CLIENT_LABELS: dict[str, str] = {
    "besu": "Besu",
    "erigon": "Erigon",
    "geth": "Geth",
    "nethermind": "Nethermind",
}


# ---------------------------------------------------------------------------------------
# Figure 16: lorenz_commits.png -> figure_20_client_lorenz.png
# ---------------------------------------------------------------------------------------
def _build_commit_counts_by_client_login() -> pl.DataFrame:
    """
    Replicates:
        * Put all client commit together (dir-glob load, tag each with its client name)
        drop if identifier ==""
        rename identifier login
        gen ncomm = 1
        collapse (count) ncomm , by(client login)

    Returns one row per (client, login) with `ncomm` = that developer's total commit count on
    that client's codebase.
    """
    commits = load_all_client_commits()

    frames = []
    for client in VALID_CLIENTS:
        df = commits[client].select(pl.col("identifier").alias("login"))
        frames.append(df.with_columns(pl.lit(client).alias("client")))
    combined = pl.concat(frames, how="vertical")

    # `drop if identifier ==""` -- also drop nulls, since a null identifier is the Polars/Parquet
    # equivalent of Stata's empty string for a string column.
    combined = combined.filter(pl.col("login").is_not_null() & (pl.col("login") != ""))

    combined = combined.with_columns(pl.lit(1).alias("ncomm"))
    collapsed = combined.group_by(["client", "login"]).agg(pl.col("ncomm").sum().alias("ncomm"))
    return collapsed


def make_client_lorenz_and_gini(collapsed: pl.DataFrame) -> None:
    """
    Computes the per-client Gini (averaged across the 4 clients, replicating the `.do` file's
    `gini_av` loop over `besu erigon geth nethermind`) and plots the 4-series Lorenz curve
    (`lorenz_commits.png` original -> `figure_20_client_lorenz.png` here).

    Uses `utils.inequality.gini` / `lorenz_curve` rather than hand-rolling the Stata
    `ineqdec0` / `insobs`+`gsort`+cumsum logic.

    Note on the x-axis: the original plot's x-axis (`client_cont`) is the developer's raw RANK
    (1, 2, 3, ... sorted most-to-least prolific), restricted to `client_cont < 100` (i.e. only the
    first 99 ranked developers are actually plotted -- the original caption's "N. of Developers"
    axis is deliberately zoomed to the head of the distribution, not the full client roster, which
    can run into the thousands of one-off contributors for e.g. Erigon). `lorenz_curve()`'s own
    x-axis convention is `pct_population` (0-100, a % of developers) rather than a raw rank count,
    so this function re-derives the raw rank (0..n, where 0 is the synthetic origin point
    `lorenz_curve` prepends) alongside `lorenz_curve`'s `cum_pct_value` y-values, and applies the
    same `< 100` restriction to that raw-rank x-axis to match the original figure's actual axis.
    """
    gini_av = 0.0
    per_client_gini: dict[str, float] = {}
    for client in ("besu", "erigon", "geth", "nethermind"):  # order per the `.do` file's `foreach`
        ncomm = collapsed.filter(pl.col("client") == client).get_column("ncomm")
        g = gini(ncomm)
        per_client_gini[client] = g
        gini_av += g
    gini_av /= 4.0
    print(f"[fig_client_concentration] Per-client Gini: {per_client_gini}")
    print(f"[fig_client_concentration] Average Gini across the 4 clients (gini_av): {gini_av:.4f}")

    fig, ax = plt.subplots(figsize=(7, 6))
    for client in CLIENT_ORDER:
        ncomm = collapsed.filter(pl.col("client") == client).get_column("ncomm")
        lc = lorenz_curve(ncomm, descending=True)  # prepends the (0, 0) origin, per its own docstring
        n = ncomm.len()
        rank = list(range(0, n + 1))  # row 0 = synthetic origin, row i = the i-th most-prolific developer
        cum_pct = lc.get_column("cum_pct_value").to_list()

        # `if client_cont < 100` in the original -- zoom to the first 99 ranked developers.
        x = [r for r in rank if r < 100]
        y = cum_pct[: len(x)]
        ax.plot(x, y, label=CLIENT_LABELS[client])

    ax.set_xlabel("N. of Developers")
    ax.set_ylabel("% of Commits")
    ax.legend(loc="lower right")
    fig.tight_layout()
    out_path = OUTPUT_FIGURES / "figure_20_client_lorenz.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[fig_client_concentration] Wrote {out_path}")


# ---------------------------------------------------------------------------------------
# Figure 20d: client_company.png -> figure_16d_client_company.png
# ---------------------------------------------------------------------------------------
def make_client_company_bar() -> None:
    """
    Replicates the "CLIENT EMPLOYMENT ANALYSIS" block:
        insheet using "Data\\Raw Data\\Client_Employment.csv", clear names
        egen found = count(Name) if company ~=""
        replace found = found / _N
        sum found
        drop if company ==""
        gen one = 1
        collapse (count) one, by(company client)
        gsort -one
        gen company2 = company
        replace company2 = "Others" if one <6
        graph bar one , over(company2) over(client) asyvars stack percentages ...

    Each (company2, client) bar segment shows the mean company headcount within that segment
    (per company, not summed) -- for the "Others" segment specifically, this is the average size
    of the small companies folded into it, not their combined total headcount.
    """
    ensure_dirs()
    emp = pl.read_csv(CLIENT_EMPLOYMENT_CSV)

    # `egen found = count(Name) if company ~="" / replace found = found/_N / sum found` -- diagnostic
    # only (% of client developers with a known company), not used by any figure; reproduced as a
    # print for parity with the original's `sum found` output.
    n_total = emp.height
    n_found = emp.filter(pl.col("Company").is_not_null() & (pl.col("Company") != "")).height
    print(f"[fig_client_concentration] found (% of client devs with known company): {100.0 * n_found / n_total:.2f}%")

    emp2 = emp.filter(pl.col("Company").is_not_null() & (pl.col("Company") != ""))
    emp2 = emp2.with_columns(pl.lit(1).alias("one"))
    counts = emp2.group_by(["Company", "Client"]).agg(pl.col("one").sum().alias("one"))

    counts = counts.with_columns(
        pl.when(pl.col("one") < 6).then(pl.lit("Others")).otherwise(pl.col("Company")).alias("company2")
    )

    grouped = counts.group_by(["company2", "Client"]).agg(pl.col("one").mean().alias("val"))

    # `percentages`: normalize each client's stacked bar to sum to 100% across its company2 segments.
    totals = grouped.group_by("Client").agg(pl.col("val").sum().alias("total"))
    grouped = grouped.join(totals, on="Client").with_columns((100.0 * pl.col("val") / pl.col("total")).alias("pct"))

    clients = sorted(grouped.get_column("Client").unique().to_list())
    # Segment display order: descending by each company2's total share across all clients combined.
    segment_order = (
        grouped.group_by("company2").agg(pl.col("pct").sum().alias("tot")).sort("tot", descending=True)
        .get_column("company2").to_list()
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bottoms = [0.0] * len(clients)
    for segment in segment_order:
        seg_df = grouped.filter(pl.col("company2") == segment)
        values = []
        for c in clients:
            row = seg_df.filter(pl.col("Client") == c)
            values.append(row.get_column("pct").to_list()[0] if row.height else 0.0)
        ax.bar(clients, values, bottom=bottoms, label=segment)
        bottoms = [b + v for b, v in zip(bottoms, values)]

    ax.set_ylabel("% of Client Developers")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, fontsize="small")
    fig.tight_layout()
    out_path = OUTPUT_FIGURES / "figure_16d_client_company.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[fig_client_concentration] Wrote {out_path}")


def main() -> None:
    ensure_dirs()
    collapsed = _build_commit_counts_by_client_login()
    make_client_lorenz_and_gini(collapsed)
    make_client_company_bar()


if __name__ == "__main__":
    main()
