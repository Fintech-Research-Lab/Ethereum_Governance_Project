# Pipeline Checklist & Follow-Ups

**Note on figure/table numbers in this file:** this is a running changelog. Entries below were
written at different points as the manuscript was revised, and many cite the Figure/Table number
that was current *at the time of that entry* — several of those numbers (e.g. "Figure 24" for the
CAR event study, "Figure 12" for FEM engagement) have since shifted. Treat any number in a dated
entry below as historical. For the current numbering, see `docs/figure_table_index.md`.

**Note on `archive/` paths in this file:** this changelog references `archive/code/01_data_collection/`,
`archive/README.md`, and similar paths throughout. The `archive/` folder (dropped-analysis scripts,
stale outputs, the labor-market analysis's exploratory trail, pre-publication draft memos) is kept
in the authors' own private working copy and is **not included in this public repository**. Treat
every `archive/...` path below as a reference to that private copy, not something browsable here.

## (a) Pipeline stage checklist

Mirrors the 17-stage order defined in `code/run_pipeline.py::PIPELINE_STAGES`. `python
code/run_pipeline.py` (no flags) has been run end-to-end at least once, successfully, through all
17 stages of the paper's own reproduction, producing every intermediate dataset, figure, and table
described in `docs/figure_table_index.md`. Every stage below is checked off on that basis. Stage 17
(`did_labor_market_effects`, now Table 3 / Figure 4 of the paper — see (vi) below, and
`docs/figure_table_index.md` for current numbering) needs WRDS/Revelio access not available in
every environment, so it has been run and verified separately rather than as part of every
end-to-end run.

NOTE: this checklist previously still listed `fig_venn_diagram`, `table3_finalization_regressions`,
and `table2_fem_regressions` as active stages even after those three scripts were moved to
`archive/code/` (their outputs are not `\input`/`\includegraphics`'d anywhere in `MS_R2.tex` --
see `run_pipeline.py`'s own module docstring and `archive/README.md` for that audit's reasoning;
no dedicated entry for it exists elsewhere in this file). The archiving pass updated
`run_pipeline.py`'s docstring/stage list at the time, but not this checklist. Corrected here,
together with the addition of `table4_participation_summary` (see (x) below).

- [x] `clean_eip_authors` — Build the per-EIP author spine (Author1..Author15 / author{n}_id) from the raw EIP registry. Writes `data/interim/ethereum_cross_sectional_data_beg.parquet`.
- [x] `name_cleaning_pipeline` — Fuzzy-match name cleaning for attendees/clients/contributors/authors (4 final lists). Writes `data/interim/unique_{attendees,clients,contributors,authors}_final.parquet`.
- [x] `build_cross_sectional_dataset_pass1` — [PASS 1/2: BOOTSTRAP] Merge ~10 raw sources into the cross-sectional dataset without centrality/FEM data (those files don't exist yet). Writes `data/processed/ethereum_cross_sectional_data.{parquet,csv}`.
- [x] `fig_network_centrality` — EIP co-authorship network + betweenness/closeness/eigenvector centrality (Figures 10, 11). Writes `data/interim/centrality_all.parquet`.
- [x] `fig_fem_engagement` — Ethereum Magicians (FEM) forum engagement per EIP (Figure 12). Writes `data/interim/fem_data_for_regressions.parquet`.
- [x] `build_cross_sectional_dataset_pass2` — [PASS 2/2: FINAL] Re-run now that centrality and FEM data exist; overwrites pass 1's output with the complete, final dataset every downstream stage depends on.
- [x] `fig_eip_trends_and_concentration` — EIP volume over time + author-level concentration (Figures 2, 6, 7, 8, 9). Writes `data/interim/eip_by_authors.parquet`.
- [x] `fig_readability_and_status` — EIP text readability/length histograms + status/category pie charts (Figures 3, 18).
- [x] `fig_anonymity` — Share of non-anonymous participants among authors/attendees/client devs (Figure 4).
- [x] `fig_company_concentration` — Company/employer concentration of EIP authorship + EF share over time (Figures 16a-c, 17).
- [x] `fig_client_concentration` — Execution-client commit concentration + client-developer employer mix (Figures 20, 16d).
- [x] `fig_commit_timing` — Dev-call attendance + commit-timing event study around AllCoreDevs calls (Figures 13, 14a, 14b, 15). Needs `eip_by_authors.parquet` from `fig_eip_trends_and_concentration`.
- [x] `fig_adoption` — Stablecoin market share + oracle TVL/protocol-count adoption figures (Figures 22, 23). Independent of the cross-sectional dataset.
- [x] `fig_abnormal_returns` — Cumulative abnormal ETH returns around EIP finalization/AllCoreDevs discussion (Figure 24), plus a companion table of the same estimates at selected trading-day horizons (`car_event_study.tex`, added per request — see item below). Needs the FINAL cross-sectional dataset.
- [x] `table1_summary_stats` — Table 1 (summary statistics).
- [x] `table4_participation_summary` — Table 4 (EIP discussion/development participation by venue: FEM, GitHub, AllCoreDevs). Needs the FINAL cross-sectional dataset + `fem_data_for_regressions.parquet`. See (x) below.
- [x] `did_labor_market_effects` — Stacked-cohort DiD: EIP authorship and career outcomes in Revelio Labs LinkedIn data (Table 3, Figure 4 of the current manuscript). Independent of stages 1-16; reads only `data/raw/eip_registry/` + `data/raw/revelio/`, the latter WRDS-licensed and not included in this public repo (see README.md's "Data availability"). Writes one combined table (`table_did_results.tex` — Panel A balance, Panel B seniority, Panel C log compensation) + `EIP_W2_EventStudy.png`.

Archived (no longer pipeline stages — see `run_pipeline.py`'s module docstring and
`archive/README.md`): `fig_venn_diagram` (Figure 5, not used in the current paper),
`table3_finalization_regressions` (Table 3 + Figure 19, not used in the current paper),
`table2_fem_regressions` (Table 2, not used in the current paper).

## (b) Follow-ups / To-Do

Everything below is either already resolved (kept here as a record) or a genuinely deferred item
for a human (or a future agent) to look at. None of it blocks the pipeline from running or from
having already produced every figure/table with the fidelity described in `README.md`'s Validation
section.

### (i) Bugs fixed (per the co-author's explicit "fix the bugs, don't match the paper" direction)

All of the following were real algorithmic bugs, confirmed present in the original Stata/Python
code. All are now fixed in this package's default behavior. Two of them (marked below) actually
move a published number away from what the paper reports; the rest were already zero-impact on any
current output.

1. Off-by-one column slice folding EIP `Status` into the author name-lookup pool (`clean_eip_authors.py`) — fixed, zero effect on any output.
2. Stata descending-`gsort`-with-missing bug in the EIP-concentration collapses (`fig_eip_trends_and_concentration.py`) — fixed; **moves Figure 7's "Implemented EIPs" panel and the Figure 8/9 Gini values**, since the buggy convention was previously producing numbers far from the paper's own (which themselves reflect the correct convention).
3. `final_all.tex`'s manual LaTeX header text corrected to describe what the regression code (correctly) computes.
4. Client-commit row-max extended to span all 15 author slots (was 1-11) (`build_cross_sectional_dataset.py`).
5. `time_to_final` no longer divided by milliseconds-per-day.
6. LinkedIn per-author-slot job-title columns recovered (`job_title2_company4`, `jobtitle2_pastcompany{1,2,4}`).
7. All four EIP commit-count variables consistently fill to 0 (was only `n_contributors_eip`).
8. `"Living "` (trailing-space) status typo normalized before the `success` recode, not after.
9. Author-slot lookup dictionaries (`fig_network_centrality.py`) now scan all 15 slots (was 1-14) — recovers `author_id` 639's centrality data.
10. FEM "DROP WRONG EIP ASSOCIATIONS" filter fixed to its intended `isin`-based logic.
11. N/A — the finalization-date vs. meeting-date event-study choice was never a bug (see `fig_abnormal_returns.py`'s docstring); both remain available via `--event-type`.
12. N/A — Figure 16d's mean-vs-sum "Others" bucket statistic was verified correct (matches Stata's documented `graph bar` default), not a bug.
13. N/A — moot; the non-published `commit_call.tex` table was removed from scope entirely.
14. Row-wide scalar assignment fixed to a single-column assignment (`_row_wide_scalar_assign`).
15. `Top10_in_community.py`'s "Common" overlap table mislabeled row corrected.
16. **Erigon/Besu execution-client commit-file swap** (`utils/client_commits.py`) — fixed; Erigon's data now loads from its own file, not Besu's. **Moves Figure 4's "Top Client Developers disclosing full name" from the published 78.8% to 80.0%**, and affects Figure 5's Top-10 client-committer stats.
17. **FEM per-EIP "Created Date" MIN computed on a formatted string, not the real date** (`fig_fem_engagement.py`) — fixed to use the true chronological minimum. **Moves Figure 12a's year-by-year view totals and the `year` fixed effect feeding Table 2.**

Every fix above that changes a number keeps the original (bug-reproducing) behavior available as an
explicit, non-default opt-in (`reproduce_original_bug=True` / `missing_sorts_first=True`, per
function), for side-by-side comparison against the published paper.

### (ii) Non-determinism (fixed to be stable, with no effect on any published number)

- **`Anonymity_Flag` assignment** (`name_cleaning_pipeline.py`) is now a name-keyed join against the
  original author's historical manual-review decisions, replacing the old position-indexed overrides
  that depended on Python's hash-randomized `set()` ordering. Row order of the four output files is
  also now deterministic by default (`deterministic=True`).
- **Top-20/Top-10 client-committer `Anonymity_Flag` overrides** (`fig_anonymity.py`) are now
  name-keyed rather than position-indexed, so they stay attached to the right person even if a
  future commit-data refresh changes the exact ranking.

### (iii) Frozen / non-live-reproducible data collection steps

These raw data sources are frozen, point-in-time snapshots. If the paper is ever extended to a
later date range, each would need re-collection (not just a pipeline re-run) — see the relevant
script's own docstring in `archive/code/01_data_collection/` for exactly what changed and why re-running it
today would not reproduce the paper's original numbers:

- **FEM forum scrape** (`archive/code/01_data_collection/scrape_fem_forum.py` → `data/raw/forum/ethereum_magicians_data_scraped.csv`, `list_of_FEM_EIP_pages.csv`) — Selenium/BeautifulSoup scrape of the Ethereum Magicians (Discourse) forum, circa early 2024. Live comments/views/likes have moved on since, and Discourse's own HTML structure may have changed.
- **OpenAI/GPT meeting-date parsing** (feeding `data/raw/meetings/calls_updated_standardized.csv`) — the standardized AllCoreDevs call metadata was produced by an LLM-assisted date-parsing pass over the original `calls_updated.csv` (itself no longer present anywhere in the source tree — see `data/RAW_DATA_MANIFEST.md`). Re-running this would need the original raw call notes (not currently available) and a fresh LLM parsing pass, which is not guaranteed to reproduce identical output to the original run.
- **DeFiLlama TVL snapshots** (`data/raw/adoption/{oracle_data,USDC_MASTER,USDT_MASTER,DAI_MASTER,Total_TVL_ETH}.csv`, feeding `fig_adoption.py` / Figures 22-23) — frozen, point-in-time DeFiLlama pulls. Re-querying the live DeFiLlama API today would return current, not historical, TVL, silently invalidating any figure claiming to show "TVL as of [past date]." `archive/code/01_data_collection/` intentionally does not include a live-refetch script for this data (see `fig_adoption.py`'s "Frozen-data note").

### (iv) `GITHUB_TOKEN` environment variable

A fresh `GITHUB_TOKEN` (GitHub personal access token) environment variable is needed to usefully
re-run `archive/code/01_data_collection/fetch_eip_word_readability.py` — confirmed in its source: it calls
the GitHub Contents API and falls back to unauthenticated requests (rate-limited to 60/hour,
sufficient only for a tiny sample) with a printed warning if `GITHUB_TOKEN` is unset; setting it
raises the limit to 5,000/hour. Neither script is part of the default `run_pipeline.py` run.

Note on `fetch_eip_registry.py`: unlike `fetch_eip_word_readability.py`, this script scrapes the
`eips.ethereum.org/all` HTML listing directly rather than calling the GitHub API, and its source
contains no `GITHUB_TOKEN`/authentication logic at all — it does not need a token to re-run (though,
like the other two `archive/code/01_data_collection/` scripts, re-running it would pull the current live registry
state, not the paper's original point-in-time snapshot).

### (v) Findings about how this package's output relates to the paper's own text

Three things worth knowing when comparing this package's output to the published paper — none are
bugs in this package, and none need fixing:

- **Client-commit counts run ~9-18% higher than the paper's** (`fig_client_concentration.py`,
  Figure 20 / 16d) — root cause found: the paper's text/Figure 20 were computed from an older
  (Nov 1, 2023) commit-data pull that was superseded in the original repository by a newer
  (Dec 18-19, 2023) pull one day before the paper's text was finalized. Recomputing the paper's
  exact quoted stats from the archived older pull matches to within 0-1 across all 9 checked
  numbers. **Decision (confirmed with the paper's co-author):** this package keeps using the
  current, non-superseded data — a documented data-vintage mismatch between the paper's text and
  the repository's final state, not something to correct.
- **The paper's "~20% of meeting attendees are client developers" prose doesn't match its own
  underlying computation** (`fig_venn_diagram.py`) — confirmed by diffing against the original
  author's own historically-saved `Name_Results.csv` (11/15 rows match exactly): both the original
  project and this package actually compute ~6.2-6.4% for this quantity. This looks like an
  inaccuracy in the paper's prose, not a reproduction gap.
- **The paper's "38% y-o-y FEM forum growth" headline can't be pinned to a specific averaging
  method** (`fig_fem_engagement.py`, Figure 12a) — this package's year-by-year FEM view totals now
  match the original author's own saved output exactly (after fixing the date-string-min bug, see
  item 17 above), giving yearly growth rates of +57.0%/-7.5%/+18.3%/+47.2% (simple average ~28.7%,
  CAGR ~26.1%) — in the right direction but not an exact match to "38%." Which method the paper
  used to collapse four yearly rates into one headline figure isn't determinable from the data
  alone; low-priority, unresolved.

### (vi) Labor-market effects of EIP authorship — now Table 3 / Figure 4 of the paper

`code/03_analysis/labor_market_effects/did_labor_market_effects.py` (pipeline stage 17) asks:
does authoring an EIP change a writer's career trajectory (seniority, compensation)? It was
originally developed as an exploratory side question, independent of the paper's governance-
concentration focus, linking EIP authors to LinkedIn-derived employment histories and running a
stacked-cohort difference-in-differences design on the result. It has since been promoted into
the manuscript as Section III, cited directly as Table 3 (`\label{tab:did_main}`) and Figure 4
(`\label{fig:labor}`) — see `docs/figure_table_index.md` for the current numbering snapshot. It
is kept as its own pipeline stage because its data source (WRDS/Revelio) and dependencies are
entirely independent of the other 16 stages, not because it is unpublished.

- **Data moved in**: only the three Revelio files the script actually reads —
  `author_to_revelio_userid.parquet`, `revelio_user.parquet`, `revelio_positions_enriched.parquet`
  — copied to `data/raw/revelio/` (all three already zstd-compressed, all under 2.2MB). The other
  two required inputs, `eip_startdates.csv` and `allEIPsandAuthorsv2.csv`, were already present at
  `data/raw/eip_registry/` from the paper's own pipeline — nothing needed to move for those. The
  eight other Revelio files in `revelio_pull/` (raw `revelio_positions.parquet`,
  `revelio_company_mapping.parquet`, `revelio_education*.parquet`, `revelio_skills.parquet`,
  `revelio_role_lookup_*.parquet`, `revelio_regions.parquet`) are not read by the DiD script and
  were left out of the package.
- **Provenance of the three Revelio files**: Revelio Labs (a commercial LinkedIn-derived data
  vendor) is the ultimate source, accessed through a WRDS (Wharton Research Data Services)
  institutional license. `archive/code/01_data_collection/pull_revelio.py` (ported in from
  `Ethereum_Governance_Project/archive/Data/Data Gathering Code/pull_revelio.py`, paths adapted to
  this package's `config.py`) connects to WRDS and matches EIP/forum author names against
  `revelio.individual_user.profile_linkedin_url` (474 of 491 resolve to a Revelio `user_id`), then
  pulls the `individual_user`/`individual_positions`/`individual_user_education`/
  `individual_user_skills` tables filtered to those ids. `archive/code/01_data_collection/
  enrich_revelio.py` runs afterward, joining in `company_mapping`/`individual_role_lookup_v2`/
  `individual_role_lookup_v3`/`regions` (also queried live from WRDS) to produce the `_enriched`
  positions file. Both scripts are HISTORICAL/OPTIONAL, exactly like the three paper-facing
  `archive/code/01_data_collection/` scripts — not run by `run_pipeline.py`, kept for provenance
  only. Re-running either needs a live WRDS/Revelio account with credentials (neither is bundled
  here) and would query Revelio's *current* database rather than the exact original pull —
  `revelio_user`'s own `updated_dt` field spans 2021-01-16 to 2026-06-01, confirming it was always
  a live/recent pull, not a fixed historical snapshot — so a fresh run would not reproduce
  `data/raw/revelio/*.parquet` bit-for-bit. The seed list they need,
  `data/raw/revelio/_revelio_input.csv` (491 rows: `author_id, author_name, best_url,
  linkedin_slug`), is now checked in, so both scripts are at least *structurally* runnable by
  anyone with the right WRDS access, even though re-running them is not how this package's frozen
  Revelio inputs should be regenerated day to day.
- **Known bug in the three older `archive/code/01_data_collection/` scripts, found while adding the
  two above**: `fetch_eip_registry.py`, `fetch_eip_word_readability.py`, and `scrape_fem_forum.py`
  each resolve `code/config.py` via `Path(__file__).resolve().parents[1]`, which from their actual
  location (`archive/code/01_data_collection/`) lands on `archive/code/` (no `config.py` there)
  instead of the real `code/` three levels up (`parents[3]`). None of the three is ever executed by
  `run_pipeline.py`, so this has never surfaced, but running any of them directly, as their own
  docstrings suggest, would raise `ModuleNotFoundError: No module named 'config'`.
  `pull_revelio.py`/`enrich_revelio.py` use the correct `parents[3]` and don't have this problem.
  Flagged as a follow-up task rather than fixed here (pre-existing, out of scope for this change).
- **Deliberate pandas exception**: this script is kept in pandas throughout, unlike the rest of the
  package's Polars-only convention. The cohort/matching step is a per-event loop over
  `scipy.spatial.distance.cdist` results keyed by pandas' `groupby`/`.loc` indexing, and the
  estimation step builds `statsmodels` design matrices with `pandas.get_dummies` and grouped
  demeaning — porting that combination to Polars would touch exactly the matching/regression logic
  this analysis exists to get right, for no numerical benefit. See the module's own docstring
  ("A NOTE ON PANDAS") for the full reasoning; this mirrors `config.py`'s existing carve-out for
  `statsmodels`/`sklearn`-dependent scripts, just scoped to the whole file rather than a boundary
  conversion.
- **Replication check**: `python did_labor_market_effects.py --rebuild`, run from raw data with no
  cache reused, reproduces the co-author-supplied results table numerically exactly — 356 cohorts /
  353 treated / 403 clusters / 6,073 observations; seniority static +0.221<sup>\*\*\*</sup>, ATT
  +0.237<sup>\*\*</sup>, junior +0.284<sup>\*\*</sup>, senior +0.150 (n.s.); log compensation static
  +0.090<sup>\*\*</sup>, ATT +0.091<sup>\*</sup>, junior +0.093<sup>\*</sup>, senior +0.085 (n.s.) —
  and the balance panel matched byte-identically before the tables were merged (see next item).
  Absorbed-vs-dummy-variable coefficient agreement at each run: ~4e-15 (seniority), ~3e-14 (log
  compensation).
- **Single combined table**: originally two separate files (`table_did_results.tex` for the DiD
  estimates, `table_balance.tex` for covariate balance). Per request, merged into ONE table,
  ONE `\label{tab:did_main}`, with three panels in order: Panel A covariate balance (at $t-1$),
  Panel B seniority, Panel C log compensation. Panel A has its own 6-numeric-column `tabular`
  (Treated/Control/Difference/SMD/t-stat/p-value); Panels B and C each have their own 4-column
  `tabular` (Static/Dynamic/Junior/Senior) — see the next item for why they're two separate
  `tabular`s rather than one shared block. The notes text was merged from the two originals
  (deduplicating the restated matching-design explanation) rather than concatenated verbatim.
  `output/tables/table_balance.tex` (the old standalone file, generated earlier in this same
  session) was deleted since its content now lives inside Panel A of `table_did_results.tex`.
- **Found and fixed: a silent content-loss bug, caught by actually compiling the table to PDF.**
  The first version of the combined table wrapped everything (notes + all three panels) in a
  floating `\begin{table}` environment with the note in a `\caption*{\begin{minipage}...}`. That
  combination is a rigid box that cannot break across a page; when it's taller than one page
  (this one comfortably is, given the ~900-word merged note), standard LaTeX does not paginate it,
  warn, or error — it silently drops everything past the bottom of the page. The compiled PDF
  looked completely normal (clean compile, zero warnings, reported "1 page") but contained only
  the notes and the first 3 rows of Panel A; Panels B and C never appeared anywhere in the file.
  Caught by extracting the PDF's actual text layer and noticing it stopped mid-Panel-A, then
  confirmed by a placeholder-note test showing every panel renders fine once the note is short
  enough. Fixed in `write_latex()` by dropping the floating wrapper entirely
  (`\refstepcounter{table}` + a manual heading instead of `\caption`), letting the note flow as an
  ordinary paragraph, and splitting Panels B and C into two independent, self-contained `tabular`s
  (each repeating its own column header and sample-size/FE rows — identical between the two
  outcomes, since both are estimated on the same matched sample) so each panel can land wherever it
  fits across a page break instead of being forced into one un-splittable ~25-row block. The table
  now spans 3 pages (title+notes / Panel A+B / Panel C) with no lost content and no wasted blank
  space — verified by rendering every page and extracting the text layer to confirm all three
  panels and every summary statistic are present. No LaTeX distribution existed on this machine
  before this check; MiKTeX was installed (via winget) specifically to compile and inspect this.
- **Terminology and table-content edits, per request**: (a) "writer" → "author" throughout the
  table's notes and row labels (also the module docstring/comments, for consistency) — the
  underlying `author_id` column and matching logic were never renamed, only user-facing text;
  (b) the static row is now labeled "Treated $\times$ Post ($t\geq0$)" instead of just "Post"; (c)
  the ATT row (`Treated $\times$ Post` beneath the dynamic column) was removed from both Panel B
  and Panel C, and the note's sentence describing it was trimmed to match — the underlying
  `estimate()` function still computes the ATT internally (used by `main()`'s console diagnostic
  output and `verify()`), it is simply no longer written to the table.
- **Panel A now reports only "Total compensation (USD)"**, not "Log total compensation" — the
  `log_comp` row was removed from `BALANCE_VARS`. The underlying matching procedure is unaffected
  (Mahalanobis distance is still computed on log compensation internally); this only changes what
  the balance table displays. Note this makes the earlier Jensen's-inequality discussion (why the
  log-comp means matched almost exactly at 11.757 while the USD means differ by ~$5k/2.5%) no
  longer visible side-by-side in the table itself — worth remembering if that gap in
  "Total compensation (USD)" alone ever looks surprising without the log-comp row next to it for
  context.
- **Split the event-study figure into two separate files**, per request: `make_figure()` (one
  two-panel PNG) became `make_figures()`, writing `EIP_W2_EventStudy_Seniority.png` and
  `EIP_W2_EventStudy_LogComp.png` independently instead of one combined image. Each is now its
  own standalone single-panel chart at its own size (5.4x4.2in vs. the combined figure's 10x4.2in
  for two panels), not a crop of the old combined image. The old `EIP_W2_EventStudy.png` is no
  longer produced by `main()`; the stale copy from the prior run was left in place pending the
  user's confirmation to remove it (see project convention: never delete without explicit
  consent).
- **Not yet done**: a methodological review of the design (matching approach, inference,
  interpretation of the ATT) has not been written up. Flagged for discussion, not a code issue.

### (vii) CAR event-study table added to `fig_abnormal_returns.py` (Figure 24 companion), per request

Figure 24 only ever plotted the CAR event study (mean CAR by trading day, with a confidence
band); there was no tabular presentation of the same estimates. Added `build_car_table_rows()`
and `write_car_table()` to `code/03_analysis/token_price_effect/fig_abnormal_returns.py`, wired
into `main()`, writing `output/tables/car_event_study.tex`: a two-column table (S&P 500 benchmark,
Bitcoin benchmark) at 19 selected trading-day horizons (every 5 days from t=-40 to t=+40, plus
t=-1 and t=0), using the exact same per-day sample and statistic (`_mean_ci()`'s mean/std/n) that
the figure itself already plots, restricted to the same Core/Networking category filter, so the
table's numbers match the figure exactly rather than being a separately-derived estimate. Each
day's estimate is computed independently (matching the figure's own day-by-day construction), not
a single joint regression with day dummies, which would require deciding how to cluster standard
errors across days for the same EIP; since the figure makes no such joint-estimation claim, the
table does not either. Added to `MS_R2.tex` right after Figure `fig:CAR`, referencing it via
`\ref{fig:CAR}` (not a hardcoded figure number, since this draft's actual figure numbers do not
match the original published paper's Figure/Table numbering, the paper having been substantially
restructured since; see below).

Verification performed before adding this to the paper:
- Compiled the table standalone (clean, no LaTeX warnings) and confirmed its point estimates
  visually match Figure 24's plotted lines at t=0 (SPY: 0.299 vs. the figure's plotted ~0.3;
  BTC: 0.124 vs. ~0.12).
- The table's Observations count (48 events for both benchmarks, constant across all 19
  horizons, i.e. no edge-of-sample truncation in practice) does not match the paper's own text
  ("41 out of 51 finalized Core EIPs"); traced this to Category composition, not a data error:
  the plotted/tabulated sample is `Category in (Core, Networking)` (41 Core + 7 Networking = 48),
  while the "41 out of 51" sentence describes Core only. This filter (Core+Networking) is not
  something this change introduced; `plot_car_with_ci()` already used it before this table
  existed. Flagging here since it was not previously written down anywhere.
- Cross-checked the paper's cited "12% price run-up in the 25 days preceding a Core EIP approval"
  (BTC benchmark) against CAR(t=0) minus CAR(t=-25): 13.2% on the Core+Networking sample, 13.6%
  on Core only. Both are close enough to the cited 12% that this reads as a rounding/approximation
  in the existing prose, not a new inconsistency; left the prose as is since it was not part of
  this request.

While verifying the addition compiled correctly in the full document (the first time this
session that `MS_R2.tex` itself, not just a standalone table, has actually been compiled locally,
now that MiKTeX is installed), found and fixed one unrelated, pre-existing fatal compile error: a
raw Unicode minus sign and "≥" character in the labor-market section's junior/senior split
sentence (from the user's own recent Overleaf edit), which pdfLaTeX cannot render outside a LaTeX
math command. Fixed to `$t=-1$` and `$\geq$`. The full document now compiles cleanly (60 pages),
with the only remaining warning being the already-documented missing `\label{tab:did_main}` in
`Tables/table_did_results_mod.tex` (see section (vi) above; a deliberate choice per the user's
exact-match request, not something this change touches).

One side effect worth knowing: inserting a new `table` environment early in the document (in
Section 2, before the previously-first table in Section 4's Summary Statistics) shifts every
subsequent table's auto-numbered "Table N" up by one (Summary Statistics, FEM regressions, and
EIP finalization/implementation each move up one number from where they were). This is expected
LaTeX behavior given the paper's actual current section order (which already placed the new
labor-market section, with its own table, before Summary Statistics), not something to fix; the
numbers will keep shifting as more tables are added while this draft is still being revised.

(viii) Merged a large, independent Overleaf rewrite (commit `be17fce`, 464 lines net changed) with
the CAR-table commit above (`9d87b50`), producing merge commit `3c44b52`, pushed to Overleaf.

The Overleaf-side commit rewrote the abstract, restructured the Transparency and Openness section
(new AllCoreDevs and GitHub-commits paragraphs, a new synthesis paragraph, a renamed section title),
and expanded several other sections. Only one region genuinely overlapped with this session's own
edits: the junior/senior labor-market sentence, where this session's Unicode-to-LaTeX math fix
($t=-1$, $\geq$) collided with the user's own (separately written) expanded compensation paragraph
that also touched the same sentence with a different, compile-safe fix (`$>=$`). Resolved by keeping
the user's expanded paragraph and re-applying the earlier `$t=-1$`/`$\geq$` math-mode fix on top of
it, and by removing one em-dash that arrived with the merged text. Verified after resolving: no
conflict markers remain, no em-dashes or raw Unicode math characters anywhere in the file, and the
document (49 pages after bibtex + 2 more passes) compiles with no fatal errors.

Found, but did NOT fix (not part of this request, and fixing them would mean guessing the user's
intent): the merged-in rewrite left four dangling `\ref{}`s with no matching `\label{}` anywhere in
the document, all inside content the user rewrote on Overleaf (not touched by this session):
- `\ref{fig:commit_call}` (line ~284) — the GitHub-commits figure this pointed to was rewritten and
  is now labeled `fig:commit_total` instead.
- `\ref{fig:venn}` (line ~641) — no `fig:venn` label exists anywhere; only `fig:attendees_year` and
  `fig:attendees` remain nearby.
- `\ref{subsec_determinants}` and `\ref{subsec:infl_authors}` — no matching `\subsection` labels
  exist anywhere in the current document.
These are non-fatal (pdfLaTeX renders "??" in their place and compilation still succeeds), but should
be pointed out to the user since they arose from the user's own restructuring and only they know
whether the intent was to point `fig:commit_call` at `fig:commit_total`, or whether the referencing
sentences themselves are now stale and should be cut/rewritten.

(ix) FEM raw data source replaced: `fem_posts_by_eip.csv` instead of
`ethereum_magicians_data_scraped.csv`

`code/03_analysis/community_engagement/fig_fem_engagement.py` now reads
`data/raw/forum/fem_posts_by_eip.csv` (a comment-level scrape, one row per comment with a real
`user` column) instead of `data/raw/forum/ethereum_magicians_data_scraped.csv` (one row per
thread, with a `Comment Authors` dict-literal string column requiring `ast.literal_eval` to
unpack). The old file is kept in place for provenance; nothing in the pipeline reads it anymore.

Both files have essentially the same collection cutoff (the new file's last comment timestamp is
2023-06-21, matching the old scrape's stated June 21, 2023 cutoff almost to the day), but the new
file is substantially more complete. After the same inner-join restriction to the official
612-EIP cross-sectional dataset that this script has always applied:

| | Old source | New source |
|---|---|---|
| EIPs matched | 346 | 448 |
| Unique commenters | 1,101 | 1,370 |
| Total comments | 6,416 | 9,271 |
| Total views | 1,617,301 | 3,410,892 |
| Total likes | 4,675 | 7,129 |
| Top-10 contributors' share | 24.8% | 23.3% |
| Gini (comments per user) | 71.6% | 72.6% |
| Views CAGR 2018-2022 | ~12.2% (recomputed; paper stated 26%, confirmed wrong) | 12.63% |

The concentration structure (top-10 share, Gini) is stable across both sources; only the raw
totals and EIP coverage change substantially. Since the two sources share essentially the same
end date, the most likely explanation is that the old scrape under-covered the forum (missed
threads, undercounted views on threads it did capture), not that the forum grew between the two
scrapes. This has not been independently confirmed (no scrape-date metadata was available to
check directly), so it is reported as the leading explanation, not a certainty.

Dropped in the rewrite: the old script's `TITLE_DROPS`/`TITLE_EIP_CORRECTIONS` hand-fixes for
known-bad EIP associations (EIPs 75/2/0 mismatched during the old scrape). Checked the new file
directly for the same three EIP numbers: no matching rows found, so these were specific fixes for
specific rows in the old scrape and are not carried forward.

Lost in the switch: the old file's per-EIP `Links` column has no equivalent in the new
comment-level file. `links` is now always null in `fem_data_for_regressions.parquet`; this is not
fabricated and matches `build_cross_sectional_dataset.py`'s own existing no-FEM-data fallback for
that column. Checked `table2_fem_regressions.py`: it does not reference `links` at all, so no
downstream regression depends on this field.

Paper text updated to match (`MS_R2.tex`): the "346 EIPs discussed on the board" sentence (now
448), and the FEM concentration paragraph's five numbers (1,101 to 1,370 contributors; "1.6M" to
"3.4M" views; 6,416 to 9,271 comments; 4,675 to 7,129 likes; "about 26%" to "about 13%" CAGR;
24.8% to 23.3% top-10 share; 71.6% to 72.6% Gini). Both FEM figures
(`Figures/FEM_Views_year.png`, `Figures/FEM_Lorenz_Comments.png`) regenerated from the new source
and copied over the old images at the same filenames.

Not touched: the GitHub-commits-per-EIP figure (`fig:commit_total`, a completely separate raw
file, `eip_commit_beg.xlsx`) and the client-development commit-concentration analysis (a third,
unrelated GitHub dataset). Neither was part of this request.

(x) Table 4 added: EIP discussion/development participation by venue (FEM, GitHub, AllCoreDevs)

New script `code/03_analysis/community_engagement/table4_participation_summary.py`, added as
pipeline stage 16 (after `table1_summary_stats`, before `did_labor_market_effects`). Produces
`output/tables/participation_summary.tex`, copied to `paper/latex/Tables/` and wired
into `MS_R2.tex` as Table 4 (`\label{tab:participation_summary}`), placed in
`\subsection{Concentration in EIP Discussion}` (`subsec:concentration_EIP_Discussion`) right
after the FEM and AllCoreDevs figures. Only the table itself was added; the surrounding
discussion text is still to be written (explicitly deferred by request).

History: this started as an off-pipeline side analysis ("here is a new version of the github
data... check whether results change") of a new raw file, one row per GitHub PR/issue
comment-or-review event (`eip`, `source`, `ref`, `kind` in {comment, review, review_comment},
`user`, `at`), which had no prior equivalent in this package -- the existing
`eip_commit_beg.xlsx` only has commits (actual code changes), not comment/review feedback. That
exploration (bot filtering, comment-vs-review breakdowns, FEM/GitHub/AllCoreDevs comparison
tables) was run ad hoc outside the repo; this entry documents its promotion into the pipeline
proper, not that prior exploration itself.

New raw data added: `data/raw/github/github_activity_clean.csv` (21,619 rows; copied in
unchanged). Two bot accounts excluded (`eip-automerger`, `maxrobot`) after scanning every unique
`user` value for bot-like names -- no others found.

Panel construction:
- **Panel A (FEM)**: reuses the existing `data/interim/fem_data_for_regressions.parquet`
  (Comments/Views/Likes/Active Participants = replies/views/likes/users), zero-filled over the
  612-EIP sample.
- **Panel B (GitHub)**: Commits reuses `eip_commit_beg.xlsx` with the same `eth-bot` exclusion
  as `fig_commit_timing.py::make_commits_per_eip()` (a different bot account than Panel B's own
  comment/review source, since it's a different platform-level log). Comment = `kind == "comment"`
  count from the new file; Reviews combines `kind` in {`review`, `review_comment`} (a review's own
  verdict plus any inline, line-anchored follow-up comments on it).
- **Panel C (AllCoreDevs)**: Active Participants (`acd_participants`) reuses the SAME cleaned
  meeting-attendee identity pipeline as `fig_commit_timing.py::_build_attendee_meeting_panel()`
  (flatten `dev_calls_attendees_standardized_v2.csv`, `clean_text()`, then the `Mapping_File.csv`
  name-correction map), not a naive comma-split on raw attendee strings. This deliberately gives a
  LOWER number than the earlier off-pipeline exploration's naive count (mean 7.27 vs. 8.92, max
  139 vs. 199) -- the naive version double-counted raw name-spelling variants as distinct people;
  the cleaned version is consistent with how every other AllCoreDevs figure in this paper (14a,
  14b) counts attendees. A "Meetings discussed at" row (`acd_meetings`, the count of distinct
  AllCoreDevs sessions an EIP appeared in) was computed but deliberately NOT included as a
  displayed row, per request.

New shared utility: `utils.reg_tables.format_panel_stats_table()` -- a multi-panel Mean/Median/
Std. Dev./Min/Max LaTeX table, mirroring the `\multicolumn{n}{l}{\textbf{Panel A. ...}}`
convention already used by Table 3's `table_did_results_mod.tex`, rather than introducing a new
table style. No N or zero-count column is shown (the denominator is the same fixed, zero-filled
612-EIP sample for every row).

`run_pipeline.py` correction made in the same pass: its `PIPELINE_STAGES` list had never actually
been updated when `fig_venn_diagram`/`table3_finalization_regressions`/`table2_fem_regressions`
were archived (see note at the top of (a) above) -- those three stages still pointed at files that
no longer exist at their old paths, which would have crashed a full pipeline run. Removed here,
alongside adding the new `table4_participation_summary` stage; the module docstring's DAG
description, ASCII sketch, and stage count were updated to match (17 stages total).

(xi) Prepared the package for public GitHub release (2026-11-02)

Five changes, made together so the package can be published as-is:

- **Removed outputs not in the current paper**: `fig_readability_and_status.py` no longer
  generates `success.png` (an EIP-status pie chart from the pre-revision paper's old "Figure 18");
  `fig_commit_timing.py` no longer fits the commits-around-dev-calls regression or generates
  `figure_15_commits_around_devcalls.png` (the pre-revision paper's old "Figure 15"); and
  `fig_abnormal_returns.py` no longer runs its two placebo CAR falsification designs or generates
  their four figures / two tables. None of these is referenced anywhere in the current
  `MS_R2.tex` (confirmed by full-text search before removing each). `run_pipeline.py`'s
  `expected_outputs` for the two affected stages were updated to point at files those scripts
  still actually produce (they previously pointed at the now-removed files, which would have
  silently broken `--skip-existing`).
- **Corrected the "labor-market analysis is a companion, not part of the paper" claim**, repeated
  in this file, `README.md`, and `did_labor_market_effects.py`'s own docstring. That was accurate
  when first written but went stale once the analysis was promoted into the manuscript as Section
  III (Table 3 / Figure 4) during the R2 revision. All three now describe it correctly.
- **Excluded WRDS-licensed and scraped-LinkedIn data from the public repo** via `.gitignore`:
  `data/raw/revelio/{author_to_revelio_userid.parquet,revelio_positions_enriched.parquet,
  revelio_user.parquet,_revelio_input.csv}` and `data/raw/social/{linkedin_data.csv,
  client_employment.csv}`. See `README.md`'s "Data availability" section for exactly which
  figures/tables this affects and how to regenerate them with your own access.
- **Excluded `revelio_pull/`** (the superseded, pre-pipeline exploratory work area) from the public
  repo entirely, also via `.gitignore` — it duplicates `labor_market_effects/` with extra Revelio
  fields, its own copy of the name-to-LinkedIn-URL crosswalk, and pre-publication draft memos/
  reports, none of which belong in a public release.
- **Rewrote `docs/figure_table_index.md`** from scratch against the current `MS_R2.tex` (it
  previously described the pre-revision paper: 24 figures, Table 2/3 = the now-archived
  regressions) and added each active script's current Figure/Table number + `\label{}` to its own
  module docstring, so the mapping is discoverable from either direction. Added a note (this
  file's top, and that file's own text) that figure/table numbers are a dated snapshot, not a
  fixed fact, since the manuscript is still under revision.

`git init` was run for the first time in this package's history (previously only the authors'
private `paper/latex_overleaf/` working copy was version-controlled, via its Overleaf-synced
remote; this public repo instead ships a flattened, non-git snapshot of that content at
`paper/latex/`, since git refuses to nest one repo inside another).
