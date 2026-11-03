"""
reg_tables.py
=============

Shared LaTeX regression-table and coefficient-plot formatting for the "Decentralized Crypto
Governance?" replication package (Fracassi, Khoja, Schar, 2024, SSRN 4691000).

Why this module exists
-----------------------
The original project relied on Stata's `eststo` / `esttab` workflow to turn fitted-model
output into publication-ready LaTeX tables, and `coefplot` to turn coefficient vectors into
figures. This package re-implements those two workflows around `statsmodels` fitted results
so that the same rendering logic is reused across every regression-based table/figure:

    - Table 1: summary statistics (`format_summary_stats_table`)
    - Table 2: FEM (Ethereum Magicians forum) engagement regressions, 4 columns
    - Table 3: EIP finalization/implementation regressions, 6 columns, with
               Category FE / Company FE / Year FE indicator rows
    - Figure 15's `commit_call.tex`: event-study table with `eform`-exponentiated
      coefficients and an EIP-meeting-cohort FE indicator row
    - Figure 15's `commit_call.png` and Figure 19's `cdum_coef.png`: coefficient plots
      (`plot_coefficients`), replicating Stata's `coefplot`

Design note: pandas at the boundary
------------------------------------
`statsmodels` fitted-result objects (`.params`, `.pvalues`, `.conf_int()`, etc.) are
native pandas Series/DataFrames -- that is simply what `statsmodels` returns, and this
module does not try to fight that. Per project convention, this module converts each such
pandas object to plain Python / polars immediately at the point of use and never threads a
pandas object through more than one line of code.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

# ---------------------------------------------------------------------------------------
# Table 1's exact variable list (paper's published Table 1), for reference by callers.
# Exposed here (rather than only in a docstring) so a caller can `from reg_tables import
# TABLE1_VARIABLES` instead of retyping this list and risking a transcription mismatch.
# ---------------------------------------------------------------------------------------
TABLE1_VARIABLES: list[str] = [
    "Anonymous Author",
    "Finalized",
    "Implemented",
    "N. EIP Authors",
    "N. Twitter Followers (K)",
    "N. Github Followers",
    "N. Words in EIP (k)",
    "Readability Score",
]
# Narrowed from an original 15-variable list (which also included Betweenness Centrality,
# Community Engagement Index, FEM Comments/Likes/Unique Users/FEM Views, and Social Influence
# Index -- all PCA-index or FEM-engagement rows) to match what the actual published
# `Tables/summstat.tex` contains: those 7 rows were already absent from the published table
# (hand-trimmed at some point), so `table1_summary_stats.py` was updated to stop computing them
# too, rather than silently generating a 15-row table nothing displays.


def _stars(pvalue: float, stars_thresholds: tuple[float, float, float]) -> str:
    """
    Return the significance-star string for a p-value, given ascending (p10, p05, p01)
    thresholds. E.g. with the default (0.1, 0.05, 0.01): p < 0.01 -> '***',
    p < 0.05 -> '**', p < 0.1 -> '*', otherwise ''.
    """
    p10, p05, p01 = sorted(stars_thresholds, reverse=True)
    if pvalue < p01:
        return "***"
    if pvalue < p05:
        return "**"
    if pvalue < p10:
        return "*"
    return ""


def _escape_latex(text: str) -> str:
    """Minimal LaTeX-special-character escaping for coefficient/column labels."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text


def _fmt(x: float, decimals: int = 3) -> str:
    """Fixed-decimal numeric formatting shared by every numeric cell in this module."""
    return f"{x:.{decimals}f}"


def format_regression_table(
    models: list[Any],
    column_labels: list[str],
    out_path: str | Path,
    coef_labels: dict[str, str] | None = None,
    fe_rows: dict[str, list[bool]] | None = None,
    stars_thresholds: tuple[float, float, float] = (0.1, 0.05, 0.01),
    eform: bool = False,
    notes: str | None = None,
    keep_coef_pattern: str | None = None,
) -> None:
    """
    Render a list of fitted statsmodels regression results as a LaTeX tabular, replicating
    Stata's `eststo`/`esttab` multi-column table workflow.

    Used by:
        - Table 2: FEM engagement regressions (4 columns)
        - Table 3: EIP finalization/implementation regressions (6 columns), with
          `fe_rows={"Category FE": [...], "Company FE": [...], "Year FE": [...]}`
        - Figure 15's `commit_call.tex`: event-study table, `eform=True`,
          `fe_rows={"EIP-Meeting Cohort FE": [...]}`

    Parameters
    ----------
    models : list
        Fitted statsmodels results objects (e.g. from `sm.OLS(...).fit()`), one per column.
        Each must expose `.params`, `.tvalues`, `.pvalues`, `.conf_int()`, `.nobs`, and
        `.rsquared_adj` (the standard `RegressionResultsWrapper` interface).
    column_labels : list[str]
        Header label for each column (e.g. `["(1)", "(2)", "(3)", "(4)"]`), same length
        as `models`.
    out_path : str | Path
        Destination `.tex` file. Parent directories are created if missing.
    coef_labels : dict[str, str], optional
        Maps a raw model coefficient name (as it appears in `.params.index`) to a display
        label. Any coefficient encountered that is NOT a key in this dict falls back to its
        raw variable name verbatim (LaTeX-escaped).
    fe_rows : dict[str, list[bool]], optional
        Maps a fixed-effects block label (e.g. `"Category FE"`) to a list of booleans, one
        per column, rendered as a "Yes"/"No" row beneath the coefficient rows. This mirrors
        Stata's `indicate()` option in `esttab`. It is passed explicitly by the caller
        rather than auto-detected from the model, because in this project's regressions the
        FE block is not always represented as literal dummy-variable coefficients in
        `.params` (e.g. it may be absorbed via a within/demeaning transform), so there is no
        reliable way to infer "was this FE included?" from the fitted model object alone.
    stars_thresholds : tuple[float, float, float], default (0.1, 0.05, 0.01)
        Ascending (p10, p05, p01) significance thresholds mapped to */**/***.
    eform : bool, default False
        If True, exponentiate coefficients and confidence-interval bounds before display
        (i.e. report exp(beta) rather than beta). See the TODO comment at that code path.
    notes : str, optional
        Free-text note rendered as a `\\multicolumn` footer row (e.g. significance-level
        legend, sample description). Kept purely descriptive per project convention --
        do not put an interpretive claim about the results here; that belongs in the
        surrounding prose, not baked into the table itself.
    keep_coef_pattern : str, optional
        DESIGN ADDITION (not in the original spec): a regex applied to raw coefficient
        names to decide which coefficients get their own row, analogous to Stata esttab's
        `keep()`/`drop()` option. Default `None` shows every coefficient found in the union
        of all models' `.params`. Use this if a model's design matrix literally includes FE
        dummy coefficients (e.g. patsy's `C(category)[T.foo]`) that should be summarized only
        via `fe_rows` and not printed as individual rows.

    Returns
    -------
    None
        Writes the LaTeX table to `out_path`.
    """
    if len(models) != len(column_labels):
        raise ValueError("models and column_labels must have the same length.")

    n_cols = len(models)

    # -- Collect the ordered union of coefficient names across all models -----------------
    # (preserves first-appearance order, e.g. model 1's variables, then any new ones
    # introduced only in later columns).
    ordered_coefs: list[str] = []
    seen: set[str] = set()
    for model in models:
        for name in model.params.index:  # pandas Index -> plain str iteration
            if name not in seen:
                seen.add(name)
                ordered_coefs.append(name)

    if keep_coef_pattern is not None:
        pattern = re.compile(keep_coef_pattern)
        ordered_coefs = [c for c in ordered_coefs if pattern.search(c)]

    coef_labels = coef_labels or {}

    # -- Per-model, per-coefficient (estimate, tstat, pvalue) extraction -------------------
    # Converts each statsmodels (pandas-backed) result to plain Python dicts immediately,
    # per this module's pandas-at-the-boundary convention.
    per_model_estimates: list[dict[str, float]] = []
    per_model_tstats: list[dict[str, float]] = []
    per_model_pvalues: list[dict[str, float]] = []

    for model in models:
        params = model.params.to_dict()
        tvalues = model.tvalues.to_dict()
        pvalues = model.pvalues.to_dict()

        if eform:
            # ------------------------------------------------------------------------
            # TODO(fidelity-check): the original Stata code applies `eform` (i.e.
            # reports exp(beta) confidence intervals) to what appears to be a *linear*
            # OLS specification, not a logit/Poisson/other model where an exponentiated
            # coefficient has a natural (odds-ratio / incidence-rate-ratio)
            # interpretation. Exponentiating an OLS coefficient is unusual and its
            # substantive meaning here is unclear. This behavior is preserved as-is
            # (faithful-first) so the reproduced `commit_call.tex` numbers match the
            # original pipeline's output exactly. Before trusting these particular
            # numbers, cross-check them against the paper's actual published Figure 15
            # / commit_call values, and confirm with the authors whether `eform` was
            # applied deliberately or is itself a carried-over artifact.
            # ------------------------------------------------------------------------
            conf_int = model.conf_int(alpha=0.10)  # 90% CI, per the paper's levels(90) convention
            params = {k: float(np.exp(v)) for k, v in params.items()}
            # Exponentiated CI bounds are computed here for completeness/consistency with
            # `eform`, even though this function does not currently render a CI column.
            _ = {k: (float(np.exp(row[0])), float(np.exp(row[1]))) for k, row in conf_int.iterrows()}

        per_model_estimates.append(params)
        per_model_tstats.append(tvalues)
        per_model_pvalues.append(pvalues)

    # -- Build the LaTeX table --------------------------------------------------------------
    col_spec = "l" + "c" * n_cols
    lines: list[str] = []
    lines.append(r"\begin{tabular}{" + col_spec + "}")
    lines.append(r"\toprule")
    header = " & " + " & ".join(_escape_latex(lbl) for lbl in column_labels) + r" \\"
    lines.append(header)
    lines.append(r"\midrule")

    for coef in ordered_coefs:
        display_name = _escape_latex(coef_labels.get(coef, coef))

        coef_cells = []
        tstat_cells = []
        for m in range(n_cols):
            est = per_model_estimates[m].get(coef)
            if est is None:
                coef_cells.append("")
                tstat_cells.append("")
                continue
            p = per_model_pvalues[m].get(coef, 1.0)
            t = per_model_tstats[m].get(coef, float("nan"))
            coef_cells.append(f"{_fmt(est)}{_stars(p, stars_thresholds)}")
            tstat_cells.append(f"({_fmt(t)})")

        lines.append(display_name + " & " + " & ".join(coef_cells) + r" \\")
        lines.append(" & " + " & ".join(tstat_cells) + r" \\")

    # -- Fixed-effects indicator rows --------------------------------------------------------
    if fe_rows:
        lines.append(r"\midrule")
        for fe_label, flags in fe_rows.items():
            if len(flags) != n_cols:
                raise ValueError(
                    f"fe_rows[{fe_label!r}] has {len(flags)} entries, expected {n_cols} "
                    "(one per column)."
                )
            cells = ["Yes" if flag else "No" for flag in flags]
            lines.append(_escape_latex(fe_label) + " & " + " & ".join(cells) + r" \\")

    # -- Observations / Adjusted R^2 ---------------------------------------------------------
    lines.append(r"\midrule")
    obs_cells = [str(int(model.nobs)) for model in models]
    lines.append("Observations & " + " & ".join(obs_cells) + r" \\")
    r2_cells = [_fmt(float(model.rsquared_adj)) for model in models]
    lines.append(r"Adjusted R$^2$ & " + " & ".join(r2_cells) + r" \\")
    lines.append(r"\bottomrule")

    if notes:
        lines.append(
            r"\multicolumn{" + str(n_cols + 1) + "}{l}{\\footnotesize " + _escape_latex(notes) + "} \\\\"
        )

    lines.append(r"\end{tabular}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_summary_stats_table(
    df: pl.DataFrame,
    variables: list[str],
    var_labels: dict[str, str],
    out_path: str | Path,
) -> None:
    """
    Render a Table-1-style summary statistics LaTeX table: one row per variable, columns
    for N, Mean, Std. Dev., Min, p25, p50, p75, Max.

    Used by: Table 1 of the paper, whose exact variable list is:
        Anonymous Author, Betweenness Centrality, Community Engagement Index, FEM Comments,
        FEM Likes, FEM Unique Users, FEM Views, Finalized, Implemented, N. EIP Authors,
        N. Twitter Followers (K), N. Github Followers, N. Words in EIP (k), Readability
        Score, Social Influence Index.
    (This list is also exposed as `reg_tables.TABLE1_VARIABLES` so a caller does not need
    to retype it.)

    Parameters
    ----------
    df : pl.DataFrame
        Analysis-ready dataset containing (at least) the columns named in `variables`.
    variables : list[str]
        Column names in `df` to summarize, in the order they should appear in the table.
    var_labels : dict[str, str]
        Maps each entry in `variables` to its display label (e.g. the paper's Table 1
        variable names above, if `df`'s column names differ, such as snake_case).
    out_path : str | Path
        Destination `.tex` file. Parent directories are created if missing.

    Returns
    -------
    None
        Writes the LaTeX table to `out_path`.

    Notes
    -----
    Percentiles (p25/p50/p75) are computed with Polars' default `interpolation="linear"`
    quantile method. Stata's `summarize, detail` uses a slightly different order-statistic
    convention for percentiles than linear interpolation; for large N (as in this project's
    samples) the numerical difference is negligible, but this is noted here explicitly in
    case a reviewer diffs individual percentile values against the original Stata output.
    """
    rows: list[dict[str, Any]] = []

    for var in variables:
        if var not in df.columns:
            raise KeyError(f"Variable {var!r} not found in df columns.")
        label = var_labels.get(var, var)

        col = df.select(pl.col(var).drop_nulls()).to_series()
        n = col.len()
        if n == 0:
            rows.append(
                {
                    "Variable": label,
                    "N": 0,
                    "Mean": float("nan"),
                    "Std. Dev.": float("nan"),
                    "Min": float("nan"),
                    "p25": float("nan"),
                    "p50": float("nan"),
                    "p75": float("nan"),
                    "Max": float("nan"),
                }
            )
            continue

        rows.append(
            {
                "Variable": label,
                "N": n,
                "Mean": col.mean(),
                "Std. Dev.": col.std(),
                "Min": col.min(),
                "p25": col.quantile(0.25, interpolation="linear"),
                "p50": col.quantile(0.50, interpolation="linear"),
                "p75": col.quantile(0.75, interpolation="linear"),
                "Max": col.max(),
            }
        )

    stats_df = pl.DataFrame(rows)

    col_headers = ["Variable", "N", "Mean", "Std. Dev.", "Min", "p25", "p50", "p75", "Max"]
    lines: list[str] = []
    lines.append(r"\begin{tabular}{l" + "r" * (len(col_headers) - 1) + "}")
    lines.append(r"\toprule")
    lines.append(" & ".join(col_headers) + r" \\")
    lines.append(r"\midrule")

    for row in stats_df.iter_rows(named=True):
        cells = [_escape_latex(str(row["Variable"])), str(row["N"])]
        for key in ("Mean", "Std. Dev.", "Min", "p25", "p50", "p75", "Max"):
            cells.append(_fmt(row[key]))
        lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_panel_stats_table(
    panels: list[tuple[str, dict[str, pl.Series]]],
    out_path: str | Path,
) -> None:
    """
    Render a multi-panel summary-statistics LaTeX table: each panel gets its own
    `\\multicolumn` header row, followed by one row per variable with Mean, Median,
    Std. Dev., Min, Max -- no N column (each row states its own sampling unit/N via its
    label and this function trusts the caller to make that unit clear, since different
    rows -- even within the same panel -- may be computed over different populations;
    see `table4_participation_summary.py`'s Panel C, a per-meeting series, versus Panels
    A/B's per-EIP series).

    Used by: Table 4 (EIP discussion/development participation by venue -- FEM, GitHub,
    AllCoreDevs), via `table4_participation_summary.py`. Mirrors the existing
    `\\multicolumn{n}{l}{\\textbf{Panel A. ...}}` convention already used by
    `Tables/table_did_results_mod.tex` (Table 3), rather than introducing a new style.

    Parameters
    ----------
    panels : list[(str, dict[str, pl.Series])]
        One entry per panel, in display order: `(panel_title, {display_label: series})`.
        Each series is summarized independently -- rows need not share a common length or
        population (e.g. one row over 612 EIPs, another over 142 meetings). No null-handling
        is performed here, by design: a series with true missingness (as opposed to a
        genuine zero) must be resolved by the caller before this function is called.
    out_path : str | Path
        Destination `.tex` file. Parent directories are created if missing.

    Returns
    -------
    None
        Writes the LaTeX table to `out_path`.
    """
    col_headers = ["", "Mean", "Median", "Std. Dev.", "Min", "Max"]
    lines: list[str] = []
    lines.append(r"\begin{tabular}{l" + "r" * (len(col_headers) - 1) + "}")
    lines.append(r"\toprule")
    lines.append(" & ".join(col_headers) + r" \\")

    for panel_title, rows in panels:
        lines.append(r"\midrule")
        lines.append(r"\multicolumn{" + str(len(col_headers)) + "}{l}{\\textbf{" + _escape_latex(panel_title) + "}} \\\\")
        for label, col in rows.items():
            cells = [
                _escape_latex(label),
                _fmt(col.mean(), 2),
                _fmt(col.median(), 2),
                _fmt(col.std(), 2),
                _fmt(float(col.min()), 2),
                _fmt(float(col.max()), 2),
            ]
            lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_coefficients(
    params: dict[str, float],
    conf_int: dict[str, tuple[float, float]],
    out_path: str | Path,
    keep_pattern: str | None = None,
    xline: float | None = None,
    labels: dict[str, str] | None = None,
    title: str | None = None,
) -> None:
    """
    Render a horizontal coefficient plot with confidence-interval error bars, replicating
    Stata's `coefplot`.

    Used by:
        - Figure 19's `cdum_coef.png`: company fixed-effect coefficients from Table 3,
          column 1
        - Figure 15's `commit_call.png`: weekly event-study coefficients, with
          `xline=0` marking the AllCoreDevs-call event week

    Parameters
    ----------
    params : dict[str, float]
        Maps coefficient name -> point estimate. Typically built from a fitted statsmodels
        result via `model.params.to_dict()` (converting from pandas at the call site, per
        this module's pandas-at-the-boundary convention).
    conf_int : dict[str, tuple[float, float]]
        Maps the SAME coefficient names -> (lower, upper) confidence bounds.
        **Important**: the paper reports all confidence intervals at the 90% level
        (`levels(90)` in every Stata `coefplot`/regression call in the original project).
        `statsmodels`' default `.conf_int()` returns a 95% CI -- to match the paper, callers
        must explicitly request `model.conf_int(alpha=0.10)` before building this dict.
        This function does not re-derive alpha; it plots whatever bounds it is given.
    out_path : str | Path
        Destination image file (e.g. `.png`). Parent directories are created if missing.
    keep_pattern : str, optional
        Regex applied to coefficient names; only matching coefficients are plotted (mirrors
        Stata coefplot's `keep()` option). Default `None` plots every key in `params`.
    xline : float, optional
        If given, draws a vertical reference line at this x-value (e.g. `0` to mark the
        null effect / event week).
    labels : dict[str, str], optional
        Maps a coefficient name to its display label on the y-axis. Falls back to the raw
        coefficient name if absent.
    title : str, optional
        Plot title. Per project convention, this must be purely descriptive (what is
        plotted, its axes/units/sample) -- never an interpretive claim about the result
        (e.g. do not write something like "effect fades after the call"). Any such
        interpretation belongs in the surrounding paper text, not in the figure itself.

    Returns
    -------
    None
        Saves the figure to `out_path`.
    """
    names = list(params.keys())
    if keep_pattern is not None:
        pattern = re.compile(keep_pattern)
        names = [n for n in names if pattern.search(n)]

    if not names:
        raise ValueError("No coefficients left to plot after applying keep_pattern.")

    missing_ci = [n for n in names if n not in conf_int]
    if missing_ci:
        raise KeyError(f"conf_int is missing entries for: {missing_ci}")

    labels = labels or {}
    display_labels = [labels.get(n, n) for n in names]

    estimates = np.array([params[n] for n in names], dtype=float)
    lowers = np.array([conf_int[n][0] for n in names], dtype=float)
    uppers = np.array([conf_int[n][1] for n in names], dtype=float)

    # Error bar half-widths, one-sided from the point estimate to each CI bound.
    err_low = estimates - lowers
    err_high = uppers - estimates

    y_positions = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.35 * len(names))))
    ax.errorbar(
        estimates,
        y_positions,
        xerr=[err_low, err_high],
        fmt="o",
        color="black",
        ecolor="gray",
        capsize=3,
    )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(display_labels)
    ax.invert_yaxis()  # first coefficient at the top, matching Stata coefplot's default order

    if xline is not None:
        ax.axvline(x=xline, color="red", linestyle="--", linewidth=1)

    if title:
        ax.set_title(title)

    ax.set_xlabel("Coefficient estimate (90% CI)")
    fig.tight_layout()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    # This module's public functions all depend on statsmodels-fitted result objects
    # (format_regression_table) or on data passed in from a caller (format_summary_stats_table,
    # plot_coefficients); there is no meaningful file-free smoke test to run here beyond
    # verifying the module imports cleanly, which happens simply by running this file.
    print("reg_tables module imported successfully; no standalone smoke test defined.")
