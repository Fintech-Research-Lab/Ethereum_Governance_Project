"""
fig_adoption.py
===============

Reproduces **Figure 18** (`\\label{fig:stable_perc}`/`fig:stable`, "Stablecoin Concentration") and
**Figure 19** (`\\label{fig:oracle}`, "Oracle Concentration") of the current manuscript,
`paper/latex/MS_R2.tex`. Figure numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date.

Paper: Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.

Figures produced (paper section "Concentration in Client Adoption"):
    * Figure 18a -- "Stablecoin Share of Total Ethereum DeFi TVL"
      (data: `stable_perc.png` in the original) -- total combined USDC+USDT+DAI TVL
      as a fraction of total Ethereum DeFi TVL, over time.
    * Figure 18b -- "Stablecoin Market Share (USDC / USDT / DAI)"
      (data: `stable.png` in the original) -- market share of each of USDC, USDT, DAI
      within the combined stablecoin TVL, over time (stacked-area style).
    * Figure 19a -- "Oracle TVL Market Share" (`oracle_pie.png` in the original) --
      pie chart of TVL secured by each major oracle protocol (Chainlink, Chronicle,
      Pyth, TWAP, RedStone), with every smaller oracle collapsed into "others".
    * Figure 19b -- "Oracle Protocol Count" (`oracle_bar.png` in the original) -- bar
      chart of the number of protocols relying on TVL >= $150M for each major oracle.

Ported from: `Analysis\\Adoption Analysis\\Oracle_Stablecoin_analysis.do`.

Two implementation notes: (1) the stablecoin market-share plot applies no lower-bound
date filter, plotting the full available date range; (2) the "others" bucket in the
oracle pie chart is constructed via an explicit synthetic row representing every
smaller oracle collapsed together.

Frozen-data note (see `archive/code/01_data_collection/README` / project docstring
conventions): this script's INPUTS are frozen, point-in-time DeFiLlama TVL snapshots
(`oracle_data.csv`, `USDC_MASTER.csv`, `USDT_MASTER.csv`, `DAI_MASTER.csv`,
`Total_TVL_ETH.csv`, all under `data/raw/adoption/`). Re-querying the live DeFiLlama
API today would return CURRENT, not historical, TVL, silently invalidating any
figure that claims to show "TVL as of [past date]" -- see `archive/code/01_data_collection/`
for why a live re-fetch script was intentionally not written for this analysis. This
script itself IS fully deterministic and reproducible given those frozen inputs; it is
only the upstream *data collection* step that is frozen-by-necessity, not this one.

Dynamic column-sum design (faithfully preserved): the original's stablecoin loop uses
Stata's `ds` (describe short) to enumerate ALL columns in each `*_MASTER.csv` at
runtime and sums every one of them except `evt_date` via a `capture egen rowtotal`
loop -- i.e. it has NO fixed/hardcoded list of venue columns, so a future snapshot
that adds a new DeFi venue column would automatically be picked up and summed. This
port replicates that dynamic design directly in Polars: `_stablecoin_daily_total()`
below sums `pl.exclude(["evt_date"])` (via `pl.sum_horizontal`) rather than a
hardcoded venue list, matching the original's intentionally dynamic behavior.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DATA_RAW, OUTPUT_FIGURES, ensure_dirs  # noqa: E402

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

ADOPTION_RAW = DATA_RAW / "adoption"

# `gen small = (tvl < 150000000 | tvl==.)`
ORACLE_TVL_THRESHOLD = 150_000_000

STABLE_FILES = {
    "USDC": "USDC_MASTER.csv",
    "USDT": "USDT_MASTER.csv",
    "DAI": "DAI_MASTER.csv",
}

# `keep if date < date("11-18-2023", "MDY")`
STABLE_END_DATE = date(2023, 11, 18)
# NOTE: the original .do file ALSO has a commented-out lower-bound line immediately
# above the one above (`*keep if date > date("01-05-2021", "MDY")`). A leading `*` in
# Stata is a full-line comment, so that lower bound is never applied. This port
# preserves that exactly -- no lower-bound filter is applied to the market-share
# series below, matching the .do file's actual (not its apparently-intended) behavior.


# ---------------------------------------------------------------------------------
# ORACLE (Figure 19)
# ---------------------------------------------------------------------------------
def build_oracle_tables() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Reproduce the ORACLE section of `Oracle_Stablecoin_analysis.do`.

    Returns
    -------
    (pie_df, bar_df) :
        pie_df -- one row per "large" oracle (tvl >= ORACLE_TVL_THRESHOLD) plus one
            synthetic "others" row (the summed tvl of every oracle below the
            threshold). Feeds Figure 19a (TVL pie chart).
        bar_df -- pie_df with the "others" row excluded. Feeds Figure 19b (protocol
            count bar chart).
    """
    df = pl.read_csv(ADOPTION_RAW / "oracle_data.csv")
    # The raw CSV's first column has an empty header (a leftover pandas row-index
    # column from however `oracle_data.csv` was originally exported). Stata's
    # `insheet` names an unnamed column "v1"; the original .do file uses `v1` for
    # exactly one purpose -- identifying the single blank observation appended by
    # `insobs 1` below (`replace small = 0 if v1==.`). We keep that same column
    # (renamed for clarity) for the same purpose rather than inventing a different
    # mechanism.
    first_col = df.columns[0]
    df = df.rename({first_col: "row_idx"})

    # `insobs 1` -- append a single wholly-blank observation.
    blank_row = pl.DataFrame({c: [None] for c in df.columns}, schema=df.schema)
    df = pl.concat([df, blank_row], how="vertical")

    # `gen small = (tvl < 150000000 | tvl==.)`
    df = df.with_columns(
        ((pl.col("tvl") < ORACLE_TVL_THRESHOLD) | pl.col("tvl").is_null()).alias("small")
    )

    # `bys small: egen tvl2 = total(tvl)` -- Stata's `total()` ignores (skips) missing
    # values when summing, which is also Polars' default `.sum()` null behavior.
    df = df.with_columns(pl.col("tvl").sum().over("small").alias("tvl2"))

    # `replace oracle = "others" if oracle==""` -- the blank row's `oracle` field
    # reads back as null (empty CSV cell), so we treat null the same as "".
    df = df.with_columns(
        pl.when(pl.col("oracle").is_null() | (pl.col("oracle") == ""))
        .then(pl.lit("others"))
        .otherwise(pl.col("oracle"))
        .alias("oracle")
    )

    # `replace tvl = tvl2 if tvl==.` -- only the blank/"others" row still has a null
    # `tvl` at this point, so this assigns it the summed TVL of every "small" oracle.
    df = df.with_columns(
        pl.when(pl.col("tvl").is_null())
        .then(pl.col("tvl2"))
        .otherwise(pl.col("tvl"))
        .alias("tvl")
    )

    # `replace small = 0 if v1==.` -- pull the "others" aggregate row OUT of the
    # "small" bucket so it appears as its own slice/bar alongside the individually
    # large oracles (this is the only row with a null `row_idx`).
    df = df.with_columns(
        pl.when(pl.col("row_idx").is_null())
        .then(pl.lit(False))
        .otherwise(pl.col("small"))
        .alias("small")
    )

    # `gsort -tvl`
    df = df.sort("tvl", descending=True)

    # `graph pie tvl if small == 0, over(oracle) sort desc ...`
    pie_df = df.filter(~pl.col("small"))
    # `graph bar num* if small == 0 & oracle ~= "others", over(oracle) ...`
    bar_df = pie_df.filter(pl.col("oracle") != "others")
    return pie_df, bar_df


def plot_oracle_pie(pie_df: pl.DataFrame, out_path: Path) -> None:
    labels = pie_df["oracle"].to_list()
    values = pie_df["tvl"].to_list()
    fig, ax = plt.subplots(figsize=(7, 7), facecolor="white")
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def plot_oracle_bar(bar_df: pl.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="white")
    ax.bar(bar_df["oracle"].to_list(), bar_df["num_protocols_with_tvl_gt_0"].to_list())
    ax.set_ylabel("Number of Protocols")
    ax.yaxis.grid(True)
    fig.autofmt_xdate(rotation=45)
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------------
# STABLECOIN (Figure 18)
# ---------------------------------------------------------------------------------
def _stablecoin_daily_total(name: str) -> pl.DataFrame:
    """Reproduce, per stablecoin, the `ds` / `capture egen rowtotal` loop:
    dynamically sum EVERY column present in the `*_MASTER.csv` file except
    `evt_date` (no hardcoded venue list -- see module docstring), treating a missing
    per-venue value as 0 (Stata `rowtotal` default; matches Polars `sum_horizontal`).
    """
    # `infer_schema_length=None` scans the WHOLE file (not just a leading sample)
    # to determine each column's dtype. Several venue columns (e.g. Balancer,
    # Bancor, Yearn) are entirely blank for the earliest dates -- with the
    # default sample-based inference those all-blank leading rows would make
    # Polars infer them as String, which would then silently drop them from the
    # dynamic sum below (a type mismatch this port must not introduce: Stata's
    # own `insheet`/`ds` scans the whole file, so those columns ARE numeric and
    # ARE summed in the original once real values start appearing later in the
    # series).
    df = pl.read_csv(ADOPTION_RAW / STABLE_FILES[name], infer_schema_length=None)
    value_cols = [c for c in df.columns if c != "evt_date"]
    df = df.with_columns(pl.sum_horizontal([pl.col(c) for c in value_cols]).alias("total"))
    df = df.with_columns(pl.lit(name).alias("stable"))
    return df.select(["evt_date", "total", "stable"])


def build_stablecoin_wide() -> pl.DataFrame:
    """Reproduce the `append` + `reshape wide` + market-share block."""
    long_df = pl.concat([_stablecoin_daily_total(name) for name in STABLE_FILES], how="vertical")

    # `reshape wide total, i(evt_date) j(stable) string` + the three `rename`s.
    wide = long_df.pivot(values="total", index="evt_date", columns="stable")

    # `egen total = rowtotal(DAI USDC USDT)`
    wide = wide.with_columns(
        pl.sum_horizontal([pl.col("DAI"), pl.col("USDC"), pl.col("USDT")]).alias("total")
    )
    # `replace DAI = DAI/total` / `replace USDC = USDC/total` / `replace USDT = USDT/total`
    wide = wide.with_columns(
        [
            (pl.col("DAI") / pl.col("total")).alias("DAI"),
            (pl.col("USDC") / pl.col("total")).alias("USDC"),
            (pl.col("USDT") / pl.col("total")).alias("USDT"),
        ]
    )
    # `egen two = rowtotal(USDC USDT)` / `egen three = rowtotal(two DAI)`
    wide = wide.with_columns(pl.sum_horizontal([pl.col("USDC"), pl.col("USDT")]).alias("two"))
    wide = wide.with_columns(pl.sum_horizontal([pl.col("two"), pl.col("DAI")]).alias("three"))

    # `gen date = dofc(clock(evt_date, "YMD hm"))` -- evt_date looks like
    # "2020-09-16 00:00".
    wide = wide.with_columns(
        pl.col("evt_date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M", strict=False).alias("date")
    )
    return wide


def plot_stable_market_share(wide: pl.DataFrame, out_path: Path) -> None:
    """Figure 18b (`stable.png`): USDC/USDT/DAI market share, stacked-area style."""
    df = wide.filter(pl.col("date").dt.date() < STABLE_END_DATE).sort("date")
    x = df["date"].to_list()
    three = df["three"].to_list()
    two = df["two"].to_list()
    usdc = df["USDC"].to_list()

    fig, ax = plt.subplots(figsize=(9, 6), facecolor="white")
    # The original draws three overlapping `twoway area` layers back-to-front
    # (three, then two, then USDC). None of the three series is itself a
    # "layer difference" -- each is plotted from 0 -- but drawing largest-first,
    # smallest-last with opaque fills visually produces a stacked band per
    # stablecoin (DAI on top, USDT in the middle, USDC on the bottom). Reproduced
    # here with the identical draw order via three `fill_between` calls.
    ax.fill_between(x, 0, three, label="DAI", color="#4C72B0")
    ax.fill_between(x, 0, two, label="USDT", color="#DD8452")
    ax.fill_between(x, 0, usdc, label="USDC", color="#55A868")
    ax.set_ylim(0, 1)
    ax.set_yticks([i / 5 for i in range(6)])
    ax.set_xlabel("Date")
    ax.set_ylabel("TVL Market Share")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
    fig.autofmt_xdate(rotation=45)
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def build_stablecoin_pct_of_tvl(wide: pl.DataFrame) -> pl.DataFrame:
    """Reproduce the "TREND IN TOTAL STABLECOIN MARKET VS TOTAL TVL" block."""
    stable = wide.select(
        [pl.col("date").dt.date().alias("date"), pl.col("total").alias("stable")]
    )

    tvl = pl.read_csv(ADOPTION_RAW / "Total_TVL_ETH.csv")
    tvl = tvl.rename({"Protocol": "date_str", "Total": "total"})
    # Total_TVL_ETH's date column looks like "29/06/2018" / "1/7/2018" (D/M/Y, no
    # leading zeros) -- matches Stata's `date(date, "DMY")`.
    tvl = tvl.with_columns(
        pl.col("date_str").str.strptime(pl.Date, "%d/%m/%Y", strict=False).alias("date")
    ).drop("date_str")

    # `merge 1:1 date using temp` with Total_TVL_ETH as the (already-in-memory)
    # master and the stablecoin series as the "using" file, then `drop if _merge==2`
    # (rows found only in the "using"/stablecoin data). A left join from the TVL
    # side already excludes those, so no separate drop step is needed here.
    merged = tvl.join(stable, on="date", how="left")

    # `egen mindate = min(date) if _merge==3` / `drop if date<mindate` -- trim the
    # TVL series so it starts at the first date the stablecoin data actually merges.
    min_matched_date = merged.filter(pl.col("stable").is_not_null())["date"].min()
    merged = merged.filter(pl.col("date") >= min_matched_date)

    # `gen perc = stable / total`
    merged = merged.with_columns((pl.col("stable") / pl.col("total")).alias("perc"))
    return merged.select(["date", "perc"]).sort("date")


def plot_stable_pct_of_tvl(pct_df: pl.DataFrame, out_path: Path) -> None:
    """Figure 18a (`stable_perc.png`): stablecoin TVL as a share of total ETH TVL."""
    x = pct_df["date"].to_list()
    y = pct_df["perc"].to_list()
    fig, ax = plt.subplots(figsize=(9, 6), facecolor="white")
    ax.plot(x, y)
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Stablecoin TVL Market Share")
    ax.yaxis.grid(True)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
    fig.autofmt_xdate(rotation=45)
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def main() -> None:
    ensure_dirs()

    pie_df, bar_df = build_oracle_tables()
    plot_oracle_pie(pie_df, OUTPUT_FIGURES / "figure_23a_oracle_tvl_share.png")
    plot_oracle_bar(bar_df, OUTPUT_FIGURES / "figure_23b_oracle_protocol_count.png")

    wide = build_stablecoin_wide()
    plot_stable_market_share(wide, OUTPUT_FIGURES / "figure_22b_stablecoin_market_share.png")
    pct_df = build_stablecoin_pct_of_tvl(wide)
    plot_stable_pct_of_tvl(pct_df, OUTPUT_FIGURES / "figure_22a_stablecoin_pct_of_tvl.png")


if __name__ == "__main__":
    main()
