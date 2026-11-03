"""
config.py
=========

Central configuration for the "Decentralized Crypto Governance?" replication package.

Paper
-----
Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
and Concentration in Ethereum Decision-Making." SSRN 4691000.

Why this file exists
---------------------
The original project's Stata (.do) and Python (.py) scripts each began with a hardcoded,
developer-specific working-directory line, e.g.:

    cd "C:/Users/<developer>/Box/Research/.../Ethereum_Governance_Project/..."
    os.chdir("C:/Users/<developer>/Box Sync/Ethereum Governance/...")

Three different developers each had their own Box sync path baked into ~15 different scripts
across the pipeline. This meant the pipeline could only ever run, unmodified, on one of those
three specific machines. Any new contributor (or, now, anyone attempting to replicate the
paper) had to hunt down and hand-edit every single hardcoded path before anything would run.

This module replaces ALL of that. Every script in this package should start with:

    from config import PROJECT_ROOT, DATA_RAW, DATA_INTERIM, DATA_PROCESSED, DATA_REFERENCE, \
        OUTPUT_FIGURES, OUTPUT_TABLES, PAPER_PDF

`PROJECT_ROOT` is resolved dynamically from this file's own location on disk (via
`pathlib.Path(__file__).resolve()`), so the package works out of the box on any machine,
in any directory, for any user -- no manual editing required, ever.

Directory layout
-----------------
    <PROJECT_ROOT>/
        code/                   <- this file lives at <PROJECT_ROOT>/code/config.py
        data/
            raw/                <- DATA_RAW: untouched source extracts (Stata .dta converted to
                                   .parquet, scraped API pulls, manually collected CSVs, etc.)
            interim/             <- DATA_INTERIM: partially cleaned / merged intermediate outputs
            processed/           <- DATA_PROCESSED: final, analysis-ready datasets
            reference/           <- DATA_REFERENCE: the ORIGINAL authors' published outputs
                                   (figures, tables, numbers copied from the SSRN paper/appendix)
                                   kept ONLY for diffing/verification against this reproduction's
                                   output. This is NOT a pipeline input -- nothing in code/ should
                                   ever read data/reference/ as part of a normal run; it exists
                                   purely so a verification script can compare "our Figure 8" to
                                   "their published Figure 8" side by side.
        output/
            figures/            <- OUTPUT_FIGURES: regenerated .png/.pdf figures
            tables/             <- OUTPUT_TABLES: regenerated .tex table fragments
        paper/                  <- PAPER_PDF lives here (the SSRN 4691000 PDF itself)

Usage
-----
    from config import DATA_RAW, OUTPUT_TABLES, ensure_dirs
    ensure_dirs()  # optional: create any directories that don't yet exist
    df = pl.read_parquet(DATA_RAW / "eip_registry" / "eips.parquet")

Design note on ensure_dirs()
-----------------------------
`ensure_dirs()` is deliberately NOT called automatically at import time. Auto-creating
directories as a side effect of `import config` is a bit too "magical" for a public academic
replication package -- a reader inspecting the code should be able to see exactly when and
where directories get created. Instead, each entry-point script should call `ensure_dirs()`
explicitly near the top of its `if __name__ == "__main__":` block (or at the very top of a
notebook), right where a reader would expect setup to happen. This module simply exposes the
tool; it does not use it unasked.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------
# This file lives at <PROJECT_ROOT>/code/config.py, so PROJECT_ROOT is two levels up
# from this file: config.py -> code/ -> <PROJECT_ROOT>/.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Data directories
# ---------------------------------------------------------------------------
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM: Path = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
# Original published outputs, for diffing/verification only -- NOT a pipeline input.
DATA_REFERENCE: Path = PROJECT_ROOT / "data" / "reference"

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------
OUTPUT_FIGURES: Path = PROJECT_ROOT / "output" / "figures"
OUTPUT_TABLES: Path = PROJECT_ROOT / "output" / "tables"

# ---------------------------------------------------------------------------
# Paper
# ---------------------------------------------------------------------------
# The SSRN 4691000 PDF. Filename is not enforced here since the exact filename of the
# downloaded PDF may vary; scripts that need the PDF directly should glob for "*.pdf"
# under PAPER_DIR if this exact name is not present.
PAPER_DIR: Path = PROJECT_ROOT / "paper"
PAPER_PDF: Path = PAPER_DIR / "Decentralized_Crypto_Governance.pdf"


def ensure_dirs() -> None:
    """
    Create every directory referenced by this config module, if it does not already exist.

    This is a convenience helper, not an import-time side effect (see the module docstring's
    "Design note on ensure_dirs()" for why). Call it explicitly from a script's entry point,
    e.g.:

        if __name__ == "__main__":
            ensure_dirs()
            ...

    It is safe to call repeatedly (uses `exist_ok=True`) and safe to call from multiple
    scripts in the same run.
    """
    dirs = (
        DATA_RAW,
        DATA_INTERIM,
        DATA_PROCESSED,
        DATA_REFERENCE,
        OUTPUT_FIGURES,
        OUTPUT_TABLES,
        PAPER_DIR,
    )
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Tiny smoke test: print the resolved paths so a user can sanity-check them on their
    # own machine without needing to read this file's source.
    print(f"PROJECT_ROOT      = {PROJECT_ROOT}")
    print(f"DATA_RAW          = {DATA_RAW}")
    print(f"DATA_INTERIM      = {DATA_INTERIM}")
    print(f"DATA_PROCESSED    = {DATA_PROCESSED}")
    print(f"DATA_REFERENCE    = {DATA_REFERENCE}")
    print(f"OUTPUT_FIGURES    = {OUTPUT_FIGURES}")
    print(f"OUTPUT_TABLES     = {OUTPUT_TABLES}")
    print(f"PAPER_PDF         = {PAPER_PDF}")
    ensure_dirs()
    print("All directories ensured to exist.")
