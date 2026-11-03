"""
fig_abnormal_returns.py
========================

Paper: Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.

Reproduces **Figure 3** (`\\label{fig:CAR}`, "Ethereum Governance and Token Price") and **Table 2**
(`\\label{tab:car_event_study}`, "Cumulative Abnormal Returns around AllCoreDevs Discussion of
Finalized Core EIPs") of the current manuscript, `paper/latex/MS_R2.tex`. Figure/table
numbers shift as the paper is revised; see `docs/figure_table_index.md` for the current numbering
snapshot and its date. The `\\label`s are the stable identifiers.

Cumulative Abnormal Return (CAR) event study around the date each finalized Core EIP (NOT
Core+Networking -- see "Category scope" below) was last discussed at an AllCoreDevs meeting, using
daily 4:00pm US/Eastern close prices for ETH, benchmarked against (a) SPY and (b) BTC. A
+/-40-trading-day window is built around each event; CAR is averaged across events with a ~90%
confidence band (`1.645 * std / sqrt(n)`).

Both benchmark series share ETH's own calendar: `build_returns_panel()` left-joins
onto SPY's dates, so BTC's return series (like ETH's) has one observation per
NYSE trading day, not a separate 24/7 calendar -- any BTC/ETH price movement over
a weekend or market holiday is folded into the following trading day's return.

Category scope: `plot_car_with_ci()` and `build_car_table_rows()` both restrict
to `Category == "Core"` only. An earlier version of this script used
Core+Networking (N=48); a direct comparison (documented in `PIPELINE_TODO.md`)
showed the 7 Networking EIPs don't materially change the result, so the sample
was narrowed to Core-only (N=41) to match the paper's own "41 out of 51
finalized Core EIPs" prose, rather than rewriting the prose to describe
Core+Networking.
    * Figure 3a -- "CAR (ETH vs. SPY benchmark)"  -> `figure_24a_car_spy.png`
    * Figure 3b -- "CAR (ETH vs. BTC benchmark)"  -> `figure_24b_car_btc.png`

Ported from: `Analysis\\Abnormal Returns\\abnormal return analysis.py`.

Event definition
-------------------
Two event definitions are possible for a finalized EIP: its finalization date, or the date it was
last discussed at an AllCoreDevs meeting. The default here (`event_type="meeting"`) uses the
meeting date, matching the published figure; pass `--event-type eip_finalization` on the CLI
(or `event_type="eip_finalization"` to `main()` / `run_meeting_or_finalization_event_study()`) to
run the finalization-date event study instead.

SPY price caching
--------------------
SPY prices are fetched via yfinance, whose historical data can be revised/backfilled after the
fact. This script caches a successful fetch at `data/interim/spy_prices_cache.parquet`
(`fetch_spy_prices()`) and prefers the cache on subsequent runs, so results stay reproducible run
to run; pass `--no-spy-cache` (or `use_cache=False`) to force a fresh live fetch. The script always
prints which source (cache vs. live) was used.

Scope note: a separate fork-announcement CAR event study (+/-60 trading days around each hard
fork's block-activation date) is not part of the published paper's Figure 3 and is not computed
here. This script also previously ran two placebo falsification designs (pseudo-events at each
cohort's own t=-40 and t=-80); neither is referenced anywhere in the current `MS_R2.tex`
(confirmed via a full-text search for "placebo"), so they are no longer generated here. See
`PIPELINE_TODO.md` for the removal record.

Inputs (see `data/RAW_DATA_MANIFEST.md`):
    data/raw/prices/eth_prices.csv                       (hourly ETH OHLC)
    data/raw/prices/btc_prices.csv                       (hourly BTC OHLC)
    data/raw/eip_registry/finaleip_enddates.csv           (EIP "Final" end-dates)
    data/raw/meetings/calls_updated_standardized.csv      (AllCoreDevs call metadata)
    data/processed/ethereum_cross_sectional_data.parquet  (THIS package's own
        reproduced cross-sectional dataset -- built by
        code/02_data_preparation/build_cross_sectional_dataset.py. Deliberately
        NOT data/reference/Ethereum_Cross-sectional_Data.parquet, which per
        config.py's convention is verification-only and never a pipeline input.)

Outputs:
    output/figures/figure_24a_car_spy.png
    output/figures/figure_24b_car_btc.png
    output/tables/car_event_study.tex   The same estimates underlying Figure 3, at
        selected trading-day horizons, as a two-column table (SPY benchmark, BTC
        benchmark) -- see `build_car_table_rows()` / `write_car_table()`.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_FIGURES, OUTPUT_TABLES, ensure_dirs  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402
from scipy import stats as sps  # noqa: E402

PRICES_RAW = DATA_RAW / "prices"
EIP_RAW = DATA_RAW / "eip_registry"
MEETINGS_RAW = DATA_RAW / "meetings"
CROSS_SECTIONAL_PARQUET = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
SPY_CACHE = DATA_INTERIM / "spy_prices_cache.parquet"

EASTERN = "America/New_York"

EventType = Literal["meeting", "eip_finalization"]


def _read_csv_latin1(path: Path) -> pl.DataFrame:
    """Read a CSV decoded as Latin-1, matching the original's `encoding='latin1'`
    (Polars' own `read_csv(encoding=...)` only supports utf8/utf8-lossy, not
    arbitrary codecs, so we decode to text ourselves first)."""
    text = path.read_bytes().decode("latin1")
    return pl.read_csv(io.StringIO(text))


# ---------------------------------------------------------------------------------
# ETH / BTC daily 4pm-ET close series
# ---------------------------------------------------------------------------------
def _load_hourly_close_series(csv_path: Path, close_col_alias: str) -> pl.DataFrame:
    """Collapse an hourly OHLC CSV (Coinbase-style: `START` UTC timestamp, `CLOSE`)
    to one row per calendar day at the 4:00pm US/Eastern close, forward-filling any
    missing hours -- matching the original's
    `pd.date_range(...).ffill()` gap-fill followed by `.dt.hour == 15`.

    Only `START`/`CLOSE` are read (unlike the original, which forward-fills the
    entire raw dataframe including OHLCV columns nothing downstream ever uses);
    this changes no output value since every other raw column is discarded by the
    original before it is ever used either.
    """
    df = pl.read_csv(csv_path, columns=["START", "CLOSE"])
    df = df.with_columns(
        pl.col("START")
        .str.strptime(pl.Datetime("us"), "%Y-%m-%dT%H:%M:%SZ", strict=False)
        .dt.replace_time_zone("UTC")
    )
    df = df.sort("START").unique(subset=["START"], keep="last", maintain_order=True)

    # Build a complete hourly grid spanning [min, max] in UTC -- a fixed-offset
    # zone with no DST folds/gaps -- and left-join the raw closes onto it, then
    # forward-fill. Constructing the grid in UTC rather than in US/Eastern (as the
    # original pandas code implicitly does via tz-aware `pd.date_range`) sidesteps
    # DST-transition ambiguity in the grid construction itself; the 4pm-ET close
    # selection below still operates on the correct Eastern local wall-clock time
    # for every row, so this is an implementation detail, not a behavior change.
    min_ts = df["START"].min()
    max_ts = df["START"].max()
    grid = pl.DataFrame(
        {"START": pl.datetime_range(min_ts, max_ts, interval="1h", time_zone="UTC", eager=True)}
    )
    full = grid.join(df, on="START", how="left").sort("START")
    full = full.with_columns(pl.col("CLOSE").fill_null(strategy="forward"))

    # Keep only the row representing the 4:00pm ET close. The original keeps
    # hour==15 because `START` is the PERIOD-START timestamp of an hourly bar, so
    # the 3-4pm bar's (start-of-period) close IS the 4pm price.
    full = full.with_columns(pl.col("START").dt.convert_time_zone(EASTERN).alias("date_et"))
    eod = full.filter(pl.col("date_et").dt.hour() == 15)
    eod = eod.sort("date_et").rename({"date_et": "date", "CLOSE": close_col_alias})
    return eod.select(["date", close_col_alias])


def build_daily_close_series() -> tuple[pl.DataFrame, pl.DataFrame, tuple]:
    eth = _load_hourly_close_series(PRICES_RAW / "eth_prices.csv", "eth_close")
    btc = _load_hourly_close_series(PRICES_RAW / "btc_prices.csv", "btc_close")
    min_ts = eth["date"].min()
    max_ts = eth["date"].max()
    return eth, btc, (min_ts, max_ts)


# ---------------------------------------------------------------------------------
# SPY (live external call, with a point-in-time cache)
# ---------------------------------------------------------------------------------
def fetch_spy_prices(min_ts, max_ts, use_cache: bool = True) -> pl.DataFrame:
    """Fetch SPY daily closes (auto-adjusted) via yfinance, aligned to the same
    4pm-ET timestamp convention as the ETH/BTC series. See module docstring for the
    cache-vs-live-fetch policy.
    """
    if use_cache and SPY_CACHE.exists():
        print(f"[fetch_spy_prices] SOURCE: cache -- reading {SPY_CACHE}")
        return pl.read_parquet(SPY_CACHE)

    print(
        "[fetch_spy_prices] SOURCE: LIVE yfinance fetch (no cache found, or "
        "use_cache=False was requested). This queries the unofficial Yahoo "
        "Finance API; historical values can be revised/backfilled after the fact."
    )
    import yfinance as yf  # imported lazily so the cache path never requires it

    min_dt = min_ts.replace(tzinfo=None)
    max_dt = max_ts.replace(tzinfo=None)
    spy_pd = yf.Ticker("spy").history(start=min_dt, end=max_dt, auto_adjust=True)
    # pandas -> Polars immediately at this hard boundary (per project convention;
    # yfinance only returns pandas natively).
    spy_pd = spy_pd.reset_index()
    spy = pl.from_pandas(spy_pd)
    spy = spy.rename({"Close": "spy_close"})
    date_col = "Date" if "Date" in spy.columns else "index"
    # yfinance's index comes back tz-aware in the exchange's local tz
    # (America/New_York for SPY) already; convert (no-op if already Eastern) and
    # shift to the same "4pm" timestamp convention used for eth/btc.
    spy = spy.with_columns(
        (pl.col(date_col).dt.convert_time_zone(EASTERN) + pl.duration(hours=15)).alias("date")
    )
    spy = spy.select(["date", "spy_close"])

    ensure_dirs()
    spy.write_parquet(SPY_CACHE, compression="zstd")
    print(f"[fetch_spy_prices] Wrote fresh SPY prices to cache: {SPY_CACHE}")
    return spy


# ---------------------------------------------------------------------------------
# Returns panel
# ---------------------------------------------------------------------------------
def build_returns_panel(eth: pl.DataFrame, btc: pl.DataFrame, spy: pl.DataFrame) -> pl.DataFrame:
    """`dat = merge(spy, eth, on='date', how='left'); dat = merge(dat, btc, ...)`,
    then daily simple returns and abnormal returns vs. SPY / BTC."""
    dat = spy.join(eth, on="date", how="left").join(btc, on="date", how="left")
    dat = dat.sort("date")
    dat = dat.with_columns(
        [
            (pl.col("eth_close") / pl.col("eth_close").shift(1) - 1).alias("eth_ret"),
            (pl.col("spy_close") / pl.col("spy_close").shift(1) - 1).alias("spy_ret"),
            (pl.col("btc_close") / pl.col("btc_close").shift(1) - 1).alias("btc_ret"),
        ]
    )
    dat = dat.with_columns(
        [
            (pl.col("eth_ret") - pl.col("spy_ret")).alias("AR"),
            (pl.col("eth_ret") - pl.col("btc_ret")).alias("AR_btc"),
        ]
    )
    return dat


# ---------------------------------------------------------------------------------
# Event lists
# ---------------------------------------------------------------------------------
def _load_cross_sectional() -> pl.DataFrame:
    if not CROSS_SECTIONAL_PARQUET.exists():
        raise FileNotFoundError(
            f"{CROSS_SECTIONAL_PARQUET} not found. Run "
            "code/02_data_preparation/build_cross_sectional_dataset.py first -- "
            "this script deliberately reads THIS package's own reproduced "
            "cross-sectional dataset, not data/reference/ (verification-only, "
            "per config.py's DATA_REFERENCE convention)."
        )
    return pl.read_parquet(CROSS_SECTIONAL_PARQUET)


def build_eip_finalization_events(dat: pl.DataFrame, min_ts) -> pl.DataFrame:
    """Finalization-date event definition: one event per finalized EIP, dated at its
    "Final" status end-date (`finaleip_enddates.csv`)."""
    eip = _read_csv_latin1(EIP_RAW / "finaleip_enddates.csv")
    cs = _load_cross_sectional()
    eip = eip.join(
        cs.select(["eip_number", "Category"]), left_on="Number", right_on="eip_number", how="inner"
    )
    eip = eip.filter(pl.col("Status") == "Final").select(
        [pl.col("Number").alias("EIP"), pl.col("End").alias("ann_date"), "Category"]
    )
    eip = eip.with_columns(
        (
            pl.col("ann_date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).cast(pl.Datetime)
            .dt.replace_time_zone(EASTERN)
            + pl.duration(hours=15)
        ).alias("ann_date")
    )
    eip = eip.sort("ann_date")
    eip = eip.join_asof(dat.select(["date"]), left_on="ann_date", right_on="date", strategy="backward")
    eip = eip.filter(pl.col("date") > min_ts).drop_nulls(["date"])
    return eip.select(["EIP", "ann_date", "date", "Category"])


def build_eip_meeting_events(dat: pl.DataFrame, min_ts) -> pl.DataFrame:
    """DEFAULT event definition (`event = eip_meeting` -- the original's only
    active assignment). One event per finalized, non-Meta/non-Informational EIP,
    dated at the LAST AllCoreDevs meeting date on which it was discussed
    (`calls_updated_standardized.csv`)."""
    meeting = pl.read_csv(MEETINGS_RAW / "calls_updated_standardized.csv")
    eip2 = meeting.select(["Date", "EIP", "Meeting"])
    # Explode the comma-separated "EIP-123, EIP-456" agenda column. Polars'
    # explode naturally re-attaches Date/Meeting to every exploded row, which is
    # what the original achieves via a more roundabout index-aligned outer merge
    # (`pd.merge(..., left_index=True, right_index=True, how='outer')`) -- same
    # end result, reached more directly.
    eip2 = eip2.with_columns(pl.col("EIP").str.split(",")).explode("EIP")
    eip2 = eip2.with_columns(
        pl.col("EIP").str.strip_chars().str.replace("EIP-", "").alias("EIP")
    )
    eip2 = eip2.with_columns(pl.col("EIP").cast(pl.Int64, strict=False))
    eip2 = eip2.drop_nulls(["EIP"])

    cs = _load_cross_sectional()
    final = cs.filter(pl.col("status") == "Final").select(["eip_number", "status", "edate", "Category"])
    final = final.filter(~pl.col("Category").is_in(["Informational", "Meta"]))

    eip2 = eip2.join(final, left_on="EIP", right_on="eip_number", how="inner")
    eip2 = eip2.with_columns(
        pl.col("Date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("Date")
    )

    # `eip2.groupby('eip_number')['Date'].idxmax()` -- keep, per EIP, only the row
    # with the latest meeting Date. pandas' idxmax() breaks ties by taking the
    # FIRST occurrence of the max value in the (pre-groupby) row order, so we
    # reproduce that explicitly (max-per-group, then first tied row in original
    # order) rather than a sort+last, which would break ties the opposite way.
    eip2 = eip2.with_columns(pl.col("Date").max().over("EIP").alias("_max_date"))
    eip2 = eip2.filter(pl.col("Date") == pl.col("_max_date")).drop("_max_date")
    eip2 = eip2.group_by("EIP", maintain_order=True).first()

    eip2 = eip2.with_columns(
        (
            pl.col("Date").cast(pl.Datetime).dt.replace_time_zone(EASTERN)
            + pl.duration(hours=15)
        ).alias("Date")
    )
    eip2 = eip2.sort("Date")
    eip2 = eip2.join_asof(dat.select(["date"]), left_on="Date", right_on="date", strategy="backward")
    eip2 = eip2.filter(pl.col("Date") > min_ts).drop_nulls(["date"])
    return eip2.select(["Date", "EIP", "Meeting", "date", "Category"])




# ---------------------------------------------------------------------------------
# CAR window construction
# ---------------------------------------------------------------------------------
def _trading_day_index(dat: pl.DataFrame) -> pl.DataFrame:
    """`dat.dropna()`, sorted by date, with a stable Int64 trading-day index `N`
    attached. Cast to Int64 (not the default UInt32 row index) because `diff`
    below is computed as `N - event_N`, which must support negative values."""
    idx = dat.drop_nulls().sort("date")
    idx = idx.with_row_index("N").with_columns(pl.col("N").cast(pl.Int64))
    return idx


def _car_window(
    dat_idx: pl.DataFrame,
    event_date,
    window: int,
    compounding: bool,
    labels: dict,
) -> pl.DataFrame | None:
    """Build the +/-`window` trading-day CAR frame for a single event.

    Matches the original per-event loop exactly: `diff` is computed against the
    FULL trading-day history first (a stable trading-day offset), the frame is
    THEN trimmed to the window, and CAR is a cumulative statistic of AR computed
    *within the trimmed window* -- i.e. it restarts at each event rather than
    accumulating from the start of the whole price history.
    """
    match = dat_idx.filter(pl.col("date") == event_date)
    if match.height == 0:
        return None
    event_n = match["N"][0]
    out = dat_idx.with_columns((pl.col("N") - event_n).alias("diff"))
    out = out.filter((pl.col("diff") > -window - 1) & (pl.col("diff") < window + 1)).sort("diff")
    if compounding:
        # Fork event study: `CAR = (AR + 1).cumprod() - 1`.
        out = out.with_columns(
            [
                ((pl.col("AR") + 1).cum_prod() - 1).alias("CAR"),
                ((pl.col("AR_btc") + 1).cum_prod() - 1).alias("CAR_btc"),
            ]
        )
    else:
        # EIP (meeting / finalization) event study: `CAR = AR.cumsum()`.
        out = out.with_columns(
            [pl.col("AR").cum_sum().alias("CAR"), pl.col("AR_btc").cum_sum().alias("CAR_btc")]
        )
    for col, value in labels.items():
        out = out.with_columns(pl.lit(value).alias(col))
    return out


def run_eip_car(dat: pl.DataFrame, events: pl.DataFrame, window: int = 40) -> pl.DataFrame:
    """+/-40-trading-day CAR (simple cumulative sum) around each EIP event's
    matched trading date."""
    dat_idx = _trading_day_index(dat)
    frames = []
    for row in events.iter_rows(named=True):
        frame = _car_window(
            dat_idx,
            row["date"],
            window,
            compounding=False,
            labels={"eip": row["EIP"], "Category": row["Category"]},
        )
        if frame is not None:
            frames.append(frame)
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical")


# ---------------------------------------------------------------------------------
# Event-type dispatch
# ---------------------------------------------------------------------------------
def run_meeting_or_finalization_event_study(
    dat: pl.DataFrame, min_ts, event_type: EventType = "meeting"
) -> pl.DataFrame:
    """
    Run the CAR event study for the given event definition -- the AllCoreDevs-meeting
    date (`event_type="meeting"`, the default, matching the published figure) or
    the EIP's own finalization date (`event_type="eip_finalization"`).
    """
    if event_type == "meeting":
        events = build_eip_meeting_events(dat, min_ts)
    elif event_type == "eip_finalization":
        events = build_eip_finalization_events(dat, min_ts)
    else:
        raise ValueError(
            f"Unknown event_type: {event_type!r} (expected 'meeting' or 'eip_finalization')"
        )
    return run_eip_car(dat, events, window=40)


# ---------------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------------
def _mean_ci(df: pl.DataFrame, car_col: str) -> pl.DataFrame:
    """Per-`diff` mean plus a ~90% confidence band (`1.645 * std / sqrt(n)`),
    matching the original's `groupby('diff')['CAR'].mean()/.std()/.count()`."""
    g = (
        df.group_by("diff")
        .agg(
            [
                pl.col(car_col).mean().alias("mean"),
                pl.col(car_col).std().alias("std"),
                pl.col(car_col).count().alias("n"),
            ]
        )
        .sort("diff")
    )
    # `std` (and so `ci`) is null for any `diff` with only one observation
    # (Polars' `.std()` of a single value is undefined, not 0) -- fill with 0
    # rather than leave null, so a too-small sample degrades to a zero-width
    # band around the point estimate instead of crashing `fill_between` below.
    g = g.with_columns((1.645 * pl.col("std").fill_null(0.0) / pl.col("n").sqrt()).alias("ci"))
    g = g.with_columns(
        [(pl.col("mean") - pl.col("ci")).alias("ci_lower"), (pl.col("mean") + pl.col("ci")).alias("ci_upper")]
    )
    return g


def plot_car_with_ci(
    df: pl.DataFrame, car_col: str, out_path: Path, xlabel: str, event_label: str
) -> None:
    """Figure 3a/3b: mean CAR +/- 90%-ish CI band, restricted to Core EIPs
    (`df[df['Category']=='Core']`) -- NOT Core+Networking; see
    `PIPELINE_TODO.md` for why this was narrowed from the broader
    Core+Networking sample used earlier."""
    df1 = df.filter(pl.col("Category") == "Core")
    g = _mean_ci(df1, car_col)
    x = g["diff"].to_list()
    mean = g["mean"].to_list()
    lo = g["ci_lower"].to_list()
    hi = g["ci_upper"].to_list()

    fig, ax = plt.subplots(figsize=(8, 6), facecolor="white")
    ax.plot(x, mean)
    ax.fill_between(x, lo, hi, color="b", alpha=0.15)
    ax.axvline(x=0, color="red", linestyle="--", label=event_label)
    ax.yaxis.grid(True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Average Cumulative Abnormal Returns")
    fig.autofmt_xdate(rotation=45)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------------
# CAR event-study table (the same estimates as plot_car_with_ci, in tabular form)
# ---------------------------------------------------------------------------------
CAR_TABLE_HORIZONS: list[int] = [
    -40, -35, -30, -25, -20, -15, -10, -5, -1, 0, 1, 5, 10, 15, 20, 25, 30, 35, 40,
]


def _stars_tex(p: float) -> str:
    if p is None or p != p:  # NaN-safe: p != p is True only for NaN
        return ""
    return "$^{***}$" if p < 0.01 else "$^{**}$" if p < 0.05 else "$^{*}$" if p < 0.10 else ""


def build_car_table_rows(df: pl.DataFrame, horizons: list[int] = CAR_TABLE_HORIZONS) -> pl.DataFrame:
    """One row per selected relative-day horizon, with mean/SE/t-stat/p-value for
    both the SPY- and BTC-benchmarked CAR, restricted to Core EIPs -- the exact
    same sample and per-day statistic (`mean`, `std`, `n`) computed by
    `_mean_ci()` and plotted in `plot_car_with_ci()`, so the table's numbers match
    Figure 3 exactly rather than being a separately-derived estimate.

    Each horizon's (mean, SE, t, p) is computed independently, matching the
    figure's own day-by-day construction -- not a single joint regression with
    day dummies, which would additionally require deciding how to cluster
    standard errors across days for the same EIP. Since the figure itself makes
    no such joint-estimation claim, the table does not either.
    """
    df1 = df.filter(pl.col("Category") == "Core")
    rows = []
    for h in horizons:
        row: dict = {"day": h}
        for col, tag in [("CAR", "spy"), ("CAR_btc", "btc")]:
            sub = df1.filter(pl.col("diff") == h).select(pl.col(col).drop_nulls()).to_series()
            n = sub.len()
            mean = sub.mean() if n > 0 else None
            se = (sub.std() / (n**0.5)) if n > 1 else None
            t = (mean / se) if (mean is not None and se) else None
            p = float(2 * (1 - sps.t.cdf(abs(t), df=n - 1))) if t is not None else None
            row[f"{tag}_mean"], row[f"{tag}_se"], row[f"{tag}_t"], row[f"{tag}_p"], row[f"{tag}_n"] = (
                mean, se, t, p, n,
            )
        rows.append(row)
    return pl.DataFrame(rows)


def write_car_table(table_df: pl.DataFrame, out_path: Path, event_label: str) -> None:
    """Render `build_car_table_rows()`'s output as a two-column LaTeX table
    (SPY benchmark, BTC benchmark), one row per horizon plus a shared
    Observations row, matching the coefficient/t-stat-in-parentheses layout used
    throughout the rest of this package's regression tables (see
    `code/utils/reg_tables.py::format_regression_table`).
    """
    lines: list[str] = [
        r"% ===== Table: CAR event-study estimates (SPY and BTC benchmarks) =====",
        r"% Companion to Figure \ref{fig:CAR}: same estimates, selected horizons, tabular form.",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        rf" & CAR (S\&P 500 benchmark) & CAR (Bitcoin benchmark) \\",
        r"\midrule",
    ]
    n_spy = n_btc = None
    for row in table_df.iter_rows(named=True):
        day = row["day"]
        lbl = rf"$t={day:+d}$" if day != 0 else r"$t=0$ (" + event_label + ")"

        def cell(mean, p):
            return f"{mean:.3f}{_stars_tex(p)}" if mean is not None else ""

        def se_cell(se):
            return f"({se:.3f})" if se is not None else ""

        lines.append(
            f"\\quad {lbl} & {cell(row['spy_mean'], row['spy_p'])} & "
            f"{cell(row['btc_mean'], row['btc_p'])} \\\\"
        )
        lines.append(f" & {se_cell(row['spy_se'])} & {se_cell(row['btc_se'])} \\\\")
        n_spy, n_btc = row["spy_n"], row["btc_n"]
    lines += [
        r"\midrule",
        rf"Observations (events) & {n_spy} & {n_btc} \\",
        r"\bottomrule",
        r"\end{tabular}",
    ]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


# ---------------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------------
def main(event_type: EventType = "meeting", use_spy_cache: bool = True) -> None:
    ensure_dirs()

    eth, btc, (min_ts, max_ts) = build_daily_close_series()
    spy = fetch_spy_prices(min_ts, max_ts, use_cache=use_spy_cache)
    dat = build_returns_panel(eth, btc, spy)

    print(f"[main] Running EIP event study with event_type={event_type!r}.")
    if event_type == "meeting":
        events = build_eip_meeting_events(dat, min_ts)
        xlabel = "Trading Days to AllCoreDevs Meeting Date"
        event_label = "Final Discussion Date"
    else:
        events = build_eip_finalization_events(dat, min_ts)
        xlabel = "Trading Days to EIP Finalization Date"
        event_label = "Finalization Date"

    car_df = run_eip_car(dat, events, window=40)

    plot_car_with_ci(car_df, "CAR", OUTPUT_FIGURES / "figure_24a_car_spy.png", xlabel, event_label)
    plot_car_with_ci(car_df, "CAR_btc", OUTPUT_FIGURES / "figure_24b_car_btc.png", xlabel, event_label)

    table_df = build_car_table_rows(car_df)
    write_car_table(table_df, OUTPUT_TABLES / "car_event_study.tex", event_label)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--event-type",
        choices=["meeting", "eip_finalization"],
        default="meeting",
        help=(
            "Event definition for the Figure 3 CAR event study. 'meeting' "
            "(default) uses the last AllCoreDevs meeting date discussing each "
            "finalized EIP, matching the published figure. 'eip_finalization' "
            "uses the EIP's own finalization date instead."
        ),
    )
    parser.add_argument(
        "--no-spy-cache",
        action="store_true",
        help="Force a live yfinance re-fetch of SPY prices even if a cached copy exists.",
    )
    args = parser.parse_args()
    main(event_type=args.event_type, use_spy_cache=not args.no_spy_cache)
