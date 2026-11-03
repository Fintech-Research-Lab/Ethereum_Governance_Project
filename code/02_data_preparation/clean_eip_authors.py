"""
clean_eip_authors.py
=====================

Part of the reproduction package for:
    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
    Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.

Replaces
--------
`Data/Data Gathering Code/pythoncode to prepare data merging.py` from the original
messy project.

Feeds
-----
This script's main output (`ethereum_cross_sectional_data_beg.parquet`) is the very
first cross-sectional build step: it takes the raw EIP registry
(`allEIPsandAuthorsv2.csv`, one row per EIP with a free-text, comma-separated
`Author` field) and turns it into a one-row-per-EIP table with up to 15 individually
identified `Author1`...`Author15` columns and matching `author1_id`...`author15_id`
columns. Downstream, this table is merged with everything else (commit data, meeting
attendance, social/employment data, etc.) to build the paper's master cross-sectional
dataset (`Ethereum_Cross-sectional_Data`), which in turn feeds essentially every
EIP-level and author-level result in the paper: author concentration / Lorenz curves,
Gini-by-year, EIP-by-category, centrality analyses, and the summary-statistics table.

What this script does
------------------------
1. Reads the raw EIP registry CSV (Latin-1 encoded -- see `_read_latin1_csv_as_utf8`
   below) and the EIP-author roster CSV.
2. Splits each EIP's free-text `Author` field on commas into up to 15 individual
   author-name tokens, stripping parenthetical asides (e.g. "(@handle)") and
   anything in angle brackets (e.g. "<email@...>").
3. Applies a hand-built, ~34-entry typo/mojibake correction dictionary
   (`WRONG_NAMES` / `RIGHT_NAMES` below) to fix known encoding mangling and
   misspellings in author names.
4. De-duplicates repeated authors within a single EIP's author list (preserving
   first-occurrence order), producing the final `Author1`...`Author15` columns.
5. Maps each cleaned author name to its `author_id` via the roster, producing
   `author1_id`...`author15_id`.
6. Applies one manual status override: EIP 1283's `Status` is forced to "Stagnant"
   (a data-quality correction on the raw registry, applied post-hoc after upstream
   investigation).
7. Writes the resulting cross-sectional "beg" (beginning-of-pipeline) table.
8. Writes an updated author roster containing only the names actually seen among
   this run's EIPs.

Raw data is immutable
------------------------
`data/raw/` is never written to. The name-frequency-filtered roster (item 8 above)
is written to `data/interim/unique_author_names_with_id_updated.parquet` instead
(see `OUTPUT_AUTHOR_ROSTER` below), saved as Parquet since it's consumed
programmatically by `name_cleaning_pipeline.py` and other downstream scripts.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add code/ to sys.path
from config import DATA_INTERIM, DATA_RAW, ensure_dirs  # noqa: E402

# ---------------------------------------------------------------------------
# Inputs / outputs
# ---------------------------------------------------------------------------
RAW_EIP_AUTHORS_CSV = DATA_RAW / "eip_registry" / "allEIPsandAuthorsv2.csv"
RAW_AUTHOR_ROSTER_CSV = DATA_RAW / "eip_registry" / "unique_author_names_with_id.csv"

OUTPUT_CROSS_SECTIONAL_BEG = DATA_INTERIM / "ethereum_cross_sectional_data_beg.parquet"
OUTPUT_AUTHOR_ROSTER = DATA_INTERIM / "unique_author_names_with_id_updated.parquet"

N_AUTHOR_SLOTS = 15  # Author1..Author15 / author1_id..author15_id

# ---------------------------------------------------------------------------
# Hand-built typo / mojibake correction dictionary
# ---------------------------------------------------------------------------
# Author names known to appear mangled (encoding issues, typos, or inconsistent
# spelling) in the raw EIP registry, mapped to their corrected form. 'lightclient'
# appears twice below; both map to the same corrected value ("Matt Garnett"), so the
# duplicate is harmless.
WRONG_NAMES: list[str] = [
    "Christian ReitwieÃŸner", "Lightclient", "Marius van der Wijden", "Muhammed Emin Ayd?n",
    "Mücahit Büyüky?lmaz", "Pawe? Bylica", "Piotr Kosi?ski", "Sergio D. Lerner",
    "g. nicholas dandrea", "and Arran Schlosberg", "Piotr KosiÅ„ski", "Benjamin Hauser",
    "Señor Doggo", "Felix J Lange", "Pandapip1", "Martin Swende", "lightclient",
    "lightclient", "qizhou", "Tomasz Stanczak", "Zainan Zhou", "fubuloubu",
    "Süleyman Karda?", "Tomá Jan?a", "tefan imec", "Jessica", "Roy",
    "Christian ReitwieBner", "Agustín Aguilar", "Joel Torstensson", "Michael D. Carter",
    "PhD", "et al.", "Christian Reitwießner",
]
RIGHT_NAMES: list[str] = [
    "Christian Reitwiessner", "Matt Garnett", "Marius Van Der Wijden", "Muhammed Emin Aydın",
    "Mücahit Büyükyılmaz", "Pawel Bylica", "Piotr Kosinski", "Sergio Demian Lerner",
    "g. nicholas d'andrea", "Arran Schlosberg", "Piotr Kosiński", "Ben Hauser",
    "Bryant Eisenbach", "Felix Lange", "Gavin John", "Martin Holst Swende", "Matt Garnett",
    "Matt Garnett", "Qi Zhou", "Tomasz Kajetan Stanczak", "Zainan Victor Zhou",
    "Bryant Eisenbach", "Suleman Kardas", "Tomas Jansa", "Stefan Simec", "Jessica Zheng",
    "Roy Shang", "c", "Agustin Aguilar", "Joel Thorstensson", "Michael Carter", "", "",
    "Christian Reitwiessner",
]
assert len(WRONG_NAMES) == len(RIGHT_NAMES) == 34

# dict(zip(...)) semantics: for the one repeated key ("lightclient"), the LAST
# occurrence wins when building the dict -- here both occurrences map to the same
# value ("Matt Garnett") so this is a no-op duplication, not a behavior change.
NAME_DICT: dict[str, str] = dict(zip(WRONG_NAMES, RIGHT_NAMES))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str | None:
    """
    Strip parenthetical asides (e.g. "(@handle)") and angle-bracketed text (e.g.
    "<email@example.com>") from a name, then trim whitespace. Returns None for an
    empty result, so it can be filtered out downstream.
    """
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.strip()
    return None if text == "" else text


def _read_latin1_csv_as_utf8(path: Path) -> pl.DataFrame:
    """
    Read a CSV that was authored/encoded as Latin-1 (ISO-8859-1), exactly as the
    original script did with `pd.read_csv(path, encoding='latin1')`.

    Polars' `read_csv` has no `encoding="latin1"` option (only "utf8"/"utf8-lossy"),
    so we decode the raw bytes as Latin-1 in Python first (a lossless 1:1
    byte<->codepoint mapping) and re-encode the resulting text as UTF-8 before handing
    it to Polars. This produces byte-for-byte the same Unicode codepoints that pandas'
    `encoding='latin1'` would have produced -- including the mojibake sequences (e.g.
    "ReitwieÃŸner") that `WRONG_NAMES` above exists to fix.
    """
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("latin1")
    return pl.read_csv(io.BytesIO(text.encode("utf-8")))


def _split_and_correct(author_field: str) -> list[str]:
    """
    Split one EIP's raw `Author` field on commas, clean each token (see
    `clean_text`), drop empty/None tokens, and apply `NAME_DICT` corrections.
    """
    tokens = author_field.split(",")
    cleaned = [clean_text(tok) for tok in tokens]
    cleaned = [c for c in cleaned if c is not None]
    return [NAME_DICT.get(name, name) for name in cleaned]


def _rearrange_dedup(names: list[str | None]) -> list[str | None]:
    """
    De-duplicate a row's author slots, preserving first-occurrence order (a repeated
    missing/None slot collapses to a single trailing None, same as any other repeated
    value), then pad to `N_AUTHOR_SLOTS` with None so every row has exactly 15 slots.
    """
    seen: set[str | None] = set()
    out: list[str | None] = []
    for name in names:
        if name not in seen:
            out.append(name)
            seen.add(name)
    if len(out) > N_AUTHOR_SLOTS:
        raise ValueError(
            f"Row has {len(out)} de-duplicated author slots, exceeding N_AUTHOR_SLOTS={N_AUTHOR_SLOTS}."
        )
    return out + [None] * (N_AUTHOR_SLOTS - len(out))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def load_raw_eip_authors() -> pl.DataFrame:
    """Read `allEIPsandAuthorsv2.csv` (Number, Title, Author, Status)."""
    return _read_latin1_csv_as_utf8(RAW_EIP_AUTHORS_CSV)


def load_author_roster() -> pl.DataFrame:
    """Read `unique_author_names_with_id.csv` (author_id, Full_Name, GitHub_Username, Anonymity_Flag)."""
    return pl.read_csv(RAW_AUTHOR_ROSTER_CSV)


def build_cross_sectional_beg(
    dat: pl.DataFrame, author_roster: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Core port of `pythoncode to prepare data merging.py`.

    Returns
    -------
    (cross_sectional_beg, updated_author_roster)
        `cross_sectional_beg` : one row per EIP with eip_number, Title, Author,
            Status, Author1..Author15, author1_id..author15_id.
        `updated_author_roster` : the input roster filtered down to names that were
            actually observed among this run's cleaned author lists (mirrors the
            original's `new_author_in_author`, saved -- in this package -- to
            `data/interim/` instead of overwriting the raw input).
    """
    rows = dat.to_dicts()

    author1_15_rows: list[list[str | None]] = []
    for row in rows:
        corrected = _split_and_correct(row["Author"])
        author1_15_rows.append(_rearrange_dedup(corrected))

    # Pool of every author name actually seen across this run's cleaned Author1..15
    # slots -- used below to filter the roster down to names actually in use, and to
    # build the name -> author_id lookup.
    all_author_values = [v for sub in author1_15_rows for v in sub]
    new_author_pool = set(v for v in all_author_values if v is not None)

    new_author_in_author = author_roster.filter(pl.col("Full_Name").is_in(list(new_author_pool)))

    author_dict: dict[str, int] = dict(
        zip(new_author_in_author["Full_Name"].to_list(), new_author_in_author["author_id"].to_list())
    )

    # Build column-by-column (rather than row-of-dicts) so Polars' schema inference
    # cannot get confused by all-null early rows in a given author-slot column.
    columns: dict[str, list[object]] = {
        "eip_number": [row["Number"] for row in rows],
        "Title": [row["Title"] for row in rows],
        "Author": [row["Author"] for row in rows],
        "Status": [row["Status"] for row in rows],
    }
    for i in range(1, N_AUTHOR_SLOTS + 1):
        columns[f"Author{i}"] = [slots[i - 1] for slots in author1_15_rows]
    for i in range(1, N_AUTHOR_SLOTS + 1):
        columns[f"author{i}_id"] = [
            (author_dict.get(slots[i - 1]) if slots[i - 1] is not None else None) for slots in author1_15_rows
        ]

    schema = {"eip_number": pl.Int64, "Title": pl.Utf8, "Author": pl.Utf8, "Status": pl.Utf8}
    for i in range(1, N_AUTHOR_SLOTS + 1):
        schema[f"Author{i}"] = pl.Utf8
    for i in range(1, N_AUTHOR_SLOTS + 1):
        schema[f"author{i}_id"] = pl.Int64

    cross_sectional = pl.DataFrame(columns, schema=schema)

    # Manual override: EIP 1283's Status is corrected to "Stagnant".
    cross_sectional = cross_sectional.with_columns(
        pl.when(pl.col("eip_number") == 1283)
        .then(pl.lit("Stagnant"))
        .otherwise(pl.col("Status"))
        .alias("Status")
    )

    return cross_sectional, new_author_in_author


def generate_review_candidates() -> None:
    """
    Optional -- for transparency only.

    The original script contains no separate "candidate generation for manual
    review" step (unlike the fuzzy-matching name-cleaning scripts): the
    `WRONG_NAMES`/`RIGHT_NAMES` correction dictionary above was hand-built by
    inspection, not generated by any programmatic candidate-list step. This function
    exists only to document that fact and satisfy the package-wide convention that
    every name-cleaning script expose a `generate_review_candidates()` hook -- there
    is nothing to generate here. A full reproduction run does not need to call this.
    """
    return None


def main() -> None:
    ensure_dirs()

    dat = load_raw_eip_authors()
    author_roster = load_author_roster()

    cross_sectional, updated_roster = build_cross_sectional_beg(dat, author_roster)

    cross_sectional.write_parquet(OUTPUT_CROSS_SECTIONAL_BEG, compression="zstd")
    updated_roster.write_parquet(OUTPUT_AUTHOR_ROSTER, compression="zstd")

    print(f"Wrote {OUTPUT_CROSS_SECTIONAL_BEG} ({cross_sectional.shape[0]} rows, {cross_sectional.shape[1]} cols)")
    print(f"Wrote {OUTPUT_AUTHOR_ROSTER} ({updated_roster.shape[0]} rows, {updated_roster.shape[1]} cols)")


if __name__ == "__main__":
    main()
