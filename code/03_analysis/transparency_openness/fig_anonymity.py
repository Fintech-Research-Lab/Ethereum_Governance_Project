"""
fig_anonymity.py
==================

Reproduces **Figure 6** (`\\label{fig:anon}`, "Anonymity in the Ethereum Governance Process") of
the current manuscript, `paper/latex/MS_R2.tex`. Figure numbers shift as the paper is
revised; see `docs/figure_table_index.md` for the current numbering snapshot and its date.

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Paper section: Transparency. Figure 6 is a 3-bar chart of the percentage of people who disclose
their full (non-anonymous) name in each of three governance-participation roles: EIP Authors,
AllCoreDevs meeting Attendees, and Top (by commit count) Client Developers.

Ported from: `Analysis\\Anonymity Analysis\\Anonymity Analysis.py`.

Output: `output/figures/figure_04_anonymity.png`.

Data sources
------------
- `data/raw/eip_registry/unique_author_names_with_id.csv` -- the raw author roster, read with
  explicit Latin-1 decoding (see `_read_latin1_csv_as_utf8`). Columns: `author_id`, `Full_Name`,
  `GitHub_Username`, `Anonymity_Flag`.
- `data/processed/ethereum_cross_sectional_data.parquet` -- columns `author1_id..author15_id`,
  `sdate`, melted long and inner-joined back to the roster above to get one (author_id,
  Anonymity_Flag) row per author-slot-appearance, then averaged per `author_id` (numerically a
  no-op since `Anonymity_Flag` is constant per author, but expressed as a `groupby(...).mean()`
  since that generalizes cleanly if a future author ever has a slot-dependent attribute).
- `data/interim/unique_attendees_final.parquet` (from
  `code/02_data_preparation/name_cleaning_pipeline.py`) -- column `Anonymity_Flag`, used
  directly (one row per unique cleaned attendee name).
- Client commits via `utils.client_commits.load_all_client_commits()` -- each of the four
  execution clients' own commit history.

Design notes
-------------
1. **Per-column name normalization before ranking client developers.** A handful of commit
   authors appear under more than one spelling in the raw git history (e.g. a full name, an
   email-derived handle, and a nickname all referring to the same Nethermind developer). These
   are normalized to one canonical name each via `_row_wide_scalar_assign()` before computing
   each client's top-20-by-commit-count list, so the same person isn't split across multiple rows.
2. **Top-20 selection and Anonymity_Flag overrides are both name-keyed, not position-keyed.**
   `_top_n_by_count()` ranks by commit count with a stable, alphabetical-name tie-break (so the
   ranking itself is reproducible run-to-run); `_GETH_TOP20_OVERRIDES` / `_BESU_TOP20_OVERRIDES` /
   `_NETHERMIND_TOP20_OVERRIDES` then apply a small number of manual-review corrections to
   specific, named individuals whose disclosed/pseudonymous status the plain "contains a space"
   heuristic gets wrong (e.g. a person's real name recorded as a single-word git handle). Keying
   these by name means the correction always follows the right person even if a future commit-data
   refresh changes exactly who ranks where.

Not computed (would have no effect on Figure 6)
-------------------------------------------------
The original script also independently loaded `unique_clients_final.csv` and
`unique_contributorsonly_final.csv`, cleaned them up, and then never referenced either variable
again -- the bar chart only ever needs `authors`, `attendees['Anonymity_Flag']`, and
`client_top20['Anonymity_Flag']`. Neither input is loaded here, both to avoid an unnecessary
cross-script dependency on `fig_venn_diagram.py` (which is what actually produces the
`unique_contributorsonly_final` equivalent in this package) and because they would have zero
effect on this figure's output.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path
from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_FIGURES, ensure_dirs  # noqa: E402
from utils.client_commits import load_client_commits  # noqa: E402

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
RAW_AUTHOR_ROSTER_CSV = DATA_RAW / "eip_registry" / "unique_author_names_with_id.csv"
CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
ATTENDEES_FINAL_PATH = DATA_INTERIM / "unique_attendees_final.parquet"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
OUTPUT_FIGURE_PATH = OUTPUT_FIGURES / "figure_04_anonymity.png"

AUTHOR_ID_COLS = [f"author{i}_id" for i in range(1, 16)]


# ---------------------------------------------------------------------------
# Small local helpers (duplicated rather than cross-imported from
# code/02_data_preparation/*, since every code/03_analysis/ script is designed to
# be self-contained and runnable on its own).
# ---------------------------------------------------------------------------
def _read_latin1_csv_as_utf8(path: Path) -> pl.DataFrame:
    """
    Read a CSV that was authored/encoded as Latin-1 (ISO-8859-1), exactly matching the
    original's explicit `pd.read_csv(..., encoding='latin-1')` call for this specific file.
    Polars' `read_csv` has no `encoding="latin1"` option, so we decode the raw bytes as Latin-1
    in Python first and re-encode as UTF-8 before handing the text to Polars (same approach as
    `code/02_data_preparation/clean_eip_authors.py::_read_latin1_csv_as_utf8`).
    """
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("latin1")
    return pl.read_csv(io.BytesIO(text.encode("utf-8")))


def _row_wide_scalar_assign(df: pl.DataFrame, mask: pl.Expr, value: str) -> pl.DataFrame:
    """Set the `author` column to `value` for every row matching `mask`, leaving every other
    column untouched -- used to collapse a developer's several recorded name spellings down to
    one canonical name before ranking commit counts."""
    return df.with_columns(pl.when(mask).then(pl.lit(value)).otherwise(pl.col("author")).alias("author"))


def _top_n_by_count(df: pl.DataFrame, n: int) -> pl.DataFrame:
    """
    Rank authors by commit count and return the top `n`.

    Ties are broken by author name (ascending) via a stable sort, since client-commit data
    carries no separate author-id to break ties on -- name is the only available, and a
    perfectly adequate, secondary key. This makes the ranking fully deterministic and
    reproducible run-to-run: combined with the name-keyed Anonymity_Flag overrides (see
    `_GETH_TOP20_OVERRIDES` etc. below), only WHO sits exactly at the top-20/21 boundary can
    shift if the underlying commit data changes, never which specific person receives which
    Anonymity_Flag.
    """
    counts = (
        df.group_by("author")
        .agg(pl.col("date").count().alias("n"))
        .sort("author")
        .sort("n", descending=True, maintain_order=True)
    )
    return counts.head(n)


def _anonymity_flags_from_names(names: list[str], overrides: dict[str, int] | None = None) -> list[int]:
    """Assign Anonymity_Flag to each name: 0 (real full name disclosed) if the name contains a
    space, 1 (pseudonymous / handle) otherwise. Any name present in `overrides` (a
    Name -> Anonymity_Flag dict) takes that value instead -- see `_GETH_TOP20_OVERRIDES` below
    for what these are."""
    flags = [0 if (" " in n) else 1 for n in names]
    if overrides:
        for i, n in enumerate(names):
            if n in overrides:
                flags[i] = overrides[n]
    return flags


# ---------------------------------------------------------------------------
# Manual Anonymity_Flag corrections for the top-20 client-developer lists
# ---------------------------------------------------------------------------
# The base "contains a space" heuristic misclassifies a small number of specific,
# known individuals within each client's top-20 committer list -- e.g. a real,
# disclosed identity recorded as a single-word git handle. These corrections are
# keyed by the individual's name (not by their rank/row position in the list), so
# each one always follows the right person: if a future commit-data refresh changes
# exactly who ranks where, a correction simply stops applying if its person drops out
# of the top 20, rather than silently landing on whoever replaces them.
_GETH_TOP20_OVERRIDES = {"ucwong": 0}
_BESU_TOP20_OVERRIDES = {"MadelineMurray": 0, "garyschulte": 0, "Jason Frame": 0, "Chris Mckay": 0}
_NETHERMIND_TOP20_OVERRIDES = {"SebastianDremo": 0}


# ---------------------------------------------------------------------------
# 1. EIP authors: mean Anonymity_Flag per unique author, derived from the cross-sectional data
# ---------------------------------------------------------------------------
def compute_author_anonymity(author_roster: pl.DataFrame) -> pl.DataFrame:
    """
    Port of the original's:
        cs = cs[[author1_id..author15_id, sdate]]
        author_df = cs.melt(id_vars='sdate', value_vars=author_id_cols, ...)
        author_df = author_df[pd.notnull(author_df['Author_id'])]
        author_df = pd.merge(author_df, authors, left_on='Author_id', right_on='author_id', how='inner')
        authors = author_df.groupby('Author_id')['Anonymity_Flag'].mean()

    Returns a 2-column DataFrame (`Author_id`, `Anonymity_Flag`), one row per unique author_id
    that appears in at least one EIP's author-slot columns AND matches the roster.
    """
    cs = pl.read_parquet(CROSS_SECTIONAL_PATH).select([*AUTHOR_ID_COLS, "sdate"])
    author_df = cs.melt(id_vars="sdate", value_vars=AUTHOR_ID_COLS, variable_name="number", value_name="Author_id")
    author_df = author_df.filter(pl.col("Author_id").is_not_null())
    author_df = author_df.join(
        author_roster.select(["author_id", "Anonymity_Flag"]),
        left_on="Author_id",
        right_on="author_id",
        how="inner",
    )
    return author_df.group_by("Author_id").agg(pl.col("Anonymity_Flag").mean().alias("Anonymity_Flag"))


# ---------------------------------------------------------------------------
# 2. Top-20 client developers (by commit count), across geth/besu/erigon/nethermind
# ---------------------------------------------------------------------------
def compute_client_top20_anonymity_flags() -> list[int]:
    """
    For each of the four execution clients, rank committers by commit count, take the top 20,
    and assign each an Anonymity_Flag (see `_anonymity_flags_from_names`). Returns the
    concatenated [geth, besu, erigon, nethermind] top-20 Anonymity_Flag lists, in that order.
    """
    geth = load_client_commits("geth")
    besu = load_client_commits("besu")
    erigon = load_client_commits("erigon")
    nethermind = load_client_commits("nethermind")

    # A few committers appear under more than one name spelling in the raw git history;
    # normalize each to one canonical name before ranking.
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "Tomasz Kajetan Sta?czak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "Tomasz K. Stanczak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "tkstanczak", "Tomasz Kajetan Stanczak")
    nethermind = _row_wide_scalar_assign(nethermind, pl.col("author") == "github-actions[bot]", "")
    erigon = _row_wide_scalar_assign(erigon, pl.col("author") == "alex.sharov", "Alex Sharov")

    geth_top20 = _top_n_by_count(geth, 20)
    besu_top20 = _top_n_by_count(besu, 20)
    erigon_top20 = _top_n_by_count(erigon, 20)
    nethermind_top20 = _top_n_by_count(nethermind.filter(pl.col("author") != ""), 20)

    geth_af = _anonymity_flags_from_names(geth_top20["author"].to_list(), _GETH_TOP20_OVERRIDES)
    besu_af = _anonymity_flags_from_names(besu_top20["author"].to_list(), _BESU_TOP20_OVERRIDES)
    erigon_af = _anonymity_flags_from_names(erigon_top20["author"].to_list())
    nethermind_af = _anonymity_flags_from_names(nethermind_top20["author"].to_list(), _NETHERMIND_TOP20_OVERRIDES)

    return geth_af + besu_af + erigon_af + nethermind_af


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
def make_anonymity_figure(author_pct: float, attendee_pct: float, client_pct: float) -> None:
    labels = ["EIP \n Authors", "AllCoreDevs \n Attendees", "Top Client \n Developers"]
    percentages = [author_pct, attendee_pct, client_pct]

    fig, ax = plt.subplots()
    ax.bar(labels, percentages, color=["blue", "green", "red"])
    ax.set_ylabel("Percentage of People \n Disclosing their Full Names")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURE_PATH)
    plt.close(fig)


def main() -> None:
    ensure_dirs()

    author_roster = _read_latin1_csv_as_utf8(RAW_AUTHOR_ROSTER_CSV)
    authors_mean = compute_author_anonymity(author_roster)
    attendees = pl.read_parquet(ATTENDEES_FINAL_PATH)
    client_flags = compute_client_top20_anonymity_flags()

    author_pct = (1 - authors_mean["Anonymity_Flag"].sum() / authors_mean.height) * 100
    attendee_pct = (1 - attendees["Anonymity_Flag"].sum() / attendees.height) * 100
    client_pct = (1 - sum(client_flags) / len(client_flags)) * 100

    make_anonymity_figure(author_pct, attendee_pct, client_pct)

    print(f"EIP Authors disclosing full name:            {author_pct:.1f}% (n={authors_mean.height})")
    print(f"AllCoreDevs Attendees disclosing full name:   {attendee_pct:.1f}% (n={attendees.height})")
    print(f"Top Client Developers disclosing full name:   {client_pct:.1f}% (n={len(client_flags)})")
    print(f"Wrote {OUTPUT_FIGURE_PATH}")


if __name__ == "__main__":
    main()
