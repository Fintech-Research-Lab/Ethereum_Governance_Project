"""
client_commits.py
===================

Single shared loader for the four Ethereum execution-client git-commit datasets (Geth,
Besu, Erigon, Nethermind), for the "Decentralized Crypto Governance?" replication package
(Fracassi, Khoja, Schar, 2024, SSRN 4691000).

Each client's commit history is stored as one Parquet file:

    config.DATA_RAW / "commits" / "client_commit" / f"{client}_commits.parquet"

These files are produced by a separate, parallel data-collection task and may not exist yet
at the time this module is written/imported -- that is fine; this module only needs to be
correct once they exist. Nothing here reads a file at import time.

Used by at least three analyses:
    - Client Analysis / Figure 20 (per-client commit concentration)
    - Anonymity Analysis / Figure 4
    - Top10-in-community

Why this module exists
-----------------------
Every one of the analyses above needs to load all four client commit files, so this gives
them one shared, correct loader instead of three independent copies of the same loading
logic (a file-swap bug had crept into two of the original project's three copies of this
code; this port does not reproduce it).
"""

from __future__ import annotations

import warnings

import polars as pl

import config

VALID_CLIENTS: tuple[str, ...] = ("geth", "besu", "erigon", "nethermind")


def _client_parquet_path(client: str) -> "config.Path":  # type: ignore[name-defined]
    """Return the expected Parquet path for a given client name (no existence check)."""
    return config.DATA_RAW / "commits" / "client_commit" / f"{client}_commits.parquet"


def load_client_commits(client: str, reproduce_original_bug: bool = False) -> pl.DataFrame:
    """
    Load one execution client's git-commit history from
    `config.DATA_RAW / "commits" / "client_commit" / f"{client}_commits.parquet"`.

    Parameters
    ----------
    client : str
        One of `"geth"`, `"besu"`, `"erigon"`, `"nethermind"`. Any other value raises
        `ValueError`.
    reproduce_original_bug : bool, default False
        The original project had a file-swap bug where two of its three scripts loaded
        Erigon's data from `besu_commits.dta` instead of `erigon_commits.dta`. This loader
        always returns each client's own correct data by default. Pass `True` only to
        reproduce that original bug for a side-by-side comparison against the published
        paper's Figure 4/5, which were generated from the Besu-as-Erigon data.

    Returns
    -------
    pl.DataFrame
        The requested client's raw commit-level data (one row per commit), exactly as
        stored in the source Parquet file -- no filtering or transformation is applied here.

    Raises
    ------
    ValueError
        If `client` is not one of the four valid client names.

    Notes
    -----
    This function only reads the Parquet file; it does not validate its schema or
    contents. Callers should not assume any particular column set beyond what the
    upstream data-collection task documents.
    """
    if client not in VALID_CLIENTS:
        raise ValueError(f"client must be one of {VALID_CLIENTS!r}, got {client!r}.")

    if client == "erigon" and reproduce_original_bug:
        warnings.warn(
            "load_client_commits('erigon', reproduce_original_bug=True): loading "
            "besu_commits.parquet instead of erigon_commits.parquet, to reproduce a bug in "
            "the original project's 'Anonymity Analysis.py' and 'Top10_in_community.py'. "
            "This is for side-by-side comparison against the published paper only -- the "
            "default (reproduce_original_bug=False) loads Erigon's own data.",
            stacklevel=2,
        )
        path = _client_parquet_path("besu")
    else:
        path = _client_parquet_path(client)

    return pl.read_parquet(path)


def load_all_client_commits(reproduce_original_bug: bool = False) -> dict[str, pl.DataFrame]:
    """
    Load all four execution clients' commit histories at once.

    Convenience wrapper around `load_client_commits`, calling it once per client in
    `VALID_CLIENTS` and collecting the results into a dict.

    Parameters
    ----------
    reproduce_original_bug : bool, default False
        Forwarded to `load_client_commits` for every client -- see that function's
        docstring.

    Returns
    -------
    dict[str, pl.DataFrame]
        `{"geth": ..., "besu": ..., "erigon": ..., "nethermind": ...}`, one DataFrame per
        client.
    """
    return {
        client: load_client_commits(client, reproduce_original_bug=reproduce_original_bug)
        for client in VALID_CLIENTS
    }


# NOTE: exercised by the analysis scripts that import this module (Client Analysis, Anonymity
# Analysis, Top10-in-community) once data/raw/commits/client_commit/*.parquet exist.
