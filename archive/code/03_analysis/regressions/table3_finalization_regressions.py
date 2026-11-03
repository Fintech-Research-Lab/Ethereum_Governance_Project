"""
table3_finalization_regressions.py
===================================

Reproduces **Table 3** ("Determinants of EIP Finalization and Implementation") and **Figure 19**
(`cdum_coef.png`, the company-fixed-effect coefficient plot) of:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: the EIP finalization/implementation regression analysis (the paper's main "does
transparency/influence predict getting an EIP through the process?" result).

Ported from: `Analysis\\Regression Code\\Regression Code.do`, specifically the
"Principal Component Analysis" and "Regressions" sections (everything from `pca log_gh log_tw ...`
through the `coefplot` / `cdum_coef.png` export). The upstream "ADD TOP10 COMPANY DUMMIES" section of
the same `.do` file (which builds the `cdum_*` regressors used here) is re-implemented locally in this
file (see `build_top10_company_dummies` below) rather than imported from
`code/03_analysis/company_influence/fig_company_concentration.py`, which builds the same underlying
long author-company panel independently for its own Lorenz-curve/bar-chart figures. This is a
deliberate duplication (the two files stay independently runnable; `03_analysis` is not a valid
Python package name so a clean cross-folder import is awkward), documented here and in that sibling
file's docstring.

Actual output layout produced by this file:
    - `output/tables/final_all.tex`   (Table 3, 6 columns)
    - `output/figures/cdum_coef.png`  (Figure 19: company FE coefficients, column (1) specification)

This file also exposes `build_pca_indices`, the single reusable PCA-index-construction function
requested by the conversion plan — `pca_social` ("Social Influence Index") and `pca_engag`
("Community Engagement Index") — which `table1_summary_stats.py` imports directly (same-folder
import) to compute its own summary statistics over these two composite indices.

Data source
-----------
`DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"`, produced by the sibling data-prep script
`code/02_data_preparation/build_cross_sectional_dataset.py` (confirmed present and read directly to
verify the column names below). Expected columns (Stata variable names preserved for traceability, per
project convention):
    eip_number, Category (str, capitalized -- e.g. "ERC"/"Core"/"Networking"/"Interface"),
    category_encoded (int factor code, lowercase), status (str: "Draft"/"Review"/"Last Call"/"Final"/
    "Living"/"Stagnant"/"Withdrawn"), success (0/1, pre-existing), implementation (raw 0/1/missing),
    n_authors, eip_nwords, eip_read, anon_max, betweenness_centrality, log_tw, log_gh, replies, views,
    users, likes, sdate (a date column), and the wide per-author-slot columns author1..author15,
    author{n}_id, author{n}_company1..company5, author{n}_EF_start, author{n}_EF_end (n = 1..15).

Notes
-------
- Robust standard errors: `.fit(cov_type="HC1")`, matching Stata's `reg ..., robust`.
- Confidence intervals are 90% (`model.conf_int(alpha=0.10)`), matching the paper's `levels(90)`
  convention, not statsmodels' 95% default.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.formula.api as smf
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_PROCESSED, OUTPUT_FIGURES, OUTPUT_TABLES, ensure_dirs
from utils.reg_tables import format_regression_table, plot_coefficients

CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"

N_AUTHOR_SLOTS = 15
N_COMPANY_SLOTS = 5


# ---------------------------------------------------------------------------------------
# PCA index construction (reusable -- also imported by table1_summary_stats.py)
# ---------------------------------------------------------------------------------------
def _fit_signed_pca_score(df: pl.DataFrame, inputs: list[str]) -> pl.Series:
    """
    Fit a 1-component PCA on standardized `inputs` (listwise deletion of rows with any null input,
    matching Stata's `pca` command), predict scores for every row with complete inputs (null
    elsewhere), and apply a deterministic sign convention.

    Sign convention: a PCA component's sign is mathematically arbitrary (an eigenvector and its
    negation are equally valid). Every input variable to both `pca_social` (log_gh, log_tw,
    betweenness_centrality, anon_max) and `pca_engag` (replies, views, users, likes) is a "more =
    more influence/engagement" measure, so the fitted component is flipped (negating both its
    loadings and its scores) whenever the mean of its loadings across `inputs` is negative -- this
    gives both indices a consistent "higher = more influence/engagement" direction.
    """
    complete = df.select(inputs).with_row_index("__rid").drop_nulls()
    if complete.is_empty():
        raise ValueError(f"No rows with complete data for PCA inputs {inputs!r}.")

    X = complete.select(inputs).to_numpy()
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    pca = PCA(n_components=1)
    scores = pca.fit_transform(X_std).ravel()
    loadings = pca.components_[0]

    if loadings.mean() < 0:
        scores = -scores
        loadings = -loadings  # not returned, but kept for clarity/debugging

    scored = pl.DataFrame({"__rid": complete.get_column("__rid"), "__score": scores})

    full = df.with_row_index("__rid").select("__rid").join(scored, on="__rid", how="left")
    return full.get_column("__score")


def build_pca_indices(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add `pca_social` ("Social Influence Index") and `pca_engag` ("Community Engagement Index") to
    `df`, replicating:

        pca log_gh log_tw between anon_max
        predict pca_social, score
        pca replies views users likes
        predict pca_engag, score

    `between` in the original `.do` file is Stata's unambiguous abbreviation of
    `betweenness_centrality` (the only variable in the dataset with that prefix).

    Parameters
    ----------
    df : pl.DataFrame
        Must contain columns: log_gh, log_tw, betweenness_centrality, anon_max, replies, views,
        users, likes.

    Returns
    -------
    pl.DataFrame
        `df` with two new float columns appended: `pca_social`, `pca_engag`. A row missing any one
        of its component's four inputs gets a null score for that component (matches Stata's
        listwise-deletion behavior for `pca`/`predict, score`).
    """
    pca_social = _fit_signed_pca_score(df, ["log_gh", "log_tw", "betweenness_centrality", "anon_max"])
    pca_engag = _fit_signed_pca_score(df, ["replies", "views", "users", "likes"])
    return df.with_columns(
        pca_social.alias("pca_social"),
        pca_engag.alias("pca_engag"),
    )


# ---------------------------------------------------------------------------------------
# `implemented` derivation
# ---------------------------------------------------------------------------------------
def add_implemented_column(df: pl.DataFrame) -> pl.DataFrame:
    """
    Replicates:
        gen implemented = implementation
        replace implemented = . if (status is Draft/Final/Last Call/Living/Review) & implementation ~=1

    i.e. `implemented` equals the raw `implementation` flag, EXCEPT that for statuses which have not
    yet reached a terminal outcome (Draft, Final, Last Call, Living, Review) it is set to missing
    unless the EIP was *already* actually implemented (implementation == 1) despite not (yet) being
    Withdrawn/Stagnant. This is intentional (avoids classifying "still pending" as "not implemented"),
    not a bug.
    """
    non_terminal = pl.col("status").is_in(["Draft", "Final", "Last Call", "Living", "Review"])
    return df.with_columns(
        pl.when(non_terminal & (pl.col("implementation") != 1))
        .then(None)
        .otherwise(pl.col("implementation"))
        .alias("implemented")
    )


# ---------------------------------------------------------------------------------------
# Top-10 company dummy construction (duplicated in fig_company_concentration.py -- see module
# docstring for why)
# ---------------------------------------------------------------------------------------
def _sanitize_company_name(name: str) -> str:
    """Mirror Stata's `subinstr(company," ","_",.)` + `subinstr(company,".","_",.)`, defensively
    extended to any other non-word character so the result is always a valid Python/patsy identifier
    fragment."""
    return re.sub(r"[^0-9A-Za-z_]", "_", name)


def _build_author_company_long(df: pl.DataFrame) -> pl.DataFrame:
    """
    Reshape the wide author{n}_company{c} slot columns into a long (eip_number, author_id, company)
    panel, replicating the `reshape long` + `duplicates drop` steps at the top of the "ADD TOP10
    COMPANY DUMMIES" section. Empty-string company values (Stata's `tostring`-of-numeric-missing
    produces the literal string "." for company; here we simply use null/"" interchangeably) are kept
    in the panel and filtered out by callers as needed.
    """
    frames = []
    for a in range(1, N_AUTHOR_SLOTS + 1):
        id_col = f"author{a}_id"
        if id_col not in df.columns:
            continue
        for c in range(1, N_COMPANY_SLOTS + 1):
            comp_col = f"author{a}_company{c}"
            if comp_col not in df.columns:
                continue
            frames.append(
                df.select(
                    pl.col("eip_number"),
                    pl.col(id_col).alias("author_id"),
                    pl.col(comp_col).cast(pl.Utf8).alias("company"),
                )
            )
    if not frames:
        raise KeyError("No author{n}_id / author{n}_company{c} columns found in df.")
    long_df = pl.concat(frames, how="vertical")
    long_df = long_df.filter(pl.col("author_id").is_not_null())
    return long_df.unique()


def top10_companies(long_df: pl.DataFrame) -> list[str]:
    """Top-10 companies by count of (author, eip, company) rows, replicating `gsort -one company`
    then `if _n<11`."""
    counts = (
        long_df.filter((pl.col("company").is_not_null()) & (pl.col("company") != ""))
        .group_by("company")
        .agg(pl.len().alias("one"))
        .sort(["one", "company"], descending=[True, False])
    )
    return counts.head(10).get_column("company").to_list()


def build_top10_company_dummies(df: pl.DataFrame) -> tuple[pl.DataFrame, list[str], dict[str, str]]:
    """
    Add one `cdum_<sanitized company>` 0/1 column per top-10 company (by author-EIP-pair count),
    replicating:

        foreach comp in `top10' {
            gen cdum_`comp2' = 0
            forvalues x = 1/15 { forvalues c = 1/5 {
                replace cdum_`comp2' = 1 if author`x'_company`c' == "`comp'"
            } }
        }

    Returns
    -------
    (df_with_dummies, cdum_column_names, label_map)
        `label_map` maps each `cdum_*` column name to its (sanitized) display label, mirroring the
        original's post-hoc `label var cd "`var2'"` loop (`substr(cd,6,.)` = strip the "cdum_" prefix).
    """
    long_df = _build_author_company_long(df)
    top10 = top10_companies(long_df)

    out = df
    cdum_cols: list[str] = []
    label_map: dict[str, str] = {}
    for company in top10:
        col = f"cdum_{_sanitize_company_name(company)}"
        cdum_cols.append(col)
        label_map[col] = _sanitize_company_name(company)

        member_ids = (
            long_df.filter(pl.col("company") == company)
            .select("author_id")
            .unique()
            .get_column("author_id")
        )
        # A row (EIP) gets the dummy if ANY of its author-slot ids is affiliated with this company.
        author_id_cols = [f"author{a}_id" for a in range(1, N_AUTHOR_SLOTS + 1) if f"author{a}_id" in df.columns]
        is_member = pl.any_horizontal([pl.col(c).is_in(member_ids) for c in author_id_cols])
        out = out.with_columns(pl.when(is_member).then(1).otherwise(0).alias(col))

    return out, cdum_cols, label_map


def add_ef_dummy(df: pl.DataFrame) -> pl.DataFrame:
    """
    Replicates `compdum_EF2`: 1 if any author-slot's Ethereum Foundation affiliation window
    (`author{n}_EF_start` .. `author{n}_EF_end`, end possibly missing/open-ended) covers the EIP's
    start year. The original's inner `forvalues c = 1/5` loop over company slots is redundant dead
    code (EF_start/EF_end do not vary by company slot) and is not reproduced.
    """
    year = pl.col("sdate").dt.year()
    conditions = []
    for a in range(1, N_AUTHOR_SLOTS + 1):
        start_col, end_col = f"author{a}_EF_start", f"author{a}_EF_end"
        if start_col not in df.columns or end_col not in df.columns:
            continue
        conditions.append(
            pl.col(start_col).is_not_null()
            & (pl.col(start_col) <= year)
            & (pl.col(end_col).is_null() | (pl.col(end_col) >= year))
        )
    if not conditions:
        raise KeyError("No author{n}_EF_start/EF_end columns found in df.")
    is_ef = pl.any_horizontal(conditions)
    return df.with_columns(pl.when(is_ef).then(1).otherwise(0).alias("compdum_EF2"))


# ---------------------------------------------------------------------------------------
# Regressions
# ---------------------------------------------------------------------------------------
def _formula(outcome: str, include_pca_engag: bool, cdum_cols: list[str]) -> str:
    terms = ["pca_social"]
    if include_pca_engag:
        terms.append("pca_engag")
    terms += ["n_authors", "eip_nwords", "eip_read", "C(category_encoded)", "C(year)"] + cdum_cols
    return f"{outcome} ~ " + " + ".join(terms)


def run_table3_regressions(df: pl.DataFrame, cdum_cols: list[str]):
    """
    Fit the 6 OLS specifications behind Table 3, all with HC1 robust standard errors:

        (1) reg success pca_social n_authors eip_nwords eip_read i.category_encoded cdum_* i.year, robust
        (2) reg success pca_social pca_engag n_authors eip_nwords eip_read i.category_encoded cdum_* i.year, robust
        (3) reg success pca_social n_authors eip_nwords eip_read i.category_encoded cdum_* i.year if implementation==., robust
        (4) reg success pca_social pca_engag n_authors eip_nwords eip_read i.category_encoded cdum_* i.year if implementation==., robust
        (5) reg implemented pca_social n_authors eip_nwords eip_read i.category_encoded cdum_* i.year, robust
        (6) reg implemented pca_social pca_engag n_authors eip_nwords eip_read i.category_encoded cdum_* i.year, robust

    Columns (3)-(4) restrict the sample to EIPs where `implementation` is missing.
    """
    pdf_full = df.to_pandas()
    pdf_impl_missing = df.filter(pl.col("implementation").is_null()).to_pandas()

    models = [
        smf.ols(_formula("success", False, cdum_cols), data=pdf_full).fit(cov_type="HC1"),
        smf.ols(_formula("success", True, cdum_cols), data=pdf_full).fit(cov_type="HC1"),
        smf.ols(_formula("success", False, cdum_cols), data=pdf_impl_missing).fit(cov_type="HC1"),
        smf.ols(_formula("success", True, cdum_cols), data=pdf_impl_missing).fit(cov_type="HC1"),
        smf.ols(_formula("implemented", False, cdum_cols), data=pdf_full).fit(cov_type="HC1"),
        smf.ols(_formula("implemented", True, cdum_cols), data=pdf_full).fit(cov_type="HC1"),
    ]
    return models


def main() -> None:
    ensure_dirs()

    df = pl.read_parquet(CROSS_SECTIONAL_PATH)
    df = df.with_columns(pl.col("sdate").dt.year().alias("year"))
    df = add_implemented_column(df)
    df = build_pca_indices(df)
    df, cdum_cols, cdum_labels = build_top10_company_dummies(df)
    df = add_ef_dummy(df)  # computed for parity with the original pipeline; not used as a regressor
    # (compdum_EF2 is NOT part of the `cdum_*` wildcard match in Stata, so it never entered these
    # regressions in the original either -- see eip_ef_by_year.png in fig_company_concentration.py
    # for where it IS used.)

    models = run_table3_regressions(df, cdum_cols)

    # To add to the LaTeX table manually: a header block grouping columns 1-2 as "Finalized: All
    # EIPs", 3-4 as "Finalized" (restricted to EIPs with missing `implementation`, see
    # run_table3_regressions), and 5-6 as "Implemented".
    #   & \multicolumn{4}{c}{Finalized} &  \multicolumn{2}{c}{Implemented}  \\ \cline{2-5}\cline{6-7}
    #   & \multicolumn{2}{c}{All EIPs} &  \multicolumn{2}{c}{ERC EIPs} &  \multicolumn{2}{c}{Core EIPs} \\ \cline{2-3}\cline{4-5}\cline{6-7}

    coef_labels = {
        "pca_social": "Social Influence Index",
        "pca_engag": "Community Engagement Index",
        "n_authors": "N. EIP Authors",
        "eip_nwords": "N. Words in EIP (k)",
        "eip_read": "Readability Score",
    }
    fe_rows = {
        "Category FE": [True] * 6,
        "Company FE": [True] * 6,
        "Year FE": [True] * 6,
    }
    format_regression_table(
        models=models,
        column_labels=["(1)", "(2)", "(3)", "(4)", "(5)", "(6)"],
        out_path=OUTPUT_TABLES / "final_all.tex",
        coef_labels=coef_labels,
        fe_rows=fe_rows,
        keep_coef_pattern=r"^(pca_social|pca_engag|n_authors|eip_nwords|eip_read)$",
        notes=(
            "Robust (HC1) standard errors. Significance: * p<0.10, ** p<0.05, *** p<0.01. "
            "Outcome for columns (1)-(4) is Finalized (success); columns (3)-(4) restrict the "
            "sample to observations with a missing raw implementation value. Outcome for columns "
            "(5)-(6) is Implemented."
        ),
    )

    # Figure 19: company FE coefficients from column (1)'s specification.
    col1 = models[0]
    params = col1.params.to_dict()
    conf_int_df = col1.conf_int(alpha=0.10)  # 90% CI, per the paper's levels(90) convention
    conf_int = {name: (float(row[0]), float(row[1])) for name, row in conf_int_df.iterrows()}

    plot_coefficients(
        params=params,
        conf_int=conf_int,
        out_path=OUTPUT_FIGURES / "cdum_coef.png",
        keep_pattern=r"^cdum_",
        xline=0.0,
        labels=cdum_labels,
        title="Company fixed-effect coefficients, Table 3 column (1) (outcome: Finalized)",
    )


if __name__ == "__main__":
    main()
