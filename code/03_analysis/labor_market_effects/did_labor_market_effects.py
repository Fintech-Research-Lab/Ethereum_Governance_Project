"""
did_labor_market_effects.py
============================

Reproduces **Table 3** (`\\label{tab:did_main}`, "The Effect of EIP Authorship on Seniority and
Compensation") and **Figure 4** (`\\label{fig:labor}`) of the current manuscript,
`paper/latex/MS_R2.tex`: does authoring an Ethereum Improvement Proposal (EIP) change an
author's career trajectory? Figure/table numbers shift as the paper is revised; see
`docs/figure_table_index.md` for the current numbering snapshot and its date. This analysis was
originally developed as an exploratory side question, independent of the paper's governance-
concentration focus; it has since been promoted into the manuscript as Section III.

    Fracassi, C., Khoja, M., & Schar, F. (2024). "Decentralized Crypto Governance? Transparency
    and Concentration in Ethereum Decision-Making." SSRN 4691000.

Data availability
------------------
This stage reads Revelio Labs LinkedIn-derived data (`data/raw/revelio/*.parquet`,
`_revelio_input.csv`), accessed through a WRDS institutional license. That data is NOT included
in this public repository (license terms do not permit redistribution); see README.md's "Data
availability" section for what you need to re-run this stage yourself, and
`archive/code/01_data_collection/pull_revelio.py` / `enrich_revelio.py` for the original pull
code. The already-produced output table/figure are checked in so the result is visible without
re-running.

Where this came from
---------------------
This script and its data-quality companion `data_checks.py` were developed in a separate
exploratory project that linked EIP authors to LinkedIn-derived employment histories and ran a
stacked-cohort difference-in-differences design on the result, before being promoted into this
package and the manuscript as described above.

Produces
--------
    output/tables/table_did_results.tex               One combined table, three panels: Panel A
                                                        is covariate balance at t-1; Panels B and
                                                        C are the difference-in-differences
                                                        results (static, dynamic, junior/senior
                                                        split) for seniority and log compensation
                                                        respectively
    output/figures/EIP_W2_EventStudy_Seniority.png     Event-study figure, seniority coefficients
    output/figures/EIP_W2_EventStudy_LogComp.png       Event-study figure, log compensation
                                                        coefficients

Every intermediate (the cached annual panel, the matched stacked sample, the raw
coefficients/SEs as JSON) is written to `data/interim/labor_market_effects/`, so the three files
above stay the only things this stage puts in `output/`.

SPECIFICATION
-------------
    Design      : stacked difference-in-differences, individual-author cohorts
    Window      : +/- 2 years, annual, end-of-year outcome measurement
    Treatment   : author >= 1 EIP in year g, having authored none in [g-2, g-1]
    Controls    : EIP authors with NO EIP anywhere in [g-2, g+2]
                  (a treated author is thereby excluded from any overlapping
                   cohort; controls may repeat across cohorts)
    Matching    : Stage 1 - EXACT on integer seniority at t-2 AND t-1
                  Stage 2 - Mahalanobis over log compensation at t-2, t-1
                            within the exact-seniority cell
                  Caliper - chi2(0.90, df=2); <= 3 controls per cohort
                  NOTE: prestige and education are deliberately NOT matched;
                        they are reported as out-of-sample balance checks.
    Outcomes    : seniority (Revelio 1-7) and log(total compensation)
    Estimation  : OLS, UNWEIGHTED, y in levels (compensation in logs). Author x cohort and
                  cohort x event-time fixed effects, absorbed by the exact within-transformation.
                  The same regression is also run with the effects as literal dummy variables
                  and the pipeline verifies the two agree at every run (see `verify()`).
                  Degrees of freedom follow the absorbed (`xtreg, fe`) convention.
                  SEs clustered on the author.
    ATT         : coefficient on treated x 1{t >= +1}; t = 0 estimated separately, since the
                  end-of-year outcome in the event year may reflect months after the EIP.

DATA PROVENANCE
---------------
Dates come from a single source, `data/raw/eip_registry/eip_startdates.csv` (100% coverage of
the 639 EIPs in the authoritative author list). A reconciliation against
`allEIPswithdates.csv`'s `Start` column for the 159 Final EIPs common to both finds 155 (97.5%)
identical to the day; the 4 that disagree (EIPs 6, 7, 8, 20) all match the canonical `created`
field in the ethereum/EIPs and ethereum/ERCs repositories on the `eip_startdates.csv` side, so
that file is used throughout. See `data_checks.py` to reproduce this check (not part of this
pipeline).

The EIP `Author` field is free text with no author_id, so authors are linked to Revelio Labs
person ids by fuzzy name match (`rapidfuzz.process.extractOne`, `token_sort_ratio`, threshold
80): 490 of 491 Revelio authors match, 484 of those exactly (score 100); the remaining 6 are
diacritic/encoding artifacts, all demonstrably correct. Cross-validated against a GitHub-handle
join wherever the free text carries a "(@handle)" token: 751 of 751 handle-resolvable rows agree
(100.0%) -- see `data_checks.py`.

A NOTE ON PANDAS
-----------------
This project's convention elsewhere is Polars-only, with pandas reserved for hard boundaries
that require it (see `code/config.py`'s module docstring). This script is itself such a
boundary, end to end: the cohort/matching step is a per-event Python loop over
`scipy.spatial.distance.cdist` results keyed by pandas' `groupby`/`.loc` indexing, and the
estimation step builds `statsmodels` design matrices with `pandas.get_dummies` and grouped
demeaning. Rewriting that combination in Polars would touch exactly the matching and regression
logic this analysis exists to get right, for a script whose numbers are meant to be checked
against a specific published-looking table -- not a place to introduce a translation bug. It is
kept in pandas throughout, deliberately, rather than converted at the boundary as usual.

USAGE
-----
    python did_labor_market_effects.py            # full run (rebuilds panels if needed)
    python did_labor_market_effects.py --rebuild   # force rebuild of cached panels
    python did_labor_market_effects.py --final     # restrict to finalized EIPs (see
                                                    # `build_eip_events`'s docstring: this
                                                    # discards ~3/4 of events and selects on
                                                    # the outcome; reported alongside, not
                                                    # instead of, the main "all EIPs" run)

REQUIREMENTS
------------
    pandas, numpy, scipy, statsmodels, matplotlib, pyarrow, rapidfuzz
"""

from __future__ import annotations

import sys
from pathlib import Path

import os, re, json, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from scipy.stats import chi2
from scipy import stats as sps
from scipy.spatial.distance import cdist
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # add code/ to sys.path

from config import DATA_RAW, DATA_INTERIM, OUTPUT_TABLES, OUTPUT_FIGURES, ensure_dirs

# ==============================================================================
# 0. PATHS
# ==============================================================================
RAWDATA = DATA_RAW / "eip_registry"
REVELIO = DATA_RAW / "revelio"
OUTDIR_TABLES  = OUTPUT_TABLES
OUTDIR_FIGURES = OUTPUT_FIGURES
CACHE   = DATA_INTERIM / "labor_market_effects"     # intermediate panels, results JSON/CSV

REBUILD = "--rebuild" in sys.argv
EIP_SUBSET_CLI = "final" if "--final" in sys.argv else "all"

# ==============================================================================
# 1. SPECIFICATION CONSTANTS
# ==============================================================================
W           = 2          # event window (+/- years)
N_CONTROLS  = 3           # maximum controls per cohort
CALIPER_Q   = 0.90        # caliper quantile of the chi2 distribution
FUZZY_THRESHOLD = 80      # rapidfuzz token_sort_ratio cut-off for the author name join
MIN_YEAR, MAX_YEAR = 2010, 2025


def read_cache(path):
    """Read a cached parquet, tolerating cloud-storage eviction (Box/OneDrive).

    Cloud-synced folders may leave a placeholder that raises OSError on read;
    in that case we return None so the caller rebuilds from source.
    """
    if not os.path.exists(path):
        return None
    try:
        return pd.read_parquet(path)
    except (OSError, IOError):
        print(f"      [cache unreadable, rebuilding] {os.path.basename(path)}")
        return None


def write_cache(df, path):
    try:
        df.to_parquet(path, index=False, compression="zstd")
    except (OSError, IOError):
        print(f"      [warning: could not write cache] {os.path.basename(path)}")


# ==============================================================================
# 2. BUILD EIP AUTHORSHIP EVENTS  (author_id x calendar year)
# ==============================================================================
def build_eip_events(subset="all"):
    """EIP authorship events dated by CREATION (proposal) date.

    Parameters
    ----------
    subset : {"all", "final"}
        "all"   - every EIP in the authoritative author list (639 EIPs).
        "final" - only EIPs with Status == "Final", i.e. proposals that were
                  actually adopted into the protocol. Discards roughly three
                  quarters of the events and selects on the outcome, so it is
                  reported alongside, not instead of, the full sample.

    Returns a table with one row per (author_id, EIP): author_id, Number,
    Status, best_date, eip_year, eip_month.
    """
    from rapidfuzz import process, fuzz

    # -- (i) start dates: single internal source, 100% coverage -------------
    sd = pd.read_csv(os.path.join(RAWDATA, "eip_startdates.csv"), encoding="latin-1")
    sd.columns = [c.strip() for c in sd.columns]
    sd["Number"] = pd.to_numeric(sd["EIP Number"], errors="coerce")
    sd["start"]  = pd.to_datetime(sd["Date"], errors="coerce", format="%m/%d/%Y")
    sd = sd.dropna(subset=["Number", "start"])[["Number", "start"]]

    # -- (ii) authoritative EIP-author list ---------------------------------
    auth = pd.read_csv(os.path.join(RAWDATA, "allEIPsandAuthorsv2.csv"), encoding="latin-1")
    auth["Number"] = pd.to_numeric(auth["Number"], errors="coerce")
    n_all = auth["Number"].nunique()
    if subset == "final":
        auth = auth[auth["Status"].astype(str).str.strip().str.lower() == "final"]
        print(f"      subset='final': {auth['Number'].nunique()} of {n_all} EIPs retained")

    auth = auth.merge(sd, on="Number", how="left")
    n_missing = auth["start"].isna().sum()
    if n_missing:
        print(f"      WARNING: {n_missing} EIPs have no start date and are dropped")
    auth = auth.dropna(subset=["start"])

    # -- (iii) split the free-text Author field into (name, handle) ----------
    # Example token: "Hudson Jameson (@Souptacular)" or "Martin Becze <mb@x.org>"
    # We keep the display name for matching and the handle for validation.
    def tokenise(raw):
        if not isinstance(raw, str):
            return []
        out = []
        for part in raw.split(","):
            h = re.search(r"\(@([A-Za-z0-9_\-]+)\)", part)
            nm = re.sub(r"<[^>]+>", "", part)        # strip <email>
            nm = re.sub(r"\([^)]*\)", "", nm)         # strip (@handle)
            nm = re.sub(r"\bet al\.?", "", nm).strip()
            if nm or h:
                out.append((nm, h.group(1).lower() if h else None))
        return out

    auth["tok"] = auth["Author"].apply(tokenise)
    ax = auth.explode("tok").dropna(subset=["tok"]).copy()
    ax["eip_author"] = ax["tok"].apply(lambda t: t[0])
    ax["handle"]     = ax["tok"].apply(lambda t: t[1])
    ax = ax[ax["eip_author"].astype(str).str.strip().ne("")]

    # -- (iv) link EIP authors to Revelio author_id --------------------------
    # No shared key exists (see header note), so we fuzzy-match display names.
    # 99% of accepted matches are exact strings; the remainder are diacritic
    # artifacts. Validated against GitHub handles in `data_checks.py`.
    rev = pd.read_parquet(os.path.join(REVELIO, "author_to_revelio_userid.parquet"))
    rev["author_id"] = pd.to_numeric(rev["author_id"], errors="coerce")
    eip_names = ax["eip_author"].dropna().unique().tolist()

    pairs = []
    for nm in rev["author_name"].dropna().unique():
        r = process.extractOne(nm, eip_names, scorer=fuzz.token_sort_ratio)
        if r and r[1] >= FUZZY_THRESHOLD:
            pairs.append({"author_name": nm, "eip_author": r[0]})
    link = pd.DataFrame(pairs).merge(rev[["author_name", "author_id"]], on="author_name")

    ev = (ax.merge(link[["eip_author", "author_id"]], on="eip_author")
            [["author_id", "Number", "Status", "start", "handle"]]
            .dropna(subset=["start"]))

    ev = ev.rename(columns={"start": "best_date"})
    # author_id must match the dtype used in the Revelio panel (int64), otherwise
    # the dictionary lookups in build_matched_sample() silently miss every author.
    ev["author_id"] = ev["author_id"].astype("int64")
    ev["eip_year"]  = ev["best_date"].dt.year.astype(int)
    ev["eip_month"] = ev["best_date"].dt.to_period("M")
    return ev.drop(columns=["handle"]).drop_duplicates()


# ==============================================================================
# 3. BUILD END-OF-YEAR PERSON-YEAR PANEL (+ balance covariates)
# ==============================================================================
def _normalise_ids(df):
    """Revelio stores author_id as a string in some files and a number in others.

    Normalising to int64 is essential: build_matched_sample() joins the panel to
    the EIP events through dictionary lookups, and a dtype mismatch causes every
    lookup to miss silently, yielding an empty matched sample rather than an error.
    """
    df = df.copy()
    df["author_id"] = pd.to_numeric(df["author_id"], errors="coerce").astype("int64")
    if "year" in df.columns:
        df["year"] = df["year"].astype(int)
    return df


def build_panel():
    """One row per author-year, outcomes measured at END OF YEAR.

    Positions are expanded to person-months; the end-of-year value is the last
    observed month in each calendar year.
    """
    path = os.path.join(CACHE, "eoy_annual_panel_bal.parquet")
    if not REBUILD:
        cached = read_cache(path)
        if cached is not None:
            return _normalise_ids(cached)

    pos = pd.read_parquet(os.path.join(REVELIO, "revelio_positions_enriched.parquet"))
    pos["startdate"] = pd.to_datetime(pos["startdate"], errors="coerce")
    pos["enddate"]   = pd.to_datetime(pos["enddate"],   errors="coerce")
    pos = pos.dropna(subset=["startdate"])
    pos["enddate"]   = pos["enddate"].fillna(pd.Timestamp(f"{MAX_YEAR}-12-01"))
    pos = pos[pos["enddate"] >= pos["startdate"]]

    lo = pd.Period(f"{MIN_YEAR}-01", "M"); hi = pd.Period(f"{MAX_YEAR}-12", "M")
    pos["sm"] = pos["startdate"].dt.to_period("M").clip(lower=lo)
    pos["em"] = pos["enddate"].dt.to_period("M").clip(upper=hi)
    pos = pos[pos["em"] >= pos["sm"]]

    # expand each position to person-months, keep the latest-starting job per month
    frames = []
    for _, r in pos.iterrows():
        months = pd.period_range(r["sm"], r["em"], freq="M")
        frames.append(pd.DataFrame({
            "author_id": r["author_id"], "month": months,
            "seniority": r["seniority"], "total_compensation": r["total_compensation"],
            "salary": r["salary"],
            "job_engineer": 1.0 if r["job_category_v2"] == "Engineer" else 0.0,
            "has_employer": 1.0 if pd.notna(r["rcid"]) else 0.0,
            "region_na": 1.0 if r["region"] == "Northern America" else 0.0,
            "pos_start": r["startdate"]}))
    pm = pd.concat(frames, ignore_index=True)
    pm = (pm.sort_values(["author_id", "month", "pos_start"])
            .drop_duplicates(subset=["author_id", "month"], keep="last")
            .drop(columns=["pos_start"]))

    # end-of-year snapshot
    pm["year"]   = pm["month"].dt.year
    pm["m_of_y"] = pm["month"].dt.month
    eoy = (pm.sort_values(["author_id", "year", "m_of_y"])
             .groupby(["author_id", "year"], as_index=False).last())

    # person-level covariates (used only for the balance table)
    u = pd.read_parquet(os.path.join(REVELIO, "revelio_user.parquet"))
    deg = {"High School": 1, "Associate": 2, "Bachelor": 3, "MBA": 4, "Master": 4, "Doctor": 5}
    u["degree_num"] = u["highest_degree"].map(deg)
    u["female"]     = (u["sex_predicted"] == "F").astype(float)
    u["eth_white"]  = (u["ethnicity_predicted"] == "White").astype(float)
    u["us_based"]   = (u["user_country"] == "United States").astype(float)
    u["conn500"]    = (u["numconnections"] >= 500).astype(float)   # top-coded at 500
    eoy = eoy.merge(u[["author_id", "prestige", "degree_num", "female", "eth_white",
                       "us_based", "conn500"]], on="author_id", how="left")

    eoy["log_comp"]   = np.log(eoy["total_compensation"].clip(lower=1))
    eoy["log_salary"] = np.log(eoy["salary"].clip(lower=1))
    eoy = eoy[["author_id", "year", "seniority", "total_compensation", "log_comp",
               "salary", "log_salary", "prestige", "degree_num", "female", "eth_white",
               "us_based", "conn500", "job_engineer", "has_employer", "region_na"]]
    # Revelio stores author_id as a string in some files and as a number in
    # others; normalise to int64 so that the dictionary lookups joining the
    # panel to the EIP events cannot silently miss.
    eoy = _normalise_ids(eoy)
    write_cache(eoy, path)
    return eoy


# ==============================================================================
# 4. COHORT CONSTRUCTION AND MATCHING
# ==============================================================================
def build_matched_sample(eoy, ev):
    """One cohort per treated author; exact seniority path + Mahalanobis log comp."""
    by_author = {a: g.set_index("year") for a, g in eoy.groupby("author_id")}
    eip_years = ev.groupby("author_id")["eip_year"].apply(set).to_dict()
    all_ids   = list(by_author.keys())

    # candidate treatment events: EIP in g, none in [g-W, g-1]
    events = []
    for a, ys in eip_years.items():
        for g in sorted(ys):
            if any(g - W <= y <= g - 1 for y in ys):
                continue
            events.append((a, int(g)))

    def profile(aid, g):
        """(exact key = seniority path, mahalanobis vector = log comp path)"""
        p = by_author.get(aid)
        if p is None:
            return None
        pre = [g - 2, g - 1]
        if not all(y in p.index for y in pre):
            return None
        key = tuple(int(p.loc[y, "seniority"]) for y in pre)
        vec = [float(p.loc[y, "log_comp"]) for y in pre]
        return key, vec

    caliper = chi2.ppf(CALIPER_Q, df=2)
    chunks, n_profiled, n_cohorts, n_dropped, ratios = [], 0, 0, 0, []

    for aid, g in events:
        t = profile(aid, g)
        if t is None:
            continue
        n_profiled += 1

        # eligible controls: no EIP anywhere in the window, same exact seniority path
        cands = []
        for a in all_ids:
            if a == aid:
                continue
            if any(g - W <= y <= g + W for y in eip_years.get(a, set())):
                continue
            c = profile(a, g)
            if c is None or c[0] != t[0]:
                continue
            cands.append((a, c[1]))
        if not cands:
            continue

        # ---- Stage 2: Mahalanobis distance on the log-compensation path ----
        Xt = np.array([t[1]])                       # treated author's vector
        Xc = np.array([v for _, v in cands])        # eligible controls
        cov = np.cov(np.vstack([Xt, Xc]), rowvar=False) + np.eye(2) * 1e-6
        VI  = np.linalg.pinv(cov)                   # inverse covariance
        d2  = cdist(Xt, Xc, metric="mahalanobis", VI=VI)[0] ** 2

        # ---- THE 1:3 CAP AND THE CALIPER ARE BOTH IMPOSED ON THIS LINE ----
        #   np.argsort(d2)              -> control indices, nearest first
        #   [:N_CONTROLS]               -> keep AT MOST 3 (N_CONTROLS = 3)
        #   if d2[j] <= caliper         -> and only those inside the caliper
        # Fewer than three controls are therefore accepted whenever fewer than
        # three lie within the caliper; more than three are never possible.
        # If the nearest control is outside the caliper the list is empty and
        # the treated author is dropped from the analysis entirely.
        keep = [j for j in np.argsort(d2)[:N_CONTROLS] if d2[j] <= caliper]
        if not keep:
            n_dropped += 1
            continue

        n_cohorts += 1
        ratios.append(len(keep))
        members = [(aid, 1)] + [(cands[j][0], 0) for j in keep]
        cols = ["seniority", "log_comp", "total_compensation", "prestige", "degree_num",
                "log_salary", "job_engineer", "female", "eth_white", "us_based",
                "region_na", "has_employer", "conn500"]
        for a, tr in members:
            p = by_author[a]
            yrs = [y for y in range(g - W, g + W + 1) if y in p.index]
            sub = p.loc[yrs, cols].copy()
            sub["rel_t"] = np.array(yrs) - g
            sub["treat"] = tr
            sub["author_id"] = a
            sub["event_id"]  = n_cohorts
            chunks.append(sub.reset_index(drop=True))

    st = pd.concat(chunks, ignore_index=True)
    # control weight 1/k, treated weight 1
    k = st[st["treat"] == 0].groupby("author_id")["event_id"].nunique().to_dict()
    st["weight"] = st.apply(lambda r: 1.0 if r["treat"] == 1 else 1.0 / k[r["author_id"]], axis=1)

    meta = {"events_profiled": n_profiled, "cohorts": n_cohorts,
            "dropped_caliper": n_dropped, "ratio": float(np.mean(ratios)),
            "treated": int(st[st["treat"] == 1]["author_id"].nunique()),
            "controls": int(st[st["treat"] == 0]["author_id"].nunique()),
            "obs": int(len(st))}
    return st, meta


# ==============================================================================
# 5. ESTIMATION -- THE REGRESSION, IN TWO EQUIVALENT FORMS
# ==============================================================================
#
# The estimating equation is, in levels (seniority in points, compensation in logs),
#
#     y_it = b'X_it + (author x cohort) + (cohort x event-time) + e_it
#
# and this module runs it two ways:
#
#     fit_dummies   every fixed effect is a column of the design matrix.
#                   This is `reg y x i.pc i.crt` in Stata.
#     fit_absorbed  the effects are removed by the exact within-transformation
#                   and the short regression is run on the residuals.
#                   This is `xtreg y x, fe`.
#
# Frisch-Waugh-Lovell says the coefficients are identical; `verify()` confirms it
# numerically on every pipeline run. The pipeline reports `fit_absorbed`;
# `fit_dummies` exists so the claim can be checked rather than asserted.
#
# WHY THE DUMMY SYSTEM NEEDS CARE
# -------------------------------
# Both fixed effects are nested inside the cohort: `pc` is author x cohort and
# `crt` is cohort x event-time. The bipartite graph linking them therefore breaks
# into one connected component per cohort, and the dummy system is rank deficient
# by one per cohort -- as many redundant columns as cohorts, not the single
# redundancy that `drop_first` would remove. Dropping only one column leaves a
# matrix whose SVD does not converge and whose pseudo-inverse solution is not
# the OLS fit.
#
# The system is built full rank instead:
#
#     - every author x cohort dummy, and NO intercept
#     - cohort x event-time dummies excluding one reference event-time per cohort
#
# giving rank |pc| + |crt| - (number of cohorts), which is verified at run time.
#
# DEGREES OF FREEDOM
# ------------------
# Because the dummies are genuinely in the design matrix, the cluster-robust
# finite-sample correction counts them automatically: k is the true number of
# estimated parameters, not the number of regressors of interest. There is no
# convention to choose -- this is simply what the regression returns.
#
# WEIGHTS
# -------
# Estimation is unweighted: every author-cohort-year observation counts once.
#
# They differ only in the finite-sample factor of the cluster-robust variance,
#
#     G/(G-1) * (N-1)/(N-K),
#
# because K is the number of estimated parameters. With the dummies in the matrix
# K counts them (about 2,650 in the main run); with the effects absorbed K counts
# only the regressors of interest. Stata behaves the same way: `areg` and
# `reghdfe` count the absorbed effects, `xtreg, fe` does not. The correction has
# no asymptotic justification -- cluster-robust inference is asymptotic in the
# number of clusters -- so the choice is a convention that must be stated. This
# project reports the absorbed convention (`xtreg, fe`); the dummy-variable
# convention multiplies every standard error here by 1.333.
#
_FE_CACHE = {}


def _fe_matrix(df):
    """Full-rank fixed-effect dummy block, with an orthonormal basis cached.

    The basis Q is used only to test whether a regressor lies in the span of the
    fixed effects; it plays no part in estimation, which uses the dummies
    themselves. Caching it avoids refactorising the same block once per
    specification.
    """
    key = (len(df), int(df["pc"].nunique()), int(df["crt"].nunique()),
           float(df.index.values.sum()))
    if key in _FE_CACHE:
        return _FE_CACHE[key]
    D1 = pd.get_dummies(df["pc"]).values.astype(float)          # all author x cohort
    ref = df.groupby("event_id")["rel_t"].transform("min")      # reference event time
    drop = df.loc[df["rel_t"] == ref, "crt"].unique()
    D2 = pd.get_dummies(df["crt"]).drop(columns=drop).values.astype(float)
    FE = np.column_stack([D1, D2])
    Q, _ = np.linalg.qr(FE)
    _FE_CACHE.clear()
    _FE_CACHE[key] = (FE, Q)
    return FE, Q


def build_design(df, regs):
    """Return (X, names, info) for the levels regression with FE dummies.

    Regressors of interest come first so their coefficients are read off the
    front of the parameter vector. A regressor that is collinear with the fixed
    effects -- for example an exactly-matched pre-period indicator -- is
    detected and reported rather than silently given an arbitrary coefficient.
    """
    FE, Q = _fe_matrix(df)

    # A regressor is identified only if it is not in the span of the dummies.
    kept, absorbed = [], []
    for r in regs:
        v = df[r].values.astype(float)
        resid = v - Q @ (Q.T @ v)
        scale = max(1.0, float(np.max(np.abs(v))))
        (kept if np.max(np.abs(resid)) / scale > 1e-8 else absorbed).append(r)

    X = np.column_stack([df[kept].values.astype(float), FE]) if kept else FE
    info = {"n": len(df), "k": X.shape[1], "n_fe": FE.shape[1],
            "cohorts": int(df["event_id"].nunique()), "absorbed": absorbed}
    return X, kept, info


def fit_dummies(df, outcome, regs, weights=None, cluster="author_id", check_rank=False):
    """Levels regression with the fixed effects as dummy variables (K counts them)."""
    X, kept, info = build_design(df, regs)
    if check_rank:
        info["rank"] = int(np.linalg.matrix_rank(X))
        info["full_rank"] = info["rank"] == X.shape[1]
    w = np.ones(len(df)) if weights is None else df[weights].values.astype(float)
    m = sm.WLS(df[outcome].values.astype(float), X, weights=w).fit(
        method="qr", cov_type="cluster", cov_kwds={"groups": df[cluster].values})
    out = {r: {"coef": float(m.params[i]), "se": float(m.bse[i]),
               "p": float(m.pvalues[i])} for i, r in enumerate(kept)}
    for r in info["absorbed"]:
        out[r] = None
    info["clusters"] = int(df[cluster].nunique())
    info["df_resid"] = int(m.df_resid)
    return out, info


def prep(st, outcome):
    """Sample for one outcome, with the fixed-effect keys and the indicators."""
    df = st[st[outcome].notna()].copy()
    df["pc"]  = df["author_id"].astype(str) + "_" + df["event_id"].astype(str)
    df["crt"] = df["event_id"].astype(str)  + "_" + df["rel_t"].astype(str)
    tr = df["treat"] == 1
    for t in [-2, -1, 0, 1, 2]:
        df[f"E{t:+d}"] = (tr & (df["rel_t"] == t)).astype(float)
    df["D0"]  = (tr & (df["rel_t"] == 0)).astype(float)
    df["P1"]  = (tr & (df["rel_t"] >= 1)).astype(float)
    df["P0"]  = (tr & (df["rel_t"] >= 0)).astype(float)
    df["Treated"] = df["treat"].astype(float)
    df["inv_k"] = df["weight"].astype(float)
    return df


# ---------------------------------------------------------------- absorbed form
def _within(df, cols, tol=1e-12, maxit=5000):
    """Exact two-way within-transformation by alternating projections.

    The panel is unbalanced across the two dimensions, so a single pass is not
    exact; the projections are alternated until the change falls below `tol`.
    The result is the Frisch-Waugh-Lovell residual, so the short regression that
    follows returns the same coefficients as the dummy-variable regression.
    """
    out = df.copy()
    keys = [out["pc"].values, out["crt"].values]
    for c in cols:
        v = out[c].values.astype(float)
        for _ in range(maxit):
            prev = v
            for k in keys:
                v = v - pd.Series(v).groupby(k).transform("mean").values
            if np.max(np.abs(v - prev)) < tol:
                break
        out[c + "_w"] = v
    return out


def fit_absorbed(df, outcome, regs, cluster="author_id"):
    """Same regression, fixed effects absorbed; K counts the regressors only."""
    d = _within(df, [outcome] + regs)
    X = d[[r + "_w" for r in regs]].values
    keep = X.var(axis=0) > 1e-12       # an exactly-matched term has no variation left
    kept = [regs[i] for i, k in enumerate(keep) if k]
    absorbed = [r for r in regs if r not in kept]
    m = sm.OLS(d[outcome + "_w"].values, X[:, keep]).fit(
        cov_type="cluster", cov_kwds={"groups": d[cluster].values})
    out = {r: {"coef": float(m.params[i]), "se": float(m.bse[i]),
               "p": float(m.pvalues[i])} for i, r in enumerate(kept)}
    for r in absorbed:
        out[r] = None
    info = {"n": len(d), "k_regressors": len(kept), "absorbed": absorbed,
            "clusters": int(d[cluster].nunique()),
            "n_fe": int(d["pc"].nunique() + d["crt"].nunique() - d["event_id"].nunique())}
    return out, info


def verify(df, outcome, regs):
    """Largest coefficient discrepancy between the absorbed and dummy forms."""
    a, _ = fit_absorbed(df, outcome, regs)
    b, _ = fit_dummies(df, outcome, regs)
    diffs = [abs(a[r]["coef"] - b[r]["coef"]) for r in regs if a.get(r) and b.get(r)]
    return max(diffs) if diffs else 0.0


def attach_sen_m1(st):
    """Carry seniority at t-1 onto every row of that author-cohort.

    Cohorts are matched EXACTLY on the seniority path, so within a cohort the
    treated author and all her controls share this value; the assertion below
    fails loudly if that ever stops being true. It is what makes the junior /
    senior split a property of the cohort rather than of the individual.
    """
    base = (st[st["rel_t"] == -1][["author_id", "event_id", "seniority"]]
            .rename(columns={"seniority": "sen_m1"}))
    out = st.merge(base, on=["author_id", "event_id"], how="left")
    bad = int((out.groupby("event_id")["sen_m1"].nunique() > 1).sum())
    assert bad == 0, f"{bad} cohorts vary in seniority(t-1); exact match violated"
    return out


def estimate(st, outcome):
    """The regression, with the author x cohort and cohort x event-time effects
    absorbed by the exact within-transformation.

    Three regressions per outcome, all on the same sample:
      static   -- treated x 1{t >= 0}, a single post indicator
      dynamic  -- treated x event-time indicators, t = -1 omitted
      pooled   -- treated x 1{t >= +1}, with the event year t = 0 separate
    """
    df = prep(st, outcome)

    static, info = fit_absorbed(df, outcome, ["P0"])
    dyn,    _    = fit_absorbed(df, outcome, ["E-2", "E+0", "E+1", "E+2"])
    pooled, _    = fit_absorbed(df, outcome, ["E-2", "D0", "P1"])

    # ---- the same static specification, on the two halves of the sample -----
    # Split at the MEDIAN of seniority(t-1).
    df["sen_m1"] = st.set_index(["author_id", "event_id", "rel_t"]).loc[
        list(zip(df["author_id"], df["event_id"], df["rel_t"])), "sen_m1"].values
    med = float(df["sen_m1"].median())
    splits = {}
    for key, mask in [("jr", df["sen_m1"] <= med), ("sr", df["sen_m1"] > med)]:
        sub = df[mask].copy()
        rr, ii = fit_absorbed(sub, outcome, ["P0"])
        splits[key] = {"est": rr["P0"], "n": ii["n"], "clusters": ii["clusters"],
                       "cohorts": int(sub["event_id"].nunique()),
                       "treated": int(sub[sub["treat"] == 1]["author_id"].nunique())}

    def clean(d):
        """A term the matching forces to zero has no residual variation, so its
        standard error is zero and its p-value undefined. Report it as
        `0 (by construction)` rather than as `0.000 (nan)`."""
        if d is None:
            return {"coef": 0.0, "se": 0.0, "p": None}
        if not np.isfinite(d["se"]) or not np.isfinite(d["p"]) or d["se"] < 1e-8:
            return {"coef": 0.0, "se": 0.0, "p": None}
        return dict(d)

    es = [{"rel": -1, "coef": 0.0, "se": 0.0, "p": None}]
    for t, c in [(-2, "E-2"), (0, "E+0"), (1, "E+1"), (2, "E+2")]:
        es.append({"rel": t, **clean(dyn.get(c))})
    es.sort(key=lambda r: r["rel"])

    return {"es": es,
            "median_sen": med,
            "splits": {k: {**v, "est": clean(v["est"])} for k, v in splits.items()},
            "static":   clean(static.get("P0")),
            "att":      clean(pooled.get("P1")),
            "event_yr": clean(pooled.get("D0")),
            "pre":      clean(dyn.get("E-2")),
            "info":     info}


# ==============================================================================
# 6. BALANCE TABLE (at t-1)
# ==============================================================================
BALANCE_VARS = [
    ("seniority",          "Seniority (1--7)",             "num", "A"),
    ("total_compensation", "Total compensation (USD)",     "usd", "A"),
    ("prestige",           "School prestige score",        "num", "B"),
    ("degree_num",         "Education level (1--5)",       "num", "B"),
    ("log_salary",         "Log base salary",              "num", "B"),
    ("job_engineer",       "Engineering occupation",       "pct", "B"),
    ("female",             "Female",                       "pct", "B"),
    ("eth_white",          "Ethnicity: White",             "pct", "B"),
    ("us_based",           "Based in United States",       "pct", "B"),
    ("region_na",          "Job located in North America", "pct", "B"),
    ("has_employer",       "Employer identified in data",  "pct", "B"),
    ("conn500",            "500+ LinkedIn connections",    "pct", "B"),
]


def balance_table(st):
    t1 = st[st["rel_t"] == -1]
    rows = []
    for v, label, kind, panel in BALANCE_VARS:
        tr = t1[t1["treat"] == 1][v].dropna()
        ct = t1[t1["treat"] == 0][v].dropna()
        if len(tr) < 2 or len(ct) < 2:
            continue
        diff = tr.mean() - ct.mean()
        pooled = np.sqrt(0.5 * (tr.std() ** 2 + ct.std() ** 2))
        tstat, p = sps.ttest_ind(tr, ct, equal_var=False)   # Welch
        rows.append({"var": v, "label": label, "kind": kind, "panel": panel,
                     "nT": len(tr), "nC": len(ct), "mT": tr.mean(), "mC": ct.mean(),
                     "diff": diff, "smd": diff / pooled if pooled > 0 else np.nan,
                     "t": tstat, "p": p})
    return pd.DataFrame(rows)


# ==============================================================================
# 7. FIGURE
# ==============================================================================
def _draw_event_study_panel(ax, es, ylab):
    """Draw one outcome's event-study series onto a single axes.

    No annotation boxes, no legend, no note block and no shaded pre/post
    regions -- only the estimates, their confidence intervals, and the axes.
    """
    ax.axhline(0, color="black", lw=0.9, ls="--", zorder=2)
    ax.axvline(-0.5, color="#999999", lw=0.9, ls=":", zorder=2)

    for r in es:
        t, c, se = r["rel"], r["coef"], r["se"]
        if t == -1 or se == 0:            # reference year, or zero by construction
            ax.scatter([t], [0], color="black", marker="D", s=44, zorder=6)
            continue
        lo, hi = c - 1.96 * se, c + 1.96 * se
        ax.plot([t, t], [lo, hi], color="#1a5276", lw=2.0,
                solid_capstyle="round", zorder=4)
        ax.plot([t - .07, t + .07], [lo, lo], color="#1a5276", lw=2.0, zorder=4)
        ax.plot([t - .07, t + .07], [hi, hi], color="#1a5276", lw=2.0, zorder=4)
        ax.scatter([t], [c], color="#1a5276", s=44, zorder=5,
                   edgecolors="white", lw=0.8)

    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_xticklabels(["$t-2$", "$t-1$", "$t$", "$t+1$", "$t+2$"], fontsize=10)
    ax.set_xlim(-2.5, 2.5)
    ax.set_xlabel("Years relative to EIP authorship", fontsize=10)
    ax.set_ylabel(ylab, fontsize=10)
    ax.grid(axis="y", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)


def make_figures(res, meta, seniority_path, log_comp_path, label=None):
    """Two SEPARATE single-panel event-study figures, one per outcome.

    Previously a single two-panel figure; split per request into
    `seniority_path` (seniority coefficients) and `log_comp_path` (log
    compensation coefficients), each its own standalone file rather than
    side-by-side subplots of one image.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for oc, ylab, path in [("seniority", "Seniority coefficient (1–7 scale)", seniority_path),
                            ("log_comp",  "Log compensation coefficient",     log_comp_path)]:
        fig, ax = plt.subplots(figsize=(5.4, 4.2))
        fig.patch.set_facecolor("white")
        _draw_event_study_panel(ax, res[oc]["es"], ylab)
        plt.tight_layout()
        plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)


# ==============================================================================
# 8. LATEX TABLES
# ==============================================================================
def stars_tex(p):
    if p is None: return ""
    return "$^{***}$" if p < 0.01 else "$^{**}$" if p < 0.05 else "$^{*}$" if p < 0.10 else ""

def fmt_val(v, kind):
    if kind == "usd": return f"\\${v:,.0f}"
    if kind == "pct": return f"{v*100:.1f}\\%"
    return f"{v:.3f}"

NOTE_TEXT = (
    r"The table reports covariate balance and difference-in-differences estimates of the effect of "
    r"authoring an Ethereum Improvement Proposal (EIP) on career outcomes over a "
    r"$\pm2$-year event window. An author is treated if they propose an EIP at t=0. Each treated author "
    r"is matched to at most three similar control "
    r"authors drawn from the population of EIP authors who author no EIP anywhere in the $\pm2$-year "
    r"window; Panel A shows the results of a balance test. Panel B and C report stack diff-in-diff "
    r"results for Seniority and Total Compensation (log) as outcome variable. Column~(1) reports the "
    r"static model. Column~(2) replaces it with separate coefficients for each event year, $t-1$ "
    r"omitted as the reference. Columns~(3) and~(4) "
    r"re-run column~(1) on the two halves of the sample, split at the median of seniority in the year "
    r"before authorship. Standard errors, reported in parentheses, are clustered at the author level; "
    r"$^{*}$, $^{**}$, and $^{***}$ denote statistical significance at the 10\%, 5\%, and 1\% levels, "
    r"respectively."
)


def write_latex(res, meta, bal, outdir, tag="", label="ALL EIPs"):
    """One table, three panels, reproducing exactly the hand-edited LaTeX the co-author
    settled on (structure, spacing, and all) after manually trimming an earlier
    machine-generated version:

        Panel A  Covariate balance at t-1 (Treated, Control, Difference, p-value only --
                 SMD and t-stat, present in an earlier version, are dropped here)
        Panel B  Seniority (1--7): static, dynamic, junior/senior split
        Panel C  Log compensation: static, dynamic, junior/senior split

    Two floating `\begin{table}` environments, not one: the first holds the caption, the
    note, Panel A, and Panel B; the second (`\begin{table}[t]`) holds only Panel C, pulled
    up with a literal `\vspace{-9cm}` so it sits directly under the first table rather than
    floating to wherever LaTeX would otherwise place it. This is fragile -- the -9cm is
    tuned to the current note/Panel-A/Panel-B length, and would need re-tuning by hand if
    either changes -- but it is exactly what was asked for, so it is reproduced as-is
    rather than "fixed."

    Earlier in this project a single floating `table` containing all three panels plus a
    much longer note silently lost content past the bottom of the page (see git history /
    PIPELINE_TODO.md); this two-table split is the co-author's own resolution of that same
    problem, verified by actually compiling it (see PIPELINE_TODO.md for the check).
    """
    sen, lc = res["seniority"], res["log_comp"]

    def pair(d):
        if d is None:
            return "", ""
        if d["se"] == 0:
            return "0.000", ""
        return f"{d['coef']:.3f}{stars_tex(d['p'])}", f"({d['se']:.3f})"

    def row(lbl, cells):
        """cells: 4 estimates (or None) in column order."""
        tops, bots = zip(*(pair(c) for c in cells))
        out = [rf"{lbl} & " + " & ".join(tops) + r" \\"]
        if any(bots):
            out.append(r" & " + " & ".join(bots) + r" \\")
        return out

    jr, sr = sen["splits"]["jr"], sen["splits"]["sr"]

    def panel_header():
        return [r" & (1) & (2) & (3) & (4) \\",
                r" & \multicolumn{2}{c}{Full sample} & \multicolumn{2}{c}{By pre-event seniority} \\",
                r"\cmidrule(lr){2-3} \cmidrule(lr){4-5}",
                r" & Static & Dynamic & Junior & Senior \\",
                r" & & & \small(1--3) & \small(4--7) \\", r"\midrule"]

    def panel_footer(n):
        return [r"\midrule",
                r"Author $\times$ cohort FE & Yes & Yes & Yes & Yes \\",
                r"Cohort $\times$ event-time FE & Yes & Yes & Yes & Yes \\",
                rf"Observations & {n:,} & {n:,} & {jr['n']:,} & {sr['n']:,} \\",
                r"\bottomrule"]

    def panel_bc(r_, nm):
        es = {e["rel"]: e for e in r_["es"]}
        out = [r"\begin{tabular}{lcccc}",
               r"\multicolumn{5}{l}{\textbf{Panel " + nm + r"}} \\[2pt]",
               r"\toprule"]
        out += panel_header()
        out += row(r"\quad Treated $\times$ Post ($t\geq 0$)",
                   [r_["static"], None, r_["splits"]["jr"]["est"], r_["splits"]["sr"]["est"]])
        out.append(r"\addlinespace")
        for t in [-2, -1, 0, 1, 2]:
            lbl = rf"\quad Treated $\times$ $t={t:+d}$"
            if t == -1:
                out.append(r"\quad Treated $\times$ $t=-1$ & & --- & & \\")
                continue
            out += row(lbl, [None, es[t], None, None])
        out += panel_footer(meta["obs"])
        out.append(r"\end{tabular}")
        return out

    T = [r"% ===== Table: covariate balance + difference-in-differences results =====",
         r"\begin{center}",
         r"\begin{table}",
         r" \caption{The Effect of EIP Authorship on Seniority and Compensation}",
         rf" \label{{tab:did_main{tag}}}",
         r"     \begin{small}",
         r"    \begin{minipage}{\textwidth}",
         f"      {NOTE_TEXT}",
         r"  \end{minipage}",
         r"         \end{small}",
         r"\begin{tabular}{lcccccc}",
         r"\\",
         r"",
         r"\multicolumn{5}{l}{\textbf{Panel A. Covariate Balance (at $t-1$)}} \\[2pt]",
         r"\toprule",
         r" & \multicolumn{2}{c}{Mean} & & & & \\",
         r"\cmidrule(lr){2-3}",
         r"Variable & Treated & Control & Difference  & $p$-value \\",
         r" & (1) & (2) & (3) & (4) \\",
         r"\midrule",
         r"\multicolumn{7}{l}{\textit{Variables used in matching}} \\"]
    for _, r in bal[bal["panel"] == "A"].iterrows():
        T.append(rf"\quad {r['label']} & {fmt_val(r['mT'],r['kind'])} & {fmt_val(r['mC'],r['kind'])} & "
                 rf"{fmt_val(r['diff'],r['kind'])} &  {r['p']:.3f} \\")
    T += [r"\addlinespace", r"\multicolumn{7}{l}{\textit{Variables not used in matching}} \\"]
    for _, r in bal[bal["panel"] == "B"].iterrows():
        T.append(rf"\quad {r['label']} & {fmt_val(r['mT'],r['kind'])} & {fmt_val(r['mC'],r['kind'])} & "
                 rf"{fmt_val(r['diff'],r['kind'])} &  {r['p']:.3f} \\")
    T += [r"\midrule",
          rf"Observations & {int(bal['nT'].max())} & {int(bal['nC'].max())} & &  \\",
          r"\bottomrule", r"\end{tabular}",
          r"\vspace{10pt}"]
    T += panel_bc(sen, "B. Seniority (1--7)")
    T += [r"\end{table}",
          r"\begin{table}[t]",
          r"\vspace{-9cm}"]
    T += panel_bc(lc, "C. Log compensation")
    T += [r"\end{table}",
          r"\end{center}"]

    open(os.path.join(outdir, f"table_did_results{tag}.tex"), "w",
         encoding="utf-8").write("\n".join(T) + "\n")


# ==============================================================================
# 9. MAIN
# ==============================================================================
def main(subset=None):
    ensure_dirs()
    os.makedirs(CACHE, exist_ok=True)
    subset = subset or EIP_SUBSET_CLI
    tag = "" if subset == "all" else "_final"
    label = "ALL EIPs" if subset == "all" else "FINALIZED EIPs ONLY"
    print("=" * 78)
    print(f"EIP AUTHORSHIP AND CAREER OUTCOMES — +/-2 EXACT MATCH — {label}")
    print("=" * 78)

    print("\n[1/5] Building EIP authorship events ...")
    ev = build_eip_events(subset=subset)
    print(f"      {len(ev):,} author-EIP pairs | {ev['author_id'].nunique()} authors "
          f"| years {int(ev['eip_year'].min())}-{int(ev['eip_year'].max())}")

    print("\n[2/5] Building end-of-year person-year panel ...")
    eoy = build_panel()
    print(f"      {len(eoy):,} author-years | {eoy['author_id'].nunique()} authors")

    print("\n[3/5] Constructing cohorts and matching ...")
    st, meta = build_matched_sample(eoy, ev)
    print(f"      events profiled  : {meta['events_profiled']}")
    print(f"      dropped (caliper): {meta['dropped_caliper']}")
    print(f"      cohorts matched  : {meta['cohorts']}  (1:{meta['ratio']:.2f})")
    print(f"      treated / control: {meta['treated']} / {meta['controls']}")
    print(f"      observations     : {meta['obs']:,}")

    print("\n[4/5] Estimating ...")
    st = attach_sen_m1(st)          # seniority(t-1) for the junior / senior split
    res = {}
    for oc in ["seniority", "log_comp"]:
        res[oc] = estimate(st, oc)
        r_, info = res[oc], res[oc]["info"]
        print(f"\n      --- {oc} ---")
        print(f"      n = {info['n']:,}   {info['n_fe']:,} fixed effects absorbed   "
              f"{info['clusters']} clusters")
        d = verify(prep(st, oc), oc, ["E-2", "D0", "P1"])
        print(f"      absorbed vs dummy-variable form: max |difference| = {d:.2e}")

        def show(lbl, d):
            if d["se"] == 0:
                print(f"      {lbl}: 0 (by construction)"); return
            stt = "***" if d["p"] < 0.01 else "**" if d["p"] < 0.05 else "*" if d["p"] < 0.10 else ""
            pct = f"  [{(np.exp(d['coef'])-1)*100:+.1f}%]" if oc == "log_comp" else ""
            print(f"      {lbl}: {d['coef']:+.4f} (SE {d['se']:.4f}) p={d['p']:.4f} {stt}{pct}")

        show("static  Treated x Post", r_["static"])
        for rr in r_["es"]:
            if rr["rel"] == -1:
                print("      t=-1: reference"); continue
            show(f"t={rr['rel']:+d}          ", rr)
        show("ATT (t>=+1)       ", r_["att"])
        jr, sr = r_["splits"]["jr"], r_["splits"]["sr"]
        print(f"      -- split at median seniority(t-1) = {r_['median_sen']:.0f} --")
        show(f"junior 1-3 ({jr['cohorts']} coh)", jr["est"])
        show(f"senior 4-7 ({sr['cohorts']} coh)", sr["est"])

    print("\n[5/5] Balance, figure, and LaTeX tables ...")
    bal = balance_table(st)
    print(f"\n      {'Variable':32s} {'SMD':>8s} {'p':>8s}")
    for _, r in bal.iterrows():
        print(f"      {r['label']:32s} {r['smd']:+8.3f} {r['p']:8.3f}")

    meta["subset"] = subset
    # Machine-readable versions of the tables go to CACHE (data/interim), not the
    # output/ folders: those stay limited to the LaTeX table and the two figures.
    json.dump({"meta": meta, **res}, open(os.path.join(CACHE, f"results_main{tag}.json"), "w"), indent=1)
    bal.to_csv(os.path.join(CACHE, f"balance_main{tag}.csv"), index=False)
    write_cache(st, os.path.join(CACHE, f"matched_sample_main{tag}.parquet"))
    make_figures(res, meta,
                 os.path.join(OUTDIR_FIGURES, f"EIP_W2_EventStudy_Seniority{tag}.png"),
                 os.path.join(OUTDIR_FIGURES, f"EIP_W2_EventStudy_LogComp{tag}.png"))
    write_latex(res, meta, bal, OUTDIR_TABLES, tag, label)

    print(f"\nWritten to {OUTDIR_TABLES} / {OUTDIR_FIGURES}:")
    for f in [f"table_did_results{tag}.tex", f"EIP_W2_EventStudy_Seniority{tag}.png",
              f"EIP_W2_EventStudy_LogComp{tag}.png"]:
        print(f"  - {f}")
    print(f"Written to {CACHE}:")
    for f in [f"results_main{tag}.json", f"balance_main{tag}.csv",
              f"matched_sample_main{tag}.parquet"]:
        print(f"  - {f}")
    print("\nDone.")


if __name__ == "__main__":
    main()
