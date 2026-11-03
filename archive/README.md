# Archive

This folder holds everything from this reproduction package that is **not** needed to produce the
paper's actual published results. Nothing here was deleted — it was moved here so the active
`code/`/`output/` areas contain only what reproduces Table 1, Table 2, Table 3, and Figures 1-24 of:

> Fracassi, C., Khoja, M., & Schär, F. (2024). "Decentralized Crypto Governance? Transparency and
> Concentration in Ethereum Decision-Making." SSRN 4691000.

## `archive/code/01_data_collection/`

Five historical/optional scripts that are **not** run by `code/run_pipeline.py` and never were.

Three feed the paper's own reproduction (`fetch_eip_registry.py`, `fetch_eip_word_readability.py`,
`scrape_fem_forum.py`) — every raw input they'd otherwise (re-)fetch already exists as a frozen,
point-in-time snapshot under `data/raw/`. Re-running them today would pull *current* live data (new
EIPs added since June 2023, today's GitHub/forum state), not the paper's original snapshot, so they
exist only as documented, optional references for how the raw data was originally collected — not
as part of reproducing the paper. See each script's own module docstring for details.

The other two (`pull_revelio.py`, `enrich_revelio.py`) feed the **labor-market companion analysis**
(pipeline stage 19, `code/03_analysis/labor_market_effects/`) instead — they are not related to the
paper at all. They query Revelio Labs' LinkedIn-derived panel through a WRDS institutional license
and were added here for provenance after the seed file they need
(`data/raw/revelio/_revelio_input.csv`) was supplied; see `PIPELINE_TODO.md` section (vi) and each
script's own module docstring. Re-running them needs a live WRDS/Revelio account and would query
Revelio's live database, not the exact frozen snapshot in `data/raw/revelio/`.

**Note on a pre-existing bug in the three paper-facing scripts**: `fetch_eip_registry.py`,
`fetch_eip_word_readability.py`, and `scrape_fem_forum.py` each insert
`Path(__file__).resolve().parents[1]` onto `sys.path` before `from config import ...`. From this
folder's actual location (`archive/code/01_data_collection/`), `parents[1]` resolves to
`archive/code/`, which has no `config.py` — the real one lives at `<project_root>/code/config.py`,
three levels up (`parents[3]`), not one. Since none of the three is ever executed by
`run_pipeline.py` or referenced elsewhere, this has never surfaced, but attempting to actually run
any of them as documented (`python archive/code/01_data_collection/fetch_eip_registry.py`) would
raise `ModuleNotFoundError: No module named 'config'`. `pull_revelio.py` and `enrich_revelio.py`
(added afterward) use `parents[3]` and do not have this problem. Left unfixed here since it's
pre-existing and out of scope for the current change — flagged for a follow-up.

## `archive/output/figures/` and `archive/output/tables/`

Output files that earlier versions of this package's scripts generated as harmless *extra* output
alongside a script's actually-needed paper output, or as a "completeness" addition for a result the
original authors computed but never published. Per the paper co-author's explicit instruction that
this package should produce *only* the paper's results, the generating code was edited to stop
producing these, and the already-generated stale files were moved here rather than left in
`output/` (where their presence would misleadingly suggest the pipeline still creates them):

| File | Why it isn't part of the paper | Generating script (still active — produces the actually-needed output too) |
|---|---|---|
| `company_neip1.png` | Confirmed via the paper's own LaTeX `\includegraphics` list for Figure 16: only `company_lorenz.png` (a), `company_neip2.png` (b), `company_neip3.png` (c) are shown. | `code/03_analysis/company_influence/fig_company_concentration.py` |
| `eip_by_category.png` | Figure 18's only `\includegraphics` is `success.png`. | `code/03_analysis/transparency_openness/fig_readability_and_status.py` |
| `car_fork_events_spy.png`, `car_fork_events_btc.png` | A separate fork-announcement CAR event study the original script computed but only ever `plt.show()`d — never `\includegraphics`'d anywhere in the paper (Figure 24 is the AllCoreDevs-meeting-based event study only). | `code/03_analysis/token_price_effect/fig_abnormal_returns.py` |
| `FEM_reg_out_log.tex` | Only `FEM_reg_out.tex` (the levels specification) is `\input` as Table 2; the log-outcome variant is never used in the published paper. | `code/03_analysis/regressions/table2_fem_regressions.py` |
| `table_commit_call.tex` | Never `\input` as a table anywhere; the paper shows only the coefficient **plot** (Figure 15, `\includegraphics{Figures/commit_call.png}`). The underlying regression is still fit (needed for the plot) — only the separate table export was removed. | `code/03_analysis/community_engagement/fig_commit_timing.py` |

Each "not part of the published paper" determination above was confirmed by grepping the paper's
own LaTeX source for `\input`/`\includegraphics`, not merely inferred.
