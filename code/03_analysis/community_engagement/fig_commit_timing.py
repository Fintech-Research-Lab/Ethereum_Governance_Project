"""
fig_commit_timing.py
======================

Reproduces **Figure 14** (`\\label{fig:commit_total}`, "Number of GitHub Commits by EIP") and
**Figure 15** (`\\label{fig:attendees}`, "AllCoreDevs Calls Attendees", panels a-b) of the current
manuscript, `paper/latex/MS_R2.tex`. Figure numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date. The `\\label`s are the
stable identifiers.

Paper section: Concentration in EIP Discussion (dev-call attendance and EIP-authorship overlap with
the AllCoreDevs community).

Ported from: `Analysis\\Commit Analysis Around Meetings\\eip_commit_around_devcalls.do` (read in full,
start to finish, before writing any of this file).

Outputs
-------
- `output/figures/figure_13_commits_per_eip.png`      -- original `commit_total.png`
- `output/figures/figure_14a_attendees_by_year.png`    -- original `attendees_year.png`
- `output/figures/figure_14b_attendance_vs_authorship.png` -- original `attended_eip.png`

This script originally also fit an event-study regression of commit activity around AllCoreDevs
calls and plotted its weekly coefficients (`figure_15_commits_around_devcalls.png`, the old
pre-revision paper's "Figure 15: EIP GitHub Commits around Dev Calls"). That figure is not
referenced anywhere in the current `MS_R2.tex` (confirmed via a full-text search), so the
regression and plot are no longer generated here. See `PIPELINE_TODO.md` for the removal record.

Cross-script dependency
--------------------------
This script needs `data/interim/eip_by_authors.parquet`, produced as a side-output of
`code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py::make_top10_author_charts`
(that script's docstring documents the exact schema this file relies on: columns `author`,
`id_author`, `n_eip`, `n_eip_final`, `n_eip_imp`, one row per author).

Self-contained attendee/author lookups
------------------------------------------
This script builds two lookups locally rather than depending on
`code/02_data_preparation/name_cleaning_pipeline.py`, since the shape it needs differs from what
that script produces for its own callers:
  1. A meeting-labeled flat attendee list (`_build_flat_list_with_meetings()`), pairing each
     attendee name with the meeting they attended -- needed here to attach a meeting date to each
     attendee appearance, which `name_cleaning_pipeline.py::flatten_meeting_attendees()` doesn't
     retain (its own caller only needs the flattened names). This reuses the shared `clean_text()` /
     `_read_latin1_csv_as_utf8()` helpers from `clean_eip_authors.py`, applying the attendee-name
     correction map `Mapping_File.csv` (a different, purpose-specific mapping from the
     `names_to_change*_post_manual.csv` cascade `name_cleaning_pipeline.py::clean_attendees()` uses).
  2. An attendee/author overlap pool (`_authors_pool()` / `make_attendance_vs_authorship()`),
     needed for Figure 15b -- algebraically equivalent to a plain inner join of the cleaned
     attendee-name list against the EIP-author-name pool.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path
# `02_data_preparation` starts with a digit and is therefore not a valid dotted-import package name
# (see `fig_company_concentration.py`'s module docstring for the same note re: `03_analysis`) --
# add that specific directory to sys.path directly instead.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02_data_preparation"))

from config import DATA_INTERIM, DATA_PROCESSED, DATA_RAW, OUTPUT_FIGURES, ensure_dirs
from clean_eip_authors import clean_text, _read_latin1_csv_as_utf8  # noqa: E402

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
RAW_DEV_CALLS_ATTENDEES_CSV = DATA_RAW / "meetings" / "dev_calls_attendees_standardized_v2.csv"
CALLS_CSV = DATA_RAW / "meetings" / "calls_updated_standardized.csv"
MAPPING_FILE_CSV = DATA_RAW / "name_cleaning_manual" / "Mapping_File.csv"
RAW_AUTHOR_ROSTER_CSV = DATA_RAW / "eip_registry" / "unique_author_names_with_id.csv"
EIP_COMMIT_XLSX = DATA_RAW / "commits" / "eip_commit_beg.xlsx"
CROSS_SECTIONAL_PATH = DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"
EIP_BY_AUTHORS_PATH = DATA_INTERIM / "eip_by_authors.parquet"

N_AUTHOR_SLOTS = 15


# =============================================================================
# Figure 13: commit_total.png -> figure_13_commits_per_eip.png
# =============================================================================
def make_commits_per_eip() -> None:
    """
    Replicates the "NUMBER OF COMMITS BY EIP, BROKEN DOWN BY AUTHORS AND CONTRIBUTORS" block:
        import excel eip_commit_beg.xlsx ...
        rename Username github_username; rename EIP eip_n
        drop if github_username == "eth-bot"
        gen author_dum = (Author_Id ~=.)
        gen ncommit = 1
        collapse (count) ncommit , by(eip_n author_dum)
        reshape wide ncommit, i(eip_n) j(author_dum)
        ...
        gen frac = ncommit1/ncommit_tot
        replace ncommit_tot = 30 if ncommit_tot > 30
        bys ncommit_tot: egen mean_frac = mean(frac)
        collapse (percent) eip_n,  by(ncommit_tot mean_frac)
        gen eip_n1 = eip_n * mean_frac / 100
        gen eip_n0 = eip_n * (1-mean_frac) /100
        ... stacked bar chart, x = ncommit_tot (capped at "30+"), y = eip_n1/eip_n0 stacked ...
    """
    commit = pl.read_excel(EIP_COMMIT_XLSX)
    commit = commit.rename({"Username": "github_username", "EIP": "eip_n"})
    commit = commit.filter(pl.col("github_username") != "eth-bot")
    commit = commit.with_columns(pl.col("Author_Id").is_not_null().cast(pl.Int8).alias("author_dum"))

    counts = commit.group_by(["eip_n", "author_dum"]).agg(pl.len().alias("ncommit"))
    wide = counts.pivot(values="ncommit", index="eip_n", columns="author_dum").fill_null(0)

    rename_map: dict = {}
    for col in wide.columns:
        if col in ("0", 0):
            rename_map[col] = "ncommit0"
        elif col in ("1", 1):
            rename_map[col] = "ncommit1"
    wide = wide.rename(rename_map)
    if "ncommit0" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("ncommit0"))
    if "ncommit1" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("ncommit1"))

    wide = wide.with_columns((pl.col("ncommit0") + pl.col("ncommit1")).alias("ncommit_tot"))
    wide = wide.with_columns((pl.col("ncommit1") / pl.col("ncommit_tot")).alias("frac"))

    print(
        f"[fig_commit_timing] Figure 13 summary -- ncommit_tot: mean={wide['ncommit_tot'].mean():.2f}, "
        f"frac: mean={wide['frac'].mean():.4f}"
    )

    capped = wide.with_columns(
        pl.when(pl.col("ncommit_tot") > 30).then(30).otherwise(pl.col("ncommit_tot")).alias("ncommit_tot_c")
    )
    capped = capped.with_columns(pl.col("frac").mean().over("ncommit_tot_c").alias("mean_frac"))

    total_n = capped.height
    hist = capped.group_by("ncommit_tot_c").agg(pl.len().alias("n"), pl.col("mean_frac").first().alias("mean_frac"))
    hist = hist.with_columns((100.0 * pl.col("n") / total_n).alias("pct_eip"))
    hist = hist.with_columns(
        (pl.col("pct_eip") * pl.col("mean_frac")).alias("eip_n1"),
        (pl.col("pct_eip") * (1 - pl.col("mean_frac"))).alias("eip_n0"),
    )
    hist = hist.sort("ncommit_tot_c")

    ncommit_vals = hist.get_column("ncommit_tot_c").to_list()
    labels = [str(int(v)) if v < 30 else "30+" for v in ncommit_vals]
    eip_n1 = hist.get_column("eip_n1").to_list()
    eip_n0 = hist.get_column("eip_n0").to_list()

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(labels))
    ax.bar(x, eip_n1, label="EIP Authors")
    ax.bar(x, eip_n0, bottom=eip_n1, label="EIP Contributors")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=6)
    ax.set_xlabel("Number of Commits")
    ax.set_ylabel("% of EIPs")
    ax.legend()
    fig.tight_layout()
    out_path = OUTPUT_FIGURES / "figure_13_commits_per_eip.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[fig_commit_timing] Wrote {out_path}")


# =============================================================================
# Figures 14a/14b: dev-call attendee analysis
# =============================================================================
def _build_flat_list_with_meetings() -> pl.DataFrame:
    """
    Flatten the dev-call attendee roster into one row per (meeting, attendee) appearance, keeping
    the per-row `Meeting` label (see module docstring). Reuses `clean_text()` /
    `_read_latin1_csv_as_utf8()` from `clean_eip_authors.py` for the same name-cleaning rule used
    elsewhere in this package.

    Returns columns `meeting` and `attendees` (raw, not yet corrected via `Mapping_File.csv`).
    """
    dat = _read_latin1_csv_as_utf8(RAW_DEV_CALLS_ATTENDEES_CSV)

    meetings: list[str] = []
    attendees: list[str] = []
    for meeting, attendees_field in zip(dat["Meeting"].to_list(), dat["Attendees"].to_list()):
        if attendees_field is None:
            continue
        tokens = attendees_field.split(",")
        for tok in tokens:
            cleaned = clean_text(tok)
            if cleaned is not None:
                meetings.append(meeting)
                attendees.append(cleaned)
    return pl.DataFrame({"meeting": meetings, "attendees": attendees})


def _load_mapping_file() -> pl.DataFrame:
    """
    Port of the `Mapping_File.csv` load block:
        insheet using ".../Mapping_File.csv", names clear
        rename original_name full_name
        replace full_name = "Åukasz Rozmej" if full_name == "ÃÂukasz Rozmej"
        replace full_name = subinstr(full_name,"ÃÂ", "Å",.)
        replace full_name = subinstr(full_name,"ÃÂ³", "Ã³",.)
        replace full_name = subinstr(full_name,"ÃÂ", "Å",.)
        replace full_name = subinstr(full_name,"ÃÂ©", "Ã©",.)
        replace full_name = subinstr(full_name,"ÃÂ¡", "Ã¡",.)
        replace full_name = subinstr(full_name,"ÃÂ¶", "Ã¶",.)
        rename full_name attendees
        drop v1
        duplicates drop

    The exact sequence of `subinstr` calls is preserved verbatim -- including the literal repeat of
    the "ÃÂ" -> "Å" substitution -- rather than being "cleaned up" as redundant.

    Returns a 2-column frame: `attendees` (the raw/original name, post mojibake-fix) and
    `replace_name` (the corrected name).
    """
    df = pl.read_csv(MAPPING_FILE_CSV)
    df = df.select(["Original_Name", "Replace_Name"]).rename(
        {"Original_Name": "attendees", "Replace_Name": "replace_name"}
    )
    df = df.with_columns(
        pl.when(pl.col("attendees") == "ÃÂukasz Rozmej")
        .then(pl.lit("Åukasz Rozmej"))
        .otherwise(pl.col("attendees"))
        .alias("attendees")
    )
    for old, new in [
        ("ÃÂ", "Å"),
        ("ÃÂ³", "Ã³"),
        ("ÃÂ", "Å"),  # verbatim repeat from the original -- see docstring
        ("ÃÂ©", "Ã©"),
        ("ÃÂ¡", "Ã¡"),
        ("ÃÂ¶", "Ã¶"),
    ]:
        df = df.with_columns(pl.col("attendees").str.replace_all(old, new, literal=True).alias("attendees"))
    return df.unique()


def _build_attendee_meeting_panel() -> pl.DataFrame:
    """
    Port of the "bring in meeting date" + Mapping_File-correction + flat-list-merge block, through
    the meeting-date merge. Returns one row per surviving (meeting, name) appearance, with columns
    `meeting`, `name`, `datem` (meeting year, null if unmatched), `date`, `date2`.
    """
    calls = pl.read_csv(CALLS_CSV)
    meetdate = calls.select(
        pl.col("Meeting").alias("meeting"),
        pl.col("Date").str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias("date2"),
        pl.col("Date").alias("date"),
    )
    meetdate = meetdate.with_columns(pl.col("date2").dt.year().alias("datem"))
    meetdate = meetdate.filter(pl.col("datem") >= 2015)  # `drop if datem < 2015`

    mapping = _load_mapping_file()
    flat = _build_flat_list_with_meetings()
    flat = flat.filter(pl.col("meeting") != "Meeting Template")

    joined = flat.join(mapping, on="attendees", how="left").rename({"replace_name": "name"}).drop("attendees")
    # `drop if _merge==2` (Mapping_File-only rows) is a no-op for a left join from `flat`'s
    # perspective; `drop if name==""` below reproduces the original's net effect: only flat-list
    # appearances whose raw name has an EXACT entry in Mapping_File.csv survive.
    joined = joined.filter(pl.col("name").is_not_null() & (pl.col("name") != ""))

    merged = joined.join(meetdate, on="meeting", how="left")  # `merge m:1 meeting using temp_meetdate`, drop _merge==2
    print(
        f"[fig_commit_timing] Attendee panel -- unique meetings: {merged.get_column('meeting').n_unique()}, "
        f"unique names: {merged.get_column('name').n_unique()}"
    )
    return merged


def make_attendees_by_year(panel: pl.DataFrame) -> None:
    """
    Replicates:
        bys meeting: egen n_attendees = nvals(name)
        preserve
        duplicates drop meeting datem date date2, force
        bys datem: egen n_attendees_year = mean(n_attendees)
        ... graph bar n_attendees_year, over(datem) ...
    """
    n_attendees = panel.group_by("meeting").agg(pl.col("name").n_unique().alias("n_attendees"))
    meeting_meta = panel.select(["meeting", "datem"]).unique()
    per_meeting = meeting_meta.join(n_attendees, on="meeting")

    year_avg = (
        per_meeting.filter(pl.col("datem").is_not_null())
        .group_by("datem")
        .agg(pl.col("n_attendees").mean().alias("n_attendees_year"))
        .sort("datem")
    )

    years = year_avg.get_column("datem").to_list()
    vals = year_avg.get_column("n_attendees_year").to_list()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(years, vals)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Attendees per Meeting (avg)")

    if 2023 in years:
        idx2023 = years.index(2023)
        ax.text(
            2023,
            vals[idx2023] + 0.02 * ax.get_ylim()[1],
            "*",
            ha="center",
            va="bottom",
            fontsize=16,
            fontweight="bold",
        )

    fig.tight_layout()
    out_path = OUTPUT_FIGURES / "figure_14a_attendees_by_year.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[fig_commit_timing] Wrote {out_path}")


def _meetings_attended(panel: pl.DataFrame) -> pl.DataFrame:
    """`gen one=1 / collapse (count) one, by(name) / rename name attendee_name` -- total number of
    (meeting, name) appearances per name, i.e. the number of meetings that name attended."""
    return (
        panel.group_by("name")
        .agg(pl.len().alias("meetings_attended"))
        .rename({"name": "attendee_name"})
        .sort("meetings_attended", descending=True)
    )


def _authors_pool() -> pl.Series:
    """
    Melt the wide `author{n}_id` columns of the cross-sectional dataset, join to the raw author
    roster on `author_id`, and take the unique `Full_Name` -- the pool of every EIP-author name.
    """
    cs = pl.read_parquet(CROSS_SECTIONAL_PATH)
    roster = pl.read_csv(RAW_AUTHOR_ROSTER_CSV, columns=["author_id", "Full_Name"])

    id_cols = [f"author{a}_id" for a in range(1, N_AUTHOR_SLOTS + 1) if f"author{a}_id" in cs.columns]
    long = pl.concat([cs.select(pl.col(c).alias("author_id")) for c in id_cols], how="vertical").filter(
        pl.col("author_id").is_not_null()
    )
    joined = long.join(roster, on="author_id", how="left")
    return joined.get_column("Full_Name").unique().drop_nulls()


def make_attendance_vs_authorship(panel: pl.DataFrame) -> None:
    """
    Figure 14b: for each unique meeting attendee who is also an EIP author, plot meetings attended
    against EIP count (with a fitted line), labeling notably active people (more than 40 meetings
    attended or more than 20 EIPs authored).
    """
    meetings_attended = _meetings_attended(panel)
    authors_pool = set(_authors_pool().to_list())

    matched = meetings_attended.filter(pl.col("attendee_name").is_in(list(authors_pool)))
    matched = matched.with_columns(pl.col("attendee_name").alias("author_name"))

    eip_by_authors = pl.read_parquet(EIP_BY_AUTHORS_PATH).rename({"author": "author_name"})
    final = eip_by_authors.join(matched.select(["author_name", "meetings_attended"]), on="author_name", how="inner")

    final = final.with_columns(
        pl.when((pl.col("meetings_attended") > 40) | (pl.col("n_eip") > 20))
        .then(pl.col("author_name"))
        .otherwise(None)
        .alias("label")
    )

    x = final.get_column("n_eip").to_numpy().astype(float)
    y = final.get_column("meetings_attended").to_numpy().astype(float)
    labels = final.get_column("label").to_list()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, color="black", s=15)
    if len(x) > 1:
        coeffs = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, coeffs[0] * xs + coeffs[1], color="steelblue")
    for xi, yi, lbl in zip(x, y, labels):
        if lbl is not None:
            ax.annotate(lbl, (xi, yi), fontsize=6, ha="center", va="bottom")

    ax.set_xlabel("EIPs Co-Authored")
    ax.set_ylabel("Meetings Attended")
    fig.tight_layout()
    out_path = OUTPUT_FIGURES / "figure_14b_attendance_vs_authorship.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[fig_commit_timing] Wrote {out_path}")


def main() -> None:
    ensure_dirs()

    make_commits_per_eip()

    panel = _build_attendee_meeting_panel()
    make_attendees_by_year(panel)
    make_attendance_vs_authorship(panel)


if __name__ == "__main__":
    main()
