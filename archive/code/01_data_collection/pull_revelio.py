"""
pull_revelio.py
================

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Not part of that paper -- feeds the labor-market companion analysis
--------------------------------------------------------------------
This script has nothing to do with reproducing the paper itself. It is the original pull
script behind the three Revelio Labs files consumed by
`code/03_analysis/labor_market_effects/did_labor_market_effects.py` (pipeline stage 19), kept
here purely for provenance -- see that script's module docstring ("A NOTE ON PANDAS" section)
and `PIPELINE_TODO.md` section (vi) for the full story of what that analysis is and why it's
separate from the paper.

Replaces
--------
`Ethereum_Governance_Project/archive/Data/Data Gathering Code/pull_revelio.py` in the other
(messy, pre-conversion) project -- read in full and ported here with paths adapted to this
package's `config.py` conventions. The query logic, matching logic, and output columns are
unchanged.

==================================================================================
HISTORICAL / OPTIONAL -- NOT PART OF THE DEFAULT REPRODUCTION PIPELINE
==================================================================================
This script queries Revelio Labs' LinkedIn-derived panel through a **WRDS** (Wharton Research
Data Services) institutional license -- it needs a live WRDS account with Revelio access and
a saved `pgpass` credential (`%APPDATA%/postgresql/pgpass.conf`) to run at all, and neither
travels with this package. It is provided purely for methodological transparency -- a
documented, working record of how `data/raw/revelio/author_to_revelio_userid.parquet` and
`data/raw/revelio/revelio_user.parquet` (plus the un-enriched `revelio_positions.parquet`,
enriched separately by `enrich_revelio.py`) were originally pulled -- not meant to be re-run
as part of a normal reproduction.

Re-running it today would query Revelio's LIVE database, not the original point-in-time pull:
`revelio_user`'s own `updated_dt` field already spans 2021-01-16 through 2026-06-01 in the
frozen data, confirming this was always a live/recent pull rather than a fixed historical
snapshot (see `revelio_pull/data_layout_descriptive_stats.md`, note under `revelio_user`). A
fresh run would not reproduce the exact frozen files under `data/raw/revelio/` bit-for-bit,
and its output is therefore written to `data/interim/revelio_refetch/` -- never to
`data/raw/revelio/`, which holds the frozen, analysis-exact data -- so it can never be
confused with, or accidentally overwrite, the authoritative raw files.

Input
-----
`data/raw/revelio/_revelio_input.csv` -- the seed list of EIP/forum author names + candidate
LinkedIn profile URLs (`author_id`, `author_name`, `best_url`, `linkedin_slug`; 491 rows) that
this script matches against Revelio's `individual_user.profile_linkedin_url` to obtain a
Revelio `user_id` for each. This file's own provenance (how the candidate LinkedIn URLs were
originally assembled) is not documented anywhere in this package or the archived original --
treat it as a frozen, given input.

Output (if run)
----------------
    data/interim/revelio_refetch/author_to_revelio_userid.parquet
    data/interim/revelio_refetch/revelio_user.parquet
    data/interim/revelio_refetch/revelio_positions.parquet
    data/interim/revelio_refetch/revelio_education.parquet
    data/interim/revelio_refetch/revelio_skills.parquet

Requirements
------------
    wrds, polars
"""

import os
import sys
import urllib.parse
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from config import DATA_RAW, DATA_INTERIM, ensure_dirs

import wrds
import polars as pl

INPUT_PATH = DATA_RAW / "revelio" / "_revelio_input.csv"
OUTPUT_DIR = DATA_INTERIM / "revelio_refetch"

TABLES = {"user": "individual_user", "positions": "individual_positions",
          "education": "individual_user_education", "skills": "individual_user_skills"}


def url_variants(slug: str) -> set[str]:
    """Revelio stores 'linkedin.com/in/<slug>'; non-ASCII slugs are percent-encoded.

    Probe raw + percent-encoded + accent-folded so the indexed equality match catches all.
    """
    out = {f"linkedin.com/in/{slug}"}
    enc = urllib.parse.quote(slug, safe="-_.~")
    out.add(f"linkedin.com/in/{enc}")
    out.add(f"linkedin.com/in/{enc.lower()}")
    fold = "".join(c for c in unicodedata.normalize("NFKD", slug) if not unicodedata.combining(c))
    out.add(f"linkedin.com/in/{fold}")
    return out


def main():
    ensure_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pgpass = Path(os.environ["APPDATA"]) / "postgresql" / "pgpass.conf"
    user = pgpass.read_text().strip().split(":")[3]
    db = wrds.Connection(wrds_username=user)

    inp = pl.read_csv(INPUT_PATH)
    cand2slug: dict[str, str] = {}
    for row in inp.iter_rows(named=True):
        if row["linkedin_slug"]:
            for v in url_variants(row["linkedin_slug"]):
                cand2slug[v] = row["linkedin_slug"]
    mapdf = pl.DataFrame({"profile_linkedin_url": list(cand2slug), "linkedin_slug": list(cand2slug.values())})

    # ---- match profiles -> user_id ----
    m = db.raw_sql("SELECT user_id, profile_linkedin_url FROM revelio.individual_user "
                    "WHERE profile_linkedin_url = ANY(%(u)s)", params={"u": list(cand2slug)})
    m = pl.from_pandas(m).join(mapdf, on="profile_linkedin_url", how="left").unique(["user_id", "linkedin_slug"])
    cw = inp.join(m, on="linkedin_slug", how="left")
    cw.write_parquet(OUTPUT_DIR / "author_to_revelio_userid.parquet", compression="zstd")
    cw.write_csv(OUTPUT_DIR / "author_to_revelio_userid.csv")
    matched = cw.filter(pl.col("user_id").is_not_null())
    ids = [int(x) for x in m["user_id"].unique().to_list()]
    print(f"matched {matched.height}/{inp.height} author rows -> {len(ids)} Revelio users")

    # author_id link key
    key = (matched.select(["author_id", "author_name", "user_id"]).unique()
                  .with_columns(pl.col("user_id").cast(pl.Int64)))

    # ---- pull each table, add author_id as leading column ----
    for label, tbl in TABLES.items():
        df = db.raw_sql(f"SELECT * FROM revelio.{tbl} WHERE user_id = ANY(%(i)s)", params={"i": ids})
        df = pl.from_pandas(df).with_columns(pl.col("user_id").cast(pl.Int64))
        j = key.join(df, on="user_id", how="inner")
        cols = ["author_id", "author_name"] + [c for c in j.columns if c not in ("author_id", "author_name")]
        j.select(cols).write_parquet(OUTPUT_DIR / f"revelio_{label}.parquet", compression="zstd")
        print(f"  revelio_{label}: {j.height} rows, {j.width} cols")

    db.close()
    print("DONE ->", OUTPUT_DIR)


if __name__ == "__main__":
    main()
