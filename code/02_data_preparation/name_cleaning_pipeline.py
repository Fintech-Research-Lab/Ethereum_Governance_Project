"""
name_cleaning_pipeline.py
===========================

Part of the reproduction package for:
    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
    Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.

Replaces (all four, ported in full)
------------------------------------
  1. `Analysis/.../Name Cleaning/python code to create flat list.py`
       -> `flatten_meeting_attendees()`
  2. `Analysis/.../Name Cleaning/Name Cleaning Code for Attendees.py`
       -> `clean_attendees()`
  3. `Analysis/.../Name Cleaning/Name Cleaning Code for Contributors and Clients.py`
       -> `build_unique_contributors()`, `build_unique_clients()`
  4. `Analysis/.../Name Cleaning/Name Cleaning Code Cross List.py`
       -> `cross_list_merge_and_flag()`

Feeds
-----
The four output lists this script writes (`unique_attendees_final`,
`unique_clients_final`, `unique_contributors_final`, `unique_authors_final`, all under
`data/interim/`) are the name-standardization backbone of the paper's community and
anonymity analyses: the meeting-attendee venn diagram, Top-10-in-community tables,
Client Analysis (company/employer Lorenz curves), and the Anonymity Analysis
(Figure 4-adjacent anonymity-flag statistics) all consume one or more of these lists.

High-level algorithm (same shape in all three fuzzy-matching scripts)
------------------------------------------------------------------------
Each of "for Attendees" / "for Contributors and Clients" (clients half) / "Cross
List" follows the same three-round pattern:
  1. Compute a pairwise Levenshtein similarity score (`fuzzywuzzy.fuzz.ratio`) between
     every pair of currently-unique names.
  2. Write out the pairs scoring > 76 (round 1) to a "candidate" CSV for a human to
     manually review and decide which are true duplicates.
  3. Load the frozen, human-reviewed result (a `*_post_manual.csv` with
     `Names_to_Keep` / `Names_to_Replace` columns) and apply it as a name -> name
     substitution dict.
  4. Repeat for pairs scoring in (54, 76) (round 2), then a final no-similarity-score
     manual pass over the remaining unique names (round 3).
The contributor list is the one exception: it gets a single small (8-entry)
hand-built correction dict instead of the three-round fuzzy process.

This package treats every `*_post_manual.csv` mapping file (now under
`data/raw/name_cleaning_manual/`) as a FROZEN, already-human-reviewed input -- the
functions here only ever *apply* those mappings. The expensive O(n^2)
`fuzzywuzzy.fuzz.ratio` candidate-GENERATION step (needed only to reproduce how the
`*_to_change*.csv` candidate lists were originally produced, not to reproduce the
final output) is implemented but gated behind `generate_review_candidates_*()`
functions that a full reproduction run does not need to call.

Design notes
-------------
1. `clean_text()` and the Latin-1-CSV-reading helper live in `clean_eip_authors.py`
   and are imported from there rather than redefined here, since the raw author
   roster and the dev-call attendee roster need identical text cleaning.
2. The author roster is always read directly from `data/raw/eip_registry/` (the
   pristine raw file), never from `clean_eip_authors.py`'s own output -- this keeps
   `data/raw/` strictly immutable and gives every function in this module a single,
   unambiguous source for author identity. Anonymity_Flag is assigned to that roster
   via the space-heuristic-plus-historical-reference join described in
   `_anonymity_flags()` below; this reproduces all 698 of the raw roster's own
   existing Anonymity_Flag values exactly.

A note on `unique_contributorsonly_final` (NOT produced here -- out of scope)
--------------------------------------------------------------------------------
The original project has both `unique_contributors_final.csv` (produced by "Name
Cleaning Code Cross List.py", ported here) and a second, genuinely different file,
`unique_contributorsonly_final.csv`. The latter is NOT produced by any of this
conversion's four source scripts -- it is built later by a separate script,
`Community Engagement Analysis.py` (an anti-join of the author roster against THIS
script's own `unique_contributors_final.csv` output, isolating contributors who are
NOT also EIP authors). That script is out of scope for this conversion; it belongs
to a future "community engagement" conversion task and should consume this script's
`unique_contributors_final.parquet` as one of its inputs when ported.

See `_unique_via_set` below for the row-ordering convention used when de-duplicating
name lists, and `_anonymity_flags` for how Anonymity_Flag assignment recovers the
original author's actual historical judgment calls independent of that row order.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add code/ to sys.path
from config import DATA_INTERIM, DATA_RAW, ensure_dirs  # noqa: E402
from clean_eip_authors import clean_text, _read_latin1_csv_as_utf8  # noqa: E402
from utils.client_commits import load_all_client_commits  # noqa: E402

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
RAW_DEV_CALLS_ATTENDEES_CSV = DATA_RAW / "meetings" / "dev_calls_attendees_standardized_v2.csv"
RAW_AUTHOR_ROSTER_CSV = DATA_RAW / "eip_registry" / "unique_author_names_with_id.csv"
RAW_EIP_COMMIT_XLSX = DATA_RAW / "commits" / "eip_commit_beg.xlsx"

MANUAL_DIR = DATA_RAW / "name_cleaning_manual"

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
OUTPUT_ATTENDEES_FINAL = DATA_INTERIM / "unique_attendees_final.parquet"
OUTPUT_CLIENTS_FINAL = DATA_INTERIM / "unique_clients_final.parquet"
OUTPUT_CONTRIBUTORS_FINAL = DATA_INTERIM / "unique_contributors_final.parquet"
OUTPUT_AUTHORS_FINAL = DATA_INTERIM / "unique_authors_final.parquet"
# A second, explicitly-named copy of the `authors` output above, so downstream
# scripts that need "the author roster with Anonymity_Flag" have an unambiguous
# place to read it from without depending on `cross_list_merge_and_flag()` directly.
OUTPUT_AUTHOR_ROSTER_ANONYMITY = DATA_INTERIM / "unique_author_names_with_id_anonymity.parquet"


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------
def _load_manual_mapping(path: Path) -> dict[str | None, str | None]:
    """
    Load one `*_post_manual.csv` (columns `Names_to_Keep`, `Names_to_Replace`) into a
    `{Names_to_Replace: Names_to_Keep}` dict, faithfully matching the original's
    `dict(zip(wrong_names, right_names))` where `wrong_names =
    names_to_change_mod['Names_to_Replace']` and `right_names =
    names_to_change_mod['Names_to_Keep']`.

    These files are frozen, human-reviewed reference data (see the package-wide
    conventions) -- this function only ever reads them, never regenerates them. Some
    of them contain a stray, unused 4th column (including one literal Excel `#REF!`
    error value left over from manual editing) and/or a leading unnamed index column;
    we select only the two columns we need so Polars' schema inference never has to
    look at that junk.
    """
    df = pl.read_csv(path, columns=["Names_to_Keep", "Names_to_Replace"])
    wrong = df["Names_to_Replace"].to_list()
    right = df["Names_to_Keep"].to_list()
    return dict(zip(wrong, right))


def _apply_mapping(names: list[str | None], mapping: dict[str | None, str | None]) -> list[str | None]:
    """`[mapping[n] if n in mapping else n for n in names]`, i.e. `dict.get(n, n)`."""
    return [mapping.get(n, n) for n in names]


def _unique_preserve_order(values: list) -> list:
    """
    Faithful port of pandas' `Series.unique()` / `pd.unique()`: de-duplicate while
    preserving FIRST-OCCURRENCE order. This is fully deterministic (unlike
    `_unique_via_set` below).
    """
    seen = set()
    out = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _unique_via_set(values: list, deterministic: bool = True) -> list:
    """
    De-duplicate a list of names.

    `deterministic=True` (the default) preserves first-occurrence order, so the four
    output files' row order is stable and reproducible across re-runs. Pass
    `deterministic=False` for a plain `set()`-based dedup instead, whose row order
    varies by process (Python randomizes `set` iteration order for strings by
    default). Either way, Anonymity_Flag is assigned by a NAME-keyed lookup
    (`_anonymity_flags()` in `cross_list_merge_and_flag()`), so this choice affects
    only row order, never which person gets which flag or any other computed value.
    """
    if deterministic:
        return _unique_preserve_order(values)
    return list(set(values))


def _fuzz_ratio_similarity_scores(names: list[str]) -> list[tuple[int, int, str, str, int]]:
    """
    Faithful port of the original's O(n^2) similarity-score double loop:
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                score = fuzz.ratio(names[i], names[j])
                ...
    Returns a list of (i, j, name_i, name_j, score) tuples, exactly like the
    original's `similarity_score` list.

    This is only used by the optional `generate_review_candidates_*()` functions
    (candidate-list generation for manual review) -- it is NOT needed to reproduce
    the final output, since the manually-reviewed `*_post_manual.csv` files are
    already provided as frozen inputs. It is O(n^2) and can be slow for large lists
    (thousands of names); that is faithful to the original, which had the same cost.
    """
    from fuzzywuzzy import fuzz  # imported lazily: only needed for this optional path

    scores = []
    for i, j in itertools.combinations(range(len(names)), 2):
        score = fuzz.ratio(names[i], names[j])
        scores.append((i, j, names[i], names[j], score))
    return scores


# ===========================================================================
# 1. python code to create flat list.py
# ===========================================================================
def flatten_meeting_attendees() -> list[str]:
    """
    Port of `python code to create flat list.py`.

    Reads the standardized dev-call attendee roster (one row per meeting, with a
    single comma-separated `Attendees` free-text field) and flattens it into one
    name per list element (across all meetings), applying the same `clean_text()`
    parenthetical/angle-bracket stripping used throughout this package.

    The original also builds a parallel, position-aligned `Meeting` list (repeating
    each meeting's name once per attendee) and writes both columns to
    `flat_list_meeting_attendees.csv`. Only the flattened `Attendees` names are
    actually consumed downstream (by "Name Cleaning Code for Attendees.py"), so this
    port returns just that list; nothing downstream needs the per-name meeting
    label.
    """
    dat = _read_latin1_csv_as_utf8(RAW_DEV_CALLS_ATTENDEES_CSV)

    flat_names: list[str] = []
    for attendees_field in dat["Attendees"].to_list():
        if attendees_field is None:
            continue
        tokens = attendees_field.split(",")
        cleaned = [clean_text(tok) for tok in tokens]
        flat_names.extend(c for c in cleaned if c is not None)
    return flat_names


# ===========================================================================
# 2. Name Cleaning Code for Attendees.py
# ===========================================================================
def generate_review_candidates_attendees(flat_names: list[str]) -> dict[str, pl.DataFrame]:
    """
    Optional -- for transparency only. Reproduces the three rounds of fuzzy-match
    candidate lists ("names_to_change.csv", "names_to_change2.csv",
    "names_to_change3.csv") that a human reviewed to produce the frozen
    `names_to_change*_post_manual.csv` files. A full reproduction run does not need
    to call this -- see `clean_attendees()`.
    """
    unique_attendees1 = list(set(flat_names))
    scores = _fuzz_ratio_similarity_scores(unique_attendees1)

    round1 = [s for s in scores if s[4] > 76]
    round2 = [s for s in scores if 54 < s[4] < 76]

    round1_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round1], "Names_to_Replace": [s[3] for s in round1]}
    )
    round2_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round2], "Names_to_Replace": [s[3] for s in round2]}
    )
    round3_df = pl.DataFrame({"full_name": sorted(set(flat_names), key=lambda x: (isinstance(x, str), x))})
    return {"round1": round1_df, "round2": round2_df, "round3": round3_df}


def clean_attendees(flat_names: list[str], deterministic: bool = True) -> list[str]:
    """
    Port of `Name Cleaning Code for Attendees.py`'s main (non-candidate-generation)
    path: apply the three frozen manual mapping rounds in sequence, then de-duplicate
    and drop nulls / the literal string "NONE".

    Returns the equivalent of the original's `Unique_Attendees.csv` (`full_name`
    column) -- an intermediate list consumed by `cross_list_merge_and_flag()` below,
    NOT the final `unique_attendees_final` output (that gets an additional
    cross-list fuzzy-match round and an Anonymity_Flag -- see
    `cross_list_merge_and_flag()`).
    """
    names2 = _apply_mapping(flat_names, _load_manual_mapping(MANUAL_DIR / "names_to_change_post_manual.csv"))
    names3 = _apply_mapping(names2, _load_manual_mapping(MANUAL_DIR / "names_to_change2_post_manual.csv"))
    names4 = _apply_mapping(names3, _load_manual_mapping(MANUAL_DIR / "names_to_change3_post_manual.csv"))

    unique_attendees = _unique_via_set(names4, deterministic=deterministic)
    return [n for n in unique_attendees if n is not None and n != "NONE"]


# ===========================================================================
# 3. Name Cleaning Code for Contributors and Clients.py
# ===========================================================================
# Small, hand-built 8-entry correction dict (verbatim from the original) -- unlike
# attendees/clients, the contributor list gets no fuzzy-match rounds at all, just
# this single dict applied once. Note the last entry maps a name to itself
# (a no-op, presumably left over from the original's own review process) -- ported
# exactly as-is.
_CONTRIBUTOR_WRONG_NAMES: list[str] = [
    "Afri Schoedon", "5chdn", "Andrew", "David", "Lucas", "Ratan (Rai) Sur",
    "Süleyman Kardaş", "g. nicholas d'andrea",
]
_CONTRIBUTOR_RIGHT_NAMES: list[str] = [
    "Afri Schoeden", "Afri Schoeden", "Andrew Ashikhmin", "David Bieber", "Lucas Cullen",
    "Rai Ratan Sur", "Suleman Kardas", "g. nicholas d'andrea",
]
assert len(_CONTRIBUTOR_WRONG_NAMES) == len(_CONTRIBUTOR_RIGHT_NAMES) == 8
_CONTRIBUTOR_NAME_DICT: dict[str, str] = dict(zip(_CONTRIBUTOR_WRONG_NAMES, _CONTRIBUTOR_RIGHT_NAMES))


def build_unique_contributors(deterministic: bool = True) -> list[str]:
    """
    Port of the "Contributor List" section of
    `Name Cleaning Code for Contributors and Clients.py`.

    Loads the EIP commit log (`eip_commit_beg.xlsx`), left-joins it to the author
    roster on `Username == GitHub_Username`, keeps only commits whose committer is
    NOT already a known EIP author (`left_only`, i.e. a genuine "contributor" who
    isn't already counted as an "author"), drops the `eth-bot` bot account, takes the
    unique `Author` names (order-preserving, via `pd.unique`-equivalent), applies the
    8-entry correction dict above, and de-duplicates via `set()` (see
    `_unique_via_set`'s docstring for the row-ordering convention).

    Returns the equivalent of the original's `Unique_Contributors.csv`
    (`Full_Name` column).
    """
    eip_commit = pl.read_excel(RAW_EIP_COMMIT_XLSX)
    roster = pl.read_csv(RAW_AUTHOR_ROSTER_CSV)

    joined = eip_commit.join(
        roster.select(["Full_Name", "GitHub_Username"]),
        left_on="Username",
        right_on="GitHub_Username",
        how="left",
    )
    # "left_only" (pandas merge indicator) == no matching roster row == Full_Name is null.
    contributors = joined.filter(pl.col("Full_Name").is_null())
    contributors = contributors.filter(pl.col("Author") != "eth-bot")

    names = _unique_preserve_order(contributors["Author"].to_list())
    names2 = _apply_mapping(names, _CONTRIBUTOR_NAME_DICT)
    return _unique_via_set(names2, deterministic=deterministic)


def generate_review_candidates_clients(client_names: list[str]) -> dict[str, pl.DataFrame]:
    """
    Optional -- for transparency only. Reproduces the two rounds of fuzzy-match
    candidate lists for the client list ("clients_name_to_change.csv",
    "client_names_to_change2.csv"). A full reproduction run does not need to call
    this -- see `build_unique_clients()`.
    """
    scores = _fuzz_ratio_similarity_scores(client_names)
    round1 = [s for s in scores if s[4] > 76]
    round2 = [s for s in scores if 54 < s[4] < 76]
    round1_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round1], "Names_to_Replace": [s[3] for s in round1]}
    )
    round2_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round2], "Names_to_Replace": [s[3] for s in round2]}
    )
    return {"round1": round1_df, "round2": round2_df}


def build_unique_clients(deterministic: bool = True) -> list[str]:
    """
    Port of the "Client List" section of
    `Name Cleaning Code for Contributors and Clients.py`.

    Loads all four execution clients' commit histories (via
    `utils.client_commits.load_all_client_commits`), concatenates them, takes the
    unique committer names, drops the two known bot accounts
    (`dependabot[bot]`, `github-actions[bot]`), then runs the three-round frozen
    manual-mapping cascade (`clients_name_to_change_post_manual.csv`,
    `client_names_to_change2_post_manual.csv`, `client_names_to_change3_post_manual.csv`),
    and de-duplicates via `set()` (see `_unique_via_set`'s docstring for the row-ordering convention).

    Returns the equivalent of the original's `Unique_Clients.csv` (`full_name`
    column).
    """
    commits = load_all_client_commits()
    all_authors: list[str] = []
    for client in ("geth", "besu", "erigon", "nethermind"):  # original concat order
        all_authors.extend(commits[client]["author"].to_list())

    client_unique = _unique_preserve_order(all_authors)
    client_unique = [c for c in client_unique if c not in ("dependabot[bot]", "github-actions[bot]")]

    # NOTE: the original re-derives `client_list = list(set(client_unique['full_name']
    # .tolist()))` here (a redundant extra pass through `set()` on an already-unique
    # list -- harmless, since de-duplicating an already-unique list is a no-op except
    # for reordering). We fold that into a single `_unique_via_set` call below rather
    # than two separate no-op/reorder passes, since the net effect on the SET of
    # names is identical; only intermediate row order (already non-deterministic)
    # would differ, which is immaterial for the reasons given in `_unique_via_set`.
    client_list = _unique_via_set(client_unique, deterministic=deterministic)

    names2 = _apply_mapping(client_list, _load_manual_mapping(MANUAL_DIR / "clients_name_to_change_post_manual.csv"))
    names3 = _apply_mapping(names2, _load_manual_mapping(MANUAL_DIR / "client_names_to_change2_post_manual.csv"))
    names4 = _apply_mapping(names3, _load_manual_mapping(MANUAL_DIR / "client_names_to_change3_post_manual.csv"))

    return _unique_via_set(names4, deterministic=deterministic)


# ===========================================================================
# 4. Name Cleaning Code Cross List.py
# ===========================================================================
def generate_review_candidates_crosslist(total_names: list[str]) -> dict[str, pl.DataFrame]:
    """
    Optional -- for transparency only. Reproduces the two rounds of fuzzy-match
    candidate lists for the cross-list merge ("total_names_to_change.csv",
    "total_names_to_change2.csv"). A full reproduction run does not need to call
    this -- see `cross_list_merge_and_flag()`.
    """
    unique_names = list(set(total_names))
    scores = _fuzz_ratio_similarity_scores(unique_names)
    round1 = [s for s in scores if s[4] > 76]
    round2 = [s for s in scores if 54 < s[4] < 76]
    round1_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round1], "Names_to_Replace": [s[3] for s in round1]}
    )
    round2_df = pl.DataFrame(
        {"Names_to_Keep": [s[2] for s in round2], "Names_to_Replace": [s[3] for s in round2]}
    )
    return {"round1": round1_df, "round2": round2_df}


# --- Anonymity_Flag: base heuristic + historical manual-review reference -----------
# Anonymity_Flag records whether a participant discloses their real identity (0) or
# appears under a pseudonym / handle (1). The base rule is mechanical -- a name
# containing a space reads as a real full name (0), a single "word" reads as a handle
# (1) -- but a name-based heuristic alone misclassifies a meaningful minority of
# real cases in both directions (e.g. "PegaSys Admin" contains a space but is not a
# disclosed individual; "alexwang" is one word but is a disclosed identity). The
# original project's manual reviewer resolved these case by case for every one of
# the four name lists, and those Dec-2023 review decisions were saved to disk as
# `unique_clients_final.csv`, `unique_attendees_final.csv`,
# `unique_contributors_final.csv`, and `unique_authors_final.csv` in the original
# project. This package treats those `Name -> Anonymity_Flag` decisions as frozen,
# authoritative reference data -- extracted here as
# `data/raw/name_cleaning_manual/anonymity_flag_reference_*.csv` -- and applies them
# as an override on top of the base heuristic via a left-join on Name (see
# `_anonymity_flags()` below). This is well-defined and reproducible regardless of
# row order, unlike a positional lookup would be (see `_unique_via_set` above). Any
# name not present in the reference (e.g. one that postdates the reviewed vintage of
# the data) simply falls back to the base heuristic, matching how the original
# handled every name it never hand-reviewed.
#
# Coverage of each list's current names by this reference: clients ~98% (1229/1251),
# attendees ~99% (376/377), authors ~97% (676/698), contributors ~3% (8/256) -- the
# low contributor coverage reflects this package's use of a newer client-commit data
# vintage than the 2023 reference vintage (see PIPELINE_TODO.md), and has negligible
# impact since only 2 of the 256 contributors were ever hand-reviewed to begin with --
# the heuristic was already doing nearly all of the work for that list.
_ANONYMITY_REFERENCE_FILES = {
    "clients": MANUAL_DIR / "anonymity_flag_reference_clients.csv",
    "attendees": MANUAL_DIR / "anonymity_flag_reference_attendees.csv",
    "contributors": MANUAL_DIR / "anonymity_flag_reference_contributors.csv",
    "authors": MANUAL_DIR / "anonymity_flag_reference_authors.csv",
}


def _load_anonymity_reference(list_name: str) -> dict[str, int]:
    """Load the frozen Name -> Anonymity_Flag reference table for one of the four
    name lists ("clients", "attendees", "contributors", "authors"). Returns a plain
    dict for O(1) lookup; duplicate names in the reference (none observed as of this
    writing) would resolve to the last row on load."""
    path = _ANONYMITY_REFERENCE_FILES[list_name]
    ref = pl.read_csv(path)
    return dict(zip(ref["Name"].to_list(), ref["Anonymity_Flag"].to_list()))


def _anonymity_flags(names: list[str], reference: dict[str, int]) -> list[int]:
    """
    Assign Anonymity_Flag to each name: 0 (real full name disclosed) if the name
    contains a space, 1 (pseudonymous / handle) otherwise, then override any name
    found in `reference` with the historical manual-review decision for that specific
    person (see the module-level comment above `_ANONYMITY_REFERENCE_FILES` for where
    `reference` comes from). Names not present in `reference` keep the base
    heuristic.
    """
    flags = [0 if (" " in n) else 1 for n in names]
    for i, n in enumerate(names):
        if n in reference:
            flags[i] = reference[n]
    return flags


def cross_list_merge_and_flag(
    unique_clients: list[str],
    unique_contributors: list[str],
    unique_attendees: list[str],
    deterministic: bool = True,
) -> dict[str, pl.DataFrame]:
    """
    Port of `Name Cleaning Code Cross List.py`.

    Concatenates the four already-deduplicated lists (clients, contributors, authors
    [= the full roster's Full_Name column, unmodified], attendees -- in that exact
    order, matching `pd.concat([clients, contributors, authors, attendees])`), runs
    one more three-round frozen-mapping cascade over the UNION (catching duplicates
    across list boundaries, e.g. someone listed slightly differently as an attendee
    vs. as an author), then re-splits by original list membership and de-duplicates
    each split (order-preserving, via `.unique()`-equivalent -- this step itself IS
    deterministic; only the INPUT order it receives is not, per
    `_unique_via_set`).

    The author list is deliberately NOT taken from this cross-list-corrected `total`
    (even though it is tagged `"author"` in `total_tags` above and could in principle
    be sliced back out) -- `unique_authors_final` is instead built from a fresh,
    independent read of the raw roster below, since the roster is already the
    canonical source of author identity and doesn't need the cross-list fuzzy-match
    correction that the other three (genuinely messier, free-text-sourced) lists do.

    Returns a dict with keys "attendees", "clients", "contributors", "authors", each
    a 2-column Polars DataFrame (`Name`/`Full_Name` + `Anonymity_Flag`) -- ready to be
    written as this script's four final outputs.
    """
    authors_roster = pl.read_csv(RAW_AUTHOR_ROSTER_CSV)
    author_full_names = authors_roster["Full_Name"].to_list()

    # pd.concat([clients, contributors, authors, attendees], ignore_index=True)
    total_names = list(unique_clients) + list(unique_contributors) + list(author_full_names) + list(unique_attendees)
    total_tags = (
        ["client"] * len(unique_clients)
        + ["contributor"] * len(unique_contributors)
        + ["author"] * len(author_full_names)
        + ["attendee"] * len(unique_attendees)
    )

    names2 = _apply_mapping(total_names, _load_manual_mapping(MANUAL_DIR / "total_names_to_change_post_manual.csv"))
    names3 = _apply_mapping(names2, _load_manual_mapping(MANUAL_DIR / "total_names_to_change2_post_manual.csv"))
    names4 = _apply_mapping(names3, _load_manual_mapping(MANUAL_DIR / "total_names_to_change3_post_manual.csv"))

    # total_mod['Name'] = pd.DataFrame(names4)  (position-aligned overwrite)
    attendees_mod = [n for n, tag in zip(names4, total_tags) if tag == "attendee"]
    clients_mod = [n for n, tag in zip(names4, total_tags) if tag == "client"]
    contributors_mod = [n for n, tag in zip(names4, total_tags) if tag == "contributor"]

    attendees_unique_mod = _unique_preserve_order(attendees_mod)
    clients_unique_mod = _unique_preserve_order(clients_mod)
    contributors_unique_mod = _unique_preserve_order(contributors_mod)

    # --- Anonymity_Flag (name-keyed reference join -- see Issue 19 fix above) ---
    attendees_flags = _anonymity_flags(attendees_unique_mod, _load_anonymity_reference("attendees"))
    clients_flags = _anonymity_flags(clients_unique_mod, _load_anonymity_reference("clients"))
    contributors_flags = _anonymity_flags(contributors_unique_mod, _load_anonymity_reference("contributors"))

    # Authors: read straight from the pristine roster loaded at the top of this
    # function -- we only need `author_id`, `Full_Name`, and `GitHub_Username`, so we
    # select those columns directly rather than reading everything and dropping what
    # we don't need.
    author_ids = authors_roster["author_id"].to_list()
    github_usernames = authors_roster["GitHub_Username"].to_list()
    authors_flags = _anonymity_flags(author_full_names, _load_anonymity_reference("authors"))

    return {
        "attendees": pl.DataFrame({"Name": attendees_unique_mod, "Anonymity_Flag": attendees_flags}),
        "clients": pl.DataFrame({"Name": clients_unique_mod, "Anonymity_Flag": clients_flags}),
        "contributors": pl.DataFrame({"Name": contributors_unique_mod, "Anonymity_Flag": contributors_flags}),
        "authors": pl.DataFrame(
            {
                "author_id": author_ids,
                "Full_Name": author_full_names,
                "GitHub_Username": github_usernames,
                "Anonymity_Flag": authors_flags,
            }
        ),
    }


# ===========================================================================
# Orchestration
# ===========================================================================
def main(deterministic: bool = True) -> None:
    """
    Run the full name-cleaning pipeline end-to-end and write the four final lists
    (plus the roster-with-anonymity duplicate output) to `data/interim/`.

    Parameters
    ----------
    deterministic : bool, default True
        Forwarded to every `set()`-based dedup step (see `_unique_via_set`). Default
        `True` gives a stable, order-preserving dedup, so the four output files'
        row order is reproducible across re-runs. This has no effect on
        Anonymity_Flag assignment either way (see `_anonymity_flags`).
    """
    ensure_dirs()

    flat_attendee_names = flatten_meeting_attendees()
    unique_attendees = clean_attendees(flat_attendee_names, deterministic=deterministic)
    unique_contributors = build_unique_contributors(deterministic=deterministic)
    unique_clients = build_unique_clients(deterministic=deterministic)

    final = cross_list_merge_and_flag(
        unique_clients=unique_clients,
        unique_contributors=unique_contributors,
        unique_attendees=unique_attendees,
        deterministic=deterministic,
    )

    final["attendees"].write_parquet(OUTPUT_ATTENDEES_FINAL, compression="zstd")
    final["clients"].write_parquet(OUTPUT_CLIENTS_FINAL, compression="zstd")
    final["contributors"].write_parquet(OUTPUT_CONTRIBUTORS_FINAL, compression="zstd")
    final["authors"].write_parquet(OUTPUT_AUTHORS_FINAL, compression="zstd")
    # Same content written twice under two names -- see OUTPUT_AUTHOR_ROSTER_ANONYMITY's
    # comment (this is the non-raw-overwriting replacement for the original's in-place
    # `Data/Raw Data/unique_author_names_with_id.csv` overwrite).
    final["authors"].write_parquet(OUTPUT_AUTHOR_ROSTER_ANONYMITY, compression="zstd")

    print(f"Wrote attendees: {OUTPUT_ATTENDEES_FINAL} ({final['attendees'].shape[0]} rows)")
    print(f"Wrote clients: {OUTPUT_CLIENTS_FINAL} ({final['clients'].shape[0]} rows)")
    print(f"Wrote contributors: {OUTPUT_CONTRIBUTORS_FINAL} ({final['contributors'].shape[0]} rows)")
    print(f"Wrote authors: {OUTPUT_AUTHORS_FINAL} ({final['authors'].shape[0]} rows)")
    print(f"Wrote authors (roster/anonymity duplicate): {OUTPUT_AUTHOR_ROSTER_ANONYMITY} ({final['authors'].shape[0]} rows)")


if __name__ == "__main__":
    main()
