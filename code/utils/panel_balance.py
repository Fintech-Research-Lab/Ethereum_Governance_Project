"""
panel_balance.py
=================

Shared panel-balancing utility for the "Decentralized Crypto Governance?" replication
package (Fracassi, Khoja, Schar, 2024, SSRN 4691000).

Why this module exists
-----------------------
The original project's Figure 15 event-study script (EIP commits observed in weekly
offsets around AllCoreDevs calls) used Stata's `xtset <cohort> <week>` followed by
`tsfill, full` to turn an unbalanced panel -- where a (cohort, week) row only exists if
something was actually observed that week -- into a fully balanced panel with one row for
every (cohort, week) combination, filling in the implied gaps. This matters substantively:
a week with zero commits is a real, meaningful data point for an event-study regression
(the count is genuinely zero), not a missing observation to be dropped or imputed.

This module reproduces that `xtset` + `tsfill, full` pattern in Polars via an explicit
cross-join + left-join, since Polars has no direct panel-fill primitive.

Used by: the Figure 15 event-study script only (EIP commit counts around AllCoreDevs calls,
observed at weekly offsets from -26 to +26 relative to the call date).
"""

from __future__ import annotations

from typing import Iterable

import polars as pl


def balance_panel(
    df: pl.DataFrame,
    id_col: str,
    time_col: str,
    time_range: Iterable,
    fill_values: dict[str, object] | None = None,
) -> pl.DataFrame:
    """
    Expand an unbalanced (id, time) panel into a fully balanced grid of every id crossed
    with every value in `time_range`, replicating Stata's `xtset` + `tsfill, full`.

    Used by: the Figure 15 event-study script, balancing (EIP-meeting cohort x week offset)
    so every cohort has one row per week offset from -26 to +26, with weeks that had no
    recorded commit activity filled in as zero commits rather than left absent.

    Parameters
    ----------
    df : pl.DataFrame
        The unbalanced input panel. Must contain `id_col` and `time_col`, plus any number
        of other data columns (e.g. a commit count, or per-id constant attributes such as
        an EIP number or a meeting date).
    id_col : str
        Name of the panel unit identifier column (e.g. an EIP-meeting cohort id).
    time_col : str
        Name of the time-offset column (e.g. a week offset relative to the event date).
    time_range : Iterable
        The full sequence of time-offset values that every id should have exactly one row
        for (e.g. `range(-26, 27)` for weeks -26 through +26 inclusive). Consumed once into
        a list internally, so a generator is accepted but any custom iterable must be safe
        to materialize in memory (this is a small integer grid in every known use case).
    fill_values : dict[str, object], optional
        Maps a column name to the value that should replace nulls introduced by the join
        for the (id, time) combinations that had no matching row in `df` (e.g.
        `{"n_commits": 0}` -- a cohort-week with no git activity truly had zero commits,
        which is a real data point for the regression, not a missing value).

    Returns
    -------
    pl.DataFrame
        A fully balanced panel: one row per (id, time) pair for every id in `df[id_col]`
        crossed with every value in `time_range`, sorted by `(id_col, time_col)`.

    Notes
    -----
    Column-filling behavior is deliberately split into two cases, and this split is a
    specific design choice worth calling out explicitly (it is not automatic/generic
    behavior a reader should assume):

    1. Columns named in `fill_values` are filled with their given constant (e.g. a commit
       count becomes 0 for a week with no observed commits).
    2. Every OTHER non-key column (i.e. not `id_col`, not `time_col`, and not in
       `fill_values`) is assumed to be a per-id CONSTANT attribute that simply failed to
       carry over onto the synthetic rows introduced by the cross-join (e.g. an EIP number
       or an AllCoreDevs meeting date associated with a cohort). These are filled by a
       forward-fill followed by a backward-fill WITHIN each `id_col` group (after sorting
       by `time_col`), so the id's one known value propagates to every row for that id
       regardless of which week(s) originally carried it. This is only correct if such
       columns are truly constant per id; a column that is NOT id-constant and is also
       omitted from `fill_values` will be silently (and incorrectly) forward/backward
       filled -- callers must list every genuinely time-varying column in `fill_values`.
    """
    time_values = list(time_range)
    if not time_values:
        raise ValueError("time_range must contain at least one value.")

    fill_values = fill_values or {}

    ids = df.select(pl.col(id_col).unique())
    time_grid = pl.DataFrame({time_col: time_values})

    full_grid = ids.join(time_grid, how="cross")

    balanced = full_grid.join(df, on=[id_col, time_col], how="left")

    # Case 1: explicit fill values for genuinely time-varying columns (e.g. commit counts).
    for col_name, default in fill_values.items():
        balanced = balanced.with_columns(pl.col(col_name).fill_null(default))

    # Case 2: forward-fill then backward-fill every other column within each id group,
    # for per-id-constant attributes that didn't carry onto the cross-join's synthetic rows.
    other_cols = [
        c for c in balanced.columns if c not in (id_col, time_col) and c not in fill_values
    ]

    balanced = balanced.sort([id_col, time_col])
    if other_cols:
        balanced = balanced.with_columns(
            [pl.col(c).forward_fill().backward_fill().over(id_col) for c in other_cols]
        )

    return balanced


if __name__ == "__main__":
    # ------------------------------------------------------------------------------------
    # Smoke test -- a small synthetic Polars DataFrame, no file I/O. Run with
    # `python panel_balance.py`.
    # ------------------------------------------------------------------------------------

    # Two cohorts ("A", "B"), each observed at only a subset of weeks -3..3, plus a
    # per-cohort-constant "meeting_date" attribute that should propagate to every week.
    synthetic = pl.DataFrame(
        {
            "cohort": ["A", "A", "B", "B"],
            "week": [-3, 0, -1, 2],
            "n_commits": [5, 10, 2, 1],
            "meeting_date": ["2019-01-01", "2019-01-01", "2019-06-01", "2019-06-01"],
        }
    )

    balanced = balance_panel(
        synthetic,
        id_col="cohort",
        time_col="week",
        time_range=range(-3, 4),
        fill_values={"n_commits": 0},
    )

    # Expect 2 cohorts x 7 weeks (-3..3) = 14 rows.
    assert balanced.shape[0] == 14, f"Expected 14 rows, got {balanced.shape[0]}"

    # A week with no recorded activity must be filled with 0 commits, not null.
    assert balanced.filter((pl.col("cohort") == "A") & (pl.col("week") == 1))["n_commits"][0] == 0
    assert balanced["n_commits"].null_count() == 0

    # The per-cohort-constant meeting_date must propagate to every week for that cohort.
    a_dates = balanced.filter(pl.col("cohort") == "A")["meeting_date"].unique().to_list()
    assert a_dates == ["2019-01-01"], f"meeting_date did not propagate correctly: {a_dates}"
    b_dates = balanced.filter(pl.col("cohort") == "B")["meeting_date"].unique().to_list()
    assert b_dates == ["2019-06-01"], f"meeting_date did not propagate correctly: {b_dates}"

    print("All panel_balance.py smoke tests passed.")
