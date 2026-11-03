"""
run_pipeline.py
================

Master orchestrator for the reproduction package for:

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance?
    Transparency and Concentration in Ethereum Decision-Making." SSRN 4691000.
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4691000

What this script does
----------------------
Runs, in dependency order, every data-preparation and analysis script in this package
(everything under `code/02_data_preparation/` and `code/03_analysis/`), producing every
intermediate dataset, every figure (`output/figures/`), and every table (`output/tables/`)
in the paper's reproduction.

`archive/code/01_data_collection/` is intentionally NOT included in this pipeline. Those scripts
are historical/optional live-fetch documentation of how the raw data under `data/raw/`
was originally collected (web scraping, API pulls) -- see each of their own module
docstrings. Re-running them would attempt to re-fetch data from the live internet (and,
for some sources, would not even reproduce the ORIGINAL historical snapshot -- see e.g.
`fig_adoption.py`'s "Frozen-data note"). Every script actually orchestrated below reads
only from `data/raw/` (already-collected, frozen inputs), `data/interim/`, or
`data/processed/`.

The pipeline DAG
-----------------
Seventeen stages, run strictly in the order below. One genuine circular dependency in the
original (messy, hand-run) project is resolved here via an explicit TWO-PASS design --
`build_cross_sectional_dataset.py` is invoked TWICE (stages 3 and 6).

Figure/Table numbers below are a snapshot as of the date in `docs/figure_table_index.md`
(current manuscript: `paper/latex/MS_R2.tex`, still under revision) -- they shift
as the paper changes; see that file for the current numbering and each `\label{}`.

    Stage  Script                                    Produces (key outputs)
    -----  ----------------------------------------  ------------------------------------
     1.    clean_eip_authors.py                       data/interim/ethereum_cross_sectional_data_beg.parquet
     2.    name_cleaning_pipeline.py                  data/interim/unique_{attendees,clients,
                                                       contributors,authors}_final.parquet
     3.    build_cross_sectional_dataset.py  [PASS 1] data/processed/ethereum_cross_sectional_data.{parquet,csv}
           (bootstrap -- centrality/FEM columns null; these files don't exist yet)
     4.    fig_network_centrality.py                  data/interim/centrality_all.parquet + Figures 9, 12
     5.    fig_fem_engagement.py                      data/interim/fem_data_for_regressions.parquet + Figure 13
     6.    build_cross_sectional_dataset.py  [PASS 2] data/processed/ethereum_cross_sectional_data.{parquet,csv}
           (FINAL -- overwrites pass 1's output now that centrality_all.parquet and
            fem_data_for_regressions.parquet both exist; this is the dataset every
            downstream stage below actually depends on)
     7.    fig_eip_trends_and_concentration.py         Figures 2, 7, 8, 10, 11 + data/interim/eip_by_authors.parquet
     8.    fig_readability_and_status.py               Figure 5
     9.    fig_anonymity.py                            Figure 6
    10.    fig_company_concentration.py                Figure 20 (panels a-c), Figure 21
    11.    fig_client_concentration.py                 Figure 16, Figure 20 (panel d)
    12.    fig_commit_timing.py                        Figure 14, Figure 15 (panels a-b)
           (needs data/interim/eip_by_authors.parquet from stage 7)
    13.    fig_adoption.py                             Figures 18, 19 (independent of everything else)
    14.    fig_abnormal_returns.py                     Figure 3, Table 2 (needs the FINAL dataset, stage 6)
    15.    table1_summary_stats.py                     Table 1
    16.    table4_participation_summary.py             Table 4 (needs stages 5 and 6)
    17.    did_labor_market_effects.py                 Table 3 (one combined table: Panel A balance,
                                                       Panel B seniority, Panel C log comp) + Figure 4
                                                       (EIP_W2_EventStudy_Seniority.png and
                                                       EIP_W2_EventStudy_LogComp.png). Reads only
                                                       data/raw/eip_registry/ + data/raw/revelio/,
                                                       independent of stages 1-16. Needs a local WRDS/
                                                       Revelio data pull -- see README.md's "Data
                                                       availability" section; not runnable out of the
                                                       box from what's in this public repo.

Three scripts that used to be stages here -- `fig_venn_diagram.py` (Figure 5),
`table3_finalization_regressions.py` (Table 3 + Figure 19), and `table2_fem_regressions.py`
(Table 2) -- were moved to `archive/code/` once none of their outputs turned out to be
`\includegraphics`'d or `\input` anywhere in the current paper (`MS_R2.tex`), confirmed by
grepping its LaTeX source directly, not merely inferred. `table1_summary_stats.py` used to
import `build_pca_indices`/`add_implemented_column` from `table3_finalization_regressions.py`
for two Table 1 rows (the PCA-index rows); those two rows had themselves already been cut
from the published `Tables/summstat.tex` at some point, so `table1_summary_stats.py` was
narrowed to the 8 variables actually in the published table and the small
`add_implemented_column` logic it still needs was inlined directly, removing the only real
code dependency on `table3_finalization_regressions.py` and clearing the way to archive it.
See `archive/README.md` for the full before/after and `PIPELINE_TODO.md` for the FEM
raw-data-source change that prompted this audit.

`table4_participation_summary.py` was added afterward: it was first explored as an
off-pipeline side analysis of a new GitHub comment/review data source
(`data/raw/github/github_activity_clean.csv`), then promoted into the paper as Table 4 and
into this orchestrator as a real stage -- see `PIPELINE_TODO.md` for that history.

A separate quarterly robustness check for the labor-market analysis,
`did_labor_market_effects_quarterly.py`, exists alongside `did_labor_market_effects.py` but
is NOT a pipeline stage here (it was written as a standalone side analysis, run directly,
not through this orchestrator) -- its result is cited in a footnote in `MS_R2.tex`, even
though no table/figure of its own is embedded.

ASCII dependency sketch (arrows = "must run before"):

    clean_eip_authors ---------------------------\
                                                    v
    name_cleaning_pipeline (indep.) ---------> build_cross_sectional [PASS 1]
                                                    |         |
                                    +---------------+         +----------------+
                                    v                                          v
                        fig_network_centrality                        fig_fem_engagement
                     (writes centrality_all.parquet)          (writes fem_data_for_regressions.parquet)
                                    \                                          /
                                     +---------------------+-------------------+
                                                            v
                                          build_cross_sectional [PASS 2 / FINAL]
                                                            |
        +--------------+--------------+--------------+-----+--------------+--------------+
        v              v              v              v                    v              v
  eip_trends   readability_status  anonymity   company_conc         client_conc   abnormal_returns
        |                                                                                 ^
        v                                                                                 |
  commit_timing (needs eip_by_authors.parquet from eip_trends) -------------------------- +
                                                                                            |
  adoption (fully independent; slotted in for a linear read-through) -------------------- +
                                                                                            v
                                                                            table1_summary_stats
                                                                                            |
                                                                                            v
                                                                    table4_participation_summary
                                                                    (needs stages 5 and 6)

  did_labor_market_effects (fully independent of the whole DAG above -- reads only
  data/raw/eip_registry/ and data/raw/revelio/; slotted in last so it doesn't interrupt
  the read-through of the paper's own 16 stages)

Corrections made to the originally-proposed execution order, after reading the actual
scripts (documented per the task instructions)
----------------------------------------------------------------------------------------
None at the time this orchestrator was first written. See the note above this DAG for the
later removal of three stages whose outputs turned out not to be part of the current paper.
  - All distinct scripts expose a clean, no-required-argument, importable `main()`
    function. This orchestrator therefore imports every module and calls its `main()`
    directly (never `subprocess.run`) for cleaner tracebacks within one Python process.
  - `fig_abnormal_returns.py::main()` takes two optional keyword arguments
    (`event_type="meeting"`, `use_spy_cache=True`); it is called here with no
    arguments, using its defaults.
`did_labor_market_effects.py` was added afterward, as a separate companion analysis that the
paper later came to cite directly; it also exposes a plain `main()` and is run the same way
as the other stages.

Usage
-----
    python code/run_pipeline.py                 # run the full pipeline
    python code/run_pipeline.py --list           # print all stages and exit
    python code/run_pipeline.py --skip-existing  # skip a stage if its expected output
                                                  # file(s) already exist on disk
    python code/run_pipeline.py --stage fig_anonymity   # run just one named stage

The pipeline STOPS on the first stage failure by default (later stages almost certainly
depend on earlier ones) and always prints a final summary of which stages succeeded,
failed, or were skipped.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))  # add code/ to sys.path

from config import (  # noqa: E402
    DATA_INTERIM,
    DATA_PROCESSED,
    OUTPUT_FIGURES,
    OUTPUT_TABLES,
    ensure_dirs,
)


# =============================================================================
# Pipeline stage definitions
# =============================================================================
@dataclass
class Stage:
    """One step of the pipeline."""

    name: str  # short, unique, used by --stage
    module_path: str  # dotted-ish path used to import via importlib (see _run_stage)
    description: str  # human-readable one-liner shown in --list / progress banners
    # Expected output file(s) this stage produces -- used only by --skip-existing to
    # decide whether the stage can be skipped. Not exhaustive of every file a stage
    # writes; just enough to detect "this stage has clearly already been run."
    expected_outputs: list[Path] = field(default_factory=list)
    # Extra banner text printed immediately before this stage runs (used for the two
    # build_cross_sectional_dataset.py passes, to explain WHY it runs twice).
    banner_note: str = ""


PIPELINE_STAGES: list[Stage] = [
    Stage(
        name="clean_eip_authors",
        module_path="02_data_preparation.clean_eip_authors",
        description="Build the per-EIP author spine (Author1..Author15 / author{n}_id) from the raw EIP registry.",
        expected_outputs=[DATA_INTERIM / "ethereum_cross_sectional_data_beg.parquet"],
    ),
    Stage(
        name="name_cleaning_pipeline",
        module_path="02_data_preparation.name_cleaning_pipeline",
        description="Fuzzy-match name cleaning for attendees/clients/contributors/authors (4 final lists).",
        expected_outputs=[
            DATA_INTERIM / "unique_attendees_final.parquet",
            DATA_INTERIM / "unique_clients_final.parquet",
            DATA_INTERIM / "unique_contributors_final.parquet",
            DATA_INTERIM / "unique_authors_final.parquet",
        ],
    ),
    Stage(
        name="build_cross_sectional_dataset_pass1",
        module_path="02_data_preparation.build_cross_sectional_dataset",
        description="[PASS 1/2: BOOTSTRAP] Merge ~10 raw sources into the cross-sectional dataset "
        "WITHOUT centrality/FEM data (those files don't exist on disk yet).",
        expected_outputs=[DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"],
        banner_note=(
            "PASS 1 of 2 (bootstrap): data/interim/centrality_all.parquet and "
            "data/interim/fem_data_for_regressions.parquet do not exist yet, so this pass "
            "will write centrality/FEM columns as null. This is expected -- stages 4 and 5 "
            "below produce those two files, and stage 6 re-runs this exact script to "
            "produce the FINAL, fully-populated dataset."
        ),
    ),
    Stage(
        name="fig_network_centrality",
        module_path="03_analysis.eip_concentration.fig_network_centrality",
        description="EIP co-authorship network + betweenness/closeness/eigenvector centrality (Figures 9, 12).",
        expected_outputs=[DATA_INTERIM / "centrality_all.parquet"],
    ),
    Stage(
        name="fig_fem_engagement",
        module_path="03_analysis.community_engagement.fig_fem_engagement",
        description="Ethereum Magicians (FEM) forum engagement per EIP (Figure 13).",
        expected_outputs=[DATA_INTERIM / "fem_data_for_regressions.parquet"],
    ),
    Stage(
        name="build_cross_sectional_dataset_pass2",
        module_path="02_data_preparation.build_cross_sectional_dataset",
        description="[PASS 2/2: FINAL] Re-run now that centrality_all.parquet and "
        "fem_data_for_regressions.parquet exist -- produces the complete, final dataset "
        "used by every downstream figure/table below.",
        expected_outputs=[DATA_PROCESSED / "ethereum_cross_sectional_data.parquet"],
        banner_note=(
            "PASS 2 of 2 (FINAL): data/interim/centrality_all.parquet and "
            "data/interim/fem_data_for_regressions.parquet now both exist (stages 4 and 5 "
            "already ran), so this pass OVERWRITES pass 1's output with the complete, "
            "centrality- and FEM-populated dataset. Every stage after this one depends on "
            "THIS version of the file, not pass 1's."
        ),
    ),
    Stage(
        name="fig_eip_trends_and_concentration",
        module_path="03_analysis.eip_concentration.fig_eip_trends_and_concentration",
        description="EIP volume over time + author-level concentration (Figures 2, 7, 8, 10, 11).",
        expected_outputs=[DATA_INTERIM / "eip_by_authors.parquet"],
    ),
    Stage(
        name="fig_readability_and_status",
        module_path="03_analysis.transparency_openness.fig_readability_and_status",
        description="EIP text readability/length histograms (Figure 5).",
        expected_outputs=[OUTPUT_FIGURES / "read_hist.png"],
    ),
    Stage(
        name="fig_anonymity",
        module_path="03_analysis.transparency_openness.fig_anonymity",
        description="Share of non-anonymous participants among authors/attendees/client devs (Figure 6).",
        expected_outputs=[OUTPUT_FIGURES / "figure_04_anonymity.png"],
    ),
    Stage(
        name="fig_company_concentration",
        module_path="03_analysis.company_influence.fig_company_concentration",
        description="Company/employer concentration of EIP authorship + EF share over time "
        "(Figure 20 panels a-c, Figure 21).",
        expected_outputs=[OUTPUT_FIGURES / "company_lorenz.png"],
    ),
    Stage(
        name="fig_client_concentration",
        module_path="03_analysis.client_concentration.fig_client_concentration",
        description="Execution-client commit concentration + client-developer employer mix "
        "(Figure 16, Figure 20 panel d).",
        expected_outputs=[OUTPUT_FIGURES / "figure_20_client_lorenz.png"],
    ),
    Stage(
        name="fig_commit_timing",
        module_path="03_analysis.community_engagement.fig_commit_timing",
        description="Dev-call attendance + GitHub commits per EIP (Figure 14, Figure 15 panels a-b). "
        "Needs eip_by_authors.parquet from fig_eip_trends_and_concentration (stage 7).",
        expected_outputs=[OUTPUT_FIGURES / "figure_14a_attendees_by_year.png"],
    ),
    Stage(
        name="fig_adoption",
        module_path="03_analysis.adoption_stablecoins_oracles.fig_adoption",
        description="Stablecoin market share + oracle TVL/protocol-count adoption figures (Figures 18, 19). "
        "Independent of the cross-sectional dataset; kept here for a linear read-through.",
        expected_outputs=[OUTPUT_FIGURES / "figure_22a_stablecoin_pct_of_tvl.png"],
    ),
    Stage(
        name="fig_abnormal_returns",
        module_path="03_analysis.token_price_effect.fig_abnormal_returns",
        description="Cumulative abnormal ETH returns around EIP finalization/AllCoreDevs discussion "
        "(Figure 3, Table 2). Needs the FINAL cross-sectional dataset (stage 6).",
        expected_outputs=[OUTPUT_FIGURES / "figure_24a_car_spy.png"],
    ),
    Stage(
        name="table1_summary_stats",
        module_path="03_analysis.regressions.table1_summary_stats",
        description="Table 1 (summary statistics).",
        expected_outputs=[OUTPUT_TABLES / "summstat.tex"],
    ),
    Stage(
        name="table4_participation_summary",
        module_path="03_analysis.community_engagement.table4_participation_summary",
        description="Table 4 (EIP discussion/development participation by venue -- FEM, GitHub, "
        "AllCoreDevs). Needs the FINAL cross-sectional dataset (stage 6) + "
        "fem_data_for_regressions.parquet (stage 5).",
        expected_outputs=[OUTPUT_TABLES / "participation_summary.tex"],
    ),
    Stage(
        name="did_labor_market_effects",
        module_path="03_analysis.labor_market_effects.did_labor_market_effects",
        description="Stacked-cohort DiD: EIP authorship and career outcomes (seniority, log compensation) "
        "in Revelio Labs LinkedIn data (Table 3, Figure 4) -- reads only data/raw/eip_registry/ and "
        "data/raw/revelio/, independent of every stage above. The Revelio data is WRDS-licensed and not "
        "included in this public repo (see README.md's 'Data availability'); this stage cannot run "
        "out of the box without your own WRDS/Revelio access.",
        expected_outputs=[OUTPUT_TABLES / "table_did_results.tex"],
    ),
]


# =============================================================================
# Stage execution
# =============================================================================
def _import_stage_module(module_path: str):
    """
    Import a stage's module given its `module_path` (e.g.
    "02_data_preparation.clean_eip_authors").

    The two top-level package directories under code/ (`02_data_preparation`,
    `03_analysis`) start with a digit, which makes them invalid Python package/module
    names for a normal dotted `import` statement (this exact issue is called out in
    several of the analysis scripts' own docstrings, e.g. fig_company_concentration.py
    and fig_commit_timing.py, as the reason they duplicate small helpers instead of
    cross-importing). We therefore import each stage module directly off its file path
    via `importlib`, sidestepping the package-name restriction entirely, rather than
    trying to `import` the dotted path as a real package.
    """
    code_dir = Path(__file__).resolve().parent
    rel_path = module_path.replace(".", "/") + ".py"
    file_path = code_dir / rel_path
    if not file_path.exists():
        raise FileNotFoundError(f"Stage module not found on disk: {file_path}")

    # Make sure the module's OWN directory is on sys.path before importing it, exactly
    # as if it had been run standalone via `python path/to/script.py` -- several stage
    # scripts insert their own parent directories into sys.path at import time (for
    # their own sibling imports, e.g. fig_venn_diagram.py importing fig_anonymity.py),
    # and rely on being importable/executable that way.
    module_dir = str(file_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    # Use a flat, collision-safe synthetic module name (dots aren't valid in a bare
    # module name passed to importlib this way, and the two build_cross_sectional_dataset
    # passes must resolve to the SAME already-imported module on the second pass rather
    # than re-executing top-level code twice).
    synthetic_name = "_pipeline_stage__" + module_path.replace(".", "__").replace("-", "_")
    if synthetic_name in sys.modules:
        return sys.modules[synthetic_name]

    spec = importlib.util.spec_from_file_location(synthetic_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[synthetic_name] = module
    spec.loader.exec_module(module)
    return module


def _get_entry_point(module) -> Callable[[], None]:
    """
    Return the callable to invoke for a stage's module.

    Every one of this pipeline's 17 distinct scripts exposes a clean, no-required-
    argument `main()` function (confirmed by reading each script's actual source before
    writing this orchestrator -- see the module docstring's "Corrections made" section).
    We therefore always prefer `module.main` (cleaner tracebacks, one Python process,
    no subprocess overhead). The `subprocess.run([sys.executable, str(script_path)],
    check=True)` fallback described in the design brief is intentionally not needed here
    -- every stage has a real, importable `main()` -- but is kept as an explicit,
    documented escape hatch below in case a future stage script does NOT expose one.
    """
    if hasattr(module, "main") and callable(module.main):
        return module.main
    raise AttributeError(
        f"Module {module!r} has no callable main() -- this pipeline only knows how to "
        "call an importable main() entry point. If a future stage script genuinely has "
        "no importable main() (only an if __name__ == '__main__' block), fall back to: "
        "subprocess.run([sys.executable, str(script_path)], check=True)"
    )


def _outputs_exist(stage: Stage) -> bool:
    return bool(stage.expected_outputs) and all(p.exists() for p in stage.expected_outputs)


def _run_stage(stage: Stage, index: int, total: int, skip_existing: bool) -> str:
    """
    Run one stage. Returns "ok", "skipped", or raises on failure (caller catches and
    records "failed").
    """
    banner = f"[{index}/{total}] {stage.name} -- {stage.description}"
    print("\n" + "=" * 100)
    print(banner)
    if stage.banner_note:
        print("-" * 100)
        print(stage.banner_note)
    print("=" * 100)

    if skip_existing and _outputs_exist(stage):
        print(
            f"[run_pipeline] --skip-existing: expected output(s) already exist for "
            f"'{stage.name}':"
        )
        for p in stage.expected_outputs:
            print(f"    {p} (exists={p.exists()})")
        print(f"[run_pipeline] Skipping stage '{stage.name}'.")
        return "skipped"

    module = _import_stage_module(stage.module_path)
    entry_point = _get_entry_point(module)
    entry_point()
    print(f"[run_pipeline] Stage '{stage.name}' completed successfully.")
    return "ok"


# =============================================================================
# CLI
# =============================================================================
def _print_stage_list() -> None:
    print(f"{'#':>3}  {'stage name':<38} description")
    print("-" * 100)
    for i, stage in enumerate(PIPELINE_STAGES, start=1):
        print(f"{i:>3}  {stage.name:<38} {stage.description}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Master orchestrator for the 'Decentralized Crypto Governance?' (Fracassi, Khoja & "
            "Schar, SSRN 4691000) reproduction pipeline. See this file's module docstring for "
            "the full pipeline DAG and the two-pass circular-dependency design."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip a stage if its expected output file(s) already exist on disk (useful for resuming a partial run).",
    )
    parser.add_argument(
        "--stage",
        metavar="STAGE_NAME",
        help="Run only this one named stage (see --list for valid names), then exit. "
        "No dependency ordering is enforced when using this flag -- it is for debugging "
        "a single stage, not for resuming a full run (use --skip-existing for that).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print all pipeline stages (in order) and exit without running anything.",
    )
    args = parser.parse_args(argv)

    if args.list:
        _print_stage_list()
        return 0

    ensure_dirs()

    stages_to_run = PIPELINE_STAGES
    if args.stage:
        matches = [s for s in PIPELINE_STAGES if s.name == args.stage]
        if not matches:
            valid_names = ", ".join(s.name for s in PIPELINE_STAGES)
            print(f"[run_pipeline] ERROR: unknown --stage '{args.stage}'. Valid stage names:\n  {valid_names}")
            return 2
        stages_to_run = matches

    total = len(stages_to_run)
    results: list[tuple[str, str]] = []  # (stage_name, "ok" | "skipped" | "failed")

    for i, stage in enumerate(stages_to_run, start=1):
        try:
            outcome = _run_stage(stage, i, total, skip_existing=args.skip_existing)
            results.append((stage.name, outcome))
        except Exception:
            print("\n" + "!" * 100)
            print(f"[run_pipeline] STAGE FAILED: '{stage.name}'")
            print("!" * 100)
            traceback.print_exc()
            results.append((stage.name, "failed"))
            print(
                "\n[run_pipeline] Stopping pipeline: a later stage almost certainly depends on "
                f"'{stage.name}''s output. Fix the error above, then re-run (consider "
                "--skip-existing to avoid re-doing already-completed stages)."
            )
            break

    # ------------------------------------------------------------------
    # Final summary (always printed, whether or not something failed)
    # ------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("PIPELINE SUMMARY")
    print("=" * 100)
    ran_names = {name for name, _ in results}
    not_attempted = [s.name for s in stages_to_run if s.name not in ran_names]

    for name, outcome in results:
        tag = {"ok": "OK     ", "skipped": "SKIPPED", "failed": "FAILED "}[outcome]
        print(f"  [{tag}] {name}")
    for name in not_attempted:
        print(f"  [NOT RUN] {name}")

    n_ok = sum(1 for _, o in results if o == "ok")
    n_skipped = sum(1 for _, o in results if o == "skipped")
    n_failed = sum(1 for _, o in results if o == "failed")
    print("-" * 100)
    print(
        f"Total: {len(stages_to_run)} stage(s) selected | {n_ok} succeeded | {n_skipped} skipped | "
        f"{n_failed} failed | {len(not_attempted)} not attempted"
    )
    print("=" * 100)

    return 1 if n_failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
