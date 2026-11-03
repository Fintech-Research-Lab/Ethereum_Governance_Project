"""
table1_summary_stats.py
========================

Reproduces **Table 1** (summary statistics) of:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: descriptive statistics for the main analysis sample of EIPs.

Ported from: `Analysis\\Regression Code\\Regression Code.do`, the
`local summary_list = "anon_max betweenness pca_engag replies likes users views success implemented
n_author tf_scale gh_follower eip_nwords eip_read pca_social"` / `eststo: estpost summarize
`summary_list', detail` / `esttab ... summstat.tex` block.

Output: `output/tables/summstat.tex` (Table 1).

Data source
-----------
`DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"`.

Variable -> label mapping -- NARROWED FROM THE ORIGINAL 15-VARIABLE LIST
--------------------------------------------------------------------------
The original `.do` file's `summary_list` has 15 variables, but the PUBLISHED `Tables/summstat.tex`
that is actually `\input` by the paper only ever had 8 rows -- `betweenness`, `pca_engag`, `replies`,
`likes`, `users`, `views`, and `pca_social` (Betweenness Centrality, the two PCA indices, and the
four raw FEM engagement counts) were cut from the published table at some point. This script is
narrowed to match: it only computes and writes the 8 variables actually in the published table,
rather than generating 15 rows nothing displays. See `code/utils/reg_tables.py::TABLE1_VARIABLES`
for the matching 8-label list.

    anon_max     -> Anonymous Author
    success      -> Finalized
    implemented  -> Implemented
    n_authors    -> N. EIP Authors
    tf_scale     -> N. Twitter Followers (K)
    gh_follower  -> N. Github Followers
    eip_nwords   -> N. Words in EIP (k)
    eip_read     -> Readability Score

`implemented` is not a raw source column -- it is derived from raw `implementation` (see
`_add_implemented_column()` below, inlined from `table3_finalization_regressions.py`'s
`add_implemented_column()`, the only piece of that module this script ever needed; the PCA-index
construction, `build_pca_indices()`, is no longer imported at all since neither index is in the
published table).

Note: percentiles use linear-interpolation quantiles (`format_summary_stats_table`'s convention),
which can differ negligibly at this project's N from Stata's `summarize, detail` order-statistic
convention.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_PROCESSED, OUTPUT_TABLES, ensure_dirs
from utils.reg_tables import TABLE1_VARIABLES, format_summary_stats_table

CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"

# Stata variable name -> paper display label, in TABLE1_VARIABLES' exact published order.
VARIABLE_TO_LABEL: dict[str, str] = {
    "anon_max": "Anonymous Author",
    "success": "Finalized",
    "implemented": "Implemented",
    "n_authors": "N. EIP Authors",
    "tf_scale": "N. Twitter Followers (K)",
    "gh_follower": "N. Github Followers",
    "eip_nwords": "N. Words in EIP (k)",
    "eip_read": "Readability Score",
}

assert list(VARIABLE_TO_LABEL.values()) == TABLE1_VARIABLES, (
    "VARIABLE_TO_LABEL's label order has drifted from utils.reg_tables.TABLE1_VARIABLES -- "
    "these must match exactly (see that constant's docstring)."
)


def _add_implemented_column(df: pl.DataFrame) -> pl.DataFrame:
    """Inlined from `table3_finalization_regressions.py::add_implemented_column()` (the only
    function this script used from that module; see module docstring). Replicates:
        gen implemented = implementation
        replace implemented = . if (status is Draft/Final/Last Call/Living/Review) & implementation ~=1
    i.e. `implemented` equals the raw `implementation` flag, EXCEPT that for statuses which have not
    yet reached a terminal outcome it is set to missing unless the EIP was *already* actually
    implemented despite not (yet) being Withdrawn/Stagnant. Intentional, not a bug.
    """
    non_terminal = pl.col("status").is_in(["Draft", "Final", "Last Call", "Living", "Review"])
    return df.with_columns(
        pl.when(non_terminal & (pl.col("implementation") != 1))
        .then(None)
        .otherwise(pl.col("implementation"))
        .alias("implemented")
    )


def main() -> None:
    ensure_dirs()

    df = pl.read_parquet(CROSS_SECTIONAL_PATH)
    df = _add_implemented_column(df)

    format_summary_stats_table(
        df=df,
        variables=list(VARIABLE_TO_LABEL.keys()),
        var_labels=VARIABLE_TO_LABEL,
        out_path=OUTPUT_TABLES / "summstat.tex",
    )


if __name__ == "__main__":
    main()
