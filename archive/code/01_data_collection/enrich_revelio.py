"""
enrich_revelio.py
==================

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Not part of that paper -- feeds the labor-market companion analysis
--------------------------------------------------------------------
Like `pull_revelio.py`, this script has nothing to do with reproducing the paper. It joins
dimension/lookup tables onto the raw Revelio pull to produce the enriched positions file
consumed by `code/03_analysis/labor_market_effects/did_labor_market_effects.py` (pipeline
stage 19) -- see that script's docstring and `PIPELINE_TODO.md` section (vi).

Replaces
--------
`Ethereum_Governance_Project/archive/Data/Data Gathering Code/enrich_revelio.py` in the other
(messy, pre-conversion) project -- read in full and ported here with paths adapted to this
package's `config.py` conventions. The join logic and output columns are unchanged.

==================================================================================
HISTORICAL / OPTIONAL -- NOT PART OF THE DEFAULT REPRODUCTION PIPELINE
==================================================================================
Run after `pull_revelio.py` (needs its `revelio_positions.parquet` and
`revelio_education.parquet` output). Like that script, it needs a live WRDS account with
Revelio access and is not meant to be re-run as part of a normal reproduction -- see
`pull_revelio.py`'s module docstring for why a fresh run would not reproduce the frozen
`data/raw/revelio/revelio_positions_enriched.parquet` bit-for-bit. Output goes to
`data/interim/revelio_refetch/`, alongside `pull_revelio.py`'s own output -- never to
`data/raw/revelio/`.

Joins added to positions
-------------------------
    company_mapping    (rcid)             -> co_* firmographic columns
    role_lookup_v2     (role_k1500_v2)    -> job_category_v2, role_k50..k1500_v2
    role_lookup_v3     (role_k17000_v3)   -> onet_code/onet_title, role_k10..k17000_v3
    regions            (region)           -> region_country

Joins added to education
--------------------------
    school_mapping     (rsid)             -> sch_* school firmographic columns

Output (if run)
----------------
    data/interim/revelio_refetch/revelio_company_mapping.parquet
    data/interim/revelio_refetch/revelio_role_lookup_v2.parquet
    data/interim/revelio_refetch/revelio_role_lookup_v3.parquet
    data/interim/revelio_refetch/revelio_regions.parquet
    data/interim/revelio_refetch/revelio_school_mapping.parquet
    data/interim/revelio_refetch/revelio_positions_enriched.parquet
    data/interim/revelio_refetch/revelio_education_enriched.parquet

Requirements
------------
    wrds, polars
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from config import DATA_INTERIM, ensure_dirs

import wrds
import polars as pl

OUTPUT_DIR = DATA_INTERIM / "revelio_refetch"


def anylist(df: pl.DataFrame, col: str) -> list:
    return df[col].drop_nulls().unique().to_list()


def pref(df: pl.DataFrame, prefix: str, keep: set[str]) -> pl.DataFrame:
    return df.rename({c: prefix + c for c in df.columns if c not in keep})


def main():
    ensure_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pgpass = Path(os.environ["APPDATA"]) / "postgresql" / "pgpass.conf"
    user = pgpass.read_text().strip().split(":")[3]
    db = wrds.Connection(wrds_username=user)

    pos = pl.read_parquet(OUTPUT_DIR / "revelio_positions.parquet")
    edu = pl.read_parquet(OUTPUT_DIR / "revelio_education.parquet")

    rcids = list(set(anylist(pos, "rcid")) | set(anylist(pos, "ultimate_parent_rcid")))
    rk2   = anylist(pos, "role_k1500_v2")
    rk3   = anylist(pos, "role_k17000_v3")
    rsids = anylist(edu, "rsid")
    print(f"keys: {len(rcids)} rcids, {len(rk2)} role_v2, {len(rk3)} role_v3, {len(rsids)} rsids")

    def pull(sql, params):
        return pl.from_pandas(db.raw_sql(sql, params=params))

    comp = pull("SELECT * FROM revelio.company_mapping WHERE rcid = ANY(%(k)s)", {"k": [int(x) for x in rcids]})
    v2   = pull("SELECT * FROM revelio.individual_role_lookup_v2 WHERE role_k1500_v2 = ANY(%(k)s)", {"k": rk2})
    v3   = pull("SELECT * FROM revelio.individual_role_lookup_v3 WHERE role_k17000_v3 = ANY(%(k)s)", {"k": rk3})
    reg  = pull("SELECT * FROM revelio.regions", {})
    sch  = pull("SELECT * FROM revelio.school_mapping WHERE rsid = ANY(%(k)s)", {"k": [int(x) for x in rsids]})

    # save dimension tables (filtered)
    for name, d in [("company_mapping", comp), ("role_lookup_v2", v2),
                    ("role_lookup_v3", v3), ("regions", reg), ("school_mapping", sch)]:
        d.write_parquet(OUTPUT_DIR / f"revelio_{name}.parquet", compression="zstd")
        print(f"  dim revelio_{name}: {d.height} rows")

    # ---- enrich positions ----
    p = pos.join(pref(comp, "co_", {"rcid"}).unique("rcid"), on="rcid", how="left")
    p = p.join(v2.unique("role_k1500_v2"), on="role_k1500_v2", how="left")
    p = p.join(v3.drop("onet_code").unique("role_k17000_v3"), on="role_k17000_v3", how="left")
    p = p.join(reg.rename({"country": "region_country"}).unique("region"), on="region", how="left")
    p.write_parquet(OUTPUT_DIR / "revelio_positions_enriched.parquet", compression="zstd")
    print(f"  revelio_positions_enriched: {p.height} rows, {p.width} cols")

    # ---- enrich education ---- (cast rsid on both sides: education stores it as float w/ nulls)
    edu = edu.with_columns(pl.col("rsid").cast(pl.Int64, strict=False))
    sch = sch.with_columns(pl.col("rsid").cast(pl.Int64, strict=False))
    e = edu.join(pref(sch, "sch_", {"rsid"}).unique("rsid"), on="rsid", how="left")
    e.write_parquet(OUTPUT_DIR / "revelio_education_enriched.parquet", compression="zstd")
    print(f"  revelio_education_enriched: {e.height} rows, {e.width} cols")

    db.close()
    print("ENRICH DONE ->", OUTPUT_DIR)


if __name__ == "__main__":
    main()
