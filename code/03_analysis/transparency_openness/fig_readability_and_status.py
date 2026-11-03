"""
fig_readability_and_status.py
================================

Reproduces **Figure 5** (`\\label{fig:understand}`, "EIP Readability") of the current manuscript,
`paper/latex/MS_R2.tex`. Figure/table numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date. The `\\label` is the
stable identifier.

Paper section: descriptive analysis of EIP text (readability, length).

Ported from: `Analysis\\Regression Code\\Regression Code.do`, the "ANALYSIS OF TEXT READABILITY"
section.

Output produced by this script:
    Figure 5 (`fig:understand`): read_hist.png    -- histogram of `eip_read` (readability score)
                                 nwords_hist.png   -- histogram of `eip_nwords` (EIP word count)

This script originally also produced an EIP-status pie chart (`success.png`) and, earlier still, an
EIP-category pie chart (`eip_by_category.png`). Neither is referenced anywhere in the current
`MS_R2.tex` (confirmed via a full-text search for both output filenames and for any EIP-status pie
chart), so neither is generated here. See `archive/README.md` for the category-pie removal; the
status-pie removal is recorded in `PIPELINE_TODO.md`.

Data source
-----------
`DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"`, columns `eip_read`, `eip_nwords`
(confirmed against the actual column names produced by
`code/02_data_preparation/build_cross_sectional_dataset.py`).

Notes
-----
The original `sum eip_read, d` / `sum eip_nwords, d` calls (`summarize ..., detail`) are purely
descriptive console output preceding each histogram in the `.do` file; they do not write to a file,
so are not reproduced here as an artifact (no numeric claim from them is baked into any figure or
table, per project convention -- see rule 16).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_PROCESSED, OUTPUT_FIGURES, ensure_dirs

CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"


def make_histograms(df: pl.DataFrame) -> None:
    """read_hist.png and nwords_hist.png -- plain histograms of eip_read / eip_nwords."""
    for col, out_name in (("eip_read", "read_hist.png"), ("eip_nwords", "nwords_hist.png")):
        values = df.select(pl.col(col).drop_nulls()).to_series().to_numpy()
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.hist(values, bins=30, color="0.6", edgecolor="black")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
        fig.tight_layout()
        fig.savefig(OUTPUT_FIGURES / out_name, dpi=200)
        plt.close(fig)


def main() -> None:
    ensure_dirs()

    df = pl.read_parquet(CROSS_SECTIONAL_PATH)

    make_histograms(df)


if __name__ == "__main__":
    main()
