"""
inequality.py
=============

Single shared implementation of the Gini coefficient / Lorenz curve machinery used
throughout the "Decentralized Crypto Governance?" replication package (Fracassi, Khoja,
Schar, 2024, SSRN 4691000).

Why this module exists
-----------------------
In the original Stata/Python project, essentially the same "sort values, compute a
concentration statistic" logic was hand-rolled independently at least six separate times:

    - Stata `ineqdec0`: EIP-author concentration by number of authored EIPs   (Figure 8a)
    - Stata `ineqdec0`: EIP-author concentration by percentile                (Figure 8b)
    - Stata `ineqdec0`: company-level concentration of EIP authorship         (Figure 16a)
    - Stata `ineqdec0` in a rolling 2-year window loop over calendar time      (Figure 9)
    - Stata `ineqdec0` in a per-client loop over the 4 client codebases,
      then averaged across clients                                           (Figure 20)
    - A hand-rolled Python `gini()` function for Ethereum Magicians (FEM)
      comment concentration -- the paper text reports a Gini of 71.6% for
      this series                                                            (Figure 12b)

Every one of those call sites wants exactly the same two primitives -- a Gini coefficient
and a Lorenz curve -- computed slightly differently by whichever script author touched it
last. This module consolidates all of that into one tested, documented implementation so
that every figure in the reproduction draws on the same, auditable code path.

Conventions
-----------
- All functions operate on a single non-negative numeric array (one "unit" per
  author/company/client/etc., already aggregated to whatever level the figure requires --
  aggregation itself is the caller's job, except for `rolling_window_gini`, which performs
  the collapse-then-Gini step itself since that pattern recurs identically across Figures
  9, 11, and 17).
- The Gini coefficient returned is the standard **population** Gini (not the small-sample
  bias-corrected/"unbiased" variant), matching Stata's `ineqdec0` default convention, which
  is what the original project used throughout.
"""

from __future__ import annotations

from typing import Union

import numpy as np
import polars as pl

# A Gini/Lorenz input may arrive as a numpy array, a polars Series, or a plain Python list --
# every call site above hands this module data in a different shape.
ArrayLike = Union[np.ndarray, pl.Series, list]


def _to_numpy(values: ArrayLike) -> np.ndarray:
    """
    Coerce an ArrayLike (np.ndarray | pl.Series | list[float]) to a 1-D float numpy array.

    Internal helper shared by `gini` and `lorenz_curve` so both apply identical input
    validation (non-negativity, non-empty, no NaNs) before doing any arithmetic.
    """
    if isinstance(values, pl.Series):
        arr = values.to_numpy()
    else:
        arr = np.asarray(values)
    arr = arr.astype(np.float64).ravel()

    if arr.size == 0:
        raise ValueError("gini/lorenz_curve received an empty array of values.")
    if np.isnan(arr).any():
        raise ValueError("gini/lorenz_curve received NaN values; drop or impute before calling.")
    if (arr < 0).any():
        raise ValueError(
            "gini/lorenz_curve requires non-negative values (concentration measures are "
            "undefined for negative quantities such as net positions)."
        )
    return arr


def gini(values: ArrayLike) -> float:
    """
    Compute the standard population Gini coefficient of a non-negative array.

    Used by (all replicated via this single function):
        - Figure 8a: EIP-author concentration, by number of EIPs authored
        - Figure 8b: EIP-author concentration, by percentile of authors
        - Figure 9:  rolling 2-year-window Gini of EIP authorship over time
                     (via `rolling_window_gini`, which calls this per window)
        - Figure 12b: Ethereum Magicians (FEM) comment concentration
                     (paper text reports 71.6% for this series)
        - Figure 16a: company-level concentration of EIP authorship
        - Figure 20: per-client-codebase commit concentration, averaged across the
                     4 clients (Geth, Besu, Erigon, Nethermind)

    Parameters
    ----------
    values : np.ndarray | pl.Series | list[float]
        A 1-D array of non-negative quantities, one entry per unit of observation
        (e.g. one entry per author = that author's total EIP count). Not pre-sorted.

    Returns
    -------
    float
        The Gini coefficient in [0, 1], where 0 = perfect equality (every unit holds an
        identical amount) and 1 = maximal concentration (one unit holds everything).

    Notes
    -----
    This is the **population** Gini coefficient (dividing by `n`, not `n - 1`), matching
    Stata's `ineqdec0` command, which is what every original script in this project used.
    It is NOT the small-sample bias-corrected ("unbiased") variant that some inequality
    packages default to -- do not swap this out for one of those without re-checking every
    downstream figure/table number in the paper.

    Implementation uses the closed-form sorted-rank formula, which is O(n log n) (dominated
    by the sort) rather than the naive O(n^2) pairwise-differences formula:

        G = (2 * sum(rank_i * x_i) - (n + 1) * sum(x)) / (n * sum(x))

    where values are sorted ascending and `rank_i` is the 1-indexed rank of `x_i` in that
    sorted order. This is algebraically equivalent to the mean absolute pairwise difference
    formula G = sum_i sum_j |x_i - x_j| / (2 * n^2 * mean(x)) but avoids ever materializing
    the O(n^2) pairwise difference matrix.
    """
    x = _to_numpy(values)
    n = x.size
    total = x.sum()

    if total == 0:
        # Every unit holds exactly zero -- degenerate case, defined as perfect equality.
        return 0.0

    x_sorted = np.sort(x)
    ranks = np.arange(1, n + 1)  # 1-indexed rank in ascending order
    gini_coef = (2.0 * np.sum(ranks * x_sorted) - (n + 1) * total) / (n * total)
    return float(gini_coef)


def lorenz_curve(values: ArrayLike, descending: bool = True) -> pl.DataFrame:
    """
    Compute the Lorenz curve of a non-negative array, for plotting concentration figures.

    Used by:
        - Figure 8a / 8b: cumulative share of EIPs authored vs. cumulative share of authors
        - Figure 16a: cumulative share of EIP authorship vs. cumulative share of companies
        - Any other figure in this package that plots a Lorenz-style concentration curve
          (this is the shared implementation; a caller should never re-derive this by hand)

    Parameters
    ----------
    values : np.ndarray | pl.Series | list[float]
        A 1-D array of non-negative quantities, one entry per unit of observation.
    descending : bool, default True
        Sort order used to build the cumulative curve. **Default is True (most-prolific
        first)**, matching Figure 8's caption: "the horizontal axis represents the number
        of authors, sorted from the most prolific to the least prolific ones." This is a
        specific, easy-to-get-backwards convention -- a Lorenz curve is more commonly drawn
        least-to-most (ascending), which produces the mirror-image curve. Do NOT flip this
        default without checking the exact figure caption/axis you are replicating; getting
        it backwards silently produces a curve that looks plausible but is flipped relative
        to the published figure.

    Returns
    -------
    pl.DataFrame
        Two columns:
            - `pct_population` : float, 0 to 100. Cumulative percentage of units
              (authors/companies/etc.) included so far, in the chosen sort order.
            - `cum_pct_value`  : float, 0 to 100. Cumulative percentage of the total value
              (e.g. total EIPs authored) held by that leading fraction of units.
        A synthetic leading row (0.0, 0.0) is prepended -- this mirrors Stata's `insobs`
        idiom (used in the original .do files to manually insert a zero point) so that the
        plotted curve starts at the origin rather than at the first real observation.
    """
    x = _to_numpy(values)
    total = x.sum()

    if total == 0:
        raise ValueError(
            "lorenz_curve requires a strictly positive total; all-zero input has no "
            "well-defined cumulative-share curve."
        )

    x_sorted = np.sort(x)
    if descending:
        x_sorted = x_sorted[::-1]

    n = x_sorted.size
    cum_value = np.cumsum(x_sorted)

    pct_population = 100.0 * np.arange(1, n + 1) / n
    cum_pct_value = 100.0 * cum_value / total

    df = pl.DataFrame(
        {
            "pct_population": pct_population,
            "cum_pct_value": cum_pct_value,
        }
    )

    # Prepend the synthetic (0, 0) origin point (mirrors Stata's `insobs` idiom).
    origin = pl.DataFrame({"pct_population": [0.0], "cum_pct_value": [0.0]})
    return pl.concat([origin, df], how="vertical")


def rolling_window_gini(
    df: pl.DataFrame,
    value_col: str,
    id_col: str,
    year_col: str,
    window_years: int = 2,
) -> pl.DataFrame:
    """
    Compute a Gini coefficient over rolling multi-year windows of a panel.

    Used by:
        - Figure 9:  rolling 2-year-window Gini of EIP authorship concentration over time
        - Figure 11: rolling 2-year-window Gini (same pattern, different underlying series)
        - Figure 17: rolling 2-year-window Gini (same pattern, different underlying series)

    For each window end-year `t` in the data's year range, this collapses `df` to one row
    per `id_col` representing that unit's SUM of `value_col` over the window
    `[t - window_years + 1, t]` inclusive, then computes `gini()` on that collapsed,
    one-row-per-unit series. This mirrors the original Stata pattern of looping over
    calendar years, each time collapsing counts within a trailing window and calling
    `ineqdec0` on the collapsed series.

    Parameters
    ----------
    df : pl.DataFrame
        Long/panel-format data with (at minimum) `id_col`, `year_col`, `value_col`.
        One row per (unit, year) is expected, but this is not strictly required --
        rows are summed within each (id, window) cell regardless.
    value_col : str
        Name of the numeric column to sum within each window (e.g. "n_eips", "n_commits").
    id_col : str
        Name of the column identifying the unit of observation (e.g. author, company,
        client codebase).
    year_col : str
        Name of the (integer) calendar-year column.
    window_years : int, default 2
        Width of the trailing window, in years, inclusive of the window-end year. The
        default of 2 matches every rolling-Gini figure in the original paper (Figures 9,
        11, 17), all of which use a 2-year rolling window.

    Returns
    -------
    pl.DataFrame
        One row per distinct window-end year present in `df[year_col]`, with columns:
            - `window_end_year` : int. The last (most recent) year included in the window.
            - `gini`            : float. Gini coefficient of the window-collapsed,
                                  one-row-per-`id_col` totals.

    Notes
    -----
    A window's Gini is computed only over units that actually appear at least once in that
    window (i.e. units with zero activity in every window year are naturally excluded, not
    included as explicit zeros) -- this matches the original Stata `collapse (sum)` behavior,
    which likewise only produces rows for id/year combinations present in the source data.
    """
    if window_years < 1:
        raise ValueError("window_years must be a positive integer.")

    years = df.select(pl.col(year_col)).unique().sort(year_col).to_series().to_list()

    records: list[dict] = []
    for window_end in years:
        window_start = window_end - window_years + 1
        window_df = df.filter(
            (pl.col(year_col) >= window_start) & (pl.col(year_col) <= window_end)
        )
        if window_df.is_empty():
            continue

        collapsed = (
            window_df.group_by(id_col)
            .agg(pl.col(value_col).sum().alias(value_col))
            .filter(pl.col(value_col) > 0)  # drop units with net-zero activity in the window
        )
        if collapsed.is_empty():
            continue

        window_gini = gini(collapsed.get_column(value_col))
        records.append({"window_end_year": int(window_end), "gini": window_gini})

    return pl.DataFrame(records)


if __name__ == "__main__":
    # ------------------------------------------------------------------------------------
    # Smoke tests -- pure synthetic Python data, no file I/O. Run with `python inequality.py`.
    # ------------------------------------------------------------------------------------

    # 1. Perfect equality: every unit holds the same amount -> Gini == 0.
    assert gini([1, 1, 1, 1]) == 0.0, "Equal values must give a Gini of exactly 0."

    # 2. Hand-computed 4-value example: values = [1, 2, 3, 4], sorted ascending, n=4, total=10.
    #    ranks = [1, 2, 3, 4]; sum(rank_i * x_i) = 1*1 + 2*2 + 3*3 + 4*4 = 1+4+9+16 = 30
    #    G = (2*30 - (4+1)*10) / (4*10) = (60 - 50) / 40 = 10/40 = 0.25
    expected = 0.25
    got = gini([1, 2, 3, 4])
    assert abs(got - expected) < 1e-12, f"Expected Gini={expected}, got {got}"

    # 3. Maximal concentration: one unit holds everything, the rest hold zero.
    #    values = [0, 0, 0, 10], n=4, total=10, sorted ranks*values = [1*0, 2*0, 3*0, 4*10]=40
    #    G = (2*40 - 5*10) / (4*10) = (80-50)/40 = 30/40 = 0.75
    got_max = gini([0, 0, 0, 10])
    assert abs(got_max - 0.75) < 1e-12, f"Expected 0.75, got {got_max}"

    # 4. All-zero input is defined as perfect equality (0.0), not an error.
    assert gini([0, 0, 0]) == 0.0

    # 5. Lorenz curve sanity checks on the same [1, 2, 3, 4] example.
    lc_desc = lorenz_curve([1, 2, 3, 4], descending=True)
    assert lc_desc.shape == (5, 2), "Expect n+1 rows (origin + 4 data points)."
    assert lc_desc["pct_population"][0] == 0.0 and lc_desc["cum_pct_value"][0] == 0.0
    # Descending (most-prolific-first): first real point is the single largest value (4/10=40%).
    assert abs(lc_desc["cum_pct_value"][1] - 40.0) < 1e-9
    assert abs(lc_desc["cum_pct_value"][-1] - 100.0) < 1e-9  # curve must end at (100, 100)

    lc_asc = lorenz_curve([1, 2, 3, 4], descending=False)
    # Ascending (least-prolific-first): first real point is the single smallest value (1/10=10%).
    assert abs(lc_asc["cum_pct_value"][1] - 10.0) < 1e-9

    # 6. rolling_window_gini smoke test: 3 units observed over 4 years, 2-year windows.
    synthetic_panel = pl.DataFrame(
        {
            "author": ["a", "a", "a", "a", "b", "b", "b", "b", "c", "c", "c", "c"],
            "year": [2018, 2019, 2020, 2021] * 3,
            "n_eips": [10, 10, 10, 10, 1, 1, 1, 1, 0, 0, 5, 5],
        }
    )
    roll = rolling_window_gini(synthetic_panel, value_col="n_eips", id_col="author", year_col="year")
    assert set(roll["window_end_year"].to_list()) == {2018, 2019, 2020, 2021}
    assert roll.filter(pl.col("window_end_year") == 2018)["gini"][0] > 0  # a=10, b=1 unequal
    assert (roll["gini"] >= 0).all() and (roll["gini"] <= 1).all()

    print("All inequality.py smoke tests passed.")
