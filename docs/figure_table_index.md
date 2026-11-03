# Figure & Table Index

This is the master cross-reference for the whole reproduction package. For every numbered
Figure/Table in the current manuscript —

> Fracassi, C., Khoja, M., & Schär, F. "Decentralized Crypto Governance? Transparency and
> Concentration in Ethereum Decision-Making." SSRN 4691000.

— it gives the paper section, the script in `code/` that generates it, and the output filename(s)
under `output/figures/` or `output/tables/`.

**Snapshot date: 2026-11-02. Source of truth: `paper/latex/MS_R2.tex`** (the manuscript
under revision for a Management Science resubmission), not the older SSRN PDF. The paper is still
being revised (the response-letter review has open points), so **Figure/Table numbers below will
shift again**. The stable identifier for each item is its LaTeX `\label{}`, given in the table
below; cite that, not the number, in anything meant to survive the next revision. Re-run the
cross-check in "How to refresh this file" before relying on the numbers for a submission.

An older version of this file described a pre-revision draft of the paper (24 figures, Table 2 =
FEM engagement regressions, Table 3 = EIP finalization regressions). That draft's regressions were
dropped from the paper during revision (see `archive/README.md`); the current manuscript instead
adds a labor-market/career-outcomes analysis (Table 3, Figure 4) and a new participation-by-venue
table (Table 4). This file has been rewritten against the current manuscript.

## Master table

| # | Label | Paper item | Section | Generating script | Output file(s) |
|---|---|---|---|---|---|
| Fig 1 | `EIP_process` | EIP Process (flow diagram) | Ethereum Governance | *(manual diagram, not code-generated — built in PowerPoint, see `paper/manual_figures/EIP_Flow_Chart.pptx`)* | `Figures/EIP_Process.png` |
| Fig 2 | `fig:neip_year` | Number of EIPs by Year | Data | `code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py` | `neip_by_year.png` |
| Tbl 1 | `summarystats` | Summary Statistics | Data | `code/03_analysis/regressions/table1_summary_stats.py` | `summstat.tex` |
| Fig 3 | `fig:CAR` | Ethereum Governance and Token Price (CARs, panel a = S&P 500, b = BTC) | Token Value | `code/03_analysis/token_price_effect/fig_abnormal_returns.py` | `CAR_SPY.png`, `CAR_BTC.png` |
| Tbl 2 | `tab:car_event_study` | CARs around AllCoreDevs Discussion of Finalized Core EIPs | Token Value | `code/03_analysis/token_price_effect/fig_abnormal_returns.py` | `car_event_study.tex` |
| Tbl 3 | `tab:did_main` | Effect of EIP Authorship on Seniority and Compensation (Panel A balance, B seniority, C log comp) | Labor Market | `code/03_analysis/labor_market_effects/did_labor_market_effects.py` | `table_did_results_mod.tex` (hand-formatted copy of the script's own `table_did_results.tex`; numbers match, whitespace differs) |
| Fig 4 | `fig:labor` | Seniority (a) / Total Compensation, log (b) event-study coefficients | Labor Market | `code/03_analysis/labor_market_effects/did_labor_market_effects.py` | `EIP_W2_EventStudy_Seniority.png`, `EIP_W2_EventStudy_LogComp.png` |
| Fig 5 | `fig:understand` | EIP Readability: score histogram (a), length histogram (b) | Transparency | `code/03_analysis/transparency_openness/fig_readability_and_status.py` | `read_hist.png`, `nwords_hist.png` |
| Fig 6 | `fig:anon` | Anonymity in the Ethereum Governance Process | Transparency | `code/03_analysis/transparency_openness/fig_anonymity.py` | `Anonymity_Diagram.png` |
| Fig 7 | `n_author_by_stage` | Number of EIP Authors (by stage) | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py` | `n_authors_by_stage.png` |
| Fig 8 | `top10_author` | Top 10 EIP Authors (all / finalized ERC-Interface / implemented Core-Network) | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py` | `neip_top10author.png`, `neip_final_top10author.png`, `neip_imp_top10author.png` |
| Fig 9 | `fig:between` | EIP Co-Authorship Network | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_network_centrality.py` | `eip_between_all.png` |
| Fig 10 | `lorenz_authorship` | EIP Introduction Concentration (Lorenz, by author count / percentile) | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py` | `neip_by_author.png`, `npeip_by_author.png` |
| Fig 11 | `fig:gini_year` | Concentration of EIP Production over Time (Gini, rolling) | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_eip_trends_and_concentration.py` | `gini_by_year.png` |
| Fig 12 | `fig:clustering_trends` | Decentralization of EIP Co-Authorship over Time | Concentration in EIP Proposals | `code/03_analysis/eip_concentration/fig_network_centrality.py` | `clustering_trends.png` |
| Tbl 4 | `tab:participation_summary` | Participation in EIP Discussion by Venue (Panel A FEM, B GitHub, C AllCoreDevs) | Concentration in EIP Discussion | `code/03_analysis/community_engagement/table4_participation_summary.py` | `participation_summary.tex` |
| Fig 13 | `fig:FEM` | Discussion on FEM (views by year; Lorenz of comments) | Concentration in EIP Discussion | `code/03_analysis/community_engagement/fig_fem_engagement.py` | `FEM_Views_year.png`, `FEM_Lorenz_Comments.png` |
| Fig 14 | `fig:commit_total` | Number of GitHub Commits by EIP | Concentration in EIP Discussion | `code/03_analysis/community_engagement/fig_commit_timing.py` | `commit_total.png` |
| Fig 15 | `fig:attendees` | AllCoreDevs Calls Attendees (by year; vs. authorship) | Concentration in EIP Discussion | `code/03_analysis/community_engagement/fig_commit_timing.py` | `attendees_year.png`, `attended_eip.png` |
| Fig 16 | `fig:lorenz_commits` | Client Implementation Concentration | Concentration in Client Development | `code/03_analysis/client_concentration/fig_client_concentration.py` | `lorenz_commits.png` |
| Fig 17 | `fig:forks` | History of Forks (timeline) | Concentration in Client Adoption | *(none — pure LaTeX `chronology` environment, no image)* | — |
| Fig 18 | `fig:stable_perc` / `fig:stable` | Stablecoin Concentration (TVL %, market share) | Concentration in Client Adoption | `code/03_analysis/adoption_stablecoins_oracles/fig_adoption.py` | `stable_perc.png`, `stable.png` |
| Fig 19 | `fig:oracle` | Oracle Concentration (TVL share pie; protocol count) | Concentration in Client Adoption | `code/03_analysis/adoption_stablecoins_oracles/fig_adoption.py` | `oracle_pie.png`, `oracle_bar.png` |
| Fig 20 | `fig:ncomp` | Organizations Affiliated with EIP Authors and Client Developers (panels a-d) | Section V.5 | `code/03_analysis/company_influence/fig_company_concentration.py` (panels a-c) + `code/03_analysis/client_concentration/fig_client_concentration.py` (panel d) | `company_lorenz.png`, `company_neip2.png`, `company_neip3.png`, `client_company.png` |
| Fig 21 | `fig:ef_year` | Influence of Ethereum Foundation over Time | Section V.5 | `code/03_analysis/company_influence/fig_company_concentration.py` | `eip_ef_by_year.png` |

**Totals: 21 numbered figures (one, `fig:forks`, has no image; one, `EIP_process`, is a manual
diagram), 4 numbered tables.** Figure 20 is the one item produced by two scripts, each
responsible for a disjoint subset of its panels.

## A note on filenames

Most scripts write to `output/figures/`/`output/tables/` under their own, script-native filenames
(e.g. `figure_10a_eip_network_all.png`), which are then manually copied, and sometimes renamed, into
`paper/latex/Figures/`/`Tables/` under the filename the LaTeX source actually
`\includegraphics`/`\input`s (e.g. `eip_between_all.png`). This copy step is not itself scripted.
The table above gives the paper-facing filename; each script's own docstring gives the mapping to
its native output name.

## Data availability: the labor-market analysis (Table 3, Figure 4)

`did_labor_market_effects.py` reads Revelio Labs LinkedIn-derived career data
(`data/raw/revelio/*.parquet`, `_revelio_input.csv`), accessed through a WRDS institutional
license. **That data is not included in this public repository** — WRDS license terms do not
permit redistributing the underlying vendor data — so this one stage cannot be re-run out of the
box. The already-produced table and figures are checked in under `paper/latex/`/
`output/` so the result is visible without re-running it. See the script's own docstring and
`README.md`'s "Data availability" section for what you need to regenerate it with your own
WRDS/Revelio access. The same applies to Figure 20's panels a-c (`fig_company_concentration.py`,
via the cross-sectional dataset's `author{n}_company{c}` columns, built from
`data/raw/social/linkedin_data.csv`) and panel d (`fig_client_concentration.py`, directly from
`data/raw/social/client_employment.csv`) — a separate scraped LinkedIn dataset, also excluded from
this repo for the same reason. Figure 6 (anonymity) does not depend on either file.

## Outputs generated but not part of the current paper

A few scripts generate one or more extra files, alongside their actual paper output, left over
from an earlier version of the paper or never published at all. Per the "only reproduce what the
paper publishes" convention (see `archive/README.md`), these are no longer generated by default:

| Former output | Was | Removed from |
|---|---|---|
| `success.png` | A pie chart of EIP status (pre-revision paper's "Figure 18") | `fig_readability_and_status.py` |
| `figure_15_commits_around_devcalls.png` / `commit_call.png` | A commit-timing event-study regression plot (pre-revision paper's "Figure 15") | `fig_commit_timing.py` |
| `figure_24c-f_car_placebo*.png`, `car_event_study_placebo_t{40,80}.tex` | Two placebo falsification designs for the CAR event study | `fig_abnormal_returns.py` |

Three whole scripts (and their outputs) were moved to `archive/code/` for the same reason, each
confirmed absent from `MS_R2.tex` by a direct full-text search: `table2_fem_regressions.py`
(old Table 2), `table3_finalization_regressions.py` (old Table 3 + its `cdum_coef.png`
companion figure), and `fig_venn_diagram.py` (old Figure 5). See `archive/README.md` for the
full history.

`did_labor_market_effects_quarterly.py` is an active script, not an orphan: it backs an unlabeled
robustness footnote in `MS_R2.tex` (the quarterly-frequency check) rather than a numbered
Figure/Table, so it correctly has no entry in the master table above.

## How to refresh this file

Figure/Table numbers in LaTeX are assigned at compile time and shift whenever a figure or table is
added, removed, or reordered — which happens routinely while a revision is open. Before relying on
the numbers above (e.g., for a submission or for writing a referee response), regenerate this
mapping:

1. Grep `paper/latex/MS_R2.tex` for every `\begin{figure}`/`\begin{table}` (or `\input{Tables/...}`)
   in document order, noting each one's `\label{}` and `\includegraphics`/`\input` target(s).
2. For each output filename, grep `code/03_analysis/` for the script that writes it.
3. Update the table above and this file's snapshot date.
