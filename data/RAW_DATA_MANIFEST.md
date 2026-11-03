# Raw Data Manifest

Source root: `C:\Users\cf8745\Box\Research\Ethereum Governance 2\Ethereum_Governance_Project` (READ-ONLY — nothing in it was modified, moved, or deleted).
Destination root: `C:\Users\cf8745\Box\Research\Decentralized Crypto Governance`.

All paths below are relative to those two roots. Sizes are as copied (identical to source, except the four
client-commit files and the cross-sectional reference dataset, which were converted from Stata `.dta` to
Parquet+zstd).

## `data/raw/eip_registry/`

| Source path | Destination path | Size | Rows x Cols | Notes |
|---|---|---|---|---|
| `Data\Raw Data\allEIPsandAuthorsv2.csv` | `data/raw/eip_registry/allEIPsandAuthorsv2.csv` | 68,875 B | – | Master EIP x author registry. Feeds most EIP-level analyses (centrality, EF-by-year, summary stats). |
| `Data\Raw Data\eip_startdates.csv` | `data/raw/eip_registry/eip_startdates.csv` | 10,866 B | – | EIP proposal start dates. Feeds cross-sectional data build and event-study timing. |
| `Data\Raw Data\finaleip_enddates.csv` | `data/raw/eip_registry/finaleip_enddates.csv` | 73,642 B | – | EIP "Final" status end dates. Feeds duration/stage analyses. |
| `Data\Raw Data\eip_word_count.csv` | `data/raw/eip_registry/eip_word_count.csv` | 13,126 B | – | Word counts per EIP. Feeds `nwords_hist.png` / readability stats. |
| `Data\Raw Data\eip_implementation.xlsx` | `data/raw/eip_registry/eip_implementation.xlsx` | 29,066 B | – | EIP implementation status/dates. Feeds implemented-vs-not comparisons (`final_noimpl_impl.tex`). |
| `Data\Raw Data\Fork_announcement.csv` | `data/raw/eip_registry/Fork_announcement.csv` | 1,854 B | – | Ethereum hard-fork announcement dates. Feeds event-study/fork-timing figures. |
| `Data\Raw Data\unique_author_names_with_id.csv` | `data/raw/eip_registry/unique_author_names_with_id.csv` | 19,805 B | – | Canonical EIP author name→ID crosswalk. Feeds author-level centrality/Lorenz/Gini analyses. |
| `Data\Raw Data\allEIPswithdates.csv` | `data/raw/eip_registry/allEIPswithdates.csv` | 73,648 B | – | **Copied after investigation (see step 8 below).** EIP list with start dates; referenced by a work-in-progress fetch script. |

*(First 7 rows were already copied by the prior session; verified present and non-empty, not re-copied.)*

## `data/raw/social/`

| Source path | Destination path | Size | Notes |
|---|---|---|---|
| `Data\Raw Data\twitter_data.csv` | `data/raw/social/twitter_data.csv` | 41,683 B | Author Twitter/X handles and metrics. Feeds social/EF crosswalk. |
| `Data\Raw Data\GitHub_Data.csv` | `data/raw/social/GitHub_Data.csv` | 33,841 B | Author GitHub handles/activity. Feeds commit-author matching. |
| `Data\Raw Data\linkedin_data.csv` | `data/raw/social/linkedin_data.csv` | 126,005 B | Author LinkedIn/employment profile data. Feeds client/employer analysis. |
| `Data\Raw Data\Author_EF.csv` | `data/raw/social/Author_EF.csv` | 968 B | Author↔Ethereum Foundation affiliation flag. Feeds EF-by-year figures. |
| `Data\Raw Data\client_employment.csv` | `data/raw/social/client_employment.csv` | 4,499 B | Author↔employer (client) mapping. Feeds Client Analysis (Lorenz, company figures). |

*(Already copied by the prior session; verified present and non-empty, not re-copied.)*

## `data/raw/commits/`

| Source path | Destination path | Size | Rows x Cols | Notes |
|---|---|---|---|---|
| `Data\Commit Data\Eip Commit Data\eip_commit_beg.xlsx` | `data/raw/commits/eip_commit_beg.xlsx` | 548,266 B | – | Raw EIP-repo commit log. Feeds commit-around-meetings analysis. |
| `Data\Commit Data\client_commit\besu_commits.dta` | `data/raw/commits/client_commit/besu_commits.parquet` | 245,891 B | 4,596 x 4 (`author, identifier, date, message`) | Converted Stata→Parquet (zstd) via pandas→polars. Feeds client-commit Lorenz/company analysis. |
| `Data\Commit Data\client_commit\erigon_commits.dta` | `data/raw/commits/client_commit/erigon_commits.parquet` | 684,108 B | 20,565 x 4 (same cols) | Same conversion. |
| `Data\Commit Data\client_commit\geth_commits.dta` | `data/raw/commits/client_commit/geth_commits.parquet` | 524,488 B | 14,717 x 4 (same cols) | Same conversion. |
| `Data\Commit Data\client_commit\nethermind_commits.dta` | `data/raw/commits/client_commit/nethermind_commits.parquet` | 223,926 B | 7,522 x 4 (same cols) | Same conversion. |

`Data\Commit Data\client_commit\Old Data\*.dta` intentionally NOT copied (superseded, out of scope per instructions).

## `data/raw/forum/`

| Source path | Destination path | Size | Notes |
|---|---|---|---|
| `Analysis\Magician Comments\ethereum_magicians_data_scraped.csv` | `data/raw/forum/ethereum_magicians_data_scraped.csv` | 10,830,793 B | Raw scraped Ethereum Magicians (FEM) forum comment data. Feeds Magician Comments regressions (`FEM_reg_out.tex`, Lorenz/views figures). |
| `Analysis\Magician Comments\list_of_FEM_EIP_pages.csv` | `data/raw/forum/list_of_FEM_EIP_pages.csv` | 78,641 B | List of FEM forum pages/threads scraped per EIP. Feeds the same scraping/regression pipeline. |

## `data/raw/meetings/`

| Source path | Destination path | Size | Notes |
|---|---|---|---|
| `Analysis\Meeting Attendees and Ethereum Community Analysis\calls_updated_standardized.csv` | `data/raw/meetings/calls_updated_standardized.csv` | 86,306 B | GPT/date-standardized dev-call metadata (calls, dates). Feeds meeting/commit-around-calls analysis and community engagement figures. |
| `Analysis\Meeting Attendees and Ethereum Community Analysis\Name Cleaning\dev_calls_attendees_standardized_v2.csv` | `data/raw/meetings/dev_calls_attendees_standardized_v2.csv` | 53,519 B | Standardized dev-call attendee roster (v2). Feeds attendee/name-cleaning pipeline and venn/community figures. |

**`calls_updated.csv` (pre-standardization raw version, no `_standardized` suffix):** searched the entire source
tree (file listing, not just grep) — the file does **not exist anywhere** on disk. It IS referenced as an input
by `Analysis\Abnormal Returns\Code to Create Meeting Dates.py` (`pd.read_csv('calls_updated.csv')` → writes
`calls_updated_standardized.csv`), so it was clearly the upstream input at some point, but it appears to have
been deleted/not retained in this backup of the project. Not copied because it could not be found. This is the
only requested/expected file across the entire task that could not be located.

## `data/raw/name_cleaning_manual/` (flattened, all from `Analysis\Meeting Attendees and Ethereum Community Analysis\Name Cleaning\`)

| Source file | Destination path | Size | Notes |
|---|---|---|---|
| `clients_name_to_change_post_manual.csv` | `data/raw/name_cleaning_manual/clients_name_to_change_post_manual.csv` | 1,311 B | Manually-reviewed client-name correction pass 1. |
| `client_names_to_change2_post_manual.csv` | `data/raw/name_cleaning_manual/client_names_to_change2_post_manual.csv` | 1,353 B | Manually-reviewed client-name correction pass 2. |
| `client_names_to_change3_post_manual.csv` | `data/raw/name_cleaning_manual/client_names_to_change3_post_manual.csv` | 350 B | Manually-reviewed client-name correction pass 3. |
| `names_to_change_post_manual.csv` | `data/raw/name_cleaning_manual/names_to_change_post_manual.csv` | 7,647 B | Manually-reviewed person-name correction pass 1. |
| `names_to_change2_post_manual.csv` | `data/raw/name_cleaning_manual/names_to_change2_post_manual.csv` | 1,826 B | Manually-reviewed person-name correction pass 2. |
| `names_to_change3_post_manual.csv` | `data/raw/name_cleaning_manual/names_to_change3_post_manual.csv` | 1,299 B | Manually-reviewed person-name correction pass 3. |
| `total_names_to_change_post_manual.csv` | `data/raw/name_cleaning_manual/total_names_to_change_post_manual.csv` | 741 B | Combined/total name-correction pass 1. |
| `total_names_to_change2_post_manual.csv` | `data/raw/name_cleaning_manual/total_names_to_change2_post_manual.csv` | 611 B | Combined/total name-correction pass 2. |
| `total_names_to_change3_post_manual.csv` | `data/raw/name_cleaning_manual/total_names_to_change3_post_manual.csv` | 324 B | Combined/total name-correction pass 3. |
| `Mapping_File.csv` | `data/raw/name_cleaning_manual/Mapping_File.csv` | 103,715 B | Final name→canonical-name mapping (authors/contributors). |
| `Attendees_Mapping_File.csv` | `data/raw/name_cleaning_manual/Attendees_Mapping_File.csv` | 28,021 B | Final name→canonical-name mapping (meeting attendees). |
| `Client_Mapping_File.csv` | `data/raw/name_cleaning_manual/Client_Mapping_File.csv` | 40,370 B | Final name→canonical-name mapping (clients/companies). |
| `all_Mapping_File.csv` | `data/raw/name_cleaning_manual/all_Mapping_File.csv` | 108,160 B | Combined/union of all name mappings across authors, attendees, and clients. |

All of the above feed `Name Cleaning Code for Attendees.py`, `Name Cleaning Code for Contributors and Clients.py`,
and `Name Cleaning Code Cross List.py`, which produce the standardized name lists used throughout the
community/centrality/client analyses.

## `data/raw/prices/`

| Source path | Destination path | Size | Notes |
|---|---|---|---|
| `Data\Raw Data\eth_prices.csv` | `data/raw/prices/eth_prices.csv` | 14,249,698 B | Daily/intraday ETH price series. Feeds abnormal-return (CAR) event studies. |
| `Data\Raw Data\btc_prices.csv` | `data/raw/prices/btc_prices.csv` | 16,105,005 B | Daily/intraday BTC price series (market benchmark). Feeds abnormal-return (CAR) event studies. |

Confirmed byte-identical in content to `Analysis\Abnormal Returns\eth_prices.csv` / `btc_prices.csv` (differ only
in line endings per prior verification) — those duplicates were correctly NOT copied.

## `data/raw/adoption/`

| Source path | Destination path | Size | Notes |
|---|---|---|---|
| `Analysis\Adoption Analysis\oracle_data.csv` | `data/raw/adoption/oracle_data.csv` | 409 B | Oracle protocol adoption/TVL summary. Feeds `oracle_bar.png`, `oracle_pie.png`. |
| `Analysis\Adoption Analysis\USDC_MASTER.csv` | `data/raw/adoption/USDC_MASTER.csv` | 215,088 B | USDC stablecoin adoption/volume master series. Feeds `stable.png`, `stable_perc.png`. |
| `Analysis\Adoption Analysis\USDT_MASTER.csv` | `data/raw/adoption/USDT_MASTER.csv` | 209,762 B | USDT stablecoin adoption/volume master series. Same figures. |
| `Analysis\Adoption Analysis\DAI_MASTER.csv` | `data/raw/adoption/DAI_MASTER.csv` | 257,582 B | DAI stablecoin adoption/volume master series. Same figures. |
| `Analysis\Adoption Analysis\Total_TVL_ETH.csv` | `data/raw/adoption/Total_TVL_ETH.csv` | 46,656 B | Total ETH TVL series. Feeds oracle/TVL adoption figures. |
| `Analysis\Adoption Analysis\converted_dai.sql` | `data/raw/adoption/sql_provenance/converted_dai.sql` | 17,099 B | SQL provenance/query used to build DAI_MASTER.csv (Dune/BigQuery-style query, kept for traceability only). |
| `Analysis\Adoption Analysis\converted_usdc.sql` | `data/raw/adoption/sql_provenance/converted_usdc.sql` | 19,339 B | SQL provenance for USDC_MASTER.csv. |
| `Analysis\Adoption Analysis\usdt_master.sql` | `data/raw/adoption/sql_provenance/usdt_master.sql` | 12,014 B | SQL provenance for USDT_MASTER.csv. |

*(`sql_provenance` subfolder existed but was empty prior to this session; the 3 files above were not yet present
and were copied now.)*

## `data/reference/` (verification-only outputs — NOT pipeline inputs)

| Source path | Destination path | Size | Rows x Cols | Notes |
|---|---|---|---|---|
| `Data\Raw Data\Ethereum_Cross-sectional_Data.dta` | `data/reference/Ethereum_Cross-sectional_Data.parquet` | 481,315 B | 612 x 750 | Converted Stata→Parquet (zstd). **This is the master cross-sectional dataset used to verify every other result.** See conversion-comparison note below. |
| `Data\Raw Data\Ethereum_Cross-sectional_Data_output.csv` | `data/reference/Ethereum_Cross-sectional_Data_output.csv` | 1,424,742 B | – | Original published CSV export of the cross-sectional dataset (companion to the .dta). |

### `pandas.read_stata` conversion comparison (default vs. `convert_categoricals=False`)

Both conversions were run on `Ethereum_Cross-sectional_Data.dta` and produce the **same shape (612 rows x 750
cols)** and the **same column list**. Exactly **one column differs**: `category_encoded`.
- Default (`pd.read_stata(path)`): `category_encoded` comes back as a **labeled Categorical** (Stata value labels
  applied, ordering='physical').
- `convert_categoricals=False`: `category_encoded` comes back as the **raw underlying integer code** (`Int32`),
  with no labels applied.

All other 749 columns are identical between the two conversions (checked by casting every common column to
string and comparing element-wise). **The Parquet file saved to `data/reference/` uses the default
(labeled-categorical) conversion**, i.e. `category_encoded` is stored as a Polars `Categorical`. If the
reproduction pipeline needs the raw Stata integer codes for `category_encoded` instead of the label strings,
regenerate from `Ethereum_Cross-sectional_Data.dta` with `convert_categoricals=False`.

### `data/reference/original_figures/` (43 files)

| Source path | Notes |
|---|---|
| `Analysis\Results\Figures\*.png` (18 files: `cdum_coef`, `company_lorenz`, `company_neip1/2/3`, `eip_by_category`, `eip_ef_by_year`, `gini_by_year`, `n_authors_by_stage`, `neip_by_author`, `neip_by_year`, `neip_final_top10author`, `neip_imp_top10author`, `neip_top10author`, `npeip_by_author`, `nwords_hist`, `read_hist`, `success`) | Copied all files present in this folder. **Note:** the task instructions said "all 15 PNGs" but the folder actually contains 18 — all 18 were copied (none skipped). |
| `Analysis\Abnormal Returns\CAR_BTC.png`, `CAR_SPY.png` | Event-study abnormal-return charts. |
| `Analysis\Adoption Analysis\oracle_bar.png`, `oracle_pie.png`, `stable.png`, `stable_perc.png` | Adoption figures. |
| `Analysis\Anonymity Analysis\Anonymity_Diagram.png` | Anonymity figure. |
| `Analysis\Client Analysis\client_company.png`, `lorenz_commits.png` | Client analysis figures. |
| `Analysis\Commit Analysis Around Meetings\attended_eip.png`, `attendees_year.png`, `commit_call.png`, `commit_total.png` | Commit-around-meetings figures. |
| `Analysis\Meeting Attendees and Ethereum Community Analysis\venn_diagram.png` | Community venn diagram. |
| `Analysis\Centrality Analysis\eip_between_all.png`, `eip_between_final.png`, `eip_between_imp.png`, `eip_close_all.png`, `eip_close_final.png`, `eip_close_imp.png`, `eip_eigen_all.png`, `eip_eigen_final.png`, `eip_eigen_imp.png`, `clustering_trends.png` | Only these 10 selected centrality figures copied, per instructions — all `eip_between_<number>.png` diagnostic-loop files (hundreds of them) in that folder were intentionally skipped. |
| `Analysis\Magician Comments\FEM_Lorenz_Comments.png`, `FEM_Views_year.png` | Both files already had proper `.png` extensions on disk (verified via directory listing) — copied as-is, no renaming needed. |

### `data/reference/original_tables/` (8 files)

| Source path | Notes |
|---|---|
| `Analysis\Results\Tables\commit_call.tex`, `final_all.tex`, `final_all_alt1.tex`, `final_all_alt2.tex`, `final_noimpl_impl.tex`, `summstat.tex` | Main regression/summary-stat tables (6 files). |
| `Analysis\Magician Comments\FEM_reg_out.tex`, `FEM_reg_out_log.tex` | FEM forum-comment regression tables. |

---

## Investigated, NOT copied (orphaned) — step 8 files

| # | File | Grep result across all `.py`/`.do` in source tree | Recommendation |
|---|---|---|---|
| 1 | `Data\Raw Data\allEIPswithdates.csv` | **Referenced.** Read by `Data\Raw Data\Linkedin Data\revelio_pull\Ethereum_Governance\WiP\01_fetch_eip_data.py` (`pd.read_csv(f"{RAW}/allEIPswithdates.csv", ...)`) as the "Start dates for Final EIPs (user-curated)". | **Copied** to `data/raw/eip_registry/allEIPswithdates.csv` (listed above) since it is an active input to a script, despite living in a "WiP" folder. |
| 2 | `Data\Raw Data\updated_commits.xlsx` | No matches in any `.py` or `.do` file. | Leave out — orphaned/unused. |
| 3 | `Analysis\Magician Comments\ethereum_sentiment.csv` | No matches in any `.py` or `.do` file. | Leave out — orphaned/unused. |
| 4 | `Analysis\Abnormal Returns\eth_vols.csv` | No matches in any `.py` or `.do` file (including within the Abnormal Returns folder's own scripts). | Leave out — orphaned/unused. |
| 5 | `Analysis\Meeting Attendees and Ethereum Community Analysis\Name Cleaning\author_anonymity_flag.csv` | No matches. `Anonymity Analysis.py` computes an `Anonymity_Flag` column itself from merged data rather than reading this file. | Leave out — orphaned/unused. |
| 6 | `...\Name Cleaning\Attendeelist_before_assigning_firstnames_to_multiple_persons.csv` | Only appears in a **commented-out** line in `Name Cleaning Code for Attendees.py` (`#unique_attendee4.to_csv("Attendeelist_before_assigning_firstnames_to_multiple_persons.csv")`) — not an active input or output. | Leave out — confirmed dead/inactive code path. |
| 7 | `...\Name Cleaning\flat_list_meeting_attendees_old.csv` | No matches for the `_old` filename anywhere. The non-`_old` `flat_list_meeting_attendees.csv` IS actively read by `eip_commit_around_devcalls.do`, `Top10_in_community.py`, and `Name Cleaning Code for Attendees.py`, and is written by `python code to create flat list.py`. | Confirmed superseded — leave out. |

## Files that could not be found at their expected path

- `calls_updated.csv` (see note under `data/raw/meetings/` above) — referenced by source code but the file
  itself does not exist anywhere in the source tree. This is the only file from the entire task that could not
  be located after a full-tree search.

All other files listed in the task were found at their expected paths (or, for the two `.png` files checked for
missing extensions, already had correct extensions) and copied successfully; none were 0-byte or truncated.
