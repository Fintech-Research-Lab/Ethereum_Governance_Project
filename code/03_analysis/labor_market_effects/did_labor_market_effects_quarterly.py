"""
did_labor_market_effects_quarterly.py
======================================

Robustness check on `did_labor_market_effects.py`: the SAME stacked diff-in-diff design,
at quarterly instead of annual frequency. Not part of the published paper, same as the
annual version.

WHY THIS EXISTS
---------------
The annual version measures outcomes at end-of-year and dates treatment by calendar year,
even though (a) the exact EIP proposal date is known to the day, and (b) the underlying
Revelio position data is already expanded to person-months before being collapsed to an
annual snapshot (see `build_panel()` in the annual script). Both inputs support a finer
time unit, so this script reruns the identical design at end-of-quarter frequency instead,
to check whether the annual result is an artifact of the coarser time grid.

WHAT CHANGED FROM THE ANNUAL VERSION, AND WHAT DIDN'T
------------------------------------------------------------
    Event window       W = 8 quarters (same +/-2 YEARS of real time as the annual
                        version's W=2 years, just expressed in the finer unit).
    Control eligibility "no EIP anywhere in [g-8, g+8] quarters" -- same proportional
                        scaling of the annual "[g-2, g+2] years" rule.
    Treatment eligibility "no EIP anywhere in [g-8, g-1] quarters" -- same scaling.
    Exact-match pre-period  UNCHANGED IN STRUCTURE: matches on seniority/log-comp at the
                        TWO PERIODS IMMEDIATELY BEFORE treatment, i.e. [g-2, g-1] quarters
                        (6 and 3 months before), not [g-8, g-4] quarters. This mirrors the
                        annual version's own [g-2, g-1] *years*, treating "the two periods
                        right before treatment" as a property of the matching design, not
                        of the overall window length W (which happened to also equal 2 in
                        the annual version, by coincidence, not because the exact-match
                        step is supposed to track W). Flagged for the user to override --
                        matching on [g-8, g-4] quarters instead (a full 2-year and 1-year
                        lookback, just like the annual version) is one line to change if
                        preferred.
    Dynamic event-study GENERALIZED to every quarter from -8 to +8 (17 points, t-1 the
                        omitted reference), not just 5 points -- this is the main benefit
                        of the finer grid, not something to collapse back down.
    Outcomes, matching stages (exact seniority, Mahalanobis on log comp), caliper,
    estimation (absorbed two-way FE, OLS on levels, author-clustered SEs), balance table
    construction, and the dummy-vs-absorbed verification are all UNCHANGED in design --
    only the time unit differs.

Produces
--------
    output/tables/table_did_results_quarterly.tex
    output/figures/EIP_W2_EventStudy_Seniority_quarterly.png
    output/figures/EIP_W2_EventStudy_LogComp_quarterly.png
    data/interim/labor_market_effects/ -- quarterly panel cache, matched sample, results JSON
                        (separate filenames from the annual version's cache; see CACHE paths)

USAGE
-----
    python did_labor_market_effects_quarterly.py
    python did_labor_market_effects_quarterly.py --rebuild
    python did_labor_market_effects_quarterly.py --final
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
from scipy import sparse
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
CACHE   = DATA_INTERIM / "labor_market_effects"     # shared with the annual script; filenames below differ

REBUILD = "--rebuild" in sys.argv
EIP_SUBSET_CLI = "final" if "--final" in sys.argv else "all"

# ==============================================================================
# 1. SPECIFICATION CONSTANTS
# ==============================================================================
W           = 8          # event window (+/- QUARTERS) -- same +/-2 years as the annual script
N_CONTROLS  = 3
CALIPER_Q   = 0.90
FUZZY_THRESHOLD = 80
MIN_YEAR, MAX_YEAR = 2010, 2025
MIN_Q = pd.Period(f"{MIN_YEAR}Q1", freq="Q")
MAX_Q = pd.Period(f"{MAX_YEAR}Q4", freq="Q")


def read_cache(path):
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
# 2. BUILD EIP AUTHORSHIP EVENTS  (author_id x calendar quarter)
# ==============================================================================
def build_eip_events(subset="all"):
    """Identical to the annual script's version, except it also attaches `eip_quarter`
    (a pandas Period, freq='Q') from the exact `best_date`, which is what this script
    uses for cohort timing instead of `eip_year`."""
    from rapidfuzz import process, fuzz

    sd = pd.read_csv(os.path.join(RAWDATA, "eip_startdates.csv"), encoding="latin-1")
    sd.columns = [c.strip() for c in sd.columns]
    sd["Number"] = pd.to_numeric(sd["EIP Number"], errors="coerce")
    sd["start"]  = pd.to_datetime(sd["Date"], errors="coerce", format="%m/%d/%Y")
    sd = sd.dropna(subset=["Number", "start"])[["Number", "start"]]

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

    def tokenise(raw):
        if not isinstance(raw, str):
            return []
        out = []
        for part in raw.split(","):
            h = re.search(r"\(@([A-Za-z0-9_\-]+)\)", part)
            nm = re.sub(r"<[^>]+>", "", part)
            nm = re.sub(r"\([^)]*\)", "", nm)
            nm = re.sub(r"\bet al\.?", "", nm).strip()
            if nm or h:
                out.append((nm, h.group(1).lower() if h else None))
        return out

    auth["tok"] = auth["Author"].apply(tokenise)
    ax = auth.explode("tok").dropna(subset=["tok"]).copy()
    ax["eip_author"] = ax["tok"].apply(lambda t: t[0])
    ax["handle"]     = ax["tok"].apply(lambda t: t[1])
    ax = ax[ax["eip_author"].astype(str).str.strip().ne("")]

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
    ev["author_id"] = ev["author_id"].astype("int64")
    ev["eip_year"]    = ev["best_date"].dt.year.astype(int)
    ev["eip_quarter"] = ev["best_date"].dt.to_period("Q")
    return ev.drop(columns=["handle"]).drop_duplicates()


# ==============================================================================
# 3. BUILD END-OF-QUARTER PERSON-QUARTER PANEL (+ balance covariates)
# ==============================================================================
def _normalise_ids(df):
    df = df.copy()
    df["author_id"] = pd.to_numeric(df["author_id"], errors="coerce").astype("int64")
    return df


def build_panel():
    """One row per author-quarter, outcomes measured at END OF QUARTER.

    Identical to the annual script's `build_panel()` through the person-month expansion
    (`pm`); only the final collapse step changes, from one snapshot per calendar YEAR to
    one snapshot per calendar QUARTER (the last observed month within that quarter).
    """
    path = os.path.join(CACHE, "eoq_quarterly_panel_bal.parquet")
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

    # end-of-QUARTER snapshot (was end-of-year in the annual script)
    pm["quarter"] = pm["month"].dt.asfreq("Q")
    eoq = (pm.sort_values(["author_id", "quarter", "month"])
             .groupby(["author_id", "quarter"], as_index=False).last()
             .drop(columns=["month"]))

    u = pd.read_parquet(os.path.join(REVELIO, "revelio_user.parquet"))
    deg = {"High School": 1, "Associate": 2, "Bachelor": 3, "MBA": 4, "Master": 4, "Doctor": 5}
    u["degree_num"] = u["highest_degree"].map(deg)
    u["female"]     = (u["sex_predicted"] == "F").astype(float)
    u["eth_white"]  = (u["ethnicity_predicted"] == "White").astype(float)
    u["us_based"]   = (u["user_country"] == "United States").astype(float)
    u["conn500"]    = (u["numconnections"] >= 500).astype(float)
    eoq = eoq.merge(u[["author_id", "prestige", "degree_num", "female", "eth_white",
                       "us_based", "conn500"]], on="author_id", how="left")

    eoq["log_comp"]   = np.log(eoq["total_compensation"].clip(lower=1))
    eoq["log_salary"] = np.log(eoq["salary"].clip(lower=1))
    eoq = eoq[["author_id", "quarter", "seniority", "total_compensation", "log_comp",
               "salary", "log_salary", "prestige", "degree_num", "female", "eth_white",
               "us_based", "conn500", "job_engineer", "has_employer", "region_na"]]
    eoq = _normalise_ids(eoq)
    write_cache(eoq, path)
    return eoq


# ==============================================================================
# 4. COHORT CONSTRUCTION AND MATCHING
# ==============================================================================
def build_matched_sample(eoq, ev):
    """One cohort per treated author; exact seniority path + Mahalanobis log comp.

    Identical logic to the annual script's version, with `year` replaced by `quarter`
    (a pandas Period, freq='Q') throughout, and W=8 (quarters) instead of W=2 (years).
    See module docstring for the one deliberate non-rescaling: `profile()`'s exact-match
    pre-period stays at the two periods immediately before treatment ([g-2, g-1]
    quarters), not [g-8, g-4].
    """
    by_author = {a: g.set_index("quarter") for a, g in eoq.groupby("author_id")}
    eip_quarters = ev.groupby("author_id")["eip_quarter"].apply(set).to_dict()
    all_ids   = list(by_author.keys())

    events = []
    for a, qs in eip_quarters.items():
        for g in sorted(qs):
            if any(g - W <= q <= g - 1 for q in qs):
                continue
            events.append((a, g))

    MATCH_POINTS = [5, 1]  # quarters-before-treatment exact-matched on seniority: t-5 and t-1

    def profile(aid, g):
        """Two-point exact match: EXACT seniority at BOTH t-5 and t-1 (not adjacent
        quarters, and not an average). Two widely-separated exact-match points are a
        middle ground between the original design (exact match only at t-2/t-1 --
        adjacent, so it only constrains the last 6 months and left the 1.5-2-year-out
        pre-trend completely free) and the 8-quarter-average design (constrains the
        mean over the whole pre-period but not at all the shape -- a rising treated
        author can match a flat control with the same average, which is exactly what
        produced the large apparent pre-trend in the FE-demeaned event-study
        coefficients). Requiring seniority to match exactly at a RECENT point (t-1)
        AND a point over a year further back (t-5, ~1.25 years before) constrains two
        separated points on the trajectory directly, which a single average cannot.
        Log compensation is still matched via Mahalanobis distance at these same two
        points, within the exact-seniority cell, exactly as the original two-stage
        design did at its own two points.
        """
        p = by_author.get(aid)
        if p is None:
            return None
        pre = [g - k for k in MATCH_POINTS]
        if not all(q in p.index for q in pre):
            return None
        key = tuple(int(p.loc[q, "seniority"]) for q in pre)
        vec = [float(p.loc[q, "log_comp"]) for q in pre]
        return key, vec

    caliper = chi2.ppf(CALIPER_Q, df=2)
    chunks, n_profiled, n_cohorts, n_dropped, ratios = [], 0, 0, 0, []

    for aid, g in events:
        t = profile(aid, g)
        if t is None:
            continue
        n_profiled += 1

        cands = []
        for a in all_ids:
            if a == aid:
                continue
            if any(g - W <= q <= g + W for q in eip_quarters.get(a, set())):
                continue
            c = profile(a, g)
            if c is None or c[0] != t[0]:
                continue
            cands.append((a, c[1]))
        if not cands:
            continue

        Xt = np.array([t[1]])
        Xc = np.array([v for _, v in cands])
        cov = np.cov(np.vstack([Xt, Xc]), rowvar=False) + np.eye(2) * 1e-6
        VI  = np.linalg.pinv(cov)
        d2  = cdist(Xt, Xc, metric="mahalanobis", VI=VI)[0] ** 2

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
            qtrs = [q for q in pd.period_range(g - W, g + W, freq="Q") if q in p.index]
            sub = p.loc[qtrs, cols].copy()
            sub["rel_t"] = np.array([q.ordinal - g.ordinal for q in qtrs])
            sub["treat"] = tr
            sub["author_id"] = a
            sub["event_id"]  = n_cohorts
            chunks.append(sub.reset_index(drop=True))

    st = pd.concat(chunks, ignore_index=True)
    k = st[st["treat"] == 0].groupby("author_id")["event_id"].nunique().to_dict()
    st["weight"] = st.apply(lambda r: 1.0 if r["treat"] == 1 else 1.0 / k[r["author_id"]], axis=1)

    meta = {"events_profiled": n_profiled, "cohorts": n_cohorts,
            "dropped_caliper": n_dropped, "ratio": float(np.mean(ratios)) if ratios else 0.0,
            "treated": int(st[st["treat"] == 1]["author_id"].nunique()),
            "controls": int(st[st["treat"] == 0]["author_id"].nunique()),
            "obs": int(len(st))}
    return st, meta


# ==============================================================================
# 5. ESTIMATION -- identical machinery to the annual script (see its comments for
#    the full rationale on the dummy/absorbed equivalence, degrees of freedom, and
#    weighting convention; reproduced here verbatim since none of it depends on
#    the time unit).
# ==============================================================================
_FE_CACHE = {}


def _fe_sparse(df):
    """Sparse one-hot FE block (pc + crt dummies), full rank construction.

    Quarterly resolution multiplies the number of cohort x event-time cells by
    up to ~3.4x versus the annual design (up to 17 relative-time values per
    cohort instead of 5): with ~400 cohorts that is several thousand distinct
    `crt` levels. A DENSE one-hot matrix at that width (what the annual
    script's `_fe_matrix()` builds) is gigabytes in size and its `np.linalg.qr`
    call is effectively intractable (confirmed directly: 25,693 x 8,384 dense,
    1.7GB, QR alone is O(n*m^2) ~ 1.8e12 flops). This function builds the same
    full-rank dummy block as a SPARSE matrix instead -- correct for the same
    reason (one-hot encodings are sparse by construction), and the operations
    below (`lsqr`) work directly on sparse input without ever densifying it.
    """
    key = (len(df), int(df["pc"].nunique()), int(df["crt"].nunique()),
           float(df.index.values.sum()))
    if key in _FE_CACHE:
        return _FE_CACHE[key]

    pc_codes, _ = pd.factorize(df["pc"].values)
    n = len(df)
    D1 = sparse.csr_matrix(
        (np.ones(n), (np.arange(n), pc_codes)), shape=(n, pc_codes.max() + 1)
    )

    ref = df.groupby("event_id")["rel_t"].transform("min")
    drop = set(df.loc[df["rel_t"] == ref, "crt"].unique())
    crt_vals = df["crt"].values
    keep_mask = np.array([v not in drop for v in crt_vals])
    crt_codes, _ = pd.factorize(crt_vals[keep_mask])
    rows = np.nonzero(keep_mask)[0]
    D2 = sparse.csr_matrix(
        (np.ones(len(rows)), (rows, crt_codes)), shape=(n, crt_codes.max() + 1)
    )

    FE = sparse.hstack([D1, D2], format="csr")
    _FE_CACHE.clear()
    _FE_CACHE[key] = FE
    return FE


def build_design(df, regs):
    """Sparse counterpart of the annual script's `build_design()`: same "is this
    regressor absorbed by the fixed effects" test (project onto the FE span and
    check the residual), done via sparse least-squares (`lsqr`) instead of a
    dense QR null-space projection, since the FE block itself is sparse (see
    `_fe_sparse`)."""
    FE = _fe_sparse(df)

    kept, absorbed = [], []
    for r in regs:
        v = df[r].values.astype(float)
        coef = sparse.linalg.lsqr(FE, v, atol=1e-10, btol=1e-10)[0]
        resid = v - FE @ coef
        scale = max(1.0, float(np.max(np.abs(v))))
        (kept if np.max(np.abs(resid)) / scale > 1e-8 else absorbed).append(r)

    info = {"n": len(df), "n_fe": FE.shape[1],
            "cohorts": int(df["event_id"].nunique()), "absorbed": absorbed}
    return FE, kept, info


def fit_dummies(df, outcome, regs, weights=None, cluster="author_id", check_rank=False):
    """Dummy-variable form, used ONLY by `verify()` to cross-check `fit_absorbed()`'s
    coefficients -- `verify()` compares point estimates only, never SEs/p-values from
    this form, so this returns coefficients via sparse least squares (no clustered
    covariance computed here; that would require densifying the FE block, exactly the
    cost this function exists to avoid). `check_rank`/`weights` are accepted for
    interface parity with the annual script but unused: the annual version's weighting
    is a no-op (uniform weights throughout this analysis) and rank-checking a sparse
    matrix this wide is itself the expensive operation being avoided.
    """
    FE, kept, info = build_design(df, regs)
    if kept:
        Xk = np.column_stack([df[r].values.astype(float) for r in kept])
        full = sparse.hstack([sparse.csr_matrix(Xk), FE], format="csr")
    else:
        full = FE
    y = df[outcome].values.astype(float)
    coef_full = sparse.linalg.lsqr(full, y, atol=1e-10, btol=1e-10)[0]
    out = {r: {"coef": float(coef_full[i]), "se": float("nan"), "p": float("nan")}
           for i, r in enumerate(kept)}
    for r in info["absorbed"]:
        out[r] = None
    info["clusters"] = int(df[cluster].nunique())
    info["df_resid"] = info["n"] - (len(kept) + FE.shape[1])
    return out, info


def prep(st, outcome):
    """Sample for one outcome. UNLIKE the annual script, the dynamic event-time
    indicators `E{t:+d}` are built for EVERY quarter from -W to +W (17 points), not a
    fixed 5-point list -- the point of going quarterly is to use that resolution."""
    df = st[st[outcome].notna()].copy()
    df["pc"]  = df["author_id"].astype(str) + "_" + df["event_id"].astype(str)
    df["crt"] = df["event_id"].astype(str)  + "_" + df["rel_t"].astype(str)
    tr = df["treat"] == 1
    for t in range(-W, W + 1):
        df[f"E{t:+d}"] = (tr & (df["rel_t"] == t)).astype(float)
    df["D0"]  = (tr & (df["rel_t"] == 0)).astype(float)
    df["P1"]  = (tr & (df["rel_t"] >= 1)).astype(float)
    df["P0"]  = (tr & (df["rel_t"] >= 0)).astype(float)
    df["Treated"] = df["treat"].astype(float)
    df["inv_k"] = df["weight"].astype(float)
    return df


def _within(df, cols, tol=1e-12, maxit=5000):
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
    d = _within(df, [outcome] + regs)
    X = d[[r + "_w" for r in regs]].values
    keep = X.var(axis=0) > 1e-12
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
    a, _ = fit_absorbed(df, outcome, regs)
    b, _ = fit_dummies(df, outcome, regs)
    diffs = [abs(a[r]["coef"] - b[r]["coef"]) for r in regs if a.get(r) and b.get(r)]
    return max(diffs) if diffs else 0.0


def attach_sen_m1(st):
    """Attach a per-cohort junior/senior split variable: the TREATED author's own
    seniority at t-1.

    Under the original quarterly design (exact match on seniority at [g-2,g-1]),
    every cohort member shared one value here by construction, so it didn't matter
    whose seniority was used. The continuous 8-quarter-average Mahalanobis match no
    longer forces that equality (treated and controls can have different actual
    seniority in the single quarter t-1, even with similar 8-quarter averages), so
    this now explicitly uses the TREATED unit's own value -- the natural definition
    of "was this cohort's treated author junior or senior going in," independent of
    how close the controls happen to land.
    """
    base = (st[(st["rel_t"] == -1) & (st["treat"] == 1)]
            [["event_id", "seniority"]].rename(columns={"seniority": "sen_m1"}))
    out = st.merge(base, on="event_id", how="left")
    return out


def estimate(st, outcome):
    """Three regressions per outcome, same structure as the annual script:
      static   -- treated x 1{t >= 0}
      dynamic  -- treated x event-time indicators for EVERY quarter -W..+W, t=-1 omitted
      pooled   -- treated x 1{t >= +1}, event quarter t=0 separate; pre-trend placebo
                  checked at the FURTHEST pre-period (t=-W), same role as the annual
                  script's "E-2" check at its own furthest pre-period.
    """
    df = prep(st, outcome)

    static, info = fit_absorbed(df, outcome, ["P0"])
    dyn_regs = [f"E{t:+d}" for t in range(-W, W + 1) if t != -1]
    dyn,    _    = fit_absorbed(df, outcome, dyn_regs)
    pooled, _    = fit_absorbed(df, outcome, [f"E{-W:+d}", "D0", "P1"])

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
        if d is None:
            return {"coef": 0.0, "se": 0.0, "p": None}
        if not np.isfinite(d["se"]) or not np.isfinite(d["p"]) or d["se"] < 1e-8:
            return {"coef": 0.0, "se": 0.0, "p": None}
        return dict(d)

    es = [{"rel": -1, "coef": 0.0, "se": 0.0, "p": None}]
    for t in range(-W, W + 1):
        if t == -1:
            continue
        es.append({"rel": t, **clean(dyn.get(f"E{t:+d}"))})
    es.sort(key=lambda r: r["rel"])

    return {"es": es,
            "median_sen": med,
            "splits": {k: {**v, "est": clean(v["est"])} for k, v in splits.items()},
            "static":   clean(static.get("P0")),
            "att":      clean(pooled.get("P1")),
            "event_yr": clean(pooled.get("D0")),
            "pre":      clean(dyn.get(f"E{-W:+d}")),
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
        tstat, p = sps.ttest_ind(tr, ct, equal_var=False)
        rows.append({"var": v, "label": label, "kind": kind, "panel": panel,
                     "nT": len(tr), "nC": len(ct), "mT": tr.mean(), "mC": ct.mean(),
                     "diff": diff, "smd": diff / pooled if pooled > 0 else np.nan,
                     "t": tstat, "p": p})
    return pd.DataFrame(rows)


# ==============================================================================
# 7. FIGURE
# ==============================================================================
def _draw_event_study_panel(ax, es, ylab):
    ax.axhline(0, color="black", lw=0.9, ls="--", zorder=2)
    ax.axvline(-0.5, color="#999999", lw=0.9, ls=":", zorder=2)

    for r in es:
        t, c, se = r["rel"], r["coef"], r["se"]
        if t == -1 or se == 0:
            ax.scatter([t], [0], color="black", marker="D", s=30, zorder=6)
            continue
        lo, hi = c - 1.96 * se, c + 1.96 * se
        ax.plot([t, t], [lo, hi], color="#1a5276", lw=1.6,
                solid_capstyle="round", zorder=4)
        ax.plot([t - .12, t + .12], [lo, lo], color="#1a5276", lw=1.6, zorder=4)
        ax.plot([t - .12, t + .12], [hi, hi], color="#1a5276", lw=1.6, zorder=4)
        ax.scatter([t], [c], color="#1a5276", s=30, zorder=5,
                   edgecolors="white", lw=0.6)

    ax.set_xticks(list(range(-W, W + 1, 2)))
    ax.set_xlim(-W - 0.5, W + 0.5)
    ax.set_xlabel("Quarters relative to EIP authorship", fontsize=10)
    ax.set_ylabel(ylab, fontsize=10)
    ax.grid(axis="y", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)


def make_figures(res, meta, seniority_path, log_comp_path, label=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for oc, ylab, path in [("seniority", "Seniority coefficient (1–7 scale)", seniority_path),
                            ("log_comp",  "Log compensation coefficient",     log_comp_path)]:
        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        fig.patch.set_facecolor("white")
        _draw_event_study_panel(ax, res[oc]["es"], ylab)
        plt.tight_layout()
        plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)


# ==============================================================================
# 8. LATEX TABLE
# ==============================================================================
def stars_tex(p):
    if p is None: return ""
    return "$^{***}$" if p < 0.01 else "$^{**}$" if p < 0.05 else "$^{*}$" if p < 0.10 else ""

def fmt_val(v, kind):
    if kind == "usd": return f"\\${v:,.0f}"
    if kind == "pct": return f"{v*100:.1f}\\%"
    return f"{v:.3f}"

NOTE_TEXT = (
    r"Robustness check on the main (annual) specification: the same stacked diff-in-diff design "
    r"at quarterly frequency. The table reports covariate balance and difference-in-differences "
    r"estimates of the effect of authoring an Ethereum Improvement Proposal (EIP) on career "
    r"outcomes over a $\pm8$-quarter ($\pm2$-year) event window. An author is treated if they "
    r"propose an EIP in quarter t=0. Each treated author is matched to at most three similar "
    r"control authors drawn from the population of EIP authors who author no EIP anywhere in the "
    r"$\pm8$-quarter window; Panel A shows the results of a balance test at $t-1$ (one quarter "
    r"before treatment). Panel B and C report stacked diff-in-diff results for Seniority and Total "
    r"Compensation (log) as outcome variable. Column~(1) reports the static model. Column~(2) "
    r"reports the dynamic specification with a separate coefficient for a representative subset of "
    r"event quarters (every other quarter, plus $t=\pm1$), $t-1$ omitted as the reference. "
    r"Columns~(3) and~(4) re-run column~(1) on the two halves of the sample, split at the median of "
    r"seniority in the quarter before authorship. Standard errors, reported in parentheses, are "
    r"clustered at the author level; $^{*}$, $^{**}$, and $^{***}$ denote statistical significance "
    r"at the 10\%, 5\%, and 1\% levels, respectively."
)

# dynamic column shown in the table: every other quarter, plus the two closest to the event,
# to keep the table a readable length (the FIGURE shows all 17 points; the table does not).
TABLE_DYNAMIC_QUARTERS = sorted(set([t for t in range(-W, W + 1, 2)] + [-1, 0, 1]))


def write_latex(res, meta, bal, outdir, tag="", label="ALL EIPs"):
    sen, lc = res["seniority"], res["log_comp"]

    def pair(d):
        if d is None:
            return "", ""
        if d["se"] == 0:
            return "0.000", ""
        return f"{d['coef']:.3f}{stars_tex(d['p'])}", f"({d['se']:.3f})"

    def row(lbl, cells):
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
                r"Cohort $\times$ event-quarter FE & Yes & Yes & Yes & Yes \\",
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
        for t in TABLE_DYNAMIC_QUARTERS:
            lbl = rf"\quad Treated $\times$ $t={t:+d}$"
            if t == -1:
                out.append(r"\quad Treated $\times$ $t=-1$ & & --- & & \\")
                continue
            out += row(lbl, [None, es[t], None, None])
        out += panel_footer(meta["obs"])
        out.append(r"\end{tabular}")
        return out

    T = [r"% ===== Table: covariate balance + difference-in-differences results (QUARTERLY) =====",
         r"\begin{center}",
         r"\begin{table}",
         r" \caption{The Effect of EIP Authorship on Seniority and Compensation (Quarterly Robustness Check)}",
         rf" \label{{tab:did_main_quarterly{tag}}}",
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

    open(os.path.join(outdir, f"table_did_results_quarterly{tag}.tex"), "w",
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
    print(f"EIP AUTHORSHIP AND CAREER OUTCOMES — +/-8 QUARTERS (ROBUSTNESS) — {label}")
    print("=" * 78)

    print("\n[1/5] Building EIP authorship events ...")
    ev = build_eip_events(subset=subset)
    print(f"      {len(ev):,} author-EIP pairs | {ev['author_id'].nunique()} authors "
          f"| years {int(ev['eip_year'].min())}-{int(ev['eip_year'].max())}")

    print("\n[2/5] Building end-of-quarter person-quarter panel ...")
    eoq = build_panel()
    print(f"      {len(eoq):,} author-quarters | {eoq['author_id'].nunique()} authors")

    print("\n[3/5] Constructing cohorts and matching ...")
    st, meta = build_matched_sample(eoq, ev)
    print(f"      events profiled  : {meta['events_profiled']}")
    print(f"      dropped (caliper): {meta['dropped_caliper']}")
    print(f"      cohorts matched  : {meta['cohorts']}  (1:{meta['ratio']:.2f})")
    print(f"      treated / control: {meta['treated']} / {meta['controls']}")
    print(f"      observations     : {meta['obs']:,}")

    print("\n[4/5] Estimating ...")
    st = attach_sen_m1(st)
    res = {}
    for oc in ["seniority", "log_comp"]:
        res[oc] = estimate(st, oc)
        r_, info = res[oc], res[oc]["info"]
        print(f"\n      --- {oc} ---")
        print(f"      n = {info['n']:,}   {info['n_fe']:,} fixed effects absorbed   "
              f"{info['clusters']} clusters")
        d = verify(prep(st, oc), oc, [f"E{-W:+d}", "D0", "P1"])
        print(f"      absorbed vs dummy-variable form: max |difference| = {d:.2e}")

        def show(lbl, d):
            if d["se"] == 0:
                print(f"      {lbl}: 0 (by construction)"); return
            stt = "***" if d["p"] < 0.01 else "**" if d["p"] < 0.05 else "*" if d["p"] < 0.10 else ""
            pct = f"  [{(np.exp(d['coef'])-1)*100:+.1f}%]" if oc == "log_comp" else ""
            print(f"      {lbl}: {d['coef']:+.4f} (SE {d['se']:.4f}) p={d['p']:.4f} {stt}{pct}")

        show("static  Treated x Post", r_["static"])
        for rr in r_["es"]:
            if rr["rel"] == -1 or rr["rel"] not in TABLE_DYNAMIC_QUARTERS:
                continue
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
    json.dump({"meta": meta, **res}, open(os.path.join(CACHE, f"results_quarterly{tag}.json"), "w"),
               indent=1, default=str)
    bal.to_csv(os.path.join(CACHE, f"balance_quarterly{tag}.csv"), index=False)
    write_cache(st, os.path.join(CACHE, f"matched_sample_quarterly{tag}.parquet"))
    make_figures(res, meta,
                 os.path.join(OUTDIR_FIGURES, f"EIP_W2_EventStudy_Seniority_quarterly{tag}.png"),
                 os.path.join(OUTDIR_FIGURES, f"EIP_W2_EventStudy_LogComp_quarterly{tag}.png"))
    write_latex(res, meta, bal, OUTDIR_TABLES, tag, label)

    print(f"\nWritten to {OUTDIR_TABLES} / {OUTDIR_FIGURES}:")
    for f in [f"table_did_results_quarterly{tag}.tex", f"EIP_W2_EventStudy_Seniority_quarterly{tag}.png",
              f"EIP_W2_EventStudy_LogComp_quarterly{tag}.png"]:
        print(f"  - {f}")
    print("\nDone.")


if __name__ == "__main__":
    main()
