"""
table2_fem_regressions.py
===========================

Reproduces **Table 2** (Ethereum Magicians / "FEM" forum engagement regressions) of:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: the forum-engagement determinants analysis (comments/views/likes/unique-users on the
Ethereum Magicians forum thread for each EIP), regressed on the RAW social/network/readability
components -- NOT the PCA composite indices used in Table 3. Confirmed during planning: these are two
genuinely distinct specifications and must not be accidentally unified.

Ported from: `Analysis\\Magician Comments\\FEM_regressions.do` (the entire file).

Outputs:
    - `output/tables/FEM_reg_out.tex`      (Table 2, levels: replies/views/likes/users)

A log-outcome variant is not part of the published paper and is not fit or written here.

Data sources
------------
- `DATA_INTERIM / "fem_data_for_regressions.parquet"`: the FEM forum-engagement dataset (one row per
  EIP thread: `eip` [renamed here to `eip_number`], `replies`, `views`, `likes`, `users`, and `year`
  [the FEM thread's own year, used directly rather than re-derived from the cross-sectional
  `sdate`]), produced by `code/03_analysis/community_engagement/fig_fem_engagement.py`.
- `DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"`: merged in for the covariates
  (`n_authors`, `tw_follower`, `gh_follower`, `author_commit`, `n_contributors_eip`,
  `betweenness_centrality`, `log_tw`, `log_gh`, `tf_scale`, `category_encoded`, `client_commits*`,
  `eip_read`, `eip_nwords`, `n_committing_authors`, `Category`, `anon_max`) via a left join of the
  FEM data onto the cross-sectional data (every FEM-thread row is kept; cross-sectional rows with
  no FEM counterpart are dropped).

Regression specification (identical RHS for all 8 models; robust == HC1 throughout):
    reg <outcome> n_authors log_tw log_gh betweenness_centrality anon_max eip_nwords eip_read
        i.category_encoded i.year, robust

These are plain linear OLS regressions with robust standard errors -- `eform` (exponentiated
coefficients) is not applicable here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_INTERIM, DATA_PROCESSED, OUTPUT_TABLES, ensure_dirs
from utils.reg_tables import format_regression_table

# FIX (fig_fem_engagement.py): this path originally read "FEM_data_for_regressions.parquet"
# (capital "FEM"), flagged in this file's own docstring as an "unverified best-effort inference"
# made before the producing script existed. `code/03_analysis/community_engagement/
# fig_fem_engagement.py` (the actual producer, now written) writes the file with an all-lower-case
# name, matching what `code/02_data_preparation/build_cross_sectional_dataset.py` already expected.
# Windows filesystems are case-insensitive so this specific mismatch would not actually have
# broken anything at runtime here, but the casing is corrected anyway so all three scripts agree
# exactly, per the conversion brief for `fig_fem_engagement.py`.
FEM_DATA_PATH = DATA_INTERIM / "fem_data_for_regressions.parquet"
CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"

CROSS_SECTIONAL_KEEP_COLS = [
    "eip_number",
    "n_authors",
    "tw_follower",
    "gh_follower",
    "author_commit",
    "n_contributors_eip",
    "betweenness_centrality",
    "log_tw",
    "log_gh",
    "tf_scale",
    "category_encoded",
    "eip_read",
    "eip_nwords",
    "n_committing_authors",
    "Category",
    "anon_max",
    # `client_commits*` (a wildcard group of columns in the original) is intentionally not
    # enumerated here since none of the 8 regressions below use it; add explicitly if a downstream
    # script needs it.
]


def load_fem_regression_data() -> pl.DataFrame:
    """Build the merged FEM-engagement analysis dataset, replicating the `insheet` + `rename` +
    `merge 1:1 ... keep(1 3)` block at the top of `FEM_regressions.do`."""
    fem = pl.read_csv(FEM_DATA_PATH) if FEM_DATA_PATH.suffix == ".csv" else pl.read_parquet(FEM_DATA_PATH)
    fem = fem.rename({"eip": "eip_number"})

    cross = pl.read_parquet(CROSS_SECTIONAL_PATH).select(CROSS_SECTIONAL_KEEP_COLS)

    # Stata `merge 1:1 ... keep(1 3)` == left join of the "master" (fem) onto "using" (cross),
    # keeping unmatched-master + matched rows and dropping unmatched-using rows.
    merged = fem.join(cross, on="eip_number", how="left")

    for col in ("replies", "views", "likes", "users"):
        merged = merged.with_columns((pl.col(col) + 1).log().alias(f"log_{col}"))

    # FIX (units mismatch): `eip_nwords` is scaled in THOUSANDS of words throughout this project
    # (matching Table 1/Table 3's "(k)"-labeled convention), but the paper's actual published
    # Table 2 "WordCount" row uses the RAW (un-scaled, per-single-word) word count -- evidenced by
    # its much smaller coefficient magnitude (paper: 0.01**/0.90**/0.01**/0.00**) and its row label
    # "WordCount" carrying no "(k)" suffix, unlike Table 3's explicitly-labeled "(k)" row. Table 2's
    # t-statistics already matched the paper almost exactly even with the (k)-scaled variable
    # (t-stats are invariant to linear rescaling of X), confirming this is a pure units issue
    # local to this table, not a real modeling bug. Table 3's word-count variable/units are
    # intentionally left untouched -- this derived column is only used in this script's formula.
    merged = merged.with_columns((pl.col("eip_nwords") * 1000).alias("eip_nwords_raw"))

    return merged


def _formula(outcome: str) -> str:
    return (
        f"{outcome} ~ n_authors + log_tw + log_gh + betweenness_centrality + anon_max + "
        "eip_nwords_raw + eip_read + C(category_encoded) + C(year)"
    )


def run_fem_regressions(df: pl.DataFrame):
    """Fit the 4 level-outcome models (replies, views, likes, users), all with HC1 robust
    standard errors -- this is Table 2 as published."""
    pdf = df.to_pandas()

    level_outcomes = ["replies", "views", "likes", "users"]
    return [smf.ols(_formula(outcome), data=pdf).fit(cov_type="HC1") for outcome in level_outcomes]


COEF_LABELS = {
    "n_authors": "N. EIP Authors",
    "log_tw": "N. Twitter Followers (log)",
    "log_gh": "N. Github Followers (log)",
    "betweenness_centrality": "Betweenness Centrality",
    "anon_max": "Anonymous Author",
    # Table 2's "WordCount" row uses the raw (un-scaled) word count, not the "(k)"-scaled variable
    # used elsewhere in this package.
    "eip_nwords_raw": "N. Words in EIP",
    "eip_read": "Readability Score",
    # Category dummies (Core, category_encoded == 1, is the omitted/reference level --
    # `_encode_category()` in build_cross_sectional_dataset.py assigns codes alphabetically over
    # the full category list [Core, ERC, Informational, Interface, Meta, Networking] before
    # Meta/Informational rows are filtered out, so Core=1 is always the reference group). patsy
    # names these terms by the actual numeric level value, e.g. `C(category_encoded)[T.2]`.
    "C(category_encoded)[T.2]": "ERC",
    "C(category_encoded)[T.4]": "Interface",
    "C(category_encoded)[T.6]": "Networking",
}
FE_ROWS = {"Year FE": [True] * 4}
KEEP_PATTERN = (
    r"^(n_authors|log_tw|log_gh|betweenness_centrality|anon_max|eip_nwords_raw|eip_read"
    r"|C\(category_encoded\)\[T\.(2|4|6)\])$"
)


def main() -> None:
    ensure_dirs()

    df = load_fem_regression_data()
    level_models = run_fem_regressions(df)

    column_labels = ["(1)", "(2)", "(3)", "(4)"]

    # FEM_reg_out.tex -- outcomes: replies, views, likes, users (levels).
    format_regression_table(
        models=level_models,
        column_labels=column_labels,
        out_path=OUTPUT_TABLES / "FEM_reg_out.tex",
        coef_labels=COEF_LABELS,
        fe_rows=FE_ROWS,
        keep_coef_pattern=KEEP_PATTERN,
        notes=(
            "Robust (HC1) standard errors. Significance: * p<0.10, ** p<0.05, *** p<0.01. "
            "Outcomes (1)-(4): N. Comments, N. Views, N. Likes, N. Unique Users on the Ethereum "
            "Magicians forum thread for each EIP."
        ),
    )
    # NOTE: the original `.do` file also produces a log-outcome variant, `FEM_reg_out_log.tex` --
    # not part of the published paper (confirmed: only `FEM_reg_out.tex` is `\input` anywhere in
    # `main.tex`/`JF_Initial_Submission.tex`). No longer generated here -- see `run_fem_regressions()`.


if __name__ == "__main__":
    main()
